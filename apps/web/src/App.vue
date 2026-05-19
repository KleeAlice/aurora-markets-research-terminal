<script setup lang="ts">
import {
  ArrowUpRight,
  BarChart3,
  Bell,
  Briefcase,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  FileText,
  Filter,
  Gauge,
  Globe2,
  KeyRound,
  Languages,
  LineChart,
  Menu,
  Newspaper,
  Search,
  Settings,
  Sparkles,
  Table2,
  Workflow,
  X,
} from "lucide-vue-next";
import { computed, nextTick, onMounted, ref, watch } from "vue";

import { api } from "@/api/client";
import AiAssistant from "@/components/AiAssistant.vue";
import CandlestickChart from "@/components/CandlestickChart.vue";
import ChartPanel from "@/components/ChartPanel.vue";
import type { ApiConfig, UserProfile } from "@/stores/terminal";
import type { AgentTraceEvent, EventItem, NewsCard, StockSuggestion } from "@/types";
import { useTerminalStore } from "@/stores/terminal";

const store = useTerminalStore();

const navItems = [
  { id: "dashboard", icon: Gauge },
  { id: "fundamental", icon: Table2 },
  { id: "news", icon: Newspaper },
  { id: "portfolio", icon: Briefcase },
  { id: "screener", icon: Filter },
  { id: "settings", icon: Settings },
] as const;

const rangeTabs = ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y"];
const fundamentalTabs = ["overview", "financials", "valuation", "dcf", "peers"] as const;
const newsTabs = ["all", "announcements", "earnings", "industry", "social"] as const;
const traceFilters = ["all", "search", "market", "ranking", "image", "report"] as const;

const searchDraft = ref("");
const agentSearchDraft = ref("");
const newsQuery = ref("");
const activeFundamentalTab = ref<(typeof fundamentalTabs)[number]>("overview");
const activeNewsTab = ref<(typeof newsTabs)[number]>("all");
const activeTraceFilter = ref<(typeof traceFilters)[number]>("all");
const apiDraft = ref<ApiConfig>({ ...store.apiConfig });
const profileDraft = ref<UserProfile>({ ...store.profile });
const selectedNewsId = ref("");
const selectedTopic = ref("");

type NewsFeedItem = {
  id: string;
  kind: "news" | "event" | "sentiment";
  title: string;
  source: string;
  date: string;
  category: string;
  summary: string;
  tone: "positive" | "neutral" | "negative";
  card?: NewsCard;
  event?: EventItem;
  url?: string | null;
};

function l(en: string, zh: string) {
  return store.language === "zh" ? zh : en;
}

function navLabel(id: (typeof navItems)[number]["id"]) {
  const labels = {
    dashboard: l("Dashboard", "仪表盘"),
    fundamental: l("Fundamental Analysis", "基本面分析"),
    news: l("News & Sentiment", "新闻与情绪"),
    portfolio: l("Portfolio & Compare", "组合与对比"),
    screener: l("Screener & Alerts", "筛选与提醒"),
    settings: l("Settings", "设置"),
  } as const;
  return labels[id];
}

function pageLabel(id: string) {
  const labels: Record<string, string> = {
    dashboard: l("Aurora Markets Dashboard", "Aurora Markets 仪表盘"),
    fundamental: l("Fundamental Research Workspace", "基本面研究工作台"),
    news: l("News & Sentiment Workspace", "新闻与情绪工作台"),
    portfolio: l("Portfolio & Compare Workspace", "组合与对比工作台"),
    screener: l("Screener & Alert Workspace", "筛选与提醒工作台"),
    agent: l("AI Research Candidate Workspace", "AI 研究候选工作台"),
    settings: l("Terminal Settings", "终端设置"),
  };
  return labels[id] ?? "Aurora Markets";
}

function fundamentalTabLabel(tab: (typeof fundamentalTabs)[number]) {
  const labels = {
    overview: l("Overview", "概览"),
    financials: l("Financials", "财务"),
    valuation: l("Valuation", "估值"),
    dcf: "DCF",
    peers: l("Peers", "同行"),
  } as const;
  return labels[tab];
}

function newsTabLabel(tab: (typeof newsTabs)[number]) {
  const labels = {
    all: l("All News", "全部新闻"),
    announcements: l("Announcements", "公告"),
    earnings: l("Earnings", "业绩"),
    industry: l("Industry", "行业"),
    social: l("Social Sentiment", "社交情绪"),
  } as const;
  return labels[tab];
}

function traceFilterLabel(tab: (typeof traceFilters)[number]) {
  const labels = {
    all: l("All", "全部"),
    search: l("Search", "检索"),
    market: l("Market", "行情"),
    ranking: l("Ranking", "排序"),
    image: l("Image", "图片"),
    report: l("Report", "研报"),
  } as const;
  return labels[tab];
}

function toastText(key: "date" | "notifications" | "user" | "apiTest" | "apiMissing" | "unsupported" | "loaded" | "saved" | "reset") {
  const map = {
    date: l("Date range is ready for live data integration.", "日期范围控件已预留，后续可接入真实行情。"),
    notifications: l("Alerts workspace opened.", "已打开提醒工作区。"),
    user: l("Settings opened.", "已打开设置页。"),
    apiTest: l("API fields look valid locally. Save when ready.", "本地校验通过，可以保存当前 API 配置。"),
    apiMissing: l("Please enter Base URL, model, and API key, or continue in demo mode.", "请填写 Base URL、模型名称和 API Key，或继续使用演示模式。"),
    unsupported: l("This ticker is not in the current MVP universe yet.", "该代码暂不在当前 MVP 演示范围内。"),
    loaded: l("loaded.", "已加载。"),
    saved: l("Settings saved locally.", "设置已保存在本地。"),
    reset: l("The workspace has been reset to the default research profile.", "工作台已恢复为默认研究配置。"),
  } as const;
  return map[key];
}

function dataModeLabel(mode?: string | null) {
  if (!mode) return l("Demo", "演示");
  const normalized = mode.toLowerCase();
  if (normalized === "live") return l("Live", "实时");
  if (normalized === "delayed") return l("Delayed", "延迟");
  if (normalized === "stale") return l("Stale", "陈旧");
  if (normalized === "mixed") return l("Mixed", "混合");
  return l("Demo", "演示");
}

function stepStatusLabel(status?: string) {
  switch (status) {
    case "completed":
      return l("Completed", "已完成");
    case "running":
      return l("Running", "进行中");
    case "failed":
      return l("Failed", "失败");
    default:
      return l("Queued", "排队中");
  }
}

function traceStatusLabel(status: AgentTraceEvent["status"]) {
  switch (status) {
    case "completed":
      return l("Done", "完成");
    case "running":
      return l("Running", "进行中");
    case "failed":
      return l("Failed", "失败");
    case "warning":
      return l("Warning", "警告");
    default:
      return l("Queued", "排队");
  }
}

