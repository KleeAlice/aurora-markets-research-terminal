<script setup lang="ts">
import * as echarts from "echarts";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps<{
  title: string;
  labels: string[];
  series: Array<{ name: string; data: number[]; type?: "line" | "bar"; color?: string }>;
  height?: number;
  theme?: "light" | "dark";
}>();

const el = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function render() {
  if (!el.value) return;
  chart ??= echarts.init(el.value);
  const text = props.theme === "dark" ? "#dbe7ff" : "#17233f";
  const grid = props.theme === "dark" ? "rgba(143,162,194,.18)" : "rgba(107,124,156,.18)";
  chart.setOption({
    animationDuration: 650,
    textStyle: { color: text, fontFamily: "Manrope, Segoe UI, sans-serif" },
    tooltip: { trigger: "axis", borderWidth: 0 },
    grid: { top: 34, right: 20, bottom: 26, left: 44 },
    legend: { top: 0, right: 0, textStyle: { color: text } },
    xAxis: { type: "category", data: props.labels, axisLine: { lineStyle: { color: grid } }, axisLabel: { color: text } },
    yAxis: { type: "value", splitLine: { lineStyle: { color: grid, type: "dashed" } }, axisLabel: { color: text } },
    series: props.series.map((item) => ({
      name: item.name,
      type: item.type ?? "line",
      data: item.data,
      smooth: true,
      symbolSize: 6,
      itemStyle: { color: item.color },
      areaStyle: item.type === "bar" ? undefined : { opacity: 0.08 },
    })),
  });
}

onMounted(() => {
  render();
  window.addEventListener("resize", resize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  chart?.dispose();
});

function resize() {
  chart?.resize();
}

watch(() => [props.labels, props.series, props.theme], render, { deep: true });
</script>

<template>
  <section class="chart-panel">
    <header>{{ title }}</header>
    <div ref="el" class="chart-panel__canvas" :style="{ height: `${height ?? 260}px` }" />
  </section>
</template>

