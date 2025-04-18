<!-- src/components/BaseButton.vue -->
<script setup lang="ts">
import { computed } from 'vue';

// Props: customize behavior and look
const props = defineProps({
  variant: {
    type: String as () => 'primary' | 'secondary',
    default: 'primary',
  },
  isDisabled: {
    type: Boolean,
    default: false,
  },
});

// tells parent when the button is clicked
const emit = defineEmits(['click']);

// Style based on variant prop
const variantClass = computed(() => {
  const styles = {
    primary: 'bg-accent-primary text-white hover:bg-accent-primary-light',
    secondary: 'bg-accent-secondary text-black hover:bg-accent-secondary-light',
  };
  return styles[props.variant];
});

// Combine all classes for the button
const buttonClasses = computed(() => [
  'px-4 py-2 rounded-md font-semibold transition-colors duration-200',
  variantClass.value,
  props.isDisabled ? 'opacity-50 cursor-not-allowed' : '',
]);

// Handle click if not disabled
function handleClick(event: any) {
  if (!props.isDisabled) {
    emit('click', event);
  }
}
</script>

<template>
    <button
      v-bind:class="buttonClasses"
      v-bind:disabled="isDisabled"
      @click="handleClick"
    >
      <slot />
    </button>
  </template>
  