from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from statistics import median
from uuid import uuid4

from .demo_data import CANDLES, EVENTS, FINANCIALS, HEATMAP, MARKET_OVERVIEW, NEWS, PEERS, SECURITIES, SENTIMENT, VALUATION_SNAPSHOT, WATCHLIST
from .schemas import (
    AgentConfig,
    AnalysisJob,
    AppSettings,
    CandlePoint,
    DashboardPayload,
    DcfAssumptions,
    DcfResult,
    DcfScenario,
    DcfYear,
    MetricSnapshot,
    PeerComparison,
    PeerMetric,
    ReportSection,
    ResearchReport,
)

settings = AppSettings()
jobs: dict[str, AnalysisJob] = {}


def canonical_ticker(ticker: str) -> str:
    value = ticker.upper()
    if value in {"BYD", "01211.HK", "1211.HK"}:
        return "002594.SZ"
    if value in {"TSLA.US"}:
        return "TSLA"
    return value


def list_securities():
    return list(SECURITIES.values())


def get_security(ticker: str):
    return SECURITIES[canonical_ticker(ticker)]


def get_financials(ticker: str):
    return FINANCIALS[canonical_ticker(ticker)]


def get_candles(ticker: str, range_key: str = "1D") -> list[CandlePoint]:
    from .market_data import delayed_candles

    rows, _, _ = delayed_candles(ticker, range_key)
    return rows


def get_dashboard(ticker: str) -> DashboardPayload:
    from .image_assets import build_news_image_asset
    from .market_data import delayed_quote
    from .schemas import DataStatus

    key = canonical_ticker(ticker)
    quote, source, message = delayed_quote(key)
    with ThreadPoolExecutor(max_workers=3) as executor:
        image_assets = list(executor.map(lambda pair: build_news_image_asset(pair[1], pair[0]), enumerate(NEWS[:3])))
    asset_by_title = {asset.title: asset for asset in image_assets}
    latest_news = []
    for item in NEWS:
        asset = asset_by_title.get(item.title)
        latest_news.append(
            item.model_copy(
                update={
                    "source_url": asset.source_url if asset else item.source_url,
                    "image_url": asset.local_url if asset else item.image_url,
                    "image_asset_id": asset.id if asset else item.image_asset_id,
                }
            )
        )
    insight = (
        "BYD's strong Q1 results and NEV sales growth continue to outperform industry peers. "
        "Expansion in overseas markets and vertical integration strengthen long-term competitiveness."
        if key == "002594.SZ"
        else "Tesla sentiment is mixed: energy storage and autonomy support optionality, while price cuts keep margin expectations under watch."
    )
    return DashboardPayload(
        ticker=key,
        quote=quote,
        market_strip=MARKET_OVERVIEW,
        watchlist=WATCHLIST,
        heatmap=HEATMAP,
        valuation_snapshot=VALUATION_SNAPSHOT,
        latest_news=latest_news,
        ai_insight=insight,
        data_status=DataStatus(
            mode="delayed" if source.source_type == "market_data" else "demo",
            provider=source.title,
            updated_at=datetime.now(timezone.utc),
            message=message,
        ),
        source_refs=[source],
        updated_at=datetime.now(timezone.utc),
        image_assets=image_assets,
        warnings=[] if source.source_type == "market_data" else [message],
    )


def calculate_metrics(ticker: str) -> MetricSnapshot:
    key = canonical_ticker(ticker)
    rows = FINANCIALS[key]
    latest = rows[-1]
    prev = rows[-2] if len(rows) > 1 else None

    def growth(current: float | None, previous: float | None) -> float | None:
        if current is None or previous in (None, 0):
            return None
        return (current - previous) / abs(previous)

    revenue_yoy = growth(latest.revenue, prev.revenue if prev else None)
    net_income_yoy = growth(latest.net_income, prev.net_income if prev else None)
    fcf_yoy = growth(latest.free_cash_flow, prev.free_cash_flow if prev else None)
    fcf_margin = latest.free_cash_flow / latest.revenue if latest.revenue else None
    warnings: list[str] = ["Demo data mode: refresh live provider before production use."]
    pe = 37.6 if key == "TSLA" else 23.2
    pb = 9.5 if key == "TSLA" else 4.6
    earnings_growth = net_income_yoy
    peg = None
    if earnings_growth and earnings_growth > 0 and pe:
        peg = pe / (earnings_growth * 100)
    else:
        warnings.append("PEG unavailable because earnings growth is negative or missing.")
    return MetricSnapshot(
        ticker=key,
        revenue=latest.revenue,
        revenue_yoy=revenue_yoy,
        net_income=latest.net_income,
        net_income_yoy=net_income_yoy,
        gross_margin=latest.gross_margin,
        roe=latest.roe,
        pe=pe,
        pb=pb,
        peg=peg,
        free_cash_flow=latest.free_cash_flow,
        fcf_yoy=fcf_yoy,
        fcf_margin=fcf_margin,
        data_quality_score=86 if key == "002594.SZ" else 82,
        warnings=warnings,
    )


