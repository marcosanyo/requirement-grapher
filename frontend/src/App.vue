<!-- src/App.vue -->
<template>
  <v-app>
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
