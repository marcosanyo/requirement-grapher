<!-- frontend/src/App.vue -->
<template>
  <v-app>
    <v-app-bar color="primary" app elevation="1">
      <v-app-bar-title>要件・制約分析支援システム (YAML活用版)</v-app-bar-title>
    </v-app-bar>

    <v-main class="overflow-auto">
      <v-container fluid class="pa-4">
        <requirement-input />
        <requirement-graph :store="store" />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import RequirementGraph from "./components/RequirementGraph.vue";
import RequirementInput from "./components/RequirementInput.vue";
import { useRequirementStore } from "./stores/requirement";

const store = useRequirementStore();
</script>

<style>
html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
}

.v-application {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.v-main {
  flex: 1;
}
</style>
