// frontend/src/components/RequirementGraph.vue
<template>
  <v-card height="600">
    <v-card-title class="d-flex justify-space-between align-center">
      要件・制約関係グラフ
      <v-btn color="primary" icon @click="resetView">
        <v-icon>mdi-restore</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text class="fill-height">
      <div ref="container" class="graph-container fill-height"></div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import * as d3 from "d3";
import { useRequirementStore } from "@/stores/requirement";
import { storeToRefs } from "pinia";

const store = useRequirementStore();
const { nodes, links } = storeToRefs(store);
const container = ref(null);
let simulation = null;
let svg = null;
let g = null;
let zoom = null; // zoomをトップレベルで定義

// デバッグ用
watch(
  [nodes, links],
  () => {
    console.log("Nodes:", nodes.value);
    console.log("Links:", links.value);
  },
  { immediate: true }
);

const resetView = () => {
  if (!svg || !container.value) return;

  const containerRect = container.value.getBoundingClientRect();
  const width = containerRect.width;
  const height = containerRect.height;

  const initialTransform = d3.zoomIdentity
    .translate(width / 2, height / 2)
    .scale(0.8);

  svg.transition().duration(750).call(zoom.transform, initialTransform);
};

const getNodeColor = (type) => {
  switch (type) {
    case "requirement":
      return { bg: "#e3f2fd", border: "#2196f3", text: "#1565c0" };
    case "constraint":
      return { bg: "#f3e5f5", border: "#9c27b0", text: "#6a1b9a" };
    case "implicit":
      return { bg: "#e8f5e9", border: "#4caf50", text: "#2e7d32" };
    default:
      return { bg: "#f5f5f5", border: "#9e9e9e", text: "#616161" };
  }
};

const initGraph = () => {
  if (!container.value || !nodes.value || nodes.value.length === 0) return;

  // Proxyオブジェクトを通常の配列に変換
  const normalNodes = JSON.parse(JSON.stringify(nodes.value));
  const normalLinks = JSON.parse(JSON.stringify(links.value));

  console.log("Initializing graph with nodes:", normalNodes);

  // コンテナのサイズを取得
  const containerRect = container.value.getBoundingClientRect();
  const width = containerRect.width;
  const height = containerRect.height;

  // 既存のSVGをクリア
  d3.select(container.value).selectAll("*").remove();

  // SVGを作成
  svg = d3
    .select(container.value)
    .append("svg")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("viewBox", [0, 0, width, height]);

  // 矢印マーカーの定義
  svg
    .append("defs")
    .append("marker")
    .attr("id", "arrowhead")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 20)
    .attr("refY", 0)
    .attr("markerWidth", 8)
    .attr("markerHeight", 8)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#999");

  // グラフのメインコンテナ
  g = svg.append("g");

  // ズーム機能
  const zoom = d3
    .zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svg
    .call(zoom)
    .call(
      zoom.transform,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(0.8)
    )
    // ダブルクリックによるズームを無効化
    .on("dblclick.zoom", null);

  // 中央に配置されるように初期transform
  const initialTransform = d3.zoomIdentity
    .translate(width / 2, height / 2)
    .scale(1);
  svg.call(zoom.transform, initialTransform);

  // フォースシミュレーションの設定
  simulation = d3
    .forceSimulation(normalNodes)
    .force(
      "link",
      d3
        .forceLink(normalLinks)
        .id((d) => d.id)
        .distance(200)
    )
    .force("charge", d3.forceManyBody().strength(-2000))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(100))
    .force("x", d3.forceX(width / 2).strength(0.1))
    .force("y", d3.forceY(height / 2).strength(0.1))
    .alphaDecay(0.05);

  // リンクの描画
  const link = g
    .append("g")
    .attr("class", "links")
    .selectAll("g")
    .data(normalLinks)
    .join("g");

  link
    .append("line")
    .attr("stroke", "#999")
    .attr("stroke-width", 2)
    .attr("stroke-opacity", 0.6)
    .attr("marker-end", "url(#arrowhead)");

  link
    .append("text")
    .attr("dy", -5)
    .attr("text-anchor", "middle")
    .attr("fill", "#666")
    .style("font-size", "12px")
    .text((d) => d.label);

  // ノードの描画
  const node = g
    .append("g")
    .attr("class", "nodes")
    .selectAll("g")
    .data(normalNodes)
    .join("g");

  // ノードの背景四角形
  node
    .append("rect")
    .attr("width", 160)
    .attr("height", 60)
    .attr("rx", 8)
    .attr("x", -80)
    .attr("y", -30)
    .attr("fill", (d) => getNodeColor(d.type).bg)
    .attr("stroke", (d) => getNodeColor(d.type).border)
    .attr("stroke-width", 2)
    .style("cursor", "default");

  // ノードID
  node
    .append("text")
    .attr("dy", -5)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-weight", "bold")
    .style("font-size", "14px")
    .text((d) => d.id);

  // ノードテキスト
  node
    .append("text")
    .attr("dy", 15)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-size", "12px")
    .each(function (d) {
      // テキストを複数行に分割
      const text = d3.select(this);
      const words = d.text.split(/\s+/);
      let line = [];
      let lineNumber = 0;
      const lineHeight = 1.2;
      const maxWidth = 150;

      words.forEach((word) => {
        line.push(word);
        const testWidth = this.getComputedTextLength();

        if (testWidth > maxWidth && line.length > 1) {
          line.pop();
          text
            .append("tspan")
            .attr("x", 0)
            .attr("dy", `${lineNumber === 0 ? 0 : lineHeight}em`)
            .text(line.join(" "));
          line = [word];
          lineNumber++;
        }
      });

      text
        .append("tspan")
        .attr("x", 0)
        .attr("dy", `${lineNumber === 0 ? 0 : lineHeight}em`)
        .text(line.join(" "));
    });

  // シミュレーションの更新処理
  simulation.on("tick", () => {
    link
      .select("line")
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        return d.target.x - (dx / length) * 40;
      })
      .attr("y2", (d) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        return d.target.y - (dy / length) * 40;
      });

    link
      .select("text")
      .attr("x", (d) => (d.source.x + d.target.x) / 2)
      .attr("y", (d) => (d.source.y + d.target.y) / 2);

    node.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });
};

// ノードとリンクの変更を監視
watch(
  [nodes, links],
  () => {
    if (nodes.value.length > 0) {
      initGraph();
    }
  },
  { deep: true }
);

// コンポーネントのライフサイクル
onMounted(() => {
  initGraph();
  window.addEventListener("resize", initGraph);
});

onUnmounted(() => {
  if (simulation) {
    simulation.stop();
  }
  window.removeEventListener("resize", initGraph);
});
</script>

<style scoped>
.graph-container {
  width: 100%;
  background-color: #fafafa;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.graph-container svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.links line {
  stroke-opacity: 0.6;
}

.nodes rect {
  cursor: default;
}

.nodes rect:hover {
  filter: brightness(0.95);
}
</style>
