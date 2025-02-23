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

        this.nodes = response.data.nodes;
        this.links = response.data.links;
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
