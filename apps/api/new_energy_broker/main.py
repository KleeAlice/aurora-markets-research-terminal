from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from .adapters import provider_statuses
from .config_store import load_api_config, save_api_config, save_demo_mode
from .demo_data import EVENTS, MARKET_OVERVIEW, SENTIMENT
from .image_assets import image_bytes
from .llm_providers import LLM_PROVIDER_PRESETS
from .market_data import search_market
from .research_agent import agent_runs, agent_traces, create_research_run, suggest_stocks
from .schemas import ApiProviderConfig, AppSettings, DcfAssumptions, ResearchRunRequest, StockPickerRequest
from .services import (
    agent_configs,
    build_report,
    calculate_dcf,
    calculate_metrics,
    canonical_ticker,
    create_analysis_job,
    get_candles,
    get_dashboard,
    get_financials,
    get_peer_comparison,
    get_security,
    jobs,
    list_reports,
    list_securities,
    minimal_pdf_bytes,
    settings,
    validate_report_language,
)

app = FastAPI(title="Aurora Markets Research Terminal API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "product": "aurora-markets-research-terminal", "ui_revision": "aurora-redo", "mode": settings.data_mode}


@app.get("/api/market/overview")
def market_overview():
    return MARKET_OVERVIEW


@app.get("/api/market/search")
def market_search(q: str = ""):
    return search_market(q)


@app.get("/api/market/{ticker}/candles")
def candles(ticker: str, range: str = "1D"):
    try:
        return get_candles(ticker, range)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Candles unavailable") from exc


@app.get("/api/dashboard/{ticker}")
def dashboard(ticker: str):
    try:
        return get_dashboard(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dashboard unavailable") from exc


@app.get("/api/securities")
def securities():
    return list_securities()


@app.get("/api/securities/{ticker}")
def security(ticker: str):
    try:
        return get_security(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unsupported ticker") from exc


@app.get("/api/financials/{ticker}")
def financials(ticker: str):
    try:
        return get_financials(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Financials unavailable") from exc


@app.get("/api/metrics/{ticker}")
def metrics(ticker: str):
    try:
        return calculate_metrics(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Metrics unavailable") from exc


@app.get("/api/valuation/{ticker}/peers")
def peers(ticker: str):
    try:
        return get_peer_comparison(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Peer group unavailable") from exc


@app.get("/api/valuation/{ticker}/dcf")
def dcf(ticker: str):
    try:
        return calculate_dcf(ticker)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/valuation/{ticker}/dcf")
def recalc_dcf(ticker: str, assumptions: DcfAssumptions):
    try:
        return calculate_dcf(ticker, assumptions)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/events/{ticker}")
def events(ticker: str):
    key = canonical_ticker(ticker)
    if key not in EVENTS:
        raise HTTPException(status_code=404, detail="Events unavailable")
    return EVENTS[key]


@app.get("/api/sentiment/{ticker}")
def sentiment(ticker: str):
    key = canonical_ticker(ticker)
    if key not in SENTIMENT:
        raise HTTPException(status_code=404, detail="Sentiment unavailable")
    return SENTIMENT[key]


@app.get("/api/agents")
def agents():
    return agent_configs()


@app.get("/api/providers/status")
def providers():
    return provider_statuses()


@app.post("/api/agent/stock-picker/suggestions")
def stock_picker_suggestions(payload: StockPickerRequest):
    return suggest_stocks(payload)


@app.post("/api/agent/research-runs")
def research_runs(payload: ResearchRunRequest):
    return create_research_run(payload)


@app.get("/api/agent/research-runs/{run_id}")
def research_run(run_id: str):
    if run_id not in agent_runs:
        raise HTTPException(status_code=404, detail="Research run not found")
    return agent_runs[run_id]


@app.get("/api/agent/research-runs/{run_id}/trace")
def research_run_trace(run_id: str):
    if run_id not in agent_runs:
        raise HTTPException(status_code=404, detail="Research run not found")
    return agent_traces.get(run_id, [])


@app.get("/api/agent/research-runs/{run_id}/assets")
def research_run_assets(run_id: str):
    if run_id not in agent_runs:
        raise HTTPException(status_code=404, detail="Research run not found")
    return agent_runs[run_id].assets


@app.get("/api/assets/images/{asset_id}")
def asset_image(asset_id: str):
    try:
        content, media_type = image_bytes(asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Image asset not found") from exc
    return Response(content, media_type=media_type)


@app.post("/api/analysis/jobs")
def run_analysis(payload: dict[str, str]):
    ticker = payload.get("ticker", "TSLA")
    job_type = payload.get("job_type", "full_analysis")
    return create_analysis_job(ticker, job_type)


@app.get("/api/analysis/jobs/{job_id}")
def analysis_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/reports")
def reports():
    return list_reports()


@app.get("/api/reports/{ticker}")
def report(ticker: str):
    try:
        report_model = build_report(ticker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Report unavailable") from exc
    bad_phrases = validate_report_language(report_model)
    if bad_phrases:
        raise HTTPException(status_code=422, detail={"banned_phrases": bad_phrases})
    return report_model


@app.get("/api/reports/{ticker}/markdown")
def report_markdown(ticker: str):
    return Response(build_report(ticker).markdown, media_type="text/markdown")


@app.get("/api/reports/{ticker}/html")
def report_html(ticker: str):
    return HTMLResponse(build_report(ticker).html)


@app.get("/api/reports/{ticker}/pdf")
def report_pdf(ticker: str):
    model = build_report(ticker)
    return Response(
        minimal_pdf_bytes(model),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{model.id}.pdf"'},
    )


@app.get("/api/settings")
def get_settings():
    return settings


@app.get("/api/settings/api-config")
def get_api_config():
    return load_api_config()


@app.get("/api/settings/llm-providers")
def get_llm_providers():
    return LLM_PROVIDER_PRESETS


@app.put("/api/settings/api-config")
def put_api_config(config: ApiProviderConfig):
    return save_api_config(config)


@app.post("/api/settings/api-config/demo-mode")
def put_api_config_demo_mode(config: ApiProviderConfig | None = None):
    return save_demo_mode(config)


@app.put("/api/settings")
def update_settings(next_settings: AppSettings):
    settings.data_mode = next_settings.data_mode
    settings.theme = next_settings.theme
    settings.llm_provider = next_settings.llm_provider
    settings.report_template = next_settings.report_template
    settings.disclaimer_enabled = next_settings.disclaimer_enabled
    return settings