const security = computed(() => store.dashboard?.quote ?? store.selectedSecurity);
const quotePrice = computed(() => security.value?.latest_price ?? 0);
const pageTitle = computed(() => pageLabel(store.activeView));
const marketStrip = computed(() => store.dashboard?.market_strip ?? store.market);
const agentCandidates = computed(() => (store.stockSuggestions.length ? store.stockSuggestions : store.dashboard?.selected_shortlist ?? []));
const selectedSuggestion = computed(() => store.selectedSuggestion ?? agentCandidates.value[0] ?? null);
const financialLabels = computed(() => store.financials.map((row) => String(row.fiscal_year)));
const revenueSeries = computed(() => [
  { name: l("Revenue", "收入"), data: store.financials.map((row) => row.revenue), type: "bar" as const, color: "#7bb1ff" },
  { name: l("Net Profit", "净利润"), data: store.financials.map((row) => row.net_income), color: "#2cc77b" },
]);
const sentimentLabels = computed(() => store.sentiment?.trend.map((row) => row.date.slice(5)) ?? []);
const sentimentSeries = computed(() => [
  { name: l("Positive", "正面"), data: store.sentiment?.trend.map((row) => row.positive * 100) ?? [], color: "#20b779" },
  { name: l("Neutral", "中性"), data: store.sentiment?.trend.map((row) => row.neutral * 100) ?? [], color: "#93a1b7" },
  { name: l("Negative", "负面"), data: store.sentiment?.trend.map((row) => row.negative * 100) ?? [], color: "#ff4e5f" },
]);
const newsFeed = computed<NewsFeedItem[]>(() => {
  const cards = (store.dashboard?.latest_news ?? []).map((item, index) => ({
    id: `news-${index}-${item.title}`,
    kind: "news" as const,
    title: item.title,
    source: item.source,
    date: item.date,
    category: item.category.toLowerCase(),
    summary: item.summary,
    tone: item.category.toLowerCase().includes("earnings") ? ("negative" as const) : ("positive" as const),
    card: item,
    url: item.source_url,
  }));
  const events = store.events.map((item, index) => ({
    id: `event-${index}-${item.event_title}`,
    kind: "event" as const,
    title: item.event_title,
    source: l("Research Event", "研究事件"),
    date: item.event_date,
    category: item.event_type,
    summary: item.summary,
    tone: item.risk_level === "high" ? ("negative" as const) : item.opportunity_level === "high" ? ("positive" as const) : ("neutral" as const),
    event: item,
  }));
  const social = store.sentiment
    ? [
        {
          id: `sentiment-${store.sentiment.ticker}`,
          kind: "sentiment" as const,
          title: l("Sentiment expectation gap", "情绪预期差"),
          source: l("Sentiment Model", "情绪模型"),
          date: store.sentiment.trend.at(-1)?.date ?? new Date().toISOString().slice(0, 10),
          category: "social",
          summary: store.sentiment.expectation_gap,
          tone: store.sentiment.label,
        },
      ]
    : [];
  return [...cards, ...events, ...social].sort((a, b) => b.date.localeCompare(a.date));
});
const filteredNewsFeed = computed(() => {
  const query = newsQuery.value.trim().toLowerCase();
  return newsFeed.value.filter((item) => {
    const blob = `${item.title} ${item.summary} ${item.source} ${item.category}`.toLowerCase();
    const tabMatched =
      activeNewsTab.value === "all" ||
      (activeNewsTab.value === "announcements" && item.kind === "event") ||
      (activeNewsTab.value === "earnings" && /earnings|margin|gross|revenue|financial/.test(blob)) ||
      (activeNewsTab.value === "industry" && /industry|battery|policy|product|launch|expansion|tariff/.test(blob)) ||
      (activeNewsTab.value === "social" && item.kind === "sentiment");
    const topicMatched = !selectedTopic.value || blob.includes(selectedTopic.value.toLowerCase());
    const queryMatched = !query || blob.includes(query);
    return tabMatched && topicMatched && queryMatched;
  });
});
const selectedNews = computed(() => filteredNewsFeed.value.find((item) => item.id === selectedNewsId.value) ?? filteredNewsFeed.value[0] ?? newsFeed.value[0] ?? null);
const selectedStoryImage = computed(() => {
  if (selectedNews.value?.card) return selectedNews.value.card;
  const cards = store.dashboard?.latest_news ?? [];
  const selectedWords = new Set((selectedNews.value?.title ?? "").toLowerCase().split(/\W+/).filter((word) => word.length > 4));
  return (
    cards.find((card) =>
      card.title
        .toLowerCase()
        .split(/\W+/)
        .some((word) => selectedWords.has(word)),
    ) ?? cards[0] ?? null
  );
});
const newsMetrics = computed(() => {
  const positive = store.sentiment?.trend.at(-1)?.positive ?? 0;
  const negative = store.sentiment?.trend.at(-1)?.negative ?? 0;
  return {
    total: newsFeed.value.length,
    positive: Math.round(positive * 100),
    negative: Math.round(negative * 100),
    risks: store.events.filter((item) => item.risk_level === "high" || item.risk_level === "medium").length,
  };
});
const sourceBreakdownEntries = computed(() => Object.entries(store.sentiment?.source_breakdown ?? {}));
const newsImpactBullets = computed(() => {
  const item = selectedNews.value;
  const event = item?.event as (EventItem & { financial_impact?: string; valuation_impact?: string }) | undefined;
  const bullets = [
    event?.financial_impact ?? item?.summary ?? l("Select a news item or event to inspect the investable implication.", "选择一条新闻或事件，查看它对研究判断的影响。"),
    event?.valuation_impact ?? store.sentiment?.expectation_gap ?? l("Sentiment and valuation context will appear here after data refresh.", "刷新数据后，这里会展示情绪与估值背景。"),
  ];
  if (store.metrics?.warnings?.[0]) bullets.push(store.metrics.warnings[0]);
  return bullets;
});
const tracePreview = computed(() => store.traceEvents.slice(-6).reverse());
const filteredTrace = computed(() => {
  if (activeTraceFilter.value === "all") return store.traceEvents;
  return store.traceEvents.filter((item) => item.phase === activeTraceFilter.value);
});
const assistantStatus = computed(() => {
  if (store.agentLoading) return l("Research Agent running", "研究 Agent 运行中");
  if (store.agentRun) return l("Recent run completed", "最近一次运行已完成");
  return l("Standing by", "待命");
});
const runProgress = computed(() => store.agentRun?.progress_pct ?? 0);
const selectedApiPreset = computed(() => store.llmProviders.find((item) => item.id === apiDraft.value.providerId) ?? store.llmProviders[0]);
const apiProtocolLabel = computed(() => {
  const labels = {
    "openai-compatible": l("OpenAI-compatible", "OpenAI 兼容"),
    "anthropic-messages": l("Anthropic Messages", "Anthropic Messages"),
    "azure-openai": l("Azure OpenAI", "Azure OpenAI"),
  } as const;
  return labels[apiDraft.value.protocol] ?? apiDraft.value.protocol;
});
const dataStatusCopy = computed(() => store.dashboard?.data_status?.message ?? l("Research-only output. Not investment advice.", "仅供研究，不构成投资建议。"));
const profileDisplayName = computed(() => store.profile.displayName || l("Set profile", "设置资料"));
const profileInitials = computed(() => store.profile.initials || "--");
const profileWorkspace = computed(() => store.profile.workspaceName || "Aurora Markets Research Terminal");
const profileRole = computed(() => store.profile.role || l("Not set", "未设置"));
const profileBio = computed(() => store.profile.bio || l("Complete your basic profile to personalize this research terminal.", "填写基础资料后，终端会同步显示你的研究身份。"));

onMounted(() => {
  void store.bootstrap();
});

watch(
  () => store.apiConfigOpen,
  (open) => {
    if (open) apiDraft.value = { ...store.apiConfig };
  },
);

watch(
  () => store.profile,
  (profile) => {
    profileDraft.value = { ...profile };
  },
  { deep: true },
);

function num(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);
}

