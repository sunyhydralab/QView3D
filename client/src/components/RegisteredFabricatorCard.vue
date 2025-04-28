<script setup lang="ts">
interface FabricatorProps {
  name: string
  model: string
  date: string | Date
}

const props = defineProps<FabricatorProps>()
</script>

<template>
  <div
    class="m-2 p-1 max-w-60 rounded-2xl shadow-md transition-transform duration-300 hover:scale-[1.02] dark:bg-dark-primary-light bg-white"
  >
    <div class="my-4 mx-3">
      <h2 class="text-2xl font-bold pb-2 truncate bg-gradient-to-r from-accent-primary-light to-accent-primary bg-clip-text text-transparent">{{ props.name }}</h2>
      <p class="text-dark-primary dark:text-light-primary py-1 truncate">{{ props.description }}</p>
      <p class="text-dark-primary dark:text-light-primary py-1">{{ props.date }}</p>
    </div>
  </div>
</template>
