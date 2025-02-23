<!-- src/components/RequirementGraph.vue -->
<template>
  <v-card height="100%">
    <v-card-title class="d-flex justify-space-between align-center">
      要件・制約関係グラフ
      <v-btn
        :color="isDragging ? 'primary' : undefined"
        icon
        @click="toggleDrag"
      >
        <v-icon>mdi-drag</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text class="fill-height">
      <div ref="container" class="graph-container fill-height"></div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import * as d3 from "d3";
import { useRequirementStore } from "@/stores/requirement";
import { storeToRefs } from "pinia";

const store = useRequirementStore();
const { nodes, links } = storeToRefs(store);

const container = ref(null);
const isDragging = ref(true);
let simulation = null;

const toggleDrag = () => {
  isDragging.value = !isDragging.value;
  if (simulation) {
    if (isDragging.value) {
      simulation.alpha(0.3).restart();
    } else {
      simulation.alpha(0);
    }
  }
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
  if (!container.value) return;

  // Clear any existing SVG
  d3.select(container.value).selectAll("*").remove();

  const containerRect = container.value.getBoundingClientRect();
  const width = containerRect.width;
  const height = containerRect.height;

  // Create SVG with explicit dimensions
  const svg = d3
    .select(container.value)
    .append("svg")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("viewBox", [0, 0, width, height])
    .style("display", "block");

  // 矢印マーカーの定義
  const defs = svg.append("defs");
  defs
    .append("marker")
    .attr("id", "arrowhead")
    .attr("refX", 8)
    .attr("refY", 2)
    .attr("markerWidth", 4)
    .attr("markerHeight", 4)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M 0,0 V 4 L4,2 Z")
    .attr("fill", "#999");

  // Add zoom behavior
  const g = svg.append("g");
  const zoom = d3
    .zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svg.call(zoom);

  // Initialize simulation
  simulation = d3
    .forceSimulation(nodes.value)
    .force(
      "link",
      d3
        .forceLink(links.value)
        .id((d) => d.id)
        .distance(150)
    )
    .force("charge", d3.forceManyBody().strength(-800))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(70));

  // Draw links
  const link = g
    .append("g")
    .attr("class", "links")
    .selectAll("g")
    .data(links.value)
    .join("g");

  link
    .append("line")
    .attr("stroke", "#999")
    .attr("stroke-width", 2)
    .attr("stroke-opacity", 0.6)
    .attr("marker-end", "url(#arrowhead)"); // 矢印マーカーを追加

  link
    .append("text")
    .attr("dy", -5)
    .attr("text-anchor", "middle")
    .attr("fill", "#666")
    .style("font-size", "12px")
    .text((d) => d.label);

  // Draw nodes
  const node = g
    .append("g")
    .attr("class", "nodes")
    .selectAll("g")
    .data(nodes.value)
    .join("g")
    .call(
      d3
        .drag()
        .on("start", dragStarted)
        .on("drag", dragged)
        .on("end", dragEnded)
    );

  // Background rectangles
  node
    .append("rect")
    .attr("width", 120)
    .attr("height", 60)
    .attr("rx", 8)
    .attr("x", -60)
    .attr("y", -30)
    .attr("fill", (d) => getNodeColor(d.type).bg)
    .attr("stroke", (d) => getNodeColor(d.type).border)
    .attr("stroke-width", 2);

  // Node ID text
  node
    .append("text")
    .attr("dy", -5)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-weight", "bold")
    .style("font-size", "14px")
    .text((d) => d.id);

  // Node description text
  node
    .append("text")
    .attr("dy", 15)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-size", "12px")
    .text((d) => d.text);

  // Drag functions
  function dragStarted(event) {
    if (!isDragging.value) return;
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }

  function dragged(event) {
    if (!isDragging.value) return;
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }

  function dragEnded(event) {
    if (!isDragging.value) return;
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }

  // Update simulation
  simulation.on("tick", () => {
    link
      .select("line")
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        // 終点を矩形の手前に調整
        return d.target.x - (dx / length) * 30;
      })
      .attr("y2", (d) => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        // 終点を矩形の手前に調整
        return d.target.y - (dy / length) * 30;
      });

    link
      .select("text")
      .attr("x", (d) => (d.source.x + d.target.x) / 2)
      .attr("y", (d) => (d.source.y + d.target.y) / 2);

    node.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });
};

onMounted(() => {
  setTimeout(() => {
    initGraph();
  }, 100);
});

onUnmounted(() => {
  if (simulation) {
    simulation.stop();
  }
});
</script>

<style scoped>
.graph-container {
  width: 100%;
  min-height: 600px;
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
  cursor: pointer;
}

.nodes rect:active {
  cursor: grabbing;
}
</style>
