<script setup lang="ts">
import { deleteFabricator } from '@/models/fabricator';
import { computed } from 'vue'
interface FabricatorProps {
  name: string
  model: string
  date: string | Date
  id: number
}

const props = defineProps<FabricatorProps>()
const emit = defineEmits(['deregistered'])

// Format the date if it's provided
const formattedDate = computed(() => {
  if (!props.date) return 'Unknown date'
  
  // If already a string, return as is
  if (typeof props.date === 'string') return props.date
  
  // If Date object, format it
  return new Date(props.date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
})

// Function to handle deregister button click
async function handleDeregister() {
  // TODO: Implement deregistering logic
  await deleteFabricator(props.id)
  console.log(`Deregistering fabricator: ${props.name}`)
  emit('deregistered', props.id);
}
</script>

<template>
  <div
    class="fabricator-card bg-white dark:bg-dark-primary-light rounded-xl shadow-md overflow-hidden transition-all duration-300 hover:shadow-lg"
  >
    <!-- Card header -->
    <div class="h-2 bg-gradient-to-r from-accent-primary to-accent-primary-light"></div>
    
    <!-- Card content -->
    <div class="p-5">
      <h2 
        class="text-xl font-bold mb-3 truncate text-dark-primary dark:text-light-primary"
      >
        {{ name }}
      </h2>
      
      <div class="space-y-3">
        <!-- Model info -->
        <div class="flex items-center text-gray-700 dark:text-gray-300">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-accent-primary" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0110 2v5a1 1 0 01-1 1H4a1 1 0 01-1-1V2a1 1 0 01.7-.954l6-2a1 1 0 011.3.954V2zm1.4 9.154a1 1 0 00-1.4.897v5.047a1 1 0 001.3.953l6-2A1 1 0 0019 14v-5a1 1 0 00-1-1h-5a1 1 0 00-.3.046l-6 2z" clip-rule="evenodd" />
          </svg>
          <span class="truncate text-sm">{{ model }}</span>
        </div>
        
        <!-- Date info -->
        <div class="flex items-center text-gray-700 dark:text-gray-300">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-accent-primary" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm">{{ formattedDate }}</span>
        </div>
      </div>
      
      <!-- Status indicator -->
      <div class="flex items-center mt-4">
        <div class="h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse"></div>
        <span class="text-xs text-green-600 dark:text-green-400">Online</span>
      </div>
    </div>
    
    <!-- Card actions -->
    <div 
      class="px-5 py-3 bg-gray-50 dark:bg-dark-primary flex justify-end space-x-2"
    >
      <!-- Deregister button -->
      <button 
        class="p-1 text-gray-500 hover:text-red-500 transition-colors duration-200 rounded flex items-center"
        @click="handleDeregister"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        <span class="text-sm">Deregister</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.fabricator-card {
  will-change: transform, box-shadow;
  animation: card-appear 0.5s ease forwards;
  opacity: 0;
  transform: translateY(20px);
}

@keyframes card-appear {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Growing and rising animation on hover */
.fabricator-card {
  max-width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.fabricator-card:hover {
  transform: translateY(-16px) scale(1.15);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 15px 25px -5px rgba(0, 0, 0, 0.15);
  transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.5), box-shadow 0.5s ease;
  z-index: 10;
}
</style>