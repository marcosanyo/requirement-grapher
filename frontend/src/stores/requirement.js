// frontend/src/stores/requirement.js
import { defineStore } from "pinia";
import axios from "axios";

const API_BASE_URL = "http://localhost:8086";

export const useRequirementStore = defineStore("requirement", {
  state: () => ({
    nodes: [],
    links: [],
    loading: false,
    error: null,
  }),

  actions: {
    async extractRequirements(text) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/requirements/extract`,
          { text },
          {
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
            },
          }
        );

        console.log("API Response:", response.data); // デバッグ用

        // レスポンスデータの検証
        if (
          !response.data ||
          !Array.isArray(response.data.nodes) ||
          !Array.isArray(response.data.links)
        ) {
          throw new Error("Invalid response format from API");
        }

        // descriptionがない場合はtextを使用する
        const processedNodes = response.data.nodes.map((node) => ({
          ...node,
          description: node.description || node.text,
        }));

        this.nodes = processedNodes;
        this.links = response.data.links;

        console.log("Updated store state:", {
          nodes: this.nodes,
          links: this.links,
        }); // デバッグ用
      } catch (error) {
        console.error("Error details:", error.response || error);
        this.error =
          error.response?.data?.detail || "要件の抽出に失敗しました。";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    clearGraph() {
      this.nodes = [];
      this.links = [];
      this.error = null;
    },
  },
});
