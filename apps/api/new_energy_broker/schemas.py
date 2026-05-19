from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    title: str
    url: str
    source_type: str


class Security(BaseModel):
    ticker: str
    aliases: list[str] = Field(default_factory=list)
    company_name: str
    exchange: str
    market: str
    currency: str
    sector: str
    industry: str
    latest_price: float | None
    market_cap: float | None
    latest_report_date: date | None
    data_update_status: Literal["demo", "live", "delayed", "stale", "missing"]
    thesis_tags: list[str] = Field(default_factory=list)


class DataStatus(BaseModel):
    mode: Literal["live", "delayed", "demo", "stale", "mixed"]
    provider: str
    updated_at: datetime
    message: str


class MarketPoint(BaseModel):
    label: str
    value: float
    change_pct: float
    series: list[float]


class CandlePoint(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class WatchlistItem(BaseModel):
    ticker: str
    company_name: str
    exchange: str
    price: float
    change_pct: float
    sparkline: list[float]


class HeatmapItem(BaseModel):
    ticker: str
    change_pct: float
    weight: float


class NewsCard(BaseModel):
    title: str
    source: str
    date: date
    category: str
    summary: str
    image_key: str = "ev"
    source_url: str | None = None
    image_url: str | None = None
    image_asset_id: str | None = None


class ValuationSnapshot(BaseModel):
    ticker: str
    pe: float | None
    ps: float | None
    ev_ebitda: float | None


class ImageAsset(BaseModel):
    id: str
    title: str
    source_url: str
    image_url: str | None = None
    local_url: str
    attribution: str
    width: int | None = None
    height: int | None = None
    status: Literal["downloaded", "remote", "fallback"]


class StockSuggestion(BaseModel):
    ticker: str
    company_name: str
    exchange: str
    market: str
    score: int
    thesis: str
    data_status: str
    sources: list[SourceRef] = Field(default_factory=list)


class MarketSearchResult(BaseModel):
    ticker: str
    company_name: str
    exchange: str
    market: str
    currency: str
    price: float | None = None
    change_pct: float | None = None
    data_status: str = "demo"
    source: SourceRef


class DashboardPayload(BaseModel):
    ticker: str
    quote: Security
    market_strip: list[MarketPoint]
    watchlist: list[WatchlistItem]
    heatmap: list[HeatmapItem]
    valuation_snapshot: list[ValuationSnapshot]
    latest_news: list[NewsCard]
    ai_insight: str
    data_status: DataStatus | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)
    updated_at: datetime | None = None
    selected_shortlist: list[StockSuggestion] = Field(default_factory=list)
    agent_summary: str | None = None
    image_assets: list[ImageAsset] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FinancialRow(BaseModel):
    fiscal_year: int
    revenue: float
    net_income: float
    gross_margin: float
    roe: float
    operating_cash_flow: float
    capital_expenditure: float
    free_cash_flow: float
    currency: str
    source: SourceRef


class MetricSnapshot(BaseModel):
    ticker: str
    revenue: float
    revenue_yoy: float | None
    net_income: float
    net_income_yoy: float | None
    gross_margin: float | None
    roe: float | None
    pe: float | None
    pb: float | None
    peg: float | None
    free_cash_flow: float | None
    fcf_yoy: float | None
    fcf_margin: float | None
    data_quality_score: int
    warnings: list[str] = Field(default_factory=list)


class PeerMetric(BaseModel):
    ticker: str
    company_name: str
    reason: str
    pe: float | None
    ps: float | None
    pb: float | None
    ev_ebitda: float | None
    revenue_growth: float | None
    gross_margin: float | None
    net_margin: float | None
    roe: float | None
    fcf_margin: float | None


class PeerComparison(BaseModel):
    ticker: str
    peers: list[PeerMetric]
    medians: dict[str, float | None]
    premium_discount: dict[str, float | None]


class DcfAssumptions(BaseModel):
    revenue_growth: float = 0.12
    operating_margin: float = 0.14
    tax_rate: float = 0.18
    capex_ratio: float = 0.06
    working_capital_ratio: float = 0.02
    discount_rate: float = 0.09
    terminal_growth_rate: float = 0.025
    net_debt: float = 0
    diluted_shares: float = 3_150_000_000
    forecast_years: int = 5


class DcfYear(BaseModel):
    year: int
    revenue: float
    free_cash_flow: float
    present_value: float