def _metric_medians(peers: list[PeerMetric]) -> dict[str, float | None]:
    output: dict[str, float | None] = {}
    for metric in ["pe", "ps", "pb", "ev_ebitda", "revenue_growth", "gross_margin", "net_margin", "roe", "fcf_margin"]:
        values = [getattr(peer, metric) for peer in peers if getattr(peer, metric) is not None]
        output[metric] = median(values) if values else None
    return output


def get_peer_comparison(ticker: str) -> PeerComparison:
    key = canonical_ticker(ticker)
    target = calculate_metrics(key)
    peers = PEERS[key]
    medians = _metric_medians(peers)
    premium_discount: dict[str, float | None] = {}
    target_values = {"pe": target.pe, "pb": target.pb, "gross_margin": target.gross_margin, "roe": target.roe, "fcf_margin": target.fcf_margin}
    for metric, value in target_values.items():
        base = medians.get(metric)
        premium_discount[metric] = None if value is None or base in (None, 0) else (value - base) / abs(base)
    return PeerComparison(ticker=key, peers=peers, medians=medians, premium_discount=premium_discount)


def _calculate_single_dcf(ticker: str, assumptions: DcfAssumptions, scenario: str = "base") -> DcfResult:
    key = canonical_ticker(ticker)
    latest = FINANCIALS[key][-1]
    forecast: list[DcfYear] = []
    enterprise_value = 0.0
    revenue = latest.revenue
    for index in range(1, assumptions.forecast_years + 1):
        revenue *= 1 + assumptions.revenue_growth
        nopat = revenue * assumptions.operating_margin * (1 - assumptions.tax_rate)
        capex = revenue * assumptions.capex_ratio
        working_capital = revenue * assumptions.working_capital_ratio
        fcf = max(nopat - capex - working_capital, 0)
        present_value = fcf / ((1 + assumptions.discount_rate) ** index)
        enterprise_value += present_value
        forecast.append(DcfYear(year=latest.fiscal_year + index, revenue=revenue, free_cash_flow=fcf, present_value=present_value))
    terminal_fcf = forecast[-1].free_cash_flow * (1 + assumptions.terminal_growth_rate)
    spread = assumptions.discount_rate - assumptions.terminal_growth_rate
    if spread <= 0:
        raise ValueError("Discount rate must be greater than terminal growth rate.")
    terminal_value = terminal_fcf / spread
    terminal_pv = terminal_value / ((1 + assumptions.discount_rate) ** assumptions.forecast_years)
    enterprise_value += terminal_pv
    equity_value = enterprise_value - assumptions.net_debt
    fair_value = equity_value * 1_000_000_000 / assumptions.diluted_shares
    return DcfResult(
        ticker=key,
        currency=SECURITIES[key].currency,
        forecast=forecast,
        terminal_value=terminal_value,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        fair_value_per_share=fair_value,
        scenarios=[],
        sensitivity=[],
        warnings=["DCF is assumption-sensitive and should not be treated as an absolute valuation."],
    )


