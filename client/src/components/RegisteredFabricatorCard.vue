<script setup lang="ts">
import { api } from '@/models/api';
import { addToast } from '@/components/Toast.vue';

interface FabricatorProps {
  id: number; 
  name: string;
  model: string;
  date: string | Date;
  hwid?: string;
}

const props = defineProps<FabricatorProps>()

const emit = defineEmits(['deleted'])

async function deleteFabricator() {
  try {
    console.log(`Attempting to delete printer with ID: ${props.id}`);
    // Use correct endpoint from ports.py -> deletefabricator
    await api('deletefabricator', { fabricator_id: props.id });
    addToast(`Successfully deleted ${props.name}`, 'success');
    emit('deleted', props.id);
  } catch (error) {
    console.error('Failed to delete printer:', error);
    addToast('Failed to delete printer', 'error');
  }
}
</script>

<template>
  <div
    class="m-2 p-4 max-w-60 rounded-lg shadow-md transition-all duration-300 hover:shadow-lg hover:-translate-y-1 dark:bg-dark-primary-light bg-white"
  >
    <div class="relative">
      <!-- Delete button -->
      <button 
        @click="deleteFabricator"
        class="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-7 h-7 flex items-center justify-center transition-colors"
        title="Delete printer"
      >
        <span class="sr-only">Delete</span>
        <i class="fas fa-times"></i>
      </button>

      <h2 class="text-xl font-bold pb-2 truncate dark:text-white text-gray-900">
        {{ props.name }}
      </h2>
      <p class="text-gray-700 dark:text-gray-200 py-1 truncate">{{ props.model }}</p>
      <p class="text-gray-500 dark:text-gray-400 text-sm py-1">{{ props.date }}</p>
      <p v-if="props.hwid" class="text-gray-400 dark:text-gray-500 text-xs py-1 truncate">ID: {{ props.hwid }}</p>
    </div>
  </div>
</template>