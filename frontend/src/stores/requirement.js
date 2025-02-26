// frontend/src/stores/requirement.js
import { defineStore } from "pinia";
import axios from "axios";

const API_BASE_URL = "";

export const useRequirementStore = defineStore("Requirement", {
  state: () => ({
    nodes: [],
    links: [],
    yaml: "",
    loading: false,
    processingYaml: false,
    error: null,
  }),

  actions: {
    async extractRequirementsWithYaml(text) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/requirements/extract_with_yaml`,
          { text },
          {
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
            },
          }
        );

        console.log("API Response with YAML:", response.data);

        // レスポンスデータの検証
        if (
          !response.data ||
          !response.data.yaml ||
          !response.data.graph ||
          !Array.isArray(response.data.graph.nodes) ||
          !Array.isArray(response.data.graph.links)
        ) {
          throw new Error("Invalid response format from API");
        }

        // 設定
        this.yaml = response.data.yaml;

        // descriptionがない場合はtextを使用する
        const processedNodes = response.data.graph.nodes.map((node) => ({
          ...node,
          description: node.description || node.text,
        }));

        this.nodes = processedNodes;
        this.links = response.data.graph.links;

        console.log("Updated store state:", {
          nodes: this.nodes,
          links: this.links,
          yaml: this.yaml,
        });

        return {
          yaml: this.yaml,
          graph: {
            nodes: this.nodes,
            links: this.links,
          },
        };
      } catch (error) {
        console.error("Error details:", error.response || error);
        this.error =
          error.response?.data?.detail || "要件の抽出に失敗しました。";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async extractYamlOnly(text) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/requirements/extract_yaml`,
          { text },
          {
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
            },
          }
        );

        console.log("YAML API Response:", response.data);

        if (!response.data || !response.data.yaml) {
          throw new Error("Invalid YAML response from API");
        }

        this.yaml = response.data.yaml;

        return this.yaml;
      } catch (error) {
        console.error("YAML extraction error:", error.response || error);
        this.error =
          error.response?.data?.detail ||
          "YAML形式での要件抽出に失敗しました。";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async convertYamlToGraph(yamlText) {
      this.processingYaml = true;
      this.error = null;
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/requirements/yaml_to_graph`,
          { yaml: yamlText },
          {
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
            },
          }
        );

        console.log("YAML to Graph Response:", response.data);

        if (
          !response.data ||
          !Array.isArray(response.data.nodes) ||
          !Array.isArray(response.data.links)
        ) {
          throw new Error("Invalid graph response from API");
        }

        // descriptionがない場合はtextを使用する
        const processedNodes = response.data.nodes.map((node) => ({
          ...node,
          description: node.description || node.text,
        }));

        this.nodes = processedNodes;
        this.links = response.data.links;

        return {
          nodes: this.nodes,
          links: this.links,
        };
      } catch (error) {
        console.error("YAML to Graph error:", error.response || error);
        this.error =
          error.response?.data?.detail ||
          "YAMLからグラフへの変換に失敗しました。";
        throw error;
      } finally {
        this.processingYaml = false;
      }
    },

    updateYaml(yamlText) {
      this.yaml = yamlText;
    },

    clearAll() {
      this.nodes = [];
      this.links = [];
      this.yaml = "";
      this.error = null;
    },
  },
});
