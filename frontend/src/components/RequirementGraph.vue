<!-- frontend/src/components/RequirementGraph.vue -->
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
let zoom = null;
let tooltip = null;

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
      return { fill: "#2196f3", text: "#ffffff", label: "要件" };
    case "constraint":
      return { fill: "#9c27b0", text: "#ffffff", label: "制約" };
    case "implicit":
      return { fill: "#4caf50", text: "#ffffff", label: "前提" };
    default:
      return { fill: "#9e9e9e", text: "#ffffff", label: "その他" };
  }
};

const createTooltip = () => {
  // 既存のツールチップを削除
  d3.select(container.value).select(".tooltip").remove();

  // ツールチップの作成
  tooltip = d3
    .select(container.value)
    .append("div")
    .attr("class", "tooltip")
    .style("opacity", 0)
    .style("position", "absolute")
    .style("pointer-events", "none")
    .style("background-color", "#fff")
    .style("border-radius", "6px")
    .style("padding", "12px")
    .style("box-shadow", "0 3px 14px rgba(0, 0, 0, 0.25)")
    .style("font-size", "14px")
    .style("line-height", "1.4")
    .style("max-width", "300px")
    .style("z-index", "1000")
    .style("color", "#333")
    .style("border", "1px solid rgba(0,0,0,0.1)");
};

const showTooltip = (event, d) => {
  // コンテナの位置情報を取得
  const containerRect = container.value.getBoundingClientRect();

  // マウスの相対位置を計算
  const mouseX = event.clientX - containerRect.left;
  const mouseY = event.clientY - containerRect.top;

  tooltip.transition().duration(200).style("opacity", 0.9);

  tooltip
    .html(`${d.description || d.text}`)
    .style("left", mouseX + 15 + "px")
    .style("top", mouseY - 15 + "px");
};

const hideTooltip = () => {
  tooltip.transition().duration(500).style("opacity", 0);
};

