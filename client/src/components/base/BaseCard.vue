<script setup lang="ts">
interface Props {
  gradient?: boolean;
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const props = withDefaults(defineProps<Props>(), {
  gradient: false,
  hover: true,
  padding: 'md'
});

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8'
};
</script>

<template>
  <div
    class="bg-white dark:bg-dark-primary-light rounded-xl shadow-md overflow-hidden transition-all duration-300"
    :class="[
      hover && 'hover:shadow-xl transform hover:-translate-y-1',
      paddingClasses[padding]
    ]"
  >
    <div v-if="gradient" class="h-2 bg-gradient-to-r from-accent-primary to-accent-primary-light" />
    <slot />
  </div>
</template>
