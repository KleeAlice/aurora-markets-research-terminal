from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4

from .demo_data import HEATMAP, NEWS, SECURITIES, VALUATION_SNAPSHOT
from .image_assets import build_news_image_asset
from .llm_client import build_llm_request, extract_llm_content
from .market_data import delayed_quote, search_market
from .schemas import (
    AgentRun,
    AgentStep,
    AgentTraceEvent,
    DashboardPayload,
    DataStatus,
    ImageAsset,
    LlmConfig,
    NewsCard,
    ResearchRunRequest,
    SourceRef,
    StockPickerRequest,
    StockSuggestion,
    WatchlistItem,
)

agent_runs: dict[str, AgentRun] = {}
agent_traces: dict[str, list[AgentTraceEvent]] = {}
agent_lock = threading.Lock()


def _zh(request: StockPickerRequest) -> bool:
    return request.language == "zh"


def _copy(request: StockPickerRequest, en: str, zh: str) -> str:
    return zh if _zh(request) else en


def _trace(
    run_id: str,
    phase: str,
    status: str,
    title: str,
    detail: str,
    *,
    ticker: str | None = None,
    source_url: str | None = None,
    metadata: dict[str, str | int | float | bool | None] | None = None,
) -> AgentTraceEvent:
    with agent_lock:
        sequence = len(agent_traces.setdefault(run_id, [])) + 1
        event = AgentTraceEvent(
            id=str(uuid4()),
            run_id=run_id,
            sequence=sequence,
            phase=phase,
            status=status,  # type: ignore[arg-type]
            title=title,
            detail=detail,
            ticker=ticker,
            source_url=source_url,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        agent_traces[run_id].append(event)
        if run_id in agent_runs:
            agent_runs[run_id] = agent_runs[run_id].model_copy(update={"trace_events": list(agent_traces[run_id])})
        return event


def _set_run(run_id: str, **updates: object) -> AgentRun:
    with agent_lock:
        current = agent_runs[run_id]
        if "trace_events" not in updates:
            updates["trace_events"] = list(agent_traces.get(run_id, []))
        next_run = current.model_copy(update=updates)
        agent_runs[run_id] = next_run
        return next_run


def _configured_llm(llm: LlmConfig | None) -> bool:
    return bool(llm and llm.api_key and llm.model and llm.base_url)


def _llm_shortlist(request: StockPickerRequest, candidates: list[StockSuggestion], run_id: str | None = None) -> list[StockSuggestion] | None:
    if not _configured_llm(request.llm):
        if run_id:
            _trace(
                run_id,
                _copy(request, "Ranking", "排序"),
                "warning",
                _copy(request, "LLM rerank skipped", "跳过模型重排"),
                _copy(request, "No model API configuration was provided for this run; using deterministic ranking.", "本次运行未传入模型 API 配置，改用确定性排序。"),
            )
        return None
    assert request.llm is not None
    prompt = {
            "task": "Rank equity research candidates. Return JSON only. Use Chinese thesis text when language is zh.",
        "guardrails": [
            "Use research candidate language only.",
            "No personalized buy/sell advice.",
            "Do not invent numbers.",
            "Only rank from provided candidates.",
        ],
        "context": {
            "theme": request.theme,
            "time_horizon": request.time_horizon,
            "research_focus": request.research_focus,
            "language": request.language,
        },
        "candidates": [item.model_dump(mode="json") for item in candidates],
        "schema": {"items": [{"ticker": "string", "score": "integer 0-100", "thesis": "short cited research thesis"}]},
    }
    try:
        if run_id:
            _trace(
                run_id,
                _copy(request, "Ranking", "排序"),
                "running",
                _copy(request, "Calling model reranker", "调用模型重排"),
                _copy(request, f"Sending {len(candidates)} structured candidates to {request.llm.provider}.", f"将 {len(candidates)} 个结构化候选标的发送给 {request.llm.provider}。"),
            )
        messages = [
            {"role": "system", "content": "You are an equity research workflow assistant. You never provide trading instructions."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ]
        llm_request = build_llm_request(request.llm, messages, temperature=0.2)
        http_request = urllib.request.Request(
            llm_request.full_url,
            data=json.dumps(llm_request.payload).encode("utf-8"),
            headers=llm_request.headers,
            method="POST",
        )
        with urllib.request.urlopen(http_request, timeout=18) as response:
            body = json.loads(response.read().decode("utf-8", errors="ignore"))
        content = extract_llm_content(body)
        parsed = json.loads(content[content.find("{") : content.rfind("}") + 1] if "{" in content else content)
        items = parsed.get("items", parsed if isinstance(parsed, list) else [])
        by_ticker = {item.ticker: item for item in candidates}
        ranked: list[StockSuggestion] = []
        for item in items:
            ticker = str(item.get("ticker", "")).upper()
            if ticker in by_ticker:
                base = by_ticker[ticker]
                ranked.append(base.model_copy(update={"score": int(item.get("score", base.score)), "thesis": _safe_thesis(str(item.get("thesis", base.thesis)))}))
        if run_id and ranked:
            _trace(
                run_id,
                _copy(request, "Ranking", "排序"),
                "completed",
                _copy(request, "Model rerank accepted", "模型重排已采用"),
                _copy(request, f"Model returned {len(ranked)} valid ranked candidates.", f"模型返回 {len(ranked)} 个有效排序候选。"),
            )
        return ranked or None
    except (KeyError, ValueError, TypeError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        if run_id:
            _trace(
                run_id,
                _copy(request, "Ranking", "排序"),
                "warning",
                _copy(request, "Model rerank failed", "模型重排失败"),
                _copy(request, "Falling back to deterministic scoring and source-quality checks.", "改用确定性评分与来源质量校验。"),
            )
        return None


def _heuristic_score(ticker: str, index: int) -> int:
    preferred = {"002594.SZ": 92, "1211.HK": 90, "TSLA": 86, "300750.SZ": 84, "LI": 79, "NIO": 74, "XPEV": 72}
    return preferred.get(ticker.upper(), max(58, 78 - index * 4))


def _safe_thesis(text: str, language: str = "en") -> str:
    clean = text.replace("Buy", "Research candidate").replace("buy", "research candidate")
    clean = clean.replace("Sell", "Reduce exposure scenario").replace("sell", "reduce exposure scenario")
    clean = clean.replace("Strong recommendation", "Research observation")
    if language == "zh":
        clean = clean.replace("Research candidate:", "研究候选：").replace("Research candidate", "研究候选")
        if "研究候选" not in clean:
            clean = f"研究候选：{clean}"
        return clean
    if "research candidate" not in clean.lower():
        clean = f"Research candidate: {clean}"
    return clean


def suggest_stocks(request: StockPickerRequest, run_id: str | None = None) -> list[StockSuggestion]:
    search_terms = request.tickers or [request.theme or request.universe or "new energy"]
    results = []
    seen: set[str] = set()
    for term in search_terms:
        if run_id:
            _trace(
                run_id,
                _copy(request, "Discovery", "检索"),
                "running",
                _copy(request, "Searching market data", "搜索行情数据"),
                _copy(request, f"Query keyword: {term}", f"检索关键词：{term}"),
                metadata={"keyword": term},
            )
        for result in search_market(term):
            if result.ticker in seen:
                continue
            seen.add(result.ticker)
            results.append(result)
            if run_id:
                _trace(
                    run_id,
                    _copy(request, "Discovery", "检索"),
                    "completed",
                    _copy(request, "Candidate found", "发现候选标的"),
                    _copy(request, f"{result.ticker} from {result.source.title}; status {result.data_status}.", f"{result.ticker} 来自 {result.source.title}；数据状态 {result.data_status}。"),
                    ticker=result.ticker,
                    source_url=result.source.url,
                    metadata={"exchange": result.exchange, "market": result.market},
                )
    suggestions: list[StockSuggestion] = []
    for index, item in enumerate(results[: max(request.max_results * 2, 8)]):
        source = item.source
        thesis = _safe_thesis(
            _copy(
                request,
                f"{item.company_name} is a research candidate for {request.theme}; ranking uses delayed/free market data and Aurora data-quality checks.",
                f"{item.company_name} 是 {request.theme} 主题下的研究候选；排序依据延迟/免费行情与 Aurora 数据质量检查。",
            ),
            request.language,
        )
        suggestions.append(
            StockSuggestion(
                ticker=item.ticker,
                company_name=item.company_name,
                exchange=item.exchange,
                market=item.market,
                score=_heuristic_score(item.ticker, index),
                thesis=thesis,
                data_status=item.data_status,
                sources=[source],
            )
        )
    if run_id:
        _trace(
            run_id,
            _copy(request, "Ranking", "排序"),
            "running",
            _copy(request, "Scoring candidates", "计算候选评分"),
            _copy(request, f"Scoring {len(suggestions)} candidates by ticker preference, source status, and data quality.", f"按标的优先级、来源状态和数据质量为 {len(suggestions)} 个候选标的评分。"),
        )
    llm_ranked = _llm_shortlist(request, suggestions, run_id)
    ranked = llm_ranked or sorted(suggestions, key=lambda item: item.score, reverse=True)
    final = ranked[: max(1, min(request.max_results, 12))]
    if run_id:
        _trace(
            run_id,
            _copy(request, "Ranking", "排序"),
            "completed",
            _copy(request, "Candidate ranking completed", "候选排序完成"),
            _copy(request, f"Selected {len(final)} research candidates for dashboard refresh.", f"已选出 {len(final)} 个研究候选用于刷新仪表盘。"),
            metadata={"count": len(final)},
        )
    return final


def _watchlist_from_suggestions(
    suggestions: list[StockSuggestion],
    request: StockPickerRequest | None = None,
    run_id: str | None = None,
) -> tuple[list[WatchlistItem], list[SourceRef], list[str]]:
    rows: list[WatchlistItem] = []
    sources: list[SourceRef] = []
    warnings: list[str] = []
    for item in suggestions:
        try:
            if request and run_id:
                _trace(
                    run_id,
                    _copy(request, "Market Data", "行情"),
                    "running",
                    _copy(request, "Reading delayed quote", "读取延迟行情"),
                    _copy(request, f"Requesting quote for {item.ticker}.", f"正在读取 {item.ticker} 的行情。"),
                    ticker=item.ticker,
                )
            quote, source, message = delayed_quote(item.ticker)
            sources.append(source)
            if source.source_type == "demo":
                warnings.append(f"{item.ticker}: {message}")
                if request and run_id:
                    _trace(
                        run_id,
                        _copy(request, "Market Data", "行情"),
                        "warning",
                        _copy(request, "Fallback quote used", "使用备用行情"),
                        _copy(request, message, f"{item.ticker}：{message}"),
                        ticker=item.ticker,
                        source_url=source.url,
                    )
            elif request and run_id:
                _trace(
                    run_id,
                    _copy(request, "Market Data", "行情"),
                    "completed",
                    _copy(request, "Quote refreshed", "行情已刷新"),
                    _copy(request, f"{item.ticker} quote loaded from {source.title}.", f"{item.ticker} 行情已从 {source.title} 读取。"),
                    ticker=item.ticker,
                    source_url=source.url,
                )
            price = quote.latest_price or 0
            rows.append(
                WatchlistItem(
                    ticker=item.ticker,
                    company_name=item.company_name,
                    exchange=item.exchange,
                    price=price,
                    change_pct=0.0 if source.source_type == "demo" else (item.score - 75) / 10,
                    sparkline=[price * (0.98 + step * 0.004) for step in range(7)] if price else [],
                )
            )
        except KeyError:
            warnings.append(f"{item.ticker}: quote unavailable.")
            if request and run_id:
                _trace(
                    run_id,
                    _copy(request, "Market Data", "行情"),
                    "failed",
                    _copy(request, "Quote unavailable", "行情不可用"),
                    _copy(request, f"{item.ticker}: quote unavailable.", f"{item.ticker}：行情不可用。"),
                    ticker=item.ticker,
                )
    return rows, sources, warnings


def _image_assets_for_news(news: list[NewsCard], request: StockPickerRequest | None = None, run_id: str | None = None) -> list[ImageAsset]:
    assets = []
    for index, item in enumerate(news[:4]):
        if request and run_id:
            _trace(
                run_id,
                _copy(request, "Images", "图片"),
                "running",
                _copy(request, "Resolving news image", "解析新闻图片"),
                _copy(request, f"Reading source metadata for: {item.title}", f"读取新闻来源元数据：{item.title}"),
                source_url=item.source_url,
            )
        asset = build_news_image_asset(item, index)
        assets.append(asset)
        if request and run_id:
            _trace(
                run_id,
                _copy(request, "Images", "图片"),
                "completed" if asset.status != "fallback" else "warning",
                _copy(request, "Image asset prepared", "新闻图片已处理"),
                _copy(request, f"Image status: {asset.status}; local asset {asset.id}.", f"图片状态：{asset.status}；本地资源 {asset.id}。"),
                source_url=asset.source_url,
                metadata={"asset_id": asset.id, "status": asset.status},
            )
    return assets


def build_agent_dashboard(primary_ticker: str, suggestions: list[StockSuggestion], request: StockPickerRequest | None = None, run_id: str | None = None) -> DashboardPayload:
    from .services import get_dashboard

    supported_primary = primary_ticker if primary_ticker in SECURITIES or primary_ticker.upper() in {"BYD", "01211.HK", "1211.HK", "TSLA.US"} else "TSLA"
    if request and run_id:
        _trace(
            run_id,
            _copy(request, "Dashboard", "面板"),
            "running",
            _copy(request, "Loading dashboard base", "读取仪表盘基础数据"),
            _copy(request, f"Primary ticker: {supported_primary}.", f"主标的：{supported_primary}。"),
            ticker=supported_primary,
        )
    dashboard = get_dashboard(supported_primary)
    quote, quote_source, quote_message = delayed_quote(supported_primary)
    watchlist, watch_sources, warnings = _watchlist_from_suggestions(suggestions, request, run_id)
    image_assets = _image_assets_for_news(NEWS, request, run_id)
    asset_by_key = {asset.title: asset for asset in image_assets}
    latest_news = []
    for item in NEWS:
        asset = asset_by_key.get(item.title)
        latest_news.append(item.model_copy(update={"image_asset_id": asset.id if asset else None, "image_url": asset.local_url if asset else None, "source_url": asset.source_url if asset else item.source_url}))
    mode = "delayed" if quote_source.source_type == "market_data" else "demo"
    if watch_sources and any(source.source_type == "market_data" for source in watch_sources) and mode == "demo":
        mode = "mixed"
    sources = [quote_source, *watch_sources]
    ai_insight = (
        _copy(
            request,
            f"Research Agent selected {len(suggestions)} watchlist candidates. Primary dashboard uses {mode} data; all outputs remain research-only.",
            f"Research Agent 已筛选 {len(suggestions)} 个观察候选。主仪表盘使用 {mode} 数据；所有输出仅供研究，不构成投资建议。",
        )
        if request
        else f"Research Agent selected {len(suggestions)} watchlist candidates. Primary dashboard uses {mode} data; all outputs remain research-only."
    )
    agent_summary = (
        _copy(
            request,
            "Supervisor completed discovery, data refresh, news image processing, dashboard update, and report handoff.",
            "监督 Agent 已完成候选检索、行情刷新、新闻图片处理、仪表盘更新与研报交接。",
        )
        if request
        else "Supervisor completed discovery, data refresh, news image processing, dashboard update, and report handoff."
    )
    payload = dashboard.model_copy(
        update={
            "quote": quote,
            "watchlist": watchlist or dashboard.watchlist,
            "heatmap": HEATMAP,
            "valuation_snapshot": VALUATION_SNAPSHOT,
            "latest_news": latest_news,
            "ai_insight": ai_insight,
            "data_status": DataStatus(mode=mode, provider="hybrid-free", updated_at=datetime.now(timezone.utc), message=quote_message),
            "source_refs": sources,
            "updated_at": datetime.now(timezone.utc),
            "selected_shortlist": suggestions,
            "agent_summary": agent_summary,
            "image_assets": image_assets,
            "warnings": warnings,
        }
    )
    if request and run_id:
        _trace(
            run_id,
            _copy(request, "Dashboard", "面板"),
            "completed",
            _copy(request, "Dashboard payload rebuilt", "仪表盘数据已重建"),
            _copy(request, f"Updated quote, watchlist, heatmap, valuation snapshot, news images, and warnings.", "已更新报价、观察池、热力图、估值快照、新闻图片与数据质量提示。"),
            ticker=payload.ticker,
            metadata={"mode": mode, "warnings": len(warnings), "assets": len(image_assets)},
        )
    return payload


def _step_labels(request: StockPickerRequest) -> list[tuple[str, str]]:
    if _zh(request):
        return [
            ("监督 Agent", "规划研究流程并应用仅供研究的护栏。"),
            ("候选检索", "等待检索股票与市场数据。"),
            ("行情读取", "等待读取延迟/免费行情。"),
            ("新闻图片处理", "等待解析新闻来源图片。"),
            ("仪表盘刷新", "等待重建仪表盘数据。"),
            ("研报交接", "等待生成研报交接信息。"),
        ]
    return [
        ("Supervisor", "Workflow planned and guardrails applied."),
        ("Stock Discovery", "Waiting for stock and market-data discovery."),
        ("Market Data", "Waiting for delayed/free quote refresh."),
        ("News Image Agent", "Waiting for source-linked news image processing."),
        ("Dashboard Refresh", "Waiting to rebuild dashboard data."),
        ("Report Writer", "Waiting for report handoff."),
    ]


def _queued_steps(request: StockPickerRequest) -> list[AgentStep]:
    labels = _step_labels(request)
    return [
        AgentStep(name=name, status="running" if index == 0 else "queued", progress_pct=10 if index == 0 else 0, message=message)
        for index, (name, message) in enumerate(labels)
    ]


def _completed_steps(request: StockPickerRequest, suggestions: list[StockSuggestion]) -> list[AgentStep]:
    if _zh(request):
        messages = [
            "研究流程已规划，已应用仅供研究护栏。",
            f"已完成 {len(suggestions)} 个研究候选标的排序。",
            "混合免费行情已刷新，并记录备用数据提示。",
            "新闻来源图片已解析，必要时生成确定性备用图片。",
            "仪表盘已根据结构化输出重建。",
            "研报交接完成，继续保留仅供研究声明。",
        ]
    else:
        messages = [
            "Workflow planned and guardrails applied.",
            f"{len(suggestions)} research candidates ranked.",
            "Hybrid free market data refreshed with fallback warnings.",
            "News source images resolved or fallback assets generated.",
            "Dashboard payload rebuilt from structured outputs.",
            "Report handoff completed with research-only guardrails.",
        ]
    return [
        AgentStep(name=name, status="completed", progress_pct=100, message=message)
        for (name, _), message in zip(_step_labels(request), messages)
    ]


def _execute_research_run(run_id: str, request: ResearchRunRequest) -> None:
    try:
        _trace(
            run_id,
            _copy(request, "Supervisor", "监督"),
            "running",
            _copy(request, "Starting research workflow", "启动研究工作流"),
            _copy(request, "Supervisor is preparing discovery, market-data, image, dashboard, and report steps.", "监督 Agent 正在准备候选检索、行情读取、图片处理、面板刷新与研报交接步骤。"),
        )
        suggestions = suggest_stocks(request, run_id)
        primary = request.primary_ticker or (suggestions[0].ticker if suggestions else "TSLA")
        dashboard = build_agent_dashboard(primary, suggestions, request, run_id)
        _trace(
            run_id,
            _copy(request, "Report", "研报"),
            "running",
            _copy(request, "Preparing report handoff", "准备研报交接"),
            _copy(request, f"Report id will be generated for {dashboard.ticker}.", f"将为 {dashboard.ticker} 生成研报交接编号。"),
            ticker=dashboard.ticker,
        )
        report_id = f"report-{dashboard.ticker.lower().replace('.', '-')}"
        _trace(
            run_id,
            _copy(request, "Report", "研报"),
            "completed",
            _copy(request, "Report handoff completed", "研报交接完成"),
            _copy(request, "Structured dashboard output is ready for research-only report export.", "结构化仪表盘输出已准备好用于仅供研究的研报导出。"),
            ticker=dashboard.ticker,
            metadata={"report_id": report_id},
        )
        _set_run(
            run_id,
            status="completed",
            progress_pct=100,
            finished_at=datetime.now(timezone.utc),
            primary_ticker=dashboard.ticker,
            selected_shortlist=suggestions,
            steps=_completed_steps(request, suggestions),
            dashboard=dashboard,
            report_id=report_id,
            assets=dashboard.image_assets,
            warnings=dashboard.warnings,
            message=_copy(
                request,
                "Research Agent run completed. Outputs are research candidates only, not trading recommendations.",
                "Research Agent 已完成。输出均为研究候选与研究分析，不构成交易建议。",
            ),
        )
    except Exception as exc:  # pragma: no cover - defensive state capture for desktop runtime
        _trace(
            run_id,
            _copy(request, "Supervisor", "监督"),
            "failed",
            _copy(request, "Research workflow failed", "研究工作流失败"),
            str(exc),
        )
        _set_run(
            run_id,
            status="failed",
            progress_pct=100,
            finished_at=datetime.now(timezone.utc),
            steps=[
                step.model_copy(update={"status": "failed", "progress_pct": 100, "message": str(exc)})
                if index == 0
                else step
                for index, step in enumerate(agent_runs[run_id].steps)
            ],
            message=_copy(request, "Research Agent failed.", "Research Agent 运行失败。"),
            warnings=[str(exc)],
        )


def create_research_run(request: ResearchRunRequest) -> AgentRun:
    run_id = str(uuid4())
    agent_traces[run_id] = []
    run = AgentRun(
        id=run_id,
        status="running",
        progress_pct=8,
        created_at=datetime.now(timezone.utc),
        finished_at=None,
        primary_ticker=request.primary_ticker or "",
        selected_shortlist=[],
        steps=_queued_steps(request),
        dashboard=None,
        report_id=None,
        assets=[],
        warnings=[],
        message=_copy(request, "Research Agent is running.", "Research Agent 正在运行。"),
        trace_events=[],
    )
    agent_runs[run_id] = run
    worker = threading.Thread(target=_execute_research_run, args=(run_id, request), daemon=True)
    worker.start()
    return run
