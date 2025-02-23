// src/stores/requirement.js
import { defineStore } from "pinia";

export const useRequirementStore = defineStore("requirement", {
  state: () => ({
    nodes: [
      { id: "R1", type: "requirement", text: "生産効率を20%向上" },
      { id: "R2", type: "requirement", text: "不良品率を5%未満に抑制" },
      { id: "C1", type: "constraint", text: "製造ライン稼働時間 8h以内" },
      { id: "C2", type: "constraint", text: "1日生産量 1000個以上" },
      { id: "I1", type: "implicit", text: "午前中は生産効率が高い" },
      { id: "I2", type: "implicit", text: "温度管理が重要" },
      { id: "I3", type: "implicit", text: "熟練工のセッティング" },
    ],
    links: [
      { source: "C1", target: "R1", label: "制約" },
      { source: "C2", target: "R1", label: "制約" },
      { source: "C1", target: "R2", label: "影響" },
      { source: "I1", target: "R1", label: "知見" },
      { source: "I2", target: "R2", label: "知見" },
      { source: "I3", target: "C1", label: "関連" },
      { source: "I3", target: "C2", label: "関連" },
    ],
  }),

  actions: {
    addRequirement(requirement) {
      this.nodes.push(requirement);
    },

    updateRequirement(id, updates) {
      const index = this.nodes.findIndex((node) => node.id === id);
      if (index !== -1) {
        this.nodes[index] = { ...this.nodes[index], ...updates };
      }
    },

    removeRequirement(id) {
      this.nodes = this.nodes.filter((node) => node.id !== id);
      this.links = this.links.filter(
        (link) => link.source !== id && link.target !== id
      );
    },

    addLink(source, target, label = "関連") {
      this.links.push({ source, target, label });
    },

    removeLink(source, target) {
      this.links = this.links.filter(
        (link) => !(link.source === source && link.target === target)
      );
    },
  },
});
