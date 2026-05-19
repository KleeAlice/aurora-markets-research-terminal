import { defineStore } from "pinia";

import { api } from "@/api/client";
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
  Security,
  SentimentSummary,
  StockSuggestion,
} from "@/types";

type ViewId = "dashboard" | "fundamental" | "news" | "portfolio" | "screener" | "agent" | "settings";
type Language = "en" | "zh";
type ToastTone = "info" | "success" | "warning" | "error";

export type ApiConfig = ApiProviderConfig;
export type UserProfile = {
  displayName: string;
  initials: string;
  workspaceName: string;
  role: string;
  bio: string;
  completed: boolean;
};

const LANGUAGE_KEY = "aurora-language";
const API_CONFIG_KEY = "new-energy-broker-api-config-v1";
const PROFILE_KEY = "new-energy-broker-profile-v1";

const defaultApiConfig: ApiConfig = {
  provider: "OpenAI",
  providerId: "openai",
  protocol: "openai-compatible",
  baseUrl: "https://api.openai.com/v1",
  model: "gpt-4.1-mini",
  apiKey: "",
  apiVersion: "",
  marketDataProvider: "Demo fixtures",
  marketDataKey: "",
  configured: false,
  demoMode: false,
  savedAt: "",
};

const defaultLlmProviders: LlmProviderPreset[] = [
  { id: "openai", name: "OpenAI", region: "Global", protocol: "openai-compatible", baseUrl: "https://api.openai.com/v1", defaultModel: "gpt-4.1-mini", apiKeyHint: "OpenAI API key", docsUrl: "https://platform.openai.com/docs/api-reference", notes: "OpenAI Chat Completions-compatible endpoint." },
  { id: "azure-openai", name: "Azure OpenAI", region: "Global", protocol: "azure-openai", baseUrl: "https://{resource}.openai.azure.com", defaultModel: "gpt-4.1-mini-deployment", apiKeyHint: "Azure OpenAI resource key", docsUrl: "https://learn.microsoft.com/azure/ai-foundry/openai/reference", notes: "Use your Azure resource endpoint and deployment name as the model. API version is required." },
  { id: "anthropic", name: "Anthropic Claude", region: "Global", protocol: "anthropic-messages", baseUrl: "https://api.anthropic.com", defaultModel: "claude-3-5-sonnet-latest", apiKeyHint: "Anthropic API key", docsUrl: "https://docs.anthropic.com/en/api/messages", notes: "Uses Anthropic Messages API." },
  { id: "google-gemini", name: "Google Gemini", region: "Global", protocol: "openai-compatible", baseUrl: "https://generativelanguage.googleapis.com/v1beta/openai", defaultModel: "gemini-2.5-flash", apiKeyHint: "Google AI Studio API key", docsUrl: "https://ai.google.dev/gemini-api/docs/openai", notes: "Gemini OpenAI compatibility endpoint." },
  { id: "mistral", name: "Mistral AI", region: "Global", protocol: "openai-compatible", baseUrl: "https://api.mistral.ai/v1", defaultModel: "mistral-small-latest", apiKeyHint: "Mistral API key", docsUrl: "https://docs.mistral.ai/api/", notes: "OpenAI-style chat completions endpoint." },
  { id: "xai", name: "xAI", region: "Global", protocol: "openai-compatible", baseUrl: "https://api.x.ai/v1", defaultModel: "grok-3-mini", apiKeyHint: "xAI API key", docsUrl: "https://docs.x.ai/docs/api-reference", notes: "OpenAI-compatible xAI endpoint." },
  { id: "groq", name: "Groq", region: "Global", protocol: "openai-compatible", baseUrl: "https://api.groq.com/openai/v1", defaultModel: "llama-3.3-70b-versatile", apiKeyHint: "Groq API key", docsUrl: "https://console.groq.com/docs", notes: "Groq OpenAI-compatible endpoint." },
  { id: "openrouter", name: "OpenRouter", region: "Global", protocol: "openai-compatible", baseUrl: "https://openrouter.ai/api/v1", defaultModel: "openai/gpt-4o-mini", apiKeyHint: "OpenRouter API key", docsUrl: "https://openrouter.ai/docs/api-reference/overview", notes: "Multi-provider OpenAI-like gateway." },
  { id: "together-ai", name: "Together AI", region: "Global", protocol: "openai-compatible", baseUrl: "https://api.together.xyz/v1", defaultModel: "meta-llama/Llama-3.3-70B-Instruct-Turbo", apiKeyHint: "Together API key", docsUrl: "https://docs.together.ai/reference/chat-completions", notes: "OpenAI-compatible chat completions endpoint." },
  { id: "deepseek", name: "DeepSeek", region: "China / Global", protocol: "openai-compatible", baseUrl: "https://api.deepseek.com", defaultModel: "deepseek-chat", apiKeyHint: "DeepSeek API key", docsUrl: "https://api-docs.deepseek.com/", notes: "OpenAI-compatible endpoint." },
  { id: "qwen", name: "Qwen / Alibaba Model Studio", region: "China / International", protocol: "openai-compatible", baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1", defaultModel: "qwen-plus", apiKeyHint: "DashScope API key", docsUrl: "https://www.alibabacloud.com/help/en/model-studio/use-qwen-by-calling-api", notes: "For international/Singapore region use https://dashscope-intl.aliyuncs.com/compatible-mode/v1." },
  { id: "kimi", name: "Kimi / Moonshot", region: "China", protocol: "openai-compatible", baseUrl: "https://api.moonshot.cn/v1", defaultModel: "kimi-k2.6", apiKeyHint: "Moonshot API key", docsUrl: "https://platform.kimi.com/docs/api/overview", notes: "OpenAI-compatible Kimi endpoint. Some tools also use https://api.moonshot.ai/v1." },
  { id: "zhipu-glm", name: "Zhipu GLM / Z.ai", region: "China", protocol: "openai-compatible", baseUrl: "https://open.bigmodel.cn/api/paas/v4", defaultModel: "glm-4.5-flash", apiKeyHint: "BigModel API key", docsUrl: "https://docs.bigmodel.cn/cn/guide/start/model-overview", notes: "OpenAI-compatible GLM endpoint." },
  { id: "baidu-qianfan", name: "Baidu Qianfan", region: "China", protocol: "openai-compatible", baseUrl: "https://qianfan.baidubce.com/v2", defaultModel: "ernie-4.5-turbo-128k", apiKeyHint: "Baidu Qianfan API key", docsUrl: "https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html", notes: "Qianfan v2 OpenAI-compatible endpoint." },
  { id: "tencent-hunyuan", name: "Tencent Hunyuan", region: "China", protocol: "openai-compatible", baseUrl: "https://api.hunyuan.cloud.tencent.com/v1", defaultModel: "hunyuan-turbos-latest", apiKeyHint: "Tencent Hunyuan API key", docsUrl: "https://cloud.tencent.com/document/product/1729", notes: "Hunyuan OpenAI-compatible endpoint." },
  { id: "minimax", name: "MiniMax", region: "China / Global", protocol: "openai-compatible", baseUrl: "https://api.minimax.io/v1", defaultModel: "MiniMax-M2", apiKeyHint: "MiniMax API key", docsUrl: "https://platform.minimax.io/docs/api-reference/models/openai/list-models", notes: "International endpoint. China users may use https://api.minimaxi.com/v1." },
  { id: "volcengine-ark", name: "Volcengine Ark / Doubao", region: "China", protocol: "openai-compatible", baseUrl: "https://ark.cn-beijing.volces.com/api/v3", defaultModel: "doubao-seed-1-6", apiKeyHint: "Volcengine Ark API key", docsUrl: "https://www.volcengine.com/docs/82379", notes: "Ark OpenAI-compatible endpoint." },
  { id: "siliconflow", name: "SiliconFlow", region: "China / Global", protocol: "openai-compatible", baseUrl: "https://api.siliconflow.cn/v1", defaultModel: "Qwen/Qwen3-32B", apiKeyHint: "SiliconFlow API key", docsUrl: "https://docs.siliconflow.cn/", notes: "OpenAI-compatible SiliconFlow endpoint." },
  { id: "custom", name: "Custom OpenAI-compatible", region: "Custom", protocol: "openai-compatible", baseUrl: "https://your-provider.example/v1", defaultModel: "your-model", apiKeyHint: "Provider API key", docsUrl: "", notes: "Use any provider that supports OpenAI Chat Completions-compatible requests." },
];

const defaultProfile: UserProfile = {
  displayName: "",
  initials: "",
  workspaceName: "Aurora Markets Research Terminal",
  role: "",
  bio: "",
  completed: false,
};

function readLanguage(): Language {
  const saved = window.localStorage.getItem(LANGUAGE_KEY);
  return saved === "en" ? "en" : "zh";
}

function readApiConfig(): ApiConfig {
  const saved = window.localStorage.getItem(API_CONFIG_KEY);
  if (!saved) return { ...defaultApiConfig };
  try {
    return { ...defaultApiConfig, ...JSON.parse(saved) };
  } catch {
    return { ...defaultApiConfig };
  }
}

function persistApiConfig(config: ApiConfig) {
  window.localStorage.setItem(API_CONFIG_KEY, JSON.stringify(config));
}

function readProfile(): UserProfile {
  const saved = window.localStorage.getItem(PROFILE_KEY);
  if (!saved) return { ...defaultProfile };
  try {
    return { ...defaultProfile, ...JSON.parse(saved) };
  } catch {
    return { ...defaultProfile };
  }
}

function persistProfile(profile: UserProfile) {
  window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export const useTerminalStore = defineStore("terminal", {
  state: () => ({
    theme: "light" as "light" | "dark",
    language: readLanguage(),
    sidebarCollapsed: false,
    activeView: "dashboard" as ViewId,
    selectedTicker: "002594.SZ",
    candleRange: "1D",
    loading: false,
    error: "",
    market: [] as MarketPoint[],
    dashboard: null as DashboardPayload | null,
    candles: [] as CandlePoint[],
    securities: [] as Security[],
    financials: [] as FinancialRow[],
    metrics: null as MetricSnapshot | null,
    peers: null as PeerComparison | null,
    dcf: null as DcfResult | null,
    events: [] as EventItem[],
    sentiment: null as SentimentSummary | null,
    report: null as ResearchReport | null,
    job: null as AnalysisJob | null,
    aiOpen: true,
    aiMinimized: true,
    profileSetupOpen: false,
    apiConfigOpen: false,
    agentPickerOpen: false,
    agentLoading: false,
    agentRun: null as AgentRun | null,
    traceEvents: [] as AgentTraceEvent[],
    stockSuggestions: [] as StockSuggestion[],
    selectedSuggestionTicker: "",
    marketSearchResults: [] as MarketSearchResult[],
    agentForm: {
      universe: "Global new energy",
      theme: "new energy vehicles and batteries",
      tickersText: "TSLA, BYD, 002594.SZ, 1211.HK",
      maxResults: 5,
      timeHorizon: "3-6 months",
      researchFocus: "growth, valuation, sentiment, and data quality",
    },
    profile: readProfile(),
    apiConfig: readApiConfig(),
    llmProviders: defaultLlmProviders,
    toasts: [] as Array<{ id: number; text: string; tone: ToastTone }>,
    assistantMessages: [
      { role: "assistant", text: "Hi. I can summarize fundamentals, compare peers, or refresh the demo report." },
    ] as Array<{ role: "assistant" | "user"; text: string }>,
  }),
  getters: {
    selectedSecurity(state): Security | undefined {
      return state.securities.find((item) => item.ticker === state.selectedTicker || item.aliases.includes(state.selectedTicker));
    },
    selectedSuggestion(state): StockSuggestion | undefined {
      const pool = state.stockSuggestions.length ? state.stockSuggestions : state.dashboard?.selected_shortlist ?? [];
      return pool.find((item) => item.ticker === state.selectedSuggestionTicker) ?? pool[0];
    },
  },
  actions: {
    async bootstrap() {
      this.loading = true;
      this.error = "";
      try {
        await this.restoreApiConfig();
        await this.loadLlmProviders();
        const [market, securities] = await Promise.all([api.marketOverview(), api.securities()]);
        this.market = market;
        this.securities = securities;
        await this.loadTicker(this.selectedTicker);
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load terminal data";
      } finally {
        if (!this.profile.completed) {
          this.profileSetupOpen = true;
          this.apiConfigOpen = false;
        } else if (!this.apiConfig.configured && !this.apiConfig.demoMode) {
          this.apiConfigOpen = true;
        }
        this.loading = false;
      }
    },
    async restoreApiConfig() {
      try {
        const persisted = await api.getApiConfig();
        this.apiConfig = { ...defaultApiConfig, ...persisted };
        persistApiConfig(this.apiConfig);
      } catch {
        this.apiConfig = readApiConfig();
      }
    },
    async loadLlmProviders() {
      try {
        this.llmProviders = await api.llmProviders();
      } catch {
        this.llmProviders = defaultLlmProviders;
      }
    },
    updateProfile(profile: UserProfile) {
      const wasFirstRun = this.profileSetupOpen || !this.profile.completed;
      const displayName = profile.displayName.trim();
      const workspaceName = profile.workspaceName.trim();
      const role = profile.role.trim();
      const bio = profile.bio.trim();
      const initials = profile.initials.trim().replace(/[^a-z0-9\u4e00-\u9fa5]/gi, "").slice(0, 3).toUpperCase();
      this.profile = { displayName, initials, workspaceName, role, bio, completed: Boolean(displayName && initials && workspaceName && role) };
      persistProfile(this.profile);
      this.profileSetupOpen = !this.profile.completed;
      if (wasFirstRun && this.profile.completed && !this.apiConfig.configured && !this.apiConfig.demoMode) {
        this.openApiConfig();
      }
    },
    resetProfile() {
      this.profile = { ...defaultProfile };
      persistProfile(this.profile);
      this.profileSetupOpen = true;
      this.apiConfigOpen = false;
    },
    async loadTicker(ticker: string) {
      this.selectedTicker = ticker;
      const [dashboard, candles, financials, metrics, peers, dcf, events, sentiment, report] = await Promise.all([
        api.dashboard(ticker),
        api.candles(ticker, this.candleRange),
        api.financials(ticker),
        api.metrics(ticker),
        api.peers(ticker),
        api.dcf(ticker),
        api.events(ticker),
        api.sentiment(ticker),
        api.report(ticker),
      ]);
      this.dashboard = dashboard;
      this.candles = candles;
      this.financials = financials;
      this.metrics = metrics;
      this.peers = peers;
      this.dcf = dcf;
      this.events = events;
      this.sentiment = sentiment;
      this.report = report;
    },
    async setCandleRange(range: string) {
      this.candleRange = range;
      this.candles = await api.candles(this.selectedTicker, range);
      this.showToast(this.language === "zh" ? `K 线周期已切换到 ${range}` : `Candles switched to ${range}`, "success");
    },
    setLanguage(language: Language) {
      this.language = language;
      window.localStorage.setItem(LANGUAGE_KEY, language);
      this.assistantMessages = [
        {
          role: "assistant",
          text:
            language === "zh"
              ? "你好。我可以总结基本面、比较同行、解释估值，或刷新演示研报。"
              : "Hi. I can summarize fundamentals, compare peers, or refresh the demo report.",
        },
      ];
      this.showToast(language === "zh" ? "界面语言已切换为中文" : "Interface language switched to English", "success");
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },
    openApiConfig() {
      this.apiConfigOpen = true;
    },
    closeApiConfig() {
      this.apiConfigOpen = false;
    },
    async saveApiConfig(config: ApiConfig) {
      const next = {
        ...defaultApiConfig,
        ...config,
        configured: true,
        demoMode: false,
        savedAt: new Date().toISOString(),
      };
      try {
        const saved = await api.saveApiConfig(next);
        this.apiConfig = { ...defaultApiConfig, ...saved };
      } catch {
        this.apiConfig = next;
      }
      persistApiConfig(this.apiConfig);
      this.apiConfigOpen = false;
      this.showToast(this.language === "zh" ? "API 配置已保存，下次启动会自动恢复" : "API configuration saved and will restore on next launch", "success");
    },
    async useDemoMode() {
      const next = {
        ...this.apiConfig,
        configured: false,
        demoMode: true,
        savedAt: new Date().toISOString(),
      };
      try {
        const saved = await api.useDemoMode(next);
        this.apiConfig = { ...defaultApiConfig, ...saved };
      } catch {
        this.apiConfig = next;
      }
      persistApiConfig(this.apiConfig);
      this.apiConfigOpen = false;
      this.showToast(this.language === "zh" ? "已进入演示数据模式" : "Demo data mode enabled", "info");
    },
    showToast(text: string, tone: ToastTone = "info") {
      const id = Date.now() + Math.floor(Math.random() * 1000);
      this.toasts.push({ id, text, tone });
      window.setTimeout(() => {
        this.toasts = this.toasts.filter((toast) => toast.id !== id);
      }, 3200);
    },
    openAgentPicker() {
      this.activeView = "agent";
      this.agentPickerOpen = false;
    },
    closeAgentPicker() {
      this.agentPickerOpen = false;
    },
    selectSuggestion(ticker: string) {
      this.selectedSuggestionTicker = ticker;
    },
    agentPayload(primaryTicker?: string) {
      const tickers = this.agentForm.tickersText
        .split(/[,\n]/)
        .map((item) => item.trim())
        .filter(Boolean);
      return {
        universe: this.agentForm.universe,
        theme: this.agentForm.theme,
        tickers,
        max_results: this.agentForm.maxResults,
        language: this.language,
        time_horizon: this.agentForm.timeHorizon,
        research_focus: this.agentForm.researchFocus,
        primary_ticker: primaryTicker ?? null,
        llm: this.apiConfig.configured
          ? {
              provider: this.apiConfig.provider,
              provider_id: this.apiConfig.providerId,
              protocol: this.apiConfig.protocol,
              base_url: this.apiConfig.baseUrl,
              model: this.apiConfig.model,
              api_key: this.apiConfig.apiKey,
              api_version: this.apiConfig.apiVersion,
            }
          : null,
      };
    },
    async searchMarket(query: string) {
      this.marketSearchResults = await api.marketSearch(query);
    },
    async requestStockSuggestions() {
      this.agentLoading = true;
      try {
        this.stockSuggestions = await api.stockSuggestions(this.agentPayload());
        this.selectedSuggestionTicker = this.stockSuggestions[0]?.ticker ?? "";
        this.showToast(this.language === "zh" ? "AI 已生成研究候选股票" : "AI research candidates generated", "success");
      } catch (error) {
        this.showToast(error instanceof Error ? error.message : "Failed to generate stock suggestions", "error");
      } finally {
        this.agentLoading = false;
      }
    },
    async runResearchAgent(primaryTicker?: string) {
      this.agentLoading = true;
      try {
        const started = await api.researchRun(this.agentPayload(primaryTicker));
        this.agentRun = started;
        this.traceEvents = started.trace_events ?? [];
        const run = await this.pollResearchRun(started.id);
        this.agentRun = run;
        if (run.dashboard) {
          this.dashboard = run.dashboard;
          this.selectedTicker = run.dashboard.ticker;
          this.candles = await api.candles(run.dashboard.ticker, this.candleRange);
          const [financials, metrics, peers, dcf, events, sentiment, report] = await Promise.all([
            api.financials(run.dashboard.ticker),
            api.metrics(run.dashboard.ticker),
            api.peers(run.dashboard.ticker),
            api.dcf(run.dashboard.ticker),
            api.events(run.dashboard.ticker),
            api.sentiment(run.dashboard.ticker),
            api.report(run.dashboard.ticker),
          ]);
          this.financials = financials;
          this.metrics = metrics;
          this.peers = peers;
          this.dcf = dcf;
          this.events = events;
          this.sentiment = sentiment;
          this.report = report;
        }
        this.stockSuggestions = run.selected_shortlist;
        this.selectedSuggestionTicker = run.selected_shortlist[0]?.ticker ?? "";
        this.agentPickerOpen = false;
        this.activeView = "dashboard";
        this.assistantMessages.push({
          role: "assistant",
          text:
            this.language === "zh"
              ? `Research Agent 已完成 ${run.selected_shortlist.length} 个研究候选标的筛选，并刷新仪表盘。`
              : `Research Agent completed ${run.selected_shortlist.length} research candidates and refreshed the dashboard.`,
        });
        this.showToast(this.language === "zh" ? "Research Agent 已完成" : "Research Agent completed", "success");
      } catch (error) {
        this.showToast(error instanceof Error ? error.message : "Research Agent failed", "error");
      } finally {
        this.agentLoading = false;
      }
    },
    async fetchAgentTrace(runId: string) {
      this.traceEvents = await api.getResearchTrace(runId);
      return this.traceEvents;
    },
    async pollResearchRun(runId: string) {
      let latest = await api.getResearchRun(runId);
      for (let index = 0; index < 80 && latest.status !== "completed" && latest.status !== "failed"; index += 1) {
        await this.fetchAgentTrace(runId).catch(() => []);
        await new Promise((resolve) => window.setTimeout(resolve, 250));
        latest = await api.getResearchRun(runId);
        this.agentRun = latest;
      }
      await this.fetchAgentTrace(runId).catch(() => []);
      if (latest.status === "failed") {
        throw new Error(latest.message || "Research Agent failed");
      }
      return latest;
    },
    async recalcDcf(next: DcfAssumptions) {
      this.dcf = await api.recalcDcf(this.selectedTicker, next);
      this.assistantMessages.push({
        role: "assistant",
        text:
          this.language === "zh"
            ? "DCF 已重新计算，情景区间已按当前可见假设更新。"
            : "DCF recalculated. The scenario range updated using your visible assumptions.",
      });
    },
    async runAnalysis() {
      this.job = await api.runAnalysis(this.selectedTicker);
      this.report = await api.report(this.selectedTicker);
      this.assistantMessages.push({
        role: "assistant",
        text:
          this.language === "zh"
            ? "完整分析已完成，包含演示财务数据、DCF、情绪和研报章节。"
            : "Full analysis completed with demo-grounded financials, DCF, sentiment, and report sections.",
      });
    },
    sendAssistant(text: string) {
      const clean = text.trim();
      if (!clean) return;
      this.assistantMessages.push({ role: "user", text: clean });
      const lower = clean.toLowerCase();
      if (lower.includes("dcf") || lower.includes("value")) {
        this.assistantMessages.push({
          role: "assistant",
          text:
            this.language === "zh"
              ? `基础 DCF 公允价值为 ${this.dcf?.fair_value_per_share.toFixed(2)} ${this.dcf?.currency}。这只是情景输出，不是投资建议。`
              : `Base DCF fair value is ${this.dcf?.fair_value_per_share.toFixed(2)} ${this.dcf?.currency}. Treat it as scenario output, not investment advice.`,
        });
      } else if (lower.includes("risk")) {
        this.assistantMessages.push({
          role: "assistant",
          text:
            this.language === "zh"
              ? "主要风险：毛利率压力、政策/关税变化、数据源缺口，以及 DCF 对假设高度敏感。"
              : "Main risks: margin pressure, policy/tariff changes, provider data gaps, and high DCF sensitivity.",
        });
      } else if (lower.includes("compare")) {
        this.assistantMessages.push({
          role: "assistant",
          text:
            this.language === "zh"
              ? "同行比较可在 Peers 区域查看，包含中位数和溢价/折价计算。"
              : "Peer comparison is available in the Peers tab with medians and premium/discount calculations.",
        });
      } else {
        this.assistantMessages.push({
          role: "assistant",
          text:
            this.language === "zh"
              ? "当前终端聚合了基本面、同行估值、DCF、事件、情绪和研报导出，仅用于研究分析。"
              : "The current terminal view combines fundamentals, peer valuation, DCF, events, sentiment, and report export for research-only analysis.",
        });
      }
    },
  },
});
