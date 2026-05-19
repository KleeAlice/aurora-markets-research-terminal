<script setup lang="ts">
import { Activity, Bot, ChevronUp, Filter, Minimize2, Send, ShieldCheck, Sparkles, X } from "lucide-vue-next";
import { computed, ref } from "vue";

import type { AgentTraceEvent } from "@/types";

const props = defineProps<{
  open: boolean;
  minimized: boolean;
  messages: Array<{ role: "assistant" | "user"; text: string }>;
  language?: "en" | "zh";
  status?: string;
  ticker?: string;
  traceEvents?: AgentTraceEvent[];
  progress?: number;
  summary?: string;
}>();

const emit = defineEmits<{
  close: [];
  minimize: [];
  restore: [];
  send: [text: string];
  quick: [text: string];
  openAgent: [];
}>();

const draft = ref("");

const zh = computed(() => props.language === "zh");
const visibleMessages = computed(() => props.messages.slice(-2));
const visibleTrace = computed(() => (props.traceEvents ?? []).slice(0, 5));

const copy = computed(() => ({
  title: zh.value ? "AI 研究副屏" : "AI Research Dock",
  subtitle: zh.value ? "筛选、检索、解释、汇总" : "Filter, search, explain, summarize",
  status: props.status || (zh.value ? "待命" : "Standing by"),
  ticker: props.ticker || "AI",
  open: zh.value ? "打开 AI 副屏" : "Open AI dock",
  minimize: zh.value ? "最小化" : "Minimize",
  close: zh.value ? "关闭" : "Close",
  primary: zh.value ? "AI 筛选分析" : "AI Filter & Analyze",
  primaryHint: zh.value ? "打开独立候选工作台，开始研究流程" : "Open the candidate workspace and start research",
  summary: zh.value ? "最新摘要" : "Latest Summary",
  trace: zh.value ? "工作过程" : "Work Trace",
  quick: zh.value ? "快捷动作" : "Quick Actions",
  summarize: zh.value ? "总结基本面" : "Summarize fundamentals",
  compare: zh.value ? "比较同行" : "Compare peers",
  risk: zh.value ? "解释 DCF 风险" : "Explain DCF risks",
  placeholder: zh.value ? "向 AI 研究副屏提问..." : "Ask the research dock...",
  researchOnly: zh.value ? "仅供研究，不构成投资建议" : "Research-only, not investment advice",
  latestNotes: zh.value ? "最近对话" : "Recent Notes",
  progress: zh.value ? "进度" : "Progress",
}));

function send() {
  const clean = draft.value.trim();
  if (!clean) return;
  emit("send", clean);
  draft.value = "";
}
</script>

<template>
  <Transition name="assistant-pop">
    <aside v-if="open" class="assistant" :class="{ minimized }">
      <button v-if="minimized" class="assistant__restore" type="button" @click="emit('restore')">
        <Bot :size="16" />
        <span>{{ copy.open }}</span>
        <ChevronUp :size="14" />
      </button>

      <template v-else>
        <header class="assistant__head">
          <span class="assistant__mark"><Bot :size="18" /></span>
          <span class="assistant__title">
            <strong>{{ copy.title }}</strong>
            <small>{{ copy.subtitle }}</small>
          </span>
          <button class="icon-btn" type="button" :title="copy.minimize" @click="emit('minimize')"><Minimize2 :size="15" /></button>
          <button class="icon-btn" type="button" :title="copy.close" @click="emit('close')"><X :size="15" /></button>
        </header>

        <section class="assistant__meta">
          <span><Activity :size="14" />{{ copy.status }}</span>
          <b>{{ copy.ticker }}</b>
        </section>

        <button class="assistant__agent" type="button" @click="emit('openAgent')">
          <Filter :size="17" />
          <span>
            <b>{{ copy.primary }}</b>
            <small>{{ copy.primaryHint }}</small>
          </span>
        </button>

        <div class="assistant__guardrail"><ShieldCheck :size="14" />{{ copy.researchOnly }}</div>

        <section class="assistant__summary">
          <header>
            <h4>{{ copy.summary }}</h4>
            <small>{{ copy.progress }} {{ props.progress ?? 0 }}%</small>
          </header>
          <p>{{ summary || (zh ? "运行 Agent 后会在这里显示结构化摘要。" : "Structured research summary will appear here after the Agent runs.") }}</p>
        </section>

        <section class="assistant__trace">
          <header><h4>{{ copy.trace }}</h4></header>
          <div class="assistant__trace-list">
            <article v-for="item in visibleTrace" :key="item.id" class="assistant__trace-item" :class="item.status">
              <span class="assistant__trace-dot" />
              <div>
                <strong>{{ item.title }}</strong>
                <small>{{ item.phase }} · {{ new Date(item.timestamp).toLocaleTimeString() }}</small>
              </div>
            </article>
            <p v-if="!visibleTrace.length" class="assistant__trace-empty">
              {{ zh ? "等待检索、排序与刷新事件流..." : "Waiting for search, ranking, and refresh events..." }}
            </p>
          </div>
        </section>

        <section class="assistant__messages">
          <header><h4>{{ copy.latestNotes }}</h4></header>
          <TransitionGroup name="message">
            <p v-for="(message, index) in visibleMessages" :key="`${message.role}-${index}-${message.text}`" :class="message.role">
              {{ message.text }}
            </p>
          </TransitionGroup>
        </section>

        <div class="assistant__quick">
          <button type="button" @click="emit('quick', zh ? '总结基本面' : 'Summarize fundamentals')"><Sparkles :size="14" />{{ copy.summarize }}</button>
          <button type="button" @click="emit('quick', zh ? '比较同行' : 'Compare peers')">{{ copy.compare }}</button>
          <button type="button" @click="emit('quick', zh ? '解释 DCF 风险' : 'Explain DCF risks')">{{ copy.risk }}</button>
        </div>

        <form class="assistant__composer" @submit.prevent="send">
          <input v-model="draft" :placeholder="copy.placeholder" />
          <button class="icon-btn primary" type="submit" title="Send"><Send :size="16" /></button>
        </form>
      </template>
    </aside>
  </Transition>
</template>
