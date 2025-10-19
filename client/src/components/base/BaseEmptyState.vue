<script setup lang="ts">
interface Props {
  icon: string;
  title: string;
  description?: string;
  iconColor?: string;
}

const props = withDefaults(defineProps<Props>(), {
  iconColor: 'text-gray-400'
});
</script>

<template>
  <div class="text-center py-16 animate-fade-in">
    <i :class="[icon, iconColor]" class="text-6xl mb-4" />
    <p class="text-xl font-medium text-gray-700 dark:text-gray-300">{{ title }}</p>
    <p v-if="description" class="text-gray-500 dark:text-gray-400 mt-2">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}
</style>
