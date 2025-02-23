# src/components/RequirementInput.vue
<template>
  <v-card class="mb-4">
    <v-card-title>要件・制約の入力</v-card-title>
    <v-card-text>
      <v-textarea
        v-model="inputText"
        label="要件・制約を入力してください"
        hint="自然言語で要件や制約を記述してください"
        rows="4"
        :loading="loading"
        :disabled="loading"
      ></v-textarea>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        :loading="loading"
        :disabled="!inputText.trim()"
        @click="analyzeRequirements"
      >
        分析
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from "vue";
import { useRequirementStore } from "@/stores/requirement";

const store = useRequirementStore();
const inputText = ref("");
const loading = ref(false);

async function analyzeRequirements() {
  if (!inputText.value.trim()) return;

  loading.value = true;
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: inputText.value }),
    });

    if (!response.ok) {
      throw new Error("Analysis failed");
    }

    const result = await response.json();

    // 既存のノードとリンクをクリア
    store.$reset();

    // 新しいノードとリンクを追加
    result.nodes.forEach((node) => {
      store.addRequirement(node);
    });

    result.links.forEach((link) => {
      store.addLink(link.source, link.target, link.label);
    });

    // 入力をクリア
    inputText.value = "";
  } catch (error) {
    console.error("Error analyzing requirements:", error);
    // エラー処理を追加する場合はここに実装
  } finally {
    loading.value = false;
  }
}
</script>