// テキストを短縮する関数
const shortenText = (text, maxLength = 40) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + "...";
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

  // ツールチップの作成
  createTooltip();

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
    .attr("refX", 10) // 先端位置の調整
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
  zoom = d3
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
    .scale(0.8);
  svg.call(zoom.transform, initialTransform);

  // アニメーション開始を示す視覚的効果
  svg
    .append("circle")
    .attr("cx", width / 2)
    .attr("cy", height / 2)
    .attr("r", 5)
    .attr("fill", "#4caf50")
    .transition()
    .duration(1000)
    .attr("r", 200)
    .style("opacity", 0)
    .remove();

  // シミュレーションの初期設定
  simulation = d3
    .forceSimulation(normalNodes)
    .alphaTarget(0.3) // アニメーション効果を高めるために高めのアルファ値から始める
    .velocityDecay(0.4) // 動きをやや減速させる (デフォルトは0.4)
    .force(
      "link",
      d3
        .forceLink(normalLinks)
        .id((d) => d.id)
        .distance(300)
    )
    .force("charge", d3.forceManyBody().strength(-4000))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(120))
    .force("x", d3.forceX(width / 2).strength(0.1))
    .force("y", d3.forceY(height / 2).strength(0.1))
    .alphaDecay(0.02); // アニメーションをやや長く続かせる (デフォルトは0.0228)

  // リンクの描画（アニメーション付き）
  const link = g
    .append("g")
    .attr("class", "links")
    .selectAll("g")
    .data(normalLinks)
    .join("g")
    .style("opacity", 0); // 最初は非表示

  // リンクをアニメーションで徐々に表示
  link
    .transition()
    .duration(1000)
    .delay((d, i) => 500 + i * 50) // ノードの後に少し遅れて表示
    .style("opacity", 1);

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

  // ノードの描画（アニメーション付き）
  const node = g
    .append("g")
    .attr("class", "nodes")
    .selectAll("g")
    .data(normalNodes)
    .join("g")
    .style("opacity", 0) // 最初は非表示
    .attr("transform", () => `translate(${width / 2},${height / 2})`); // 中央から始める

  // ノードをアニメーションで徐々に表示
  node
    .transition()
    .duration(1000)
    .delay((_, i) => i * 100) // ノードごとに順番に表示
    .style("opacity", 1)
    .attr("transform", (d) => `translate(${d.x},${d.y})`);

  // ノードの円形
  node
    .append("circle")
    .attr("r", 60) // 円の半径をさらに大きくする
    .attr("fill", (d) => getNodeColor(d.type).fill)
    .style("cursor", "pointer")
    .on("mouseover", function (event, d) {
      // イベントを明示的に渡す
      showTooltip(event, d);
    })
    .on("mouseout", hideTooltip);

  // ノードタイプを日本語で表示
  node
    .append("text")
    .attr("dy", -30)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-weight", "bold")
    .style("font-size", "14px")
    .text((d) => getNodeColor(d.type).label);

  // ノードの簡易テキスト
  node
    .append("text")
    .attr("dy", 0)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-size", "14px")
    .each(function (d) {
      const text = d3.select(this);
      const words = shortenText(d.text, 35).split(/\s+/);
      let line = "";
      let lineNumber = 0;
      const lineHeight = 1.3;

      words.forEach((word, i) => {
        const testLine = line + word + " ";
        // 最初の単語は必ず追加
        if (i === 0) {
          line = testLine;
        } else {
          // それ以降は長さをチェック
          if (testLine.length > 25) {
            // 行が長すぎる場合は新しい行に
            text
              .append("tspan")
              .attr("x", 0)
              .attr("dy", lineNumber === 0 ? 0 : lineHeight + "em")
              .attr("text-anchor", "middle")
              .text(line);
            line = word + " ";
            lineNumber++;
            // 3行以上になったら省略
            if (lineNumber >= 2) {
              line += "...";
              return;
            }
          } else {
            line = testLine;
          }
        }

        // 最後の単語を処理
        if (i === words.length - 1) {
          text
            .append("tspan")
            .attr("x", 0)
            .attr("dy", lineNumber === 0 ? 0 : lineHeight + "em")
            .attr("text-anchor", "middle")
            .text(line);
        }
      });
    });

  // シミュレーションの更新処理
  simulation.on("tick", () => {
    // 線の位置更新（円の淵から淵へ）
    link
      .select("line")
      .attr("x1", (d) => {
        if (!d.source.x || !d.target.x) return 0;

        const sourceX = d.source.x;
        const sourceY = d.source.y;
        const targetX = d.target.x;
        const targetY = d.target.y;

        // 線の角度を計算
        const angle = Math.atan2(targetY - sourceY, targetX - sourceX);

        // 円の半径
        const radius = 60;

        // 円の縁の座標を計算
        return sourceX + radius * Math.cos(angle);
      })
      .attr("y1", (d) => {
        if (!d.source.y || !d.target.y) return 0;

        const sourceX = d.source.x;
        const sourceY = d.source.y;
        const targetX = d.target.x;
        const targetY = d.target.y;

        // 線の角度を計算
        const angle = Math.atan2(targetY - sourceY, targetX - sourceX);

        // 円の半径
        const radius = 60;

        // 円の縁の座標を計算
        return sourceY + radius * Math.sin(angle);
      })
      .attr("x2", (d) => {
        if (!d.source.x || !d.target.x) return 0;

        const sourceX = d.source.x;
        const sourceY = d.source.y;
        const targetX = d.target.x;
        const targetY = d.target.y;

        // 線の角度を計算
        const angle = Math.atan2(targetY - sourceY, targetX - sourceX);

        // 円の半径
        const radius = 60;

        // 円の縁の座標を計算
        return targetX - radius * Math.cos(angle);
      })
      .attr("y2", (d) => {
        if (!d.source.y || !d.target.y) return 0;

        const sourceX = d.source.x;
        const sourceY = d.source.y;
        const targetX = d.target.x;
        const targetY = d.target.y;

        // 線の角度を計算
        const angle = Math.atan2(targetY - sourceY, targetX - sourceX);

        // 円の半径
        const radius = 60;

        // 円の縁の座標を計算
        return targetY - radius * Math.sin(angle);
      });

    link
      .select("text")
      .attr("x", (d) => {
        if (!d.source.x || !d.target.x) return 0;
        return (d.source.x + d.target.x) / 2;
      })
      .attr("y", (d) => {
        if (!d.source.y || !d.target.y) return 0;
        return (d.source.y + d.target.y) / 2;
      });

    // ノードのアニメーション後に位置を更新
    node.attr("transform", (d) => {
      if (!d.x || !d.y) return `translate(0,0)`;
      return `translate(${d.x},${d.y})`;
    });
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
  // 初期化前に短い遅延を入れる（DOMの準備を待つ）
  setTimeout(() => {
    initGraph();
  }, 100);

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

.nodes circle {
  cursor: pointer;
  transition: filter 0.2s;
}

.nodes circle:hover {
  filter: brightness(1.2);
}

/* スタイルをCSSからインラインに移動したため削除 */
</style>