function pct(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}%`;
}

function ratio(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined) return "--";
  return `${num(value, digits)}x`;
}

function metricPct(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined) return "--";
  return `${(value * 100).toFixed(digits)}%`;
}

function shortDate(value?: string | null) {
  if (!value) return l("Awaiting refresh", "等待刷新");
  return new Date(value).toLocaleString();
}

function securityBadge() {
  return security.value?.ticker?.slice(0, 4) ?? "A";
}

function selectNav(id: (typeof navItems)[number]["id"]) {
  store.activeView = id;
}

function openExport(format: "markdown" | "html" | "pdf") {
  window.open(api.exportUrl(store.selectedTicker, format), "_blank", "noopener,noreferrer");
  store.showToast(l("Report export opened.", "已打开研报导出。"), "success");
}

function toggleLanguage() {
  store.setLanguage(store.language === "en" ? "zh" : "en");
}

function openApiConfig() {
  apiDraft.value = { ...store.apiConfig };
  store.openApiConfig();
}

function testApiConfig() {
  if (!apiDraft.value.apiKey.trim() || !apiDraft.value.model.trim() || !apiDraft.value.baseUrl.trim()) {
    store.showToast(toastText("apiMissing"), "warning");
    return;
  }
  store.showToast(toastText("apiTest"), "success");
}

async function saveApiConfig() {
  if (!apiDraft.value.apiKey.trim() || !apiDraft.value.model.trim() || !apiDraft.value.baseUrl.trim()) {
    store.showToast(toastText("apiMissing"), "warning");
    return;
  }
  await store.saveApiConfig(apiDraft.value);
}

function applyProviderPreset(providerId: string) {
  const preset = store.llmProviders.find((item) => item.id === providerId);
  if (!preset) return;
  apiDraft.value = {
    ...apiDraft.value,
    provider: preset.name,
    providerId: preset.id,
    protocol: preset.protocol,
    baseUrl: preset.baseUrl,
    model: preset.defaultModel,
    apiVersion: preset.protocol === "azure-openai" ? apiDraft.value.apiVersion || "2025-01-01-preview" : "",
  };
}

function handleSearch() {
  const raw = searchDraft.value.trim();
  if (!raw) return;
  const normalized = raw.toUpperCase().replace(/\s+/g, "");
  const aliasMap: Record<string, string> = {
    BYD: "002594.SZ",
    "002594": "002594.SZ",
    "002594.SZ": "002594.SZ",
    "1211": "01211.HK",
    "1211.HK": "01211.HK",
    "01211.HK": "01211.HK",
    TSLA: "TSLA",
    TESLA: "TSLA",
  };
  const ticker = aliasMap[normalized];
  if (!ticker) {
    store.showToast(toastText("unsupported"), "warning");
    return;
  }
  void store.loadTicker(ticker).then(() => {
    store.activeView = "dashboard";
    store.showToast(`${ticker} ${toastText("loaded")}`, "success");
  });
}

function selectWatchlist(ticker: string) {
  const map: Record<string, string> = {
    BYD: "002594.SZ",
    TSLA: "TSLA",
    "01211": "01211.HK",
    "1211": "01211.HK",
  };
  const next = map[ticker.toUpperCase()] ?? ticker;
  void store.loadTicker(next).then(() => {
    store.activeView = "dashboard";
    store.showToast(`${next} ${toastText("loaded")}`, "success");
  }).catch(() => store.showToast(toastText("unsupported"), "warning"));
}

function setFundamentalTab(tab: (typeof fundamentalTabs)[number]) {
  activeFundamentalTab.value = tab;
}

function setNewsTab(tab: (typeof newsTabs)[number]) {
  activeNewsTab.value = tab;
  selectedNewsId.value = "";
  if (tab !== "social") selectedTopic.value = "";
}

function selectNewsItem(item: NewsFeedItem) {
  selectedNewsId.value = item.id;
}

function toggleNewsTopic(topic: string) {
  selectedTopic.value = selectedTopic.value === topic ? "" : topic;
  selectedNewsId.value = "";
}

function feedKindLabel(item: NewsFeedItem) {
  if (item.kind === "event") return l("Event", "事件");
  if (item.kind === "sentiment") return l("Sentiment", "情绪");
  return l("News", "新闻");
}

function refreshNewsWorkspace() {
  void store.loadTicker(store.selectedTicker).then(() => {
    selectedNewsId.value = "";
    store.showToast(l("News and sentiment refreshed.", "新闻与情绪已刷新。"), "success");
  });
}

async function resetSettings() {
  await store.useDemoMode();
  store.setLanguage("zh");
  store.showToast(toastText("reset"), "info");
}

function saveSettings() {
  store.showToast(toastText("saved"), "success");
}

function saveProfileSettings() {
  if (!profileDraft.value.displayName.trim() || !profileDraft.value.initials.trim() || !profileDraft.value.workspaceName.trim() || !profileDraft.value.role.trim()) {
    store.showToast(l("Please complete name, initials, workspace, and role.", "请完整填写姓名、头像缩写、工作区和角色。"), "warning");
    return;
  }
  store.updateProfile(profileDraft.value);
  store.showToast(l("Profile saved locally.", "个人资料已保存到本地。"), "success");
}

function resetProfileSettings() {
  store.resetProfile();
  profileDraft.value = { ...store.profile };
  store.showToast(l("Profile reset.", "个人资料已恢复默认。"), "info");
}

function openAgentWorkspace() {
  store.openAgentPicker();
  if (!agentCandidates.value.length) {
    void store.requestStockSuggestions();
  }
}

function searchAgentMarket() {
  const query = agentSearchDraft.value.trim() || store.agentForm.theme;
  if (!query) return;
  void store.searchMarket(query).then(() => {
    store.showToast(l("Market search completed.", "行情搜索已完成。"), "success");
  });
}

function addAgentTicker(ticker: string) {
  const existing = store.agentForm.tickersText
    .split(/[,\n]/)
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
  if (!existing.includes(ticker.toUpperCase())) {
    store.agentForm.tickersText = `${store.agentForm.tickersText}${store.agentForm.tickersText.trim() ? ", " : ""}${ticker}`;
  }
}

function pickCandidate(item: StockSuggestion) {
  store.selectSuggestion(item.ticker);
}

function runAgent(ticker?: string) {
  void store.runResearchAgent(ticker);
}

function refreshCurrentDashboard() {
  void store.loadTicker(store.selectedTicker).then(() => {
    store.showToast(l("Dashboard refreshed using the latest available data.", "仪表盘已按最新可用数据刷新。"), "success");
  });
}

function openMapped(view: "dashboard" | "fundamental" | "news" | "portfolio" | "screener" | "agent" | "settings") {
  store.activeView = view;
}

function openSettingsProfile() {
  store.activeView = "settings";
  void nextTick(() => {
    document.querySelector("#profile")?.scrollIntoView({ block: "start", behavior: "smooth" });
  });
}

function newsImageUrl(item: { image_url?: string | null; image_asset_id?: string | null }) {
  if (item.image_asset_id) return api.imageUrl(item.image_asset_id);
  if (item.image_url?.startsWith("/api/")) return `${api.baseUrl}${item.image_url}`;
  return item.image_url || "";
}

function tracePhaseLabel(item: AgentTraceEvent) {
  const labels: Record<string, string> = {
    search: l("Search", "检索"),
    market: l("Market", "行情"),
    ranking: l("Ranking", "排序"),
    image: l("Image", "图片"),
    report: l("Report", "研报"),
    dashboard: l("Dashboard", "仪表盘"),
  };
  return labels[item.phase] ?? item.phase;
}
</script>

<template>
  <div class="aurora-shell" :class="{ 'sidebar-collapsed': store.sidebarCollapsed }">
    <aside class="aurora-sidebar">
      <div class="aurora-brand">
        <div class="aurora-logo">{{ profileWorkspace.slice(0, 1).toUpperCase() }}</div>
        <div>
          <strong>{{ profileWorkspace }}</strong>
          <small>{{ l("Research Terminal", "研究终端") }}</small>
        </div>
      </div>

      <nav class="aurora-nav">
        <button
          v-for="item in navItems"
          :key="item.id"
          type="button"
          :class="{ active: store.activeView === item.id }"
          @click="selectNav(item.id)"
        >
          <component :is="item.icon" :size="18" />
          <span>{{ navLabel(item.id) }}</span>
        </button>
      </nav>

      <section class="upgrade-card">
        <strong>{{ l("Model & Data Access", "模型与数据接入") }}</strong>
        <p>{{ l("Manage model API, demo fallback, and local research preferences.", "集中管理模型 API、演示回退模式与本地研究偏好。") }}</p>
        <button type="button" @click="openApiConfig">{{ l("Open API Setup", "打开 API 配置") }}</button>
      </section>

      <button class="collapse-btn" type="button" @click="store.toggleSidebar">
        <Menu :size="16" />
      </button>
    </aside>

    <header class="aurora-topbar">
      <div class="page-headline">
        <h1>{{ pageTitle }}</h1>
        <p>{{ l("A bright, dense research workspace for new-energy equities.", "面向新能源股票的明亮高密度研究工作台。") }}</p>
      </div>

      <form class="top-search" @submit.prevent="handleSearch">
        <Search :size="18" />
        <input v-model="searchDraft" :placeholder="l('Search BYD, 1211.HK, TSLA...', '搜索 BYD、1211.HK、TSLA...')" />
        <kbd>Ctrl K</kbd>
      </form>

      <button class="date-picker" type="button" @click="store.showToast(toastText('date'), 'info')">
        <CalendarDays :size="16" />
        2026/05/12 - 2026/05/19
        <ChevronDown :size="16" />
      </button>

      <button class="language-toggle" type="button" @click="toggleLanguage">
        <Languages :size="16" />
        {{ store.language === "zh" ? "EN" : "中文" }}
      </button>

      <button class="bell" type="button" @click="store.showToast(toastText('notifications'), 'info')">
        <Bell :size="18" />
        <span />
      </button>

      <button class="user-menu" type="button" @click="openSettingsProfile">
        <span class="avatar">{{ profileInitials }}</span>
        <strong>{{ profileDisplayName }}</strong>
        <ChevronDown :size="16" />
      </button>
    </header>

    <main class="aurora-workspace">
      <section v-if="store.loading" class="loading-card">{{ l("Loading Aurora Markets...", "正在加载 Aurora Markets...") }}</section>
      <section v-else-if="store.error" class="loading-card error">{{ store.error }}</section>

      <Transition v-else name="page-swap" mode="out-in">
        <section v-if="store.activeView === 'dashboard'" key="dashboard" class="page dashboard-page">
          <div class="market-strip">
            <article v-for="item in marketStrip" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ num(item.value, item.label === "USD/CNY" ? 4 : 2) }}</strong>
              <em :class="{ down: item.change_pct < 0 }">{{ pct(item.change_pct) }}</em>
              <i class="mini-spark" :class="{ down: item.change_pct < 0 }" />
            </article>
          </div>

          <section class="panel dashboard-hero">
            <div class="dashboard-hero__intro">
              <div class="hero-kicker">
                <span class="hero-kicker__icon"><Sparkles :size="18" /></span>
                <div>
                  <small>{{ l("AI Research Control", "AI 研究控制台") }}</small>
                  <h2>{{ l("Refresh data, rank candidates, update dashboard.", "刷新数据，生成候选，更新仪表盘。") }}</h2>
                </div>
              </div>

              <div class="dashboard-hero__badges">
                <span><b>{{ l("API", "API") }}</b>{{ store.apiConfig.configured ? l("Configured", "已配置") : l("Demo", "演示") }}</span>
                <span><b>{{ l("Data", "数据") }}</b>{{ dataModeLabel(store.dashboard?.data_status?.mode) }}</span>
                <span><b>{{ l("Images", "图片") }}</b>{{ store.dashboard?.image_assets?.length ?? 0 }}</span>
              </div>

              <div class="dashboard-hero__actions">
                <button class="primary" type="button" @click="openAgentWorkspace">{{ l("Open AI Workspace", "打开 AI 工作台") }}</button>
                <button type="button" @click="refreshCurrentDashboard">{{ l("Refresh Data", "刷新行情") }}</button>
                <button type="button" @click="store.runAnalysis">{{ l("Generate Report", "生成研报") }}</button>
              </div>
            </div>

            <div class="dashboard-hero__candidate-strip">
              <button
                v-for="item in agentCandidates.slice(0, 4)"
                :key="item.ticker"
                type="button"
                class="candidate-chip"
                @click="selectWatchlist(item.ticker)"
              >
                <strong>{{ item.ticker }}</strong>
                <small>{{ item.company_name }}</small>
                <em>{{ item.score }}</em>
              </button>
              <button v-if="!agentCandidates.length" type="button" class="candidate-chip empty" @click="openAgentWorkspace">
                <strong>{{ l("No shortlist yet", "候选池尚未生成") }}</strong>
                <small>{{ l("Run AI selection to create one.", "运行 AI 选股后会在这里显示。") }}</small>
              </button>
            </div>
          </section>

          <section class="panel dashboard-focus">
            <div class="quote-block">
              <div class="quote-header">
                <span class="stock-logo" :class="security?.ticker?.toLowerCase()">{{ securityBadge() }}</span>
                <div>
                  <h2>{{ security?.ticker ?? "002594.SZ" }}</h2>
                  <p>{{ security?.company_name ?? "BYD Company Limited" }}</p>
                  <div class="pill-row">
                    <span>{{ security?.exchange ?? "SZSE" }}</span>
                    <span>{{ security?.market ?? "China" }}</span>
                  </div>
                </div>
              </div>

              <div class="quote-status-row">
                <b>{{ dataModeLabel(security?.data_update_status) }}</b>
                <span>{{ l("Research candidate", "研究候选") }}</span>
              </div>

              <div class="hero-price">
                <small>{{ security?.currency ?? "CNY" }}</small>
                {{ num(quotePrice, 2) }}
              </div>

              <small>{{ shortDate(store.dashboard?.updated_at) }} · {{ store.dashboard?.data_status?.provider ?? "Aurora Demo" }}</small>

              <div class="quote-info-grid">
                <article>
                  <span>{{ l("Provider", "数据源") }}</span>
                  <b>{{ store.dashboard?.data_status?.provider ?? "Aurora Demo" }}</b>
                </article>
                <article>
                  <span>{{ l("Shortlist", "候选池") }}</span>
                  <b>{{ agentCandidates.length }}</b>
                </article>
                <article>
                  <span>{{ l("Warnings", "警告") }}</span>
                  <b>{{ store.dashboard?.warnings?.length ?? 0 }}</b>
                </article>
              </div>

              <button class="quote-agent-btn" type="button" @click="openAgentWorkspace">{{ l("Run AI Filter", "运行 AI 筛选") }}</button>
            </div>

            <div class="chart-block">
              <div class="range-tabs">
                <button
                  v-for="range in rangeTabs"
                  :key="range"
                  :class="{ active: store.candleRange === range }"
                  type="button"
                  @click="store.setCandleRange(range)"
                >
                  {{ range }}
                </button>
              </div>
              <CandlestickChart :candles="store.candles" :current-price="quotePrice" :height="284" />
            </div>

            <aside class="ai-console">
              <header class="ai-console__head">
                <span><Workflow :size="18" /></span>
                <div>
                  <small>{{ l("AI Analysis Console", "AI 分析控制台") }}</small>
                  <h3>{{ l("Current research workflow", "当前研究工作流") }}</h3>
                </div>
              </header>

              <section class="ai-console__view">
                <b>{{ l("Current View", "当前结论") }}</b>
                <p>{{ store.dashboard?.agent_summary || store.dashboard?.ai_insight || l("Run the Agent to generate a structured view.", "运行 Agent 后会生成结构化研究结论。") }}</p>
              </section>

              <section class="ai-console__status">
                <span><b>{{ l("Data Status", "数据状态") }}</b>{{ dataModeLabel(store.dashboard?.data_status?.mode) }}</span>
                <span><b>{{ l("Workflow", "工作流") }}</b>{{ stepStatusLabel(store.agentRun?.status) }}</span>
                <span><b>{{ l("Progress", "进度") }}</b>{{ runProgress }}%</span>
              </section>

              <section class="ai-console__workflow">
                <span>{{ l("Candidate ranking", "候选排序") }}</span>
                <span>{{ l("Market refresh", "行情刷新") }}</span>
                <span>{{ l("Image processing", "图片处理") }}</span>
                <span>{{ l("Report handoff", "研报交接") }}</span>
              </section>

              <section class="ai-console__actions">
                <button class="primary" type="button" @click="openAgentWorkspace">{{ l("Run AI Filter & Analyze", "运行 AI 筛选分析") }}</button>
                <button type="button" @click="refreshCurrentDashboard">{{ l("Refresh Data", "刷新行情") }}</button>
                <button type="button" @click="store.runAnalysis">{{ l("Generate Report", "生成研报") }}</button>
                <button type="button" @click="openMapped('agent')">{{ l("View Candidate Pool", "查看候选池") }}</button>
              </section>

              <small class="ai-console__note">{{ dataStatusCopy }}</small>
            </aside>
          </section>

          <section class="dashboard-grid">
            <article class="panel">
              <header class="panel-head">
                <h3>{{ l("AI Watchlist", "AI 观察池") }}</h3>
                <button type="button" @click="openMapped('agent')">{{ l("Manage", "管理") }}</button>
              </header>
              <button
                v-for="item in store.dashboard?.watchlist"
                :key="item.ticker"
                class="watch-row"
                type="button"
                @click="selectWatchlist(item.ticker)"
              >
                <span class="stock-logo small" :class="item.ticker.toLowerCase()">{{ item.ticker.slice(0, 4) }}</span>
                <strong>{{ item.ticker }} <small>{{ item.exchange }}</small></strong>
                <i class="row-spark" :class="{ down: item.change_pct < 0 }" />
                <em :class="{ down: item.change_pct < 0 }">{{ num(item.price, 2) }}<br />{{ pct(item.change_pct) }}</em>
              </button>
            </article>

            <article class="panel">
              <header class="panel-head">
                <h3>{{ l("Market Heatmap", "市场热力图") }}</h3>
                <button type="button" @click="openMapped('screener')">{{ l("Open Screener", "打开筛选器") }}</button>
              </header>
              <div class="heatmap">
                <span
                  v-for="item in store.dashboard?.heatmap"
                  :key="item.ticker"
                  :class="{ down: item.change_pct < 0 }"
                  :style="{ flexGrow: item.weight }"
                >
                  <b>{{ item.ticker }}</b>
                  {{ pct(item.change_pct) }}
                </span>
              </div>
              <div class="heat-scale"><span>-3%</span><span>0%</span><span>+3%</span></div>
            </article>

            <article class="panel">
              <header class="panel-head">
                <h3>{{ l("Valuation Snapshot", "估值快照") }}</h3>
                <button type="button" @click="openMapped('fundamental')">{{ l("Details", "查看详情") }}</button>
              </header>
              <table>
                <thead>
                  <tr>
                    <th>{{ l("Ticker", "代码") }}</th>
                    <th>P/E</th>
                    <th>P/S</th>
                    <th>EV/EBITDA</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in store.dashboard?.valuation_snapshot" :key="row.ticker">
                    <td>{{ row.ticker }}</td>
                    <td>{{ ratio(row.pe) }}</td>
                    <td>{{ ratio(row.ps) }}</td>
                    <td>{{ ratio(row.ev_ebitda) }}</td>
                  </tr>
                </tbody>
              </table>
            </article>

            <article class="panel">
              <header class="panel-head">
                <h3>{{ l("Latest News", "最新新闻") }}</h3>
                <button type="button" @click="openMapped('news')">{{ l("View all", "查看全部") }}</button>
              </header>
              <div v-for="item in store.dashboard?.latest_news" :key="item.title" class="news-row">
                <img v-if="newsImageUrl(item)" class="news-thumb image" :src="newsImageUrl(item)" :alt="item.title" />
                <span v-else class="news-thumb" :class="item.image_key" />
                <strong>{{ item.title }}</strong>
                <small>{{ item.date }} · {{ item.source }}</small>
              </div>
            </article>
          </section>
        </section>

        <section v-else-if="store.activeView === 'fundamental'" key="fundamental" class="page fundamental-page">
          <section class="panel page-header">
            <div class="page-header__identity">
              <span class="stock-logo">{{ securityBadge() }}</span>
              <div>
                <h2>{{ security?.ticker ?? "002594.SZ" }}</h2>
                <p>{{ security?.company_name ?? "BYD Company Limited" }}</p>
                <div class="pill-row">
                  <span>{{ security?.exchange ?? "SZSE" }}</span>
                  <span>{{ security?.market ?? "China" }}</span>
                  <span>{{ l("New-energy leader", "新能源龙头") }}</span>
                </div>
              </div>
            </div>
            <div class="page-header__metrics">
              <strong>{{ security?.currency ?? "CNY" }} {{ num(quotePrice, 2) }}</strong>
              <em :class="{ red: (store.dashboard?.watchlist?.[0]?.change_pct ?? 0) < 0 }">{{ pct(store.dashboard?.watchlist?.[0]?.change_pct ?? 0) }}</em>
            </div>
            <div class="page-header__tabs">
              <button
                v-for="tab in fundamentalTabs"
                :key="tab"
                type="button"
                :class="{ active: activeFundamentalTab === tab }"
                @click="setFundamentalTab(tab)"
              >
                {{ fundamentalTabLabel(tab) }}
              </button>
            </div>
          </section>

          <div class="page-grid page-grid--fundamental">
            <ChartPanel :title="l('Revenue & Net Profit Trend', '收入与净利润趋势')" :labels="financialLabels" :series="revenueSeries" :height="320" />

            <section class="panel metric-grid">
              <article>
                <span>{{ l("Revenue", "收入") }}</span>
                <strong>{{ num(store.metrics?.revenue, 1) }}</strong>
                <em>{{ pct((store.metrics?.revenue_yoy ?? 0) * 100) }}</em>
              </article>
              <article>
                <span>{{ l("Net Income", "净利润") }}</span>
                <strong>{{ num(store.metrics?.net_income, 1) }}</strong>
                <em>{{ pct((store.metrics?.net_income_yoy ?? 0) * 100) }}</em>
              </article>
              <article>
                <span>ROE</span>
                <strong>{{ metricPct(store.metrics?.roe) }}</strong>
                <em>{{ l("TTM", "TTM") }}</em>
              </article>
              <article>
                <span>FCF</span>
                <strong>{{ num(store.metrics?.free_cash_flow, 1) }}</strong>
                <em>{{ pct((store.metrics?.fcf_yoy ?? 0) * 100) }}</em>
              </article>
            </section>

            <section class="panel">
              <header class="panel-head">
                <h3>{{ l("Valuation Summary", "估值摘要") }}</h3>
              </header>
              <table>
                <tbody>
                  <tr><td>P/E</td><td>{{ ratio(store.metrics?.pe) }}</td><td>P/B</td><td>{{ ratio(store.metrics?.pb) }}</td></tr>
                  <tr><td>PEG</td><td>{{ ratio(store.metrics?.peg) }}</td><td>EV/EBITDA</td><td>{{ ratio(store.peers?.medians?.ev_ebitda) }}</td></tr>
                </tbody>
              </table>
            </section>

            <section class="panel">
              <header class="panel-head">
                <h3>DCF</h3>
              </header>
              <div class="dcf-hero">
                <strong>{{ num(store.dcf?.fair_value_per_share, 2) }} {{ store.dcf?.currency ?? "CNY" }}</strong>
                <small>{{ l("Base fair value per share", "基础每股公允价值") }}</small>
              </div>
              <div class="pill-row">
                <span>{{ l("Discount Rate", "折现率") }} {{ metricPct(store.dcf?.scenarios?.[1]?.assumptions.discount_rate) }}</span>
                <span>{{ l("Terminal Growth", "永续增长") }} {{ metricPct(store.dcf?.scenarios?.[1]?.assumptions.terminal_growth_rate) }}</span>
              </div>
            </section>

            <section class="panel panel-span-2">
              <header class="panel-head">
                <h3>{{ l("Peers Comparison", "同行对比") }}</h3>
              </header>
              <table>
                <thead>
                  <tr>
                    <th>{{ l("Company", "公司") }}</th>
                    <th>P/E</th>
                    <th>P/S</th>
                    <th>ROE</th>
                    <th>{{ l("Reason", "原因") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="peer in store.peers?.peers.slice(0, 5)" :key="peer.ticker">
                    <td>{{ peer.company_name }}</td>
                    <td>{{ ratio(peer.pe) }}</td>
                    <td>{{ ratio(peer.ps) }}</td>
                    <td>{{ metricPct(peer.roe) }}</td>
                    <td>{{ peer.reason }}</td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section class="panel">
              <header class="panel-head">
                <h3>{{ l("AI Takeaway", "AI 结论") }}</h3>
              </header>
              <p>{{ store.dashboard?.agent_summary || store.dashboard?.ai_insight }}</p>
              <div class="pill-row">
                <span>{{ l("Research-only", "仅供研究") }}</span>
                <span>{{ l("Sources checked", "已校验来源") }}</span>
                <span>{{ l("Visible assumptions", "假设可见") }}</span>
              </div>
            </section>
          </div>
        </section>

        <section v-else-if="store.activeView === 'news'" key="news" class="page news-page">
          <div class="tabs">
            <button
              v-for="tab in newsTabs"
              :key="tab"
              type="button"
              :class="{ active: activeNewsTab === tab }"
              @click="setNewsTab(tab)"
            >
              {{ newsTabLabel(tab) }}
            </button>
          </div>

          <section class="panel news-command">
            <div>
              <small>{{ l("Current ticker", "当前标的") }}</small>
              <strong>{{ store.selectedTicker }}</strong>
              <span>{{ dataStatusCopy }}</span>
            </div>
            <label class="news-local-search">
              <Search :size="18" />
              <input v-model="newsQuery" :placeholder="l('Search news, events, topics...', '搜索新闻、事件、主题...')" />
            </label>
            <div class="news-command__actions">
              <button type="button" @click="refreshNewsWorkspace">{{ l("Refresh News", "刷新新闻") }}</button>
              <button class="primary" type="button" @click="runAgent(store.selectedTicker)">{{ l("Run AI Check", "运行 AI 核查") }}</button>
            </div>
          </section>

          <section class="news-workbench">
            <aside class="panel news-feed-panel">
              <header class="panel-head">
                <div>
                  <h3>{{ l("Research Feed", "研究信息流") }}</h3>
                  <small>{{ filteredNewsFeed.length }} / {{ newsMetrics.total }} {{ l("items", "条") }}</small>
                </div>
              </header>

              <div class="news-metric-strip">
                <article><span>{{ l("Positive", "正面") }}</span><strong>{{ newsMetrics.positive }}%</strong></article>
                <article><span>{{ l("Negative", "负面") }}</span><strong>{{ newsMetrics.negative }}%</strong></article>
                <article><span>{{ l("Risk Events", "风险事件") }}</span><strong>{{ newsMetrics.risks }}</strong></article>
              </div>

              <div class="news-feed-list">
                <button
                  v-for="item in filteredNewsFeed"
                  :key="item.id"
                  type="button"
                  class="news-feed-item"
                  :class="[item.tone, { active: selectedNews?.id === item.id }]"
                  @click="selectNewsItem(item)"
                >
                  <span>{{ feedKindLabel(item) }}</span>
                  <strong>{{ item.title }}</strong>
                  <small>{{ item.date }} · {{ item.source }}</small>
                </button>
                <div v-if="!filteredNewsFeed.length" class="empty-state compact">
                  <strong>{{ l("No matching news", "没有匹配内容") }}</strong>
                  <p>{{ l("Clear the search or switch tabs to restore the feed.", "清空搜索或切换分类即可恢复信息流。") }}</p>
                </div>
              </div>
            </aside>

            <article class="panel news-story-panel">
              <div v-if="selectedNews" class="story-detail">
                <img
                  v-if="selectedStoryImage && newsImageUrl(selectedStoryImage)"
                  class="story-photo image"
                  :src="newsImageUrl(selectedStoryImage)"
                  :alt="selectedNews.title"
                />
                <div v-else class="story-photo story-photo--fallback">
                  <span>{{ selectedNews.kind === "sentiment" ? "AI" : selectedNews.source.slice(0, 1) }}</span>
                </div>
                <div class="story-detail__copy">
                  <div class="story-meta">
                    <span>{{ selectedNews.date }}</span>
                    <span>{{ selectedNews.source }}</span>
                    <b :class="selectedNews.tone">{{ selectedNews.tone }}</b>
                  </div>
                  <h2>{{ selectedNews.title }}</h2>
                  <p>{{ selectedNews.summary }}</p>
                  <div v-if="selectedNews.event" class="event-impact-grid">
                    <article><span>{{ l("Risk", "风险") }}</span><strong>{{ selectedNews.event.risk_level }}</strong></article>
                    <article><span>{{ l("Opportunity", "机会") }}</span><strong>{{ selectedNews.event.opportunity_level }}</strong></article>
                    <article><span>{{ l("Confidence", "置信度") }}</span><strong>{{ Math.round(selectedNews.event.confidence * 100) }}%</strong></article>
                  </div>
                  <div class="story-actions">
                    <a v-if="selectedNews.url" :href="selectedNews.url" target="_blank" rel="noreferrer">{{ l("Open Source", "打开来源") }}</a>
                    <button type="button" @click="openMapped('fundamental')">{{ l("Check Fundamentals", "查看基本面") }}</button>
                    <button type="button" @click="openExport('markdown')">{{ l("Export Note", "导出笔记") }}</button>
                  </div>
                </div>
              </div>
            </article>

            <section class="news-side-stack">
              <ChartPanel :title="l('Sentiment Trend', '情绪趋势')" :labels="sentimentLabels" :series="sentimentSeries" :height="250" />

              <article class="panel topics actionable-topics">
                <h3>{{ l("Topics", "主题") }}</h3>
                <button
                  v-for="topic in store.sentiment?.topic_clusters"
                  :key="topic"
                  type="button"
                  :class="{ active: selectedTopic === topic }"
                  @click="toggleNewsTopic(topic)"
                >
                  {{ topic }}
                </button>
              </article>

              <article class="panel source-mix">
                <h3>{{ l("Source Mix", "来源结构") }}</h3>
                <div v-for="[source, count] in sourceBreakdownEntries" :key="source">
                  <span>{{ source }}</span>
                  <b>{{ count }}</b>
                  <i :style="{ width: `${Math.min(100, Number(count) * 5)}%` }" />
                </div>
              </article>
            </section>

            <article class="panel impact-card">
              <h3>{{ l("Research Impact", "研究影响") }}</h3>
              <ul>
                <li v-for="item in newsImpactBullets" :key="item">{{ item }}</li>
              </ul>
            </article>

            <article class="panel timeline-list">
              <header class="panel-head">
                <h3>{{ l("Event Timeline", "事件时间线") }}</h3>
              </header>
              <button
                v-for="event in store.events"
                :key="event.event_title"
                type="button"
                @click="selectedNewsId = `event-${store.events.indexOf(event)}-${event.event_title}`"
              >
                <span class="source-dot">{{ event.risk_level.slice(0, 1).toUpperCase() }}</span>
                <p><small>{{ event.event_date }} · {{ event.event_type }}</small><br />{{ event.event_title }}</p>
                <em>{{ event.risk_level === "high" ? l("Risk", "风险") : l("Watch", "观察") }}</em>
              </button>
            </article>
          </section>

          <section v-if="false" class="news-layout">
            <article class="panel featured-news">
              <img
                v-if="store.dashboard?.latest_news?.[0] && newsImageUrl(store.dashboard?.latest_news?.[0] ?? {})"
                class="feature-photo image"
                :src="newsImageUrl(store.dashboard?.latest_news?.[0] ?? {})"
                :alt="store.dashboard?.latest_news?.[0]?.title ?? ''"
              />
              <span v-else class="feature-photo" />
              <div>
                <b>{{ l("Featured Story", "重点新闻") }}</b>
                <h2>{{ store.dashboard?.latest_news?.[0]?.title ?? l("No featured story yet.", "暂无重点新闻。") }}</h2>
                <p>{{ store.dashboard?.latest_news?.[0]?.summary ?? l("Run the Agent to refresh source-linked news cards.", "运行 Agent 后会刷新带来源图片的新闻卡片。") }}</p>
                <em>{{ store.dashboard?.agent_summary ?? l("Research-only summary.", "仅供研究的摘要。") }}</em>
              </div>
            </article>

            <ChartPanel :title="l('Sentiment Trend', '情绪趋势')" :labels="sentimentLabels" :series="sentimentSeries" :height="300" />

            <article class="panel timeline-list">
              <header class="panel-head">
                <h3>{{ l("News Timeline", "新闻时间线") }}</h3>
              </header>
              <div v-for="event in store.events" :key="event.event_title">
                <span class="source-dot">C</span>
                <p><small>{{ event.event_date }}</small><br />{{ event.event_title }}</p>
                <em>{{ event.risk_level === "high" ? l("Risk", "风险") : l("Watch", "观察") }}</em>
              </div>
            </article>

            <article class="panel topics">
              <h3>{{ l("Key Topics", "关键主题") }}</h3>
              <span v-for="topic in store.sentiment?.topic_clusters" :key="topic">{{ topic }}</span>
            </article>

            <article class="panel impact-card">
              <h3>{{ l("AI Market Impact", "AI 市场影响") }}</h3>
              <p>{{ l("Recent news flow remains useful for scenario analysis, but still requires valuation and policy context.", "近期新闻流适合做情景分析，但仍需结合估值与政策背景理解。") }}</p>
            </article>

            <article class="panel research-summary">
              <h3>{{ l("Industry Research Summary", "行业研究摘要") }}</h3>
              <p>{{ l("NEV demand is still shaped by policy, exports, and battery cost trends.", "新能源车需求仍主要受政策、出海和电池成本趋势驱动。") }}</p>
              <p>{{ l("News image slots now prefer source-linked visuals instead of generic placeholders.", "新闻图片区优先使用带来源的真实图片，而不是随意占位图。") }}</p>
            </article>
          </section>
        </section>

        <section v-else-if="store.activeView === 'portfolio'" key="portfolio" class="page portfolio-page">
          <div class="page-grid page-grid--portfolio">
            <section class="panel stats-row">
              <article><span>{{ l("Tracked Value", "跟踪市值") }}</span><strong>1,256,780</strong><em>HKD</em></article>
              <article><span>{{ l("Day Change", "日内变化") }}</span><strong>+12,840</strong><em>+1.03%</em></article>
              <article><span>{{ l("Research Return", "研究组合回报") }}</span><strong>+156,780</strong><em>+14.24%</em></article>
            </section>

            <ChartPanel
              :title="l('Research Basket Performance', '研究篮子表现')"
              :labels="['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May']"
              :series="[
                { name: l('Research Basket', '研究篮子'), data: [-1, 2, 6, 13, 9, 12, 16], color: '#246bfe' },
                { name: l('Benchmark', '基准'), data: [-2, 1, 3, -3, -7, -1, 3], color: '#9aa6b8' },
              ]"
              :height="310"
            />

            <section class="panel">
              <h3>{{ l("Allocation by Region", "地区配置") }}</h3>
              <div class="donut">100%</div>
              <p>{{ l("China", "中国") }} 55.2%</p>
              <p>{{ l("United States", "美国") }} 28.4%</p>
              <p>{{ l("Europe", "欧洲") }} 8.7%</p>
              <p>{{ l("Cash", "现金") }} 2.4%</p>
            </section>

            <section class="panel">
              <h3>{{ l("BYD vs TSLA", "比亚迪 vs 特斯拉") }}</h3>
              <table>
                <tbody>
                  <tr><td>{{ l("Revenue Growth", "收入增长") }}</td><td>25.0%</td><td class="red">-9.2%</td></tr>
                  <tr><td>{{ l("Gross Margin", "毛利率") }}</td><td>20.1%</td><td>17.4%</td></tr>
                  <tr><td>P/E</td><td>21.0x</td><td class="red">52.3x</td></tr>
                </tbody>
              </table>
            </section>

            <section class="panel panel-span-2">
              <h3>{{ l("Research Holdings", "研究持仓") }}</h3>
              <table>
                <tbody>
                  <tr v-for="item in store.dashboard?.watchlist" :key="item.ticker" @click="selectWatchlist(item.ticker)">
                    <td>{{ item.ticker }}</td>
                    <td>{{ item.company_name }}</td>
                    <td>{{ num(item.price, 2) }}</td>
                    <td :class="{ red: item.change_pct < 0 }">{{ pct(item.change_pct) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
          </div>
        </section>

        <section v-else-if="store.activeView === 'screener'" key="screener" class="page screener-page">
          <section class="panel filter-bar">
            <span><Globe2 :size="18" />{{ l("Market", "市场") }}<b>{{ l("Global", "全球") }}</b></span>
            <span>{{ l("Industry", "行业") }}<b>{{ l("New Energy", "新能源") }}</b></span>
            <span>{{ l("Market Cap", "市值") }}<b>$10B+</b></span>
            <span>PE<b>&lt; 35</b></span>
            <span>{{ l("Revenue Growth", "收入增长") }}<b>&gt; 15% YoY</b></span>
            <button type="button" @click="openMapped('agent')">{{ l("Open AI Filter", "打开 AI 筛选") }}</button>
          </section>

          <div class="page-grid page-grid--screener">
            <section class="panel panel-span-2">
              <header class="panel-head">
                <h3>{{ l("Matched Research Candidates", "匹配到的研究候选") }}</h3>
              </header>
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{{ l("Stock", "股票") }}</th>
                    <th>{{ l("Price", "价格") }}</th>
                    <th>{{ l("Change", "涨跌") }}</th>
                    <th>P/E</th>
                    <th>{{ l("Revenue Growth", "收入增长") }}</th>
                    <th>ROE</th>
                    <th>AI</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in agentCandidates.length ? agentCandidates : (store.dashboard?.selected_shortlist ?? [])" :key="item.ticker">
                    <td>{{ index + 1 }}</td>
                    <td>{{ item.ticker }}<br /><small>{{ item.exchange }}</small></td>
                    <td>{{ num(security?.latest_price, 2) }}</td>
                    <td>{{ pct((store.dashboard?.watchlist?.[index]?.change_pct ?? 0)) }}</td>
                    <td>{{ index === 2 ? "53.3x" : "20.1x" }}</td>
                    <td>+{{ 42 - index * 5 }}.3%</td>
                    <td>{{ index === 3 ? "-8.6%" : "21.0%" }}</td>
                    <td><b class="score">{{ item.score }}</b></td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section class="panel">
              <h3>{{ l("Why these candidates?", "为什么是这些候选？") }}</h3>
              <p>{{ l("The screener mixes rules, delayed quotes, valuation visibility, and source quality into a research priority score.", "筛选器把规则、延迟行情、估值透明度和来源质量合成为研究优先级评分。") }}</p>
            </section>

            <section class="panel">
              <h3>{{ l("Alerts", "提醒") }}</h3>
              <p>{{ l("Earnings alert: CATL reports in 2 days.", "业绩提醒：宁德时代将在 2 天后发布业绩。") }}</p>
              <p>{{ l("Unusual volume: NIO volume is 3.2x normal.", "异动提醒：NIO 成交量达到平时 3.2 倍。") }}</p>
              <p>{{ l("Sentiment shift: XPEV turned positive.", "情绪提醒：小鹏情绪转正。") }}</p>
            </section>
          </div>
        </section>

        <section v-else-if="store.activeView === 'agent'" key="agent" class="page agent-page">
          <section class="agent-header panel">
            <div>
              <small>{{ l("AI Research Workspace", "AI 研究工作台") }}</small>
              <h2>{{ l("Generate candidates, review, then run research.", "生成候选，审阅后启动研究。") }}</h2>
              <p>{{ l("A compact workspace for candidate screening and trace review.", "用于候选筛选和过程追踪的紧凑工作台。") }}</p>
            </div>
            <div class="agent-header__actions">
              <button class="primary" type="button" @click="store.requestStockSuggestions" :disabled="store.agentLoading">
                {{ store.agentLoading ? l("Generating...", "生成中...") : l("Generate AI Suggestions", "生成 AI 候选") }}
              </button>
              <button type="button" @click="runAgent(selectedSuggestion?.ticker ?? undefined)" :disabled="store.agentLoading">
                {{ store.agentLoading ? l("Running...", "运行中...") : l("Run Research Agent", "运行研究 Agent") }}
              </button>
            </div>
          </section>

          <section class="agent-layout">
            <form class="panel agent-form" @submit.prevent="store.requestStockSuggestions">
              <label>
                <span>{{ l("Universe", "市场范围") }}</span>
                <input v-model="store.agentForm.universe" />
              </label>
              <label>
                <span>{{ l("Theme", "主题") }}</span>
                <input v-model="store.agentForm.theme" />
              </label>
              <label>
                <span>{{ l("Max Results", "结果数量") }}</span>
                <input v-model.number="store.agentForm.maxResults" type="number" min="1" max="12" />
              </label>
              <label>
                <span>{{ l("Time Horizon", "研究周期") }}</span>
                <input v-model="store.agentForm.timeHorizon" />
              </label>
              <label class="wide">
                <span>{{ l("Research Focus", "研究重点") }}</span>
                <input v-model="store.agentForm.researchFocus" />
              </label>
              <label class="wide">
                <span>{{ l("Manual Tickers", "手动输入代码") }}</span>
                <textarea v-model="store.agentForm.tickersText" rows="5" />
              </label>

              <div class="agent-form__search">
                <div class="agent-search">
                  <Search :size="16" />
                  <input v-model="agentSearchDraft" :placeholder="l('Search live/delayed market data', '搜索实时/延迟行情')" @keyup.enter="searchAgentMarket" />
                </div>
                <button type="button" @click="searchAgentMarket">{{ l("Search", "搜索") }}</button>
              </div>

              <div v-if="store.marketSearchResults.length" class="search-results">
                <button v-for="item in store.marketSearchResults.slice(0, 6)" :key="item.ticker" type="button" @click="addAgentTicker(item.ticker)">
                  <strong>{{ item.ticker }}</strong>
                  <span>{{ item.company_name }}</span>
                  <em>{{ l("Add", "加入") }}</em>
                </button>
              </div>
            </form>

            <section class="panel candidate-list-pane">
              <header class="panel-head">
                <h3>{{ l("Research Candidates", "研究候选") }}</h3>
                <small>{{ agentCandidates.length }} {{ l("items", "项") }}</small>
              </header>

              <div class="candidate-list">
                <button
                  v-for="item in agentCandidates"
                  :key="item.ticker"
                  type="button"
                  class="candidate-row"
                  :class="{ active: selectedSuggestion?.ticker === item.ticker }"
                  @click="pickCandidate(item)"
                >
                  <div class="candidate-row__main">
                    <strong>{{ item.ticker }}</strong>
                    <span>{{ item.company_name }}</span>
                  </div>
                  <div class="candidate-row__meta">
                    <small>{{ item.exchange }}</small>
                    <em>{{ item.data_status }}</em>
                  </div>
                  <b class="candidate-row__score">{{ item.score }}</b>
                </button>

                <div v-if="!agentCandidates.length" class="empty-state">
                  <strong>{{ l("No shortlist yet", "还没有候选池") }}</strong>
                  <p>{{ l("Generate suggestions on the left to populate this list.", "先在左侧生成建议，这里会出现候选列表。") }}</p>
                </div>
              </div>
            </section>

            <section class="panel candidate-detail-pane">
              <header class="panel-head">
                <div>
                  <h3>{{ selectedSuggestion?.ticker ?? l("Candidate detail", "候选详情") }}</h3>
                  <small>{{ selectedSuggestion?.company_name ?? l("Select a candidate from the list.", "从列表中选择一个候选。") }}</small>
                </div>
                <span v-if="selectedSuggestion" class="detail-score">{{ selectedSuggestion.score }}</span>
              </header>

              <div v-if="selectedSuggestion" class="candidate-detail">
                <div class="pill-row">
                  <span>{{ selectedSuggestion.exchange }}</span>
                  <span>{{ selectedSuggestion.market }}</span>
                  <span>{{ selectedSuggestion.data_status }}</span>
                </div>

                <article class="detail-card">
                  <label>{{ l("Research Thesis", "研究理由") }}</label>
                  <p>{{ selectedSuggestion.thesis }}</p>
                </article>

                <article class="detail-card">
                  <label>{{ l("Source References", "来源参考") }}</label>
                  <ul class="source-list">
                    <li v-for="source in selectedSuggestion.sources" :key="source.url">
                      <a :href="source.url" target="_blank" rel="noreferrer">{{ source.title }}</a>
                    </li>
                  </ul>
                </article>

                <article class="detail-card">
                  <label>{{ l("Next Actions", "下一步操作") }}</label>
                  <div class="detail-actions">
                    <button class="primary" type="button" @click="runAgent(selectedSuggestion.ticker)">{{ l("Run AI Analysis", "运行 AI 分析") }}</button>
                    <button type="button" @click="selectWatchlist(selectedSuggestion.ticker)">{{ l("Load on Dashboard", "加载到仪表盘") }}</button>
                  </div>
                </article>
              </div>
              <div v-else class="empty-state">
                <strong>{{ l("Pick a candidate", "请选择候选") }}</strong>
                <p>{{ l("The right pane now holds the full thesis so long text no longer collapses into a narrow column.", "右侧现在专门承接完整 thesis，长文本不会再挤成一条窄竖列。") }}</p>
              </div>
            </section>

            <section class="panel agent-trace-pane">
              <header class="panel-head">
                <div>
                  <h3>{{ l("AI Work Trace", "AI 工作过程") }}</h3>
                  <small>{{ l("Audit-friendly retrieval, ranking, and refresh events.", "可审计的检索、排序与刷新事件流。") }}</small>
                </div>
                <div class="trace-filters">
                  <button
                    v-for="tab in traceFilters"
                    :key="tab"
                    type="button"
                    :class="{ active: activeTraceFilter === tab }"
                    @click="activeTraceFilter = tab"
                  >
                    {{ traceFilterLabel(tab) }}
                  </button>
                </div>
              </header>

              <div v-if="store.agentRun" class="trace-progress">
                <div class="trace-progress__bar"><i :style="{ width: `${runProgress}%` }" /></div>
                <small>{{ stepStatusLabel(store.agentRun.status) }} · {{ runProgress }}%</small>
              </div>

              <div class="trace-list">
                <article v-for="item in filteredTrace" :key="item.id" class="trace-item" :class="item.status">
                  <span class="trace-item__dot" />
                  <div>
                    <div class="trace-item__head">
                      <strong>{{ item.title }}</strong>
                      <em>{{ traceStatusLabel(item.status) }}</em>
                    </div>
                    <small>{{ tracePhaseLabel(item) }} · {{ new Date(item.timestamp).toLocaleTimeString() }}</small>
                    <p>{{ item.detail }}</p>
                  </div>
                </article>
                <div v-if="!filteredTrace.length" class="empty-state compact">
                  <strong>{{ l("No trace yet", "还没有过程流") }}</strong>
                  <p>{{ l("Once the Agent starts, retrieval and ranking steps will stream here.", "Agent 启动后，检索与排序步骤会持续显示在这里。") }}</p>
                </div>
              </div>
            </section>
          </section>
        </section>

        <section v-else key="settings" class="page settings-page">
          <section class="settings-shell">
            <aside class="settings-rail panel" aria-label="Settings sections">
              <div class="settings-profile-card">
                <span class="avatar xlarge">{{ profileInitials }}</span>
                <div>
                  <strong>{{ profileDisplayName }}</strong>
                  <span>{{ profileRole }}</span>
                  <small>{{ profileWorkspace }}</small>
                </div>
              </div>

              <nav class="settings-nav">
                <a href="#profile"><span>{{ l("Profile", "个人资料") }}</span><small>{{ l("Identity", "身份") }}</small></a>
                <a href="#model-api"><span>{{ l("Model API", "模型 API") }}</span><small>{{ l("Providers", "厂商") }}</small></a>
                <a href="#preferences"><span>{{ l("Preferences", "偏好设置") }}</span><small>{{ l("Language", "语言") }}</small></a>
                <a href="#workspace"><span>{{ l("Workspace", "工作区") }}</span><small>{{ l("Layout", "布局") }}</small></a>
                <a href="#exports"><span>{{ l("Exports", "导出") }}</span><small>{{ l("Reports", "报告") }}</small></a>
                <a href="#guardrails"><span>{{ l("Guardrails", "研究边界") }}</span><small>{{ l("Safety", "安全") }}</small></a>
              </nav>
            </aside>

            <div class="settings-content">
              <article id="profile" class="panel settings-panel settings-profile-panel">
                <div class="settings-section-head">
                  <div>
                    <span>{{ l("Account", "账户") }}</span>
                    <h3>{{ l("Personal Profile", "个人资料") }}</h3>
                  </div>
                  <span class="status-pill">{{ l("Local profile", "本地资料") }}</span>
                </div>
                <div class="profile-summary">
                  <span class="avatar xlarge">{{ profileInitials }}</span>
                  <div>
                    <strong>{{ profileDisplayName }}</strong>
                    <p>{{ profileBio }}</p>
                  </div>
                </div>
                <div class="settings-field-grid">
                  <label>
                    <span>{{ l("Display name", "显示名称") }}</span>
                    <input v-model="profileDraft.displayName" />
                  </label>
                  <label>
                    <span>{{ l("Initials", "头像缩写") }}</span>
                    <input v-model="profileDraft.initials" maxlength="3" />
                  </label>
                  <label>
                    <span>{{ l("Workspace", "工作空间") }}</span>
                    <input v-model="profileDraft.workspaceName" />
                  </label>
                  <label>
                    <span>{{ l("Role", "角色") }}</span>
                    <input v-model="profileDraft.role" />
                  </label>
                </div>
                <label class="profile-bio-field">
                  <span>{{ l("Bio", "简介") }}</span>
                  <textarea v-model="profileDraft.bio" rows="3" />
                </label>
                <div class="settings-actions">
                  <button class="save-changes" type="button" @click="saveProfileSettings">{{ l("Save Profile", "保存个人资料") }}</button>
                  <button class="reset-btn" type="button" @click="resetProfileSettings">{{ l("Reset Profile", "恢复默认资料") }}</button>
                </div>
              </article>

              <article id="model-api" class="panel settings-panel">
              <h3><KeyRound :size="18" /> {{ l("API Configuration", "API 配置") }}</h3>
              <p>{{ l("Your model configuration persists locally and can be reopened here anytime.", "你的模型配置会持久化保存在本地，也可以随时在这里重新打开。") }}</p>
              <label>
                <span>{{ l("Status", "状态") }}</span>
                <button type="button" class="status-pill" @click="openApiConfig">
                  <CheckCircle2 :size="14" />
                  {{ store.apiConfig.configured ? l("Configured", "已配置") : store.apiConfig.demoMode ? l("Demo Mode", "演示模式") : l("Not Configured", "未配置") }}
                </button>
              </label>
              <label>
                <span>{{ l("Provider", "服务商") }}</span>
                <button type="button" @click="openApiConfig">{{ store.apiConfig.provider }}</button>
              </label>
              <button class="save-changes" type="button" @click="openApiConfig">{{ l("Open API Setup", "打开 API 配置") }}</button>
            </article>

              <article id="preferences" class="panel settings-panel">
              <h3><Languages :size="18" /> {{ l("Language", "语言") }}</h3>
              <p>{{ l("Chinese is the default workspace language, with English available anytime.", "中文是默认工作语言，英文可以随时切换。") }}</p>
              <label>
                <span>中文</span>
                <button type="button" :class="{ selected: store.language === 'zh' }" @click="store.setLanguage('zh')">中文</button>
              </label>
              <label>
                <span>English</span>
                <button type="button" :class="{ selected: store.language === 'en' }" @click="store.setLanguage('en')">EN</button>
              </label>
            </article>

              <article id="workspace" class="panel settings-panel">
              <h3><BarChart3 :size="18" /> {{ l("Workspace Behavior", "工作台行为") }}</h3>
              <p>{{ l("Tune the terminal for demo-first research, export, and floating AI behavior.", "调整演示优先的研究节奏、导出方式与悬浮 AI 行为。") }}</p>
              <label><span>{{ l("Sidebar", "侧边栏") }}</span><button type="button" @click="store.toggleSidebar">{{ store.sidebarCollapsed ? l("Collapsed", "已折叠") : l("Expanded", "已展开") }}</button></label>
              <label><span>{{ l("AI Dock", "AI 浮窗") }}</span><button type="button" @click="store.aiMinimized = !store.aiMinimized">{{ store.aiMinimized ? l("Minimized", "已最小化") : l("Open", "已展开") }}</button></label>
            </article>

              <article id="exports" class="panel settings-panel">
              <h3><FileText :size="18" /> {{ l("Exports", "导出") }}</h3>
              <p>{{ l("Export current research output in multiple formats.", "将当前研究输出导出为多种格式。") }}</p>
              <div class="settings-actions">
                <button type="button" @click="openExport('markdown')">Markdown</button>
                <button type="button" @click="openExport('html')">HTML</button>
                <button type="button" @click="openExport('pdf')">PDF</button>
              </div>
            </article>

              <article id="guardrails" class="panel settings-panel settings-panel--wide">
              <h3>{{ l("Research Guardrails", "研究边界") }}</h3>
              <p>{{ l("This product remains research-only. It can shortlist, summarize, rank, and refresh, but it does not place trades or give personalized investment advice.", "本产品始终定位为研究工具。它可以筛选、总结、排序和刷新面板，但不会执行交易，也不会提供个性化投资建议。") }}</p>
              <div class="pill-row">
                <span>{{ l("Research-only", "仅供研究") }}</span>
                <span>{{ l("Source-linked", "带来源") }}</span>
                <span>{{ l("Model optional", "模型可选") }}</span>
              </div>
            </article>

              <div class="settings-footer">
              <button class="save-changes" type="button" @click="saveSettings">{{ l("Save Changes", "保存设置") }}</button>
              <button class="reset-btn" type="button" @click="resetSettings">{{ l("Reset to Defaults", "恢复默认") }}</button>
              </div>
            </div>
          </section>
        </section>
      </Transition>
    </main>

    <Teleport to="body">
      <Transition name="modal-pop">
        <div v-if="store.profileSetupOpen" class="api-modal-backdrop">
          <section class="api-modal profile-setup-modal" role="dialog" aria-modal="true" :aria-label="l('Set Basic Profile', '设置基础资料')">
            <header>
              <div>
                <span class="modal-icon"><Sparkles :size="20" /></span>
                <h2>{{ l("Set Basic Profile", "设置基础资料") }}</h2>
                <p>{{ l("Complete these fields before entering the research terminal.", "首次进入前，请先填写基础身份信息。") }}</p>
              </div>
            </header>

            <form class="profile-setup-form" @submit.prevent="saveProfileSettings">
              <div class="profile-setup-preview">
                <span class="avatar xlarge">{{ profileDraft.initials.trim().slice(0, 3).toUpperCase() || "--" }}</span>
                <div>
                  <strong>{{ profileDraft.displayName || l("Your name", "你的姓名") }}</strong>
                  <small>{{ profileDraft.workspaceName || "Aurora Markets Research Terminal" }} · {{ profileDraft.role || l("Role", "角色") }}</small>
                </div>
              </div>
              <label>
                <span>{{ l("Display name", "显示名称") }}</span>
                <input v-model="profileDraft.displayName" required autocomplete="name" :placeholder="l('e.g. Researcher', '例如：研究员姓名')" />
              </label>
              <label>
                <span>{{ l("Initials", "头像缩写") }}</span>
                <input v-model="profileDraft.initials" required maxlength="3" placeholder="AB" />
              </label>
              <label>
                <span>{{ l("Workspace", "工作区名称") }}</span>
                <input v-model="profileDraft.workspaceName" required placeholder="Aurora Markets Research Terminal" />
              </label>
              <label>
                <span>{{ l("Role", "角色") }}</span>
                <input v-model="profileDraft.role" required :placeholder="l('Research Analyst', '研究分析员')" />
              </label>
              <label class="profile-setup-form__wide">
                <span>{{ l("Bio", "简介") }}</span>
                <textarea v-model="profileDraft.bio" rows="3" :placeholder="l('Optional research profile note', '可选：研究方向或说明')" />
              </label>
              <footer>
                <button class="primary" type="submit">{{ l("Enter Terminal", "进入终端") }}</button>
              </footer>
            </form>
          </section>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal-pop">
        <div v-if="store.apiConfigOpen" class="api-modal-backdrop">
          <section class="api-modal" role="dialog" aria-modal="true" :aria-label="l('Connect Your Model API', '接入模型 API')">
            <header>
              <div>
                <span class="modal-icon"><KeyRound :size="20" /></span>
                <h2>{{ l("Connect Model API", "接入模型 API") }}</h2>
                <p>{{ l("Add a provider key for full AI research, or continue in demo mode.", "填写服务商 Key 解锁 AI 研究；也可先用演示模式。") }}</p>
              </div>
              <button class="modal-close" type="button" @click="store.closeApiConfig" :aria-label="l('Close', '关闭')"><X :size="18" /></button>
            </header>

            <div class="api-modal__body">
              <ol class="api-steps">
                <li>{{ l("Pick a provider.", "选择服务商。") }}</li>
                <li>{{ l("Paste API Key.", "粘贴 API Key。") }}</li>
                <li>{{ l("Save or use demo mode.", "保存配置或使用演示模式。") }}</li>
              </ol>

              <form class="api-form" @submit.prevent="saveApiConfig">
                <label>
                  <span>{{ l("Provider", "服务商") }}</span>
                  <select v-model="apiDraft.providerId" @change="applyProviderPreset(apiDraft.providerId)">
                    <option v-for="preset in store.llmProviders" :key="preset.id" :value="preset.id">
                      {{ preset.name }} · {{ preset.region }}
                    </option>
                  </select>
                </label>
                <article v-if="selectedApiPreset" class="provider-preset-card">
                  <div>
                    <b>{{ selectedApiPreset.name }}</b>
                    <span>{{ apiProtocolLabel }}</span>
                  </div>
                  <p>{{ selectedApiPreset.notes }}</p>
                  <a v-if="selectedApiPreset.docsUrl" :href="selectedApiPreset.docsUrl" target="_blank" rel="noreferrer">
                    {{ l("Open official docs", "打开官方文档") }}
                  </a>
                </article>
                <label class="api-base-field">
                  <span>Base URL</span>
                  <input v-model="apiDraft.baseUrl" placeholder="https://api.openai.com/v1" />
                </label>
                <label>
                  <span>{{ l("Model", "模型") }}</span>
                  <input v-model="apiDraft.model" placeholder="gpt-4.1-mini" />
                </label>
                <label v-if="apiDraft.protocol === 'azure-openai'" class="api-version-field">
                  <span>API Version</span>
                  <input v-model="apiDraft.apiVersion" placeholder="2025-01-01-preview" />
                  <small>{{ l("For Azure, model should be your deployment name.", "Azure 模式下，模型名请填写 deployment name。") }}</small>
                </label>
                <label class="api-key-field">
                  <span>API Key</span>
                  <input v-model="apiDraft.apiKey" type="password" :placeholder="selectedApiPreset?.apiKeyHint || 'Provider API key'" />
                  <small>{{ l("Stored locally on this machine and only sent to the backend when a research run starts.", "只保存在本机；只有真正启动研究运行时，才会临时发送到后端。") }}</small>
                </label>
                <label>
                  <span>{{ l("Market Data Provider", "行情数据源") }}</span>
                  <input v-model="apiDraft.marketDataProvider" placeholder="Demo fixtures / Tushare / Yahoo Finance" />
                </label>
                <label>
                  <span>{{ l("Market Data Key", "行情 API Key") }}</span>
                  <input v-model="apiDraft.marketDataKey" type="password" placeholder="Optional" />
                </label>
                <footer>
                  <button class="secondary" type="button" @click="store.useDemoMode">{{ l("Use Demo Mode", "使用演示模式") }}</button>
                  <button class="secondary" type="button" @click="testApiConfig">{{ l("Test Locally", "本地测试") }}</button>
                  <button class="primary" type="submit">{{ l("Save Configuration", "保存配置") }}</button>
                </footer>
              </form>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>

    <div class="toast-stack" aria-live="polite">
      <TransitionGroup name="toast-pop">
        <article v-for="toast in store.toasts" :key="toast.id" class="toast" :class="toast.tone">
          {{ toast.text }}
        </article>
      </TransitionGroup>
    </div>

    <AiAssistant
      :open="store.aiOpen"
      :minimized="store.aiMinimized"
      :messages="store.assistantMessages"
      :language="store.language"
      :status="assistantStatus"
      :ticker="store.selectedTicker"
      :trace-events="tracePreview"
      :progress="runProgress"
      :summary="store.dashboard?.agent_summary || store.dashboard?.ai_insight || ''"
      @close="store.aiOpen = false"
      @minimize="store.aiMinimized = true"
      @restore="store.aiMinimized = false"
      @send="store.sendAssistant"
      @quick="store.sendAssistant"
      @open-agent="openAgentWorkspace"
    />
  </div>
</template>
