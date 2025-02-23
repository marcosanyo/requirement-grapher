<!-- frontend/src/App.vue -->
<template>
  <v-app>
    <v-app-bar color="primary" app elevation="1">
      <v-app-bar-title>要件・制約分析支援システム</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-4">
        <requirement-input />
        <requirement-graph />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import RequirementGraph from "./components/RequirementGraph.vue";
import RequirementInput from "./components/RequirementInput.vue";
</script>

<style>
html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}
</style>
