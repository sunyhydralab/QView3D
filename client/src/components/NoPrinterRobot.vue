<script setup lang="ts">
import { fabricatorList } from "@/models/fabricator";
</script>

<template>
  <div v-if="fabricatorList.length === 0" class="flex flex-col items-center justify-center text-cent fade show slide-down">
    <img src="@/assets/sad-robot.svg" alt="Sad Robot" class="robot" />
    <div class="text-black dark:text-white">
      No printers available. Either register a printer
      <RouterLink class="text-accent-secondary dark:text-accent-secondary-light routerLink" to="/register">here,</RouterLink>
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
