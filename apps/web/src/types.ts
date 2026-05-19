export interface SourceRef {
  title: string;
  url: string;
  source_type: string;
}

export interface Security {
  ticker: string;
  aliases: string[];
  company_name: string;
  exchange: string;
  market: string;
  currency: string;
  sector: string;
  industry: string;
  latest_price: number | null;
  market_cap: number | null;
  latest_report_date: string | null;
  data_update_status: "demo" | "live" | "delayed" | "stale" | "missing";
  thesis_tags: string[];
}

export interface DataStatus {
  mode: "live" | "delayed" | "demo" | "stale" | "mixed";
  provider: string;
  updated_at: string;
  message: string;
}

export interface MarketPoint {
  label: string;
  value: number;
  change_pct: number;
  series: number[];
}

export interface CandlePoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface WatchlistItem {
  ticker: string;
  company_name: string;
  exchange: string;
  price: number;
  change_pct: number;
  sparkline: number[];
}

export interface HeatmapItem {
  ticker: string;
  change_pct: number;
  weight: number;
}

export interface NewsCard {
  title: string;
  source: string;
  date: string;
  category: string;
  summary: string;
  image_key: string;
  source_url?: string | null;
  image_url?: string | null;
  image_asset_id?: string | null;
}

export interface ValuationSnapshot {
  ticker: string;
  pe: number | null;
  ps: number | null;
  ev_ebitda: number | null;
}

export interface ImageAsset {
  id: string;
  title: string;
  source_url: string;
  image_url: string | null;
  local_url: string;
  attribution: string;
  width: number | null;
  height: number | null;
  status: "downloaded" | "remote" | "fallback";
}

export interface StockSuggestion {
  ticker: string;
  company_name: string;
  exchange: string;
  market: string;
  score: number;
  thesis: string;
  data_status: string;
  sources: SourceRef[];
}

export interface MarketSearchResult {
  ticker: string;
  company_name: string;
  exchange: string;
  market: string;
  currency: string;
  price: number | null;
  change_pct: number | null;
  data_status: string;
  source: SourceRef;
}

export interface DashboardPayload {
  ticker: string;
  quote: Security;
  market_strip: MarketPoint[];
  watchlist: WatchlistItem[];
  heatmap: HeatmapItem[];
  valuation_snapshot: ValuationSnapshot[];
  latest_news: NewsCard[];
  ai_insight: string;
  data_status?: DataStatus | null;
  source_refs?: SourceRef[];
  updated_at?: string | null;
  selected_shortlist?: StockSuggestion[];
  agent_summary?: string | null;
  image_assets?: ImageAsset[];
  warnings?: string[];
}

export interface FinancialRow {
  fiscal_year: number;
  revenue: number;
  net_income: number;
  gross_margin: number;
  roe: number;
  operating_cash_flow: number;
  capital_expenditure: number;
  free_cash_flow: number;
  currency: string;
  source: SourceRef;
}

export interface MetricSnapshot {
  ticker: string;
  revenue: number;
  revenue_yoy: number | null;
  net_income: number;
  net_income_yoy: number | null;
  gross_margin: number | null;
  roe: number | null;
  pe: number | null;
  pb: number | null;
  peg: number | null;
  free_cash_flow: number | null;
  fcf_yoy: number | null;
  fcf_margin: number | null;
  data_quality_score: number;
  warnings: string[];
}

export interface PeerMetric {
  ticker: string;
  company_name: string;
  reason: string;
  pe: number | null;
  ps: number | null;
  pb: number | null;
  ev_ebitda: number | null;
  revenue_growth: number | null;
  gross_margin: number | null;
  net_margin: number | null;
  roe: number | null;
  fcf_margin: number | null;
}

export interface PeerComparison {
  ticker: string;
  peers: PeerMetric[];
  medians: Record<string, number | null>;
  premium_discount: Record<string, number | null>;
}

