<!-- frontend/src/components/RequirementInput.vue -->
<template>
  <v-card class="mb-4">
    <v-card-title class="d-flex justify-space-between align-center">
      要件入力
      <v-btn icon @click="clearInput" :disabled="!text">
        <v-icon>mdi-delete</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-textarea
        v-model="text"
        label="要件を入力してください"
        hint="テキストから要件、制約、暗黙知を自動抽出します"
        persistent-hint
        rows="4"
        :error="!!store.error"
        :error-messages="store.error"
      ></v-textarea>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        :loading="store.loading"
        :disabled="!text || store.loading"
        @click="handleExtractRequirements"
      >
        分析開始
      </v-btn>
    </v-card-actions>

    <v-snackbar v-model="showSnackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref } from "vue";
import { useRequirementStore } from "@/stores/requirement";

const store = useRequirementStore();
const text = ref("");
const showSnackbar = ref(false);
const snackbarText = ref("");
const snackbarColor = ref("success");

const handleExtractRequirements = async () => {
  if (!text.value.trim()) {
    snackbarText.value = "テキストを入力してください";
    snackbarColor.value = "warning";
    showSnackbar.value = true;
    return;
  }

  try {
    await store.extractRequirements(text.value);
    snackbarText.value = "要件の抽出が完了しました";
    snackbarColor.value = "success";
    showSnackbar.value = true;
  } catch (error) {
    console.error("Error extracting requirements:", error);
    snackbarText.value = store.error || "要件の抽出に失敗しました";
    snackbarColor.value = "error";
    showSnackbar.value = true;
  }
};

const clearInput = () => {
  text.value = "";
  store.clearGraph();
};
</script>
