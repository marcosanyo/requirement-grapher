<!-- frontend/src/components/RequirementInput.vue -->
<template>
  <v-card class="mb-4">
    <v-card-title class="d-flex justify-space-between align-center">
      要件入力 (YAML中間形式利用)
      <v-btn icon @click="clearInput" :disabled="!text">
        <v-icon>mdi-delete</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-textarea
        v-model="text"
        label="要件を入力してください"
        hint="テキストから要件、制約、暗黙知をYAML形式で構造化して抽出します"
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

  <v-expand-transition>
    <div v-if="store.yaml">
      <v-card class="mb-4">
        <v-card-title class="d-flex justify-space-between align-center">
          YAML中間形式
          <div>
            <v-btn
              icon
              class="me-2"
              color="primary"
              @click="applyYamlChanges"
              :loading="store.processingYaml"
              :disabled="store.processingYaml"
              v-if="yamlEdited"
            >
              <v-icon>mdi-check</v-icon>
            </v-btn>
            <v-btn icon @click="toggleYamlEdit">
              <v-icon>{{ editingYaml ? "mdi-eye" : "mdi-pencil" }}</v-icon>
            </v-btn>
          </div>
        </v-card-title>
        <v-card-text>
          <div v-if="editingYaml">
            <v-textarea
              v-model="editableYaml"
              rows="15"
              class="yaml-editor font-monospace"
              hide-details
              bg-color="grey-lighten-4"
            ></v-textarea>
          </div>
          <div v-else>
            <pre class="yaml-preview">{{ store.yaml }}</pre>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </v-expand-transition>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useRequirementStore } from "@/stores/requirement";

const store = useRequirementStore();
const text = ref("");
const showSnackbar = ref(false);
const snackbarText = ref("");
const snackbarColor = ref("success");
const editingYaml = ref(false);
const editableYaml = ref("");

// YAMLが編集されたかどうかを検出
const yamlEdited = computed(() => {
  return editableYaml.value !== store.yaml;
});

// storeのyamlが変更されたら編集用のyamlも更新
watch(
  () => store.yaml,
  (newYaml) => {
    editableYaml.value = newYaml;
  }
);

const handleExtractRequirements = async () => {
  if (!text.value.trim()) {
    snackbarText.value = "テキストを入力してください";
    snackbarColor.value = "warning";
    showSnackbar.value = true;
    return;
  }

  try {
    await store.extractRequirementsWithYaml(text.value);
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

const toggleYamlEdit = () => {
  editingYaml.value = !editingYaml.value;
  if (editingYaml.value) {
    // 編集モードに入る時に現在のYAMLを編集用にコピー
    editableYaml.value = store.yaml;
  }
};

const applyYamlChanges = async () => {
  try {
    // 編集されたYAMLをグラフに変換
    await store.convertYamlToGraph(editableYaml.value);
    // 成功したらstoreのYAMLも更新
    store.updateYaml(editableYaml.value);

    snackbarText.value = "YAMLの変更を適用しました";
    snackbarColor.value = "success";
    showSnackbar.value = true;

    // 編集モードを終了
    editingYaml.value = false;
  } catch (error) {
    console.error("Error applying YAML changes:", error);
    snackbarText.value = store.error || "YAMLの適用に失敗しました";
    snackbarColor.value = "error";
    showSnackbar.value = true;
  }
};

const clearInput = () => {
  text.value = "";
  store.clearAll();
  editingYaml.value = false;
  editableYaml.value = "";
};
</script>

<style scoped>
.yaml-preview {
  white-space: pre-wrap;
  font-family: monospace;
  background-color: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  overflow: auto;
  max-height: 400px;
}

.yaml-editor {
  font-family: monospace;
}

.font-monospace {
  font-family: "Consolas", "Monaco", "Courier New", monospace;
}
</style>