def calculate_dcf(ticker: str, assumptions: DcfAssumptions | None = None) -> DcfResult:
    key = canonical_ticker(ticker)
    base = assumptions or default_assumptions(key)
    result = _calculate_single_dcf(key, base)

    scenario_inputs = [
        ("bear", base.model_copy(update={"revenue_growth": max(base.revenue_growth - 0.05, 0.01), "operating_margin": max(base.operating_margin - 0.03, 0.01), "discount_rate": base.discount_rate + 0.015})),
        ("base", base),
        ("bull", base.model_copy(update={"revenue_growth": base.revenue_growth + 0.04, "operating_margin": base.operating_margin + 0.025, "discount_rate": max(base.discount_rate - 0.01, 0.01)})),
    ]
    scenarios: list[DcfScenario] = []
    for name, scenario_assumptions in scenario_inputs:
        item = _calculate_single_dcf(key, scenario_assumptions)
        scenarios.append(DcfScenario(name=name, fair_value_per_share=item.fair_value_per_share, enterprise_value=item.enterprise_value, equity_value=item.equity_value, assumptions=scenario_assumptions))
    sensitivity = []
    for discount in [base.discount_rate - 0.01, base.discount_rate, base.discount_rate + 0.01]:
        row = {"discount_rate": discount}
        for terminal in [base.terminal_growth_rate - 0.005, base.terminal_growth_rate, base.terminal_growth_rate + 0.005]:
            try:
                value = _calculate_single_dcf(key, base.model_copy(update={"discount_rate": discount, "terminal_growth_rate": terminal})).fair_value_per_share
            except ValueError:
                value = 0
            row[f"terminal_{terminal:.3f}"] = value
        sensitivity.append(row)
    result.scenarios = scenarios
    result.sensitivity = sensitivity
    return result


def default_assumptions(ticker: str) -> DcfAssumptions:
    key = canonical_ticker(ticker)
    if key == "TSLA":
        return DcfAssumptions(revenue_growth=0.10, operating_margin=0.13, tax_rate=0.17, capex_ratio=0.07, working_capital_ratio=0.015, discount_rate=0.095, terminal_growth_rate=0.025, net_debt=-12.0, diluted_shares=3_170_000_000)
    return DcfAssumptions(revenue_growth=0.13, operating_margin=0.105, tax_rate=0.18, capex_ratio=0.065, working_capital_ratio=0.015, discount_rate=0.085, terminal_growth_rate=0.025, net_debt=5.0, diluted_shares=2_910_000_000)


def agent_configs() -> list[AgentConfig]:
    return [
        AgentConfig(name="Supervisor Agent", purpose="Coordinate research workflow and validate completeness.", required_inputs=["ticker", "analysis_scope"], output_contract="analysis_job", guardrails=["No trading execution", "No unsupported claims"]),
        AgentConfig(name="Stock Discovery Agent", purpose="Rank research candidates from search/manual inputs.", required_inputs=["universe", "theme", "market_data"], output_contract="stock_suggestions", guardrails=["Research-candidate language only", "No buy/sell wording"]),
        AgentConfig(name="Market Data Agent", purpose="Refresh delayed/free quotes and OHLCV with provider status labels.", required_inputs=["ticker", "provider_settings"], output_contract="market_snapshot", guardrails=["Expose delayed/demo status", "Fallback with warnings"]),
        AgentConfig(name="Financial Data Agent", purpose="Retrieve and normalize financial statements.", required_inputs=["ticker", "provider_settings"], output_contract="normalized_financials", guardrails=["Do not fabricate missing fields", "Keep source references"]),
        AgentConfig(name="Metrics Calculation Agent", purpose="Calculate ratios, YoY, QoQ, and warnings.", required_inputs=["normalized_financials", "market_data"], output_contract="metric_snapshot", guardrails=["Handle negative earnings", "Expose unavailable metrics"]),
        AgentConfig(name="DCF Valuation Agent", purpose="Build editable bear/base/bull DCF model.", required_inputs=["metrics", "assumptions"], output_contract="dcf_result", guardrails=["Assumptions must be visible", "No certainty language"]),
        AgentConfig(name="News Image Agent", purpose="Resolve official/article images and local fallback thumbnails.", required_inputs=["news_items"], output_contract="image_assets", guardrails=["Keep attribution", "No random untracked image scraping"]),
        AgentConfig(name="Dashboard Refresh Agent", purpose="Update terminal panels from validated structured outputs.", required_inputs=["stock_suggestions", "market_snapshot", "image_assets"], output_contract="dashboard_payload", guardrails=["Show source/status labels", "Keep warnings visible"]),
        AgentConfig(name="Report Writer Agent", purpose="Generate cited equity research report.", required_inputs=["validated_intermediate_outputs"], output_contract="research_report", guardrails=["Every factual claim needs evidence", "No personalized advice"]),
    ]


