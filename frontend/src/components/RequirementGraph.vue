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

// グラフの表示をリセットする関数
const resetView = () => {
  if (!svg || !container.value) return;

  const containerRect = container.value.getBoundingClientRect();
  const width = containerRect.width;
  const height = containerRect.height;

  // 前提ノードを探す
  const normalNodes = JSON.parse(JSON.stringify(nodes.value));
  const implicitNodes = normalNodes.filter((node) => node.type === "implicit");
  let centerX = width / 2;
  let centerY = height / 2;

  // 前提ノードがある場合は、その中心を計算
  if (implicitNodes.length > 0) {
    let implicitCenterX = 0;
    let implicitCenterY = 0;

    implicitNodes.forEach((node) => {
      if (node.x && node.y) {
        implicitCenterX += node.x;
        implicitCenterY += node.y;
      }
    });

    if (implicitNodes.length > 0) {
      implicitCenterX /= implicitNodes.length;
      implicitCenterY /= implicitNodes.length;

      // 実際に値が計算できた場合のみ中心を更新
      if (!isNaN(implicitCenterX) && !isNaN(implicitCenterY)) {
        centerX = implicitCenterX;
        centerY = implicitCenterY;
      }
    }
  }

  const initialTransform = d3.zoomIdentity
    .translate(width / 2 - centerX, height / 2 - centerY)
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

// ノードの表示順序を制御する関数（前提ノードを最初に表示）
const getNodeDelay = (d, index, implicitNodesCount, constraintNodesCount) => {
  // 前提ノードは早めに表示
  if (d.type === "implicit") return index * 100;
  // 制約ノードは次に表示
  if (d.type === "constraint") return implicitNodesCount * 100 + index * 200;
  // 要件ノードは最後に表示
  return (implicitNodesCount + constraintNodesCount) * 150 + index * 200;
};

// 波紋エフェクトは削除

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

  // 前提ノードとその他のノードを分類
  const implicitNodes = normalNodes.filter((node) => node.type === "implicit");
  const constraintNodes = normalNodes.filter(
    (node) => node.type === "constraint"
  );
  const requirementNodes = normalNodes.filter(
    (node) => node.type === "requirement"
  );
  const implicitNodesCount = implicitNodes.length;
  const constraintNodesCount = constraintNodes.length;

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
    .attr("refX", 15) // 先端位置を少し調整
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
    // ダブルクリックによるズームを無効化
    .on("dblclick.zoom", null);

  // 前処理: ノードの初期配置を整理
  const centerX = width / 2;
  const centerY = height / 2;

  // まず前提ノード（implicitNodes）を中央付近に配置
  if (implicitNodes.length > 0) {
    // 前提ノードが複数ある場合は中央付近に円形に配置
    const implicitRadius = 80; // 前提ノードの配置半径（小さめに）

    if (implicitNodes.length > 1) {
      implicitNodes.forEach((node, i) => {
        const angle = (i / implicitNodes.length) * 2 * Math.PI;
        node.x = centerX + implicitRadius * Math.cos(angle);
        node.y = centerY + implicitRadius * Math.sin(angle);
      });
    } else {
      // 1つしかない場合は完全に中央に
      implicitNodes[0].x = centerX;
      implicitNodes[0].y = centerY;
    }
  }

  // 制約ノードは前提ノードの周りの中間距離に配置
  const constraintRadius = 180; // 制約ノードの配置半径（中間）
  constraintNodes.forEach((node, i) => {
    const angle = (i / Math.max(constraintNodes.length, 1)) * 2 * Math.PI;
    node.x = centerX + constraintRadius * Math.cos(angle);
    node.y = centerY + constraintRadius * Math.sin(angle);
  });

  // 要件ノードは最も外側に配置
  const requirementRadius = 280; // 要件ノードの配置半径（大きめ）
  requirementNodes.forEach((node, i) => {
    const angle = (i / Math.max(requirementNodes.length, 1)) * 2 * Math.PI;
    node.x = centerX + requirementRadius * Math.cos(angle);
    node.y = centerY + requirementRadius * Math.sin(angle);
  });

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
        .distance(200) // リンク長を短めに調整
    )
    .force("charge", d3.forceManyBody().strength(-3000))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(100))
    .force("x", d3.forceX(width / 2).strength(0.1))
    .force("y", d3.forceY(height / 2).strength(0.1))
    .alphaDecay(0.02); // アニメーションをやや長く続かせる (デフォルトは0.0228)

  // 前提ノードを中心に引っ張る力を追加
  simulation.force(
    "fixImplicit",
    d3.forceRadial(0, width / 2, height / 2).strength((d) => {
      return d.type === "implicit" ? 0.8 : 0.01; // 前提ノードは中心に引っ張る力を強くする
    })
  );

  // リンクの描画（アニメーション付き）
  const link = g
    .append("g")
    .attr("class", "links")
    .selectAll("g")
    .data(normalLinks)
    .join("g")
    .style("opacity", 0); // 最初は非表示

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
    .attr(
      "transform",
      (d) => `translate(${d.x || width / 2},${d.y || height / 2})`
    ); // 初期位置から始める

  // ノードの円形
  node
    .append("circle")
    .attr("r", 0) // 最初は半径0から始める
    .attr("fill", (d) => getNodeColor(d.type).fill)
    .style("cursor", "pointer")
    .on("mouseover", function (event, d) {
      showTooltip(event, d);
      // マウスオーバー時に円を少し大きくする
      d3.select(this).transition().duration(300).attr("r", 65);
    })
    .on("mouseout", function () {
      hideTooltip();
      // マウスアウト時に元のサイズに戻す
      d3.select(this).transition().duration(300).attr("r", 60);
    })
    // アニメーションで円を拡大
    .transition()
    .duration(800)
    .delay((d, i) =>
      getNodeDelay(d, i, implicitNodesCount, constraintNodesCount)
    )
    .attr("r", 60);

  // ノードタイプを日本語で表示
  node
    .append("text")
    .attr("dy", -30)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-weight", "bold")
    .style("font-size", "14px")
    .style("opacity", 0) // 最初は非表示
    .text((d) => getNodeColor(d.type).label)
    // アニメーションでテキストを表示
    .transition()
    .duration(500)
    .delay(
      (d, i) =>
        getNodeDelay(d, i, implicitNodesCount, constraintNodesCount) + 300
    ) // 円の後に表示
    .style("opacity", 1);

  // ノードの簡易テキスト
  node
    .append("text")
    .attr("dy", 0)
    .attr("text-anchor", "middle")
    .attr("fill", (d) => getNodeColor(d.type).text)
    .style("font-size", "14px")
    .style("opacity", 0) // 最初は非表示
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
    })
    // アニメーションでテキストを表示
    .transition()
    .duration(500)
    .delay(
      (d, i) =>
        getNodeDelay(d, i, implicitNodesCount, constraintNodesCount) + 500
    ) // タイプラベルの後に表示
    .style("opacity", 1);

  // ノードをアニメーションで徐々に表示
  node
    .transition()
    .duration(1000)
    .delay((d, i) =>
      getNodeDelay(d, i, implicitNodesCount, constraintNodesCount)
    ) // ノードタイプに基づいた表示順序
    .style("opacity", 1);

  // リンクをアニメーションで徐々に表示（関連性に基づいて順序付け）
  link
    .transition()
    .duration(1000)
    .delay((d) => {
      const sourceDelay = getNodeDelay(
        d.source,
        0,
        implicitNodesCount,
        constraintNodesCount
      );
      const targetDelay = getNodeDelay(
        d.target,
        0,
        implicitNodesCount,
        constraintNodesCount
      );

      // 前提ノードからのリンクを最初に表示
      if (d.source.type === "implicit") {
        return Math.max(sourceDelay, targetDelay) + 300;
      }
      // 制約ノードからのリンクを次に表示
      if (d.source.type === "constraint") {
        return Math.max(sourceDelay, targetDelay) + 400;
      }
      // その他のリンク
      return Math.max(sourceDelay, targetDelay) + 500;
    })
    .style("opacity", 1);

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

        // 円の半径と矢印マーカーの長さを考慮
        const radius = 65; // マーカーのために少し大きめに

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

        // 円の半径と矢印マーカーの長さを考慮
        const radius = 65; // マーカーのために少し大きめに

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

    // ノードの位置を更新
    node.attr("transform", (d) => {
      if (!d.x || !d.y) return `translate(0,0)`;
      return `translate(${d.x},${d.y})`;
    });
  });

  // 波紋エフェクトを削除

  // 一定時間後にシミュレーションを徐々に落ち着かせる
  setTimeout(() => {
    simulation.alphaTarget(0).alphaDecay(0.05);
  }, 2500);

  // 初期ビューをセット（前提ノードを中心に表示）
  setTimeout(() => {
    resetView();
  }, 300);
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
</style>
