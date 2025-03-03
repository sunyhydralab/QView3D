<script setup lang="ts">
import { printers } from "@/model/ports";
</script>

<template>
  <div v-if="printers.length === 0" class="d-flex flex-column align-items-center mt-3 fade show slide-down">
    <img src="@/assets/sad-robot.gif" alt="Sad Robot" class="robot" />
    <div class="text mt-3">
      No printers available. Either register a printer
      <RouterLink class="routerLink" to="/registration">here,</RouterLink>
      or restart the server.
    </div>
  </div>
</template>

<style scoped>
.robot {
  width: 25rem;
  height: auto;
  opacity: 90%;
}

@keyframes slideDown {
  from {
    transform: translateY(-50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.slide-down {
  animation: slideDown 0.5s ease-out;
}
</style>