export interface DcfAssumptions {
  revenue_growth: number;
  operating_margin: number;
  tax_rate: number;
  capex_ratio: number;
  working_capital_ratio: number;
  discount_rate: number;
  terminal_growth_rate: number;
  net_debt: number;
  diluted_shares: number;
  forecast_years: number;
}

export interface DcfScenario {
  name: "bear" | "base" | "bull";
  fair_value_per_share: number;
  enterprise_value: number;
  equity_value: number;
  assumptions: DcfAssumptions;
}

export interface DcfResult {
  ticker: string;
  currency: string;
  forecast: Array<{ year: number; revenue: number; free_cash_flow: number; present_value: number }>;
  terminal_value: number;
  enterprise_value: number;
  equity_value: number;
  fair_value_per_share: number;
  scenarios: DcfScenario[];
  sensitivity: Array<Record<string, number>>;
  warnings: string[];
}

export interface EventItem {
  event_title: string;
  event_date: string;
  event_type: string;
  summary: string;
  risk_level: "low" | "medium" | "high";
  opportunity_level: "low" | "medium" | "high";
  affected_metrics: string[];
  confidence: number;
}

export interface SentimentSummary {
  ticker: string;
  label: "positive" | "neutral" | "negative";
  score: number;
  confidence: number;
  source_breakdown: Record<string, number>;
  topic_clusters: string[];
  expectation_gap: string;
  trend: Array<{ date: string; positive: number; neutral: number; negative: number }>;
}

export interface ResearchReport {
  id: string;
  ticker: string;
  title: string;
  created_at: string;
  markdown: string;
  html: string;
  data_quality_warnings: string[];
  disclaimer: string;
}

export interface ApiProviderConfig {
  provider: string;
  providerId: string;
  protocol: "openai-compatible" | "anthropic-messages" | "azure-openai";
  baseUrl: string;
  model: string;
  apiKey: string;
  apiVersion: string;
  marketDataProvider: string;
  marketDataKey: string;
  configured: boolean;
  demoMode: boolean;
  savedAt: string;
}

export interface LlmProviderPreset {
  id: string;
  name: string;
  region: string;
  protocol: "openai-compatible" | "anthropic-messages" | "azure-openai";
  baseUrl: string;
  defaultModel: string;
  apiKeyHint: string;
  docsUrl: string;
  notes: string;
}

export interface AnalysisJob {
  id: string;
  ticker: string;
  status: "queued" | "running" | "completed" | "failed";
  progress_pct: number;
  created_report_id: string | null;
  message: string;
}

export interface AgentStep {
  name: string;
  status: "queued" | "running" | "completed" | "failed";
  progress_pct: number;
  message: string;
}

export interface AgentTraceEvent {
  id: string;
  run_id: string;
  sequence: number;
  phase: string;
  status: "queued" | "running" | "completed" | "failed" | "warning";
  title: string;
  detail: string;
  source_url?: string | null;
  ticker?: string | null;
  timestamp: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface LlmConfig {
  provider: string;
  provider_id: string;
  protocol: "openai-compatible" | "anthropic-messages" | "azure-openai";
  base_url: string;
  model: string;
  api_key: string;
  api_version: string;
}

export interface StockPickerRequest {
  universe: string;
  theme: string;
  tickers: string[];
  max_results: number;
  language: "en" | "zh";
  time_horizon: string;
  research_focus: string;
  llm?: LlmConfig | null;
}

export interface ResearchRunRequest extends StockPickerRequest {
  primary_ticker?: string | null;
}

export interface AgentRun {
  id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress_pct: number;
  created_at: string;
  finished_at: string | null;
  primary_ticker: string;
  selected_shortlist: StockSuggestion[];
  steps: AgentStep[];
  dashboard: DashboardPayload | null;
  report_id: string | null;
  assets: ImageAsset[];
  warnings: string[];
  message: string;
  trace_events: AgentTraceEvent[];
}
