<script setup lang="ts">
import * as echarts from "echarts";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import type { CandlePoint } from "@/types";

const props = defineProps<{
  candles: CandlePoint[];
  height?: number;
  currentPrice?: number | null;
}>();

const el = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function render() {
  if (!el.value) return;
  chart ??= echarts.init(el.value);
  const labels = props.candles.map((item) => item.timestamp);
  const values = props.candles.map((item) => [item.open, item.close, item.low, item.high]);
  const volumes = props.candles.map((item) => item.volume);
  const price = props.currentPrice ?? props.candles.at(-1)?.close ?? 0;

  chart.setOption({
    animationDuration: 540,
    grid: [
      { left: 26, right: 58, top: 18, height: "66%" },
      { left: 26, right: 58, bottom: 8, height: "16%" },
    ],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      borderWidth: 0,
      backgroundColor: "rgba(255,255,255,.96)",
      textStyle: { color: "#14213f" },
    },
    xAxis: [
      {
        type: "category",
        data: labels,
        boundaryGap: true,
        axisLine: { lineStyle: { color: "#dce5f3" } },
        axisLabel: { color: "#7c8aa5", hideOverlap: true, interval: Math.ceil(labels.length / 5) },
      },
      {
        type: "category",
        gridIndex: 1,
        data: labels,
        boundaryGap: true,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true,
        position: "right",
        splitLine: { lineStyle: { color: "#e6edf7", type: "dashed" } },
        axisLabel: { color: "#6b7893" },
      },
      {
        gridIndex: 1,
        splitLine: { show: false },
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
      },
    ],
    series: [
      {
        name: "Price",
        type: "candlestick",
        data: values,
        itemStyle: {
          color: "#18a66a",
          color0: "#ff3f4f",
          borderColor: "#18a66a",
          borderColor0: "#ff3f4f",
        },
        markLine: {
          symbol: "none",
          label: {
            show: true,
            position: "end",
            formatter: `${price.toFixed(2)}`,
            color: "#fff",
            backgroundColor: "#18a66a",
            borderRadius: 4,
            padding: [3, 6],
          },
          lineStyle: { color: "#18a66a", type: "dashed", width: 1 },
          data: [{ yAxis: price }],
        },
      },
      {
        name: "Volume",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: { color: "rgba(177,190,211,.28)" },
      },
    ],
  });
}

function resize() {
  chart?.resize();
}

onMounted(() => {
  render();
  window.addEventListener("resize", resize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resize);
  chart?.dispose();
});

watch(() => [props.candles, props.currentPrice], render, { deep: true });
</script>

<template>
  <div ref="el" class="candlestick-chart" :style="{ height: `${height ?? 250}px` }" />
</template>

