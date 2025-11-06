<script setup lang="ts">
interface Props {
  title: string;
  value: string | number;
  icon?: string;
  gradient?: string;
}

const props = withDefaults(defineProps<Props>(), {
  gradient: 'from-accent-primary to-accent-primary-light'
});
</script>

<template>
  <div
    class="rounded-xl p-6 text-white shadow-lg transform transition-all duration-300 hover:scale-105 bg-gradient-to-br"
    :class="gradient"
  >
    <div class="flex items-center justify-between">
      <div>
        <p class="opacity-80 text-sm">{{ title }}</p>
        <p class="text-3xl font-bold mt-1">{{ value }}</p>
      </div>
      <i v-if="icon" :class="icon" class="text-4xl opacity-60" />
    </div>
  </div>
</template>