def create_analysis_job(ticker: str, job_type: str = "full_analysis") -> AnalysisJob:
    key = canonical_ticker(ticker)
    report = build_report(key)
    job = AnalysisJob(
        id=str(uuid4()),
        ticker=key,
        job_type=job_type,
        status="completed",
        progress_pct=100,
        created_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        created_report_id=report.id,
        message="Demo analysis completed with source-grounded fixture data.",
    )
    jobs[job.id] = job
    return job


def build_report(ticker: str) -> ResearchReport:
    key = canonical_ticker(ticker)
    security = SECURITIES[key]
    metrics = calculate_metrics(key)
    dcf = calculate_dcf(key)
    sentiment = SENTIMENT[key]
    source = FINANCIALS[key][-1].source
    disclaimer = "Research-only output. This is not personalized investment advice and does not support order execution."
    sections = [
        ReportSection(title="Executive Summary", content=f"{security.company_name} is presented as a new-energy equity research case with demo-grounded financials, valuation, sentiment, and event context.", confidence=0.82, sources=[source], warnings=metrics.warnings),
        ReportSection(title="Fundamental Analysis", content=f"Latest demo revenue is {metrics.revenue:.2f} in {FINANCIALS[key][-1].currency}; gross margin is {metrics.gross_margin:.1%} and ROE is {metrics.roe:.1%}.", confidence=0.84, sources=[source], warnings=[]),
        ReportSection(title="DCF Valuation", content=f"Base-case fair value is {dcf.fair_value_per_share:.2f} {security.currency} per share under visible assumptions. The range should be read as scenario analysis, not certainty.", confidence=0.70, sources=[source], warnings=dcf.warnings),
        ReportSection(title="Public Sentiment", content=f"Sentiment is {sentiment.label} with score {sentiment.score:.2f}. Expectation gap: {sentiment.expectation_gap}", confidence=sentiment.confidence, sources=[FINANCIALS[key][-1].source], warnings=["Sentiment uses curated demo source counts."]),
        ReportSection(title="Key Risks", content="Key risks include margin pressure, policy changes, currency differences, data-provider gaps, and DCF sensitivity.", confidence=0.80, sources=[source], warnings=[]),
    ]
    markdown = "\n\n".join([f"## {section.title}\n{section.content}" for section in sections])
    markdown = f"# {security.company_name} AI Equity Research Report\n\n{markdown}\n\n> {disclaimer}\n"
    html = "<article>" + "".join([f"<section><h2>{section.title}</h2><p>{section.content}</p></section>" for section in sections]) + f"<footer>{disclaimer}</footer></article>"
    return ResearchReport(
        id=f"report-{key.lower().replace('.', '-')}",
        ticker=key,
        title=f"{security.company_name} AI Equity Research Report",
        created_at=datetime.now(timezone.utc),
        sections=sections,
        markdown=markdown,
        html=html,
        data_quality_warnings=metrics.warnings,
        disclaimer=disclaimer,
    )


def list_reports() -> list[ResearchReport]:
    return [build_report("TSLA"), build_report("002594.SZ")]


def validate_report_language(report: ResearchReport) -> list[str]:
    banned = ["you should buy", "you should sell", "guaranteed", "risk-free"]
    text = report.markdown.lower()
    return [phrase for phrase in banned if phrase in text]


def minimal_pdf_bytes(report: ResearchReport) -> bytes:
    safe_title = report.title.replace("(", "").replace(")", "")
    body = f"%PDF-1.4\n1 0 obj<<>>endobj\n2 0 obj<</Length 78>>stream\nBT /F1 18 Tf 72 720 Td ({safe_title}) Tj 0 -32 Td (Research-only demo export.) Tj ET\nendstream\nendobj\ntrailer<</Root 1 0 R>>\n%%EOF"
    return body.encode("latin-1", errors="ignore")
