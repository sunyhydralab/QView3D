<script setup lang="ts">
interface FabricatorProps {
    name: string;
    model: string;
    date: string | Date;
}

const props = defineProps<FabricatorProps>();
</script>

<template>
    <div
      class="my-10 mx-auto max-w-sm rounded-2xl shadow-md transition-transform duration-300 hover:scale-[1.02] dark:bg-light-primary-light bg-white">
      
      <!-- Header -->
      <div class="rounded-t-2xl bg-accent-primary px-6 py-4">
        <h2 class="text-xl sm:text-2xl font-semibold text-white tracking-wide">
          {{ name }}
        </h2>
      </div>
  
      <!-- Content -->
      <div class="px-6 py-4 space-y-2 dark:bg-dark-primary-light">
        <p class="text-base text-gray-600 dark:text-white font-bold">
          <span class="font-medium text-gray-800 dark:text-black dark:text-white">Model:</span> {{ model }}
        </p>
        <p class="text-base text-black text-black dark:text-white font-bold">
          <span class="font-medium text-black dark:text-white">Date Registered:</span> {{ date }}
        </p>
      </div>
    </div>
  </template>
  