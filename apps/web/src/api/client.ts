import type {
  AnalysisJob,
  ApiProviderConfig,
  AgentRun,
  AgentTraceEvent,
  CandlePoint,
  DashboardPayload,
  DcfAssumptions,
  DcfResult,
  EventItem,
  FinancialRow,
  LlmProviderPreset,
  MarketSearchResult,
  MarketPoint,
  MetricSnapshot,
  PeerComparison,
  ResearchReport,
  ResearchRunRequest,
  Security,
  SentimentSummary,
  StockPickerRequest,
  StockSuggestion,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8765";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const api = {
  baseUrl: API_BASE,
  marketOverview: () => request<MarketPoint[]>("/api/market/overview"),
  marketSearch: (query: string) => request<MarketSearchResult[]>(`/api/market/search?q=${encodeURIComponent(query)}`),
  dashboard: (ticker: string) => request<DashboardPayload>(`/api/dashboard/${encodeURIComponent(ticker)}`),
  candles: (ticker: string, range = "1D") => request<CandlePoint[]>(`/api/market/${encodeURIComponent(ticker)}/candles?range=${encodeURIComponent(range)}`),
  securities: () => request<Security[]>("/api/securities"),
  financials: (ticker: string) => request<FinancialRow[]>(`/api/financials/${encodeURIComponent(ticker)}`),
  metrics: (ticker: string) => request<MetricSnapshot>(`/api/metrics/${encodeURIComponent(ticker)}`),
  peers: (ticker: string) => request<PeerComparison>(`/api/valuation/${encodeURIComponent(ticker)}/peers`),
  dcf: (ticker: string) => request<DcfResult>(`/api/valuation/${encodeURIComponent(ticker)}/dcf`),
  recalcDcf: (ticker: string, assumptions: DcfAssumptions) =>
    request<DcfResult>(`/api/valuation/${encodeURIComponent(ticker)}/dcf`, {
      method: "POST",
      body: JSON.stringify(assumptions),
    }),
  events: (ticker: string) => request<EventItem[]>(`/api/events/${encodeURIComponent(ticker)}`),
  sentiment: (ticker: string) => request<SentimentSummary>(`/api/sentiment/${encodeURIComponent(ticker)}`),
  report: (ticker: string) => request<ResearchReport>(`/api/reports/${encodeURIComponent(ticker)}`),
  runAnalysis: (ticker: string) =>
    request<AnalysisJob>("/api/analysis/jobs", {
      method: "POST",
      body: JSON.stringify({ ticker, job_type: "full_analysis" }),
    }),
  stockSuggestions: (payload: StockPickerRequest) =>
    request<StockSuggestion[]>("/api/agent/stock-picker/suggestions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  researchRun: (payload: ResearchRunRequest) =>
    request<AgentRun>("/api/agent/research-runs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getResearchRun: (runId: string) => request<AgentRun>(`/api/agent/research-runs/${encodeURIComponent(runId)}`),
  getResearchTrace: (runId: string) => request<AgentTraceEvent[]>(`/api/agent/research-runs/${encodeURIComponent(runId)}/trace`),
  llmProviders: () => request<LlmProviderPreset[]>("/api/settings/llm-providers"),
  getApiConfig: () => request<ApiProviderConfig>("/api/settings/api-config"),
  saveApiConfig: (payload: ApiProviderConfig) =>
    request<ApiProviderConfig>("/api/settings/api-config", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  useDemoMode: (payload: ApiProviderConfig) =>
    request<ApiProviderConfig>("/api/settings/api-config/demo-mode", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  exportUrl: (ticker: string, format: "markdown" | "html" | "pdf") =>
    `${API_BASE}/api/reports/${encodeURIComponent(ticker)}/${format}`,
  imageUrl: (assetId: string) => `${API_BASE}/api/assets/images/${encodeURIComponent(assetId)}`,
};
