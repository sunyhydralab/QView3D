<script setup lang="ts">
import { printers } from "@/model/ports";
</script>

<template>
  <div v-if="printers.length === 0" style="margin-top: 1rem; margin-bottom: 1rem">
    <img src="@/assets/sad-robot.svg" alt="Sad Robot" class="robot" /><img />
  </div>
  <div v-if="printers.length === 0" style="margin-top: 1rem; font-size: large">
    No printers available. Either register a printer
    <RouterLink class="routerLink" to="/registration">here,</RouterLink>
    or restart the server.
  </div>
</template>

<style scoped>
.robot {
  width: 25rem;
  height: auto;
  opacity: 90%;
}
</style>