class DcfScenario(BaseModel):
    name: Literal["bear", "base", "bull"]
    fair_value_per_share: float
    enterprise_value: float
    equity_value: float
    assumptions: DcfAssumptions


class DcfResult(BaseModel):
    ticker: str
    currency: str
    forecast: list[DcfYear]
    terminal_value: float
    enterprise_value: float
    equity_value: float
    fair_value_per_share: float
    scenarios: list[DcfScenario]
    sensitivity: list[dict[str, float]]
    warnings: list[str]


class EventItem(BaseModel):
    event_title: str
    event_date: date
    source: SourceRef
    event_type: str
    summary: str
    financial_impact: str
    valuation_impact: str
    risk_level: Literal["low", "medium", "high"]
    opportunity_level: Literal["low", "medium", "high"]
    affected_metrics: list[str]
    confidence: float


class SentimentPoint(BaseModel):
    date: date
    positive: float
    neutral: float
    negative: float


class SentimentSummary(BaseModel):
    ticker: str
    label: Literal["positive", "neutral", "negative"]
    score: float
    confidence: float
    source_breakdown: dict[str, int]
    topic_clusters: list[str]
    expectation_gap: str
    trend: list[SentimentPoint]


class AgentConfig(BaseModel):
    name: str
    purpose: str
    required_inputs: list[str]
    output_contract: str
    guardrails: list[str]


class AnalysisJob(BaseModel):
    id: str
    ticker: str
    job_type: str
    status: Literal["queued", "running", "completed", "failed"]
    progress_pct: int
    created_at: datetime
    finished_at: datetime | None = None
    created_report_id: str | None = None
    message: str


class AgentStep(BaseModel):
    name: str
    status: Literal["queued", "running", "completed", "failed"]
    progress_pct: int
    message: str


class AgentTraceEvent(BaseModel):
    id: str
    run_id: str
    sequence: int
    phase: str
    status: Literal["queued", "running", "completed", "failed", "warning"]
    title: str
    detail: str
    source_url: str | None = None
    ticker: str | None = None
    timestamp: datetime
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class LlmConfig(BaseModel):
    provider: str = "OpenAI"
    provider_id: str = "openai"
    protocol: LlmProtocol = "openai-compatible"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4.1-mini"
    api_key: str = ""
    api_version: str = ""


class ApiProviderConfig(BaseModel):
    provider: str = "OpenAI"
    providerId: str = "openai"
    protocol: LlmProtocol = "openai-compatible"
    baseUrl: str = "https://api.openai.com/v1"
    model: str = "gpt-4.1-mini"
    apiKey: str = ""
    apiVersion: str = ""
    marketDataProvider: str = "Hybrid Free"
    marketDataKey: str = ""
    configured: bool = False
    demoMode: bool = False
    savedAt: str = ""


class StockPickerRequest(BaseModel):
    universe: str = "Global new energy"
    theme: str = "new energy vehicles and batteries"
    tickers: list[str] = Field(default_factory=list)
    max_results: int = 5
    language: Literal["en", "zh"] = "en"
    time_horizon: str = "3-6 months"
    research_focus: str = "growth, valuation, sentiment, and data quality"
    llm: LlmConfig | None = None


class ResearchRunRequest(StockPickerRequest):
    primary_ticker: str | None = None


class AgentRun(BaseModel):
    id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress_pct: int
    created_at: datetime
    finished_at: datetime | None = None
    primary_ticker: str
    selected_shortlist: list[StockSuggestion]
    steps: list[AgentStep]
    dashboard: DashboardPayload | None = None
    report_id: str | None = None
    assets: list[ImageAsset] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    message: str
    trace_events: list[AgentTraceEvent] = Field(default_factory=list)


class ReportSection(BaseModel):
    title: str
    content: str
    confidence: float
    sources: list[SourceRef]
    warnings: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    id: str
    ticker: str
    title: str
    created_at: datetime
    sections: list[ReportSection]
    markdown: str
    html: str
    data_quality_warnings: list[str]
    disclaimer: str


class AppSettings(BaseModel):
    data_mode: Literal["hybrid", "demo", "live"] = "hybrid"
    theme: Literal["light", "dark"] = "light"
    llm_provider: str = "local-demo"
    report_template: Literal["broker", "compact"] = "broker"
    disclaimer_enabled: bool = True
LlmProtocol = Literal["openai-compatible", "anthropic-messages", "azure-openai"]

