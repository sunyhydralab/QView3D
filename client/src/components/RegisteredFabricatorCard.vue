<script setup lang="ts">
import { deleteFabricator } from '@/models/fabricator';
import { computed, ref } from 'vue'
import { api } from '@/models/api'
import { addToast } from '@/components/Toast.vue'

interface FabricatorProps {
  name: string
  model: string
  date: string | Date
  id: number
  status?: string
}

const props = defineProps<FabricatorProps>()
const emit = defineEmits(['deregistered', 'statusChanged'])

// Add state for animation control
const isVisible = ref(true)
const isTogglingStatus = ref(false)

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

// Compute status display properties
const isOnline = computed(() => props.status === 'ready')
const statusColor = computed(() => isOnline.value ? 'green' : 'gray')
const statusText = computed(() => isOnline.value ? 'Online' : 'Offline')

// Function to handle deregister button click
async function handleDeregister() {
  // First trigger the fade-out animation
  isVisible.value = false

  // Wait for animation to complete before actual deletion
  setTimeout(async () => {
    // Proceed with deletion in backend
    await deleteFabricator(props.id)
    console.log(`Deregistering fabricator: ${props.name}`)
    emit('deregistered', props.id)
  }, 500) // Match this with CSS transition duration
}

// Function to toggle fabricator online/offline status
async function toggleStatus() {
  if (isTogglingStatus.value) return

  isTogglingStatus.value = true
  const newStatus = isOnline.value ? 'offline' : 'online'

  try {
    // Call the appropriate API endpoint
    const endpoint = `fabricator/${props.id}/${newStatus}`
    const result = await api(endpoint, {}, 'POST')

    if (result.success) {
      addToast(`${props.name} is now ${newStatus}`, 'success')
      emit('statusChanged', { id: props.id, status: result.status })
    } else {
      addToast(`Failed to turn ${props.name} ${newStatus}`, 'error')
    }
  } catch (error) {
    console.error(`Error toggling status for ${props.name}:`, error)
    addToast(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
  } finally {
    isTogglingStatus.value = false
  }
}
</script>

<template>
  <div
    class="fabricator-card bg-white dark:bg-dark-primary-light rounded-xl shadow-md overflow-hidden transition-all duration-500 hover:shadow-lg"
    :class="{ 'puff-out-center': !isVisible, 'opacity-100': isVisible }"
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
        <div class="flex items-center text-dark-primary dark:text-light-primary">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-accent-primary" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0110 2v5a1 1 0 01-1 1H4a1 1 0 01-1-1V2a1 1 0 01.7-.954l6-2a1 1 0 011.3.954V2zm1.4 9.154a1 1 0 00-1.4.897v5.047a1 1 0 001.3.953l6-2A1 1 0 0019 14v-5a1 1 0 00-1-1h-5a1 1 0 00-.3.046l-6 2z" clip-rule="evenodd" />
          </svg>
          <span class="truncate text-sm">{{ model }}</span>
        </div>

        <!-- Date info -->
        <div class="flex items-center text-dark-primary dark:text-light-primary">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-accent-primary" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
          </svg>
          <span class="text-sm">{{ formattedDate }}</span>
        </div>
      </div>
      
      <!-- Status indicator -->
      <div class="flex items-center mt-4">
        <div
          class="h-2 w-2 rounded-full mr-2"
          :class="{
            'bg-green-500 animate-pulse': isOnline,
            'bg-gray-400': !isOnline
          }"
        ></div>
        <span
          class="text-xs"
          :class="{
            'text-green-600 dark:text-green-400': isOnline,
            'text-gray-500 dark:text-gray-400': !isOnline
          }"
        >
          {{ statusText }}
        </span>
      </div>
    </div>

    <!-- Card actions -->
    <div
      class="px-5 py-3 bg-light-primary dark:bg-dark-primary flex justify-end space-x-2"
    >
      <!-- Turn Online/Offline button -->
      <button
        class="p-1 text-dark-primary dark:text-light-primary transition-colors duration-200 rounded flex items-center"
        :class="{
          'hover:text-green-500 dark:hover:text-green-400': !isOnline,
          'hover:text-orange-500 dark:hover:text-orange-400': isOnline,
          'opacity-50 cursor-not-allowed': isTogglingStatus
        }"
        :disabled="isTogglingStatus"
        @click="toggleStatus"
      >
        <!-- Power icon -->
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <span class="text-sm">Turn {{ isOnline ? 'Offline' : 'Online' }}</span>
      </button>

      <!-- Deregister button -->
      <button
        class="p-1 text-dark-primary dark:text-light-primary hover:text-red-500 dark:hover:text-red-400 transition-colors duration-200 rounded flex items-center"
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
  will-change: transform, box-shadow, opacity;
  animation: card-appear 0.5s ease forwards;
  transition: all 0.5s ease;
  max-width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Growing and rising animation on hover */
.fabricator-card:hover {
  transform: translateY(-16px) scale(1.15);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 15px 25px -5px rgba(0, 0, 0, 0.15);
  transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.5), box-shadow 0.5s ease;
  z-index: 10;
}

.puff-out-center {
	-webkit-animation: puff-out-center 1s cubic-bezier(0.165, 0.840, 0.440, 1.000) both;
	        animation: puff-out-center 1s cubic-bezier(0.165, 0.840, 0.440, 1.000) both;
}

/* ----------------------------------------------
 * Generated by Animista on 2025-4-29 13:50:6
 * Licensed under FreeBSD License.
 * See http://animista.net/license for more info. 
 * w: http://animista.net, t: @cssanimista
 * ---------------------------------------------- */

/**
 * ----------------------------------------
 * animation puff-out-center
 * ----------------------------------------
 */
 @-webkit-keyframes puff-out-center {
  0% {
    -webkit-transform: scale(1);
            transform: scale(1);
    -webkit-filter: blur(0px);
            filter: blur(0px);
    opacity: 1;
  }
  100% {
    -webkit-transform: scale(1.1);
            transform: scale(1.1);
    -webkit-filter: blur(4px);
            filter: blur(4px);
    opacity: 0;
  }
}
@keyframes puff-out-center {
  0% {
    -webkit-transform: scale(1);
            transform: scale(1);
    -webkit-filter: blur(0px);
            filter: blur(0px);
    opacity: 1;
  }
  100% {
    -webkit-transform: scale(1.1);
            transform: scale(1.1);
    -webkit-filter: blur(4px);
            filter: blur(4px);
    opacity: 0;
  }
}

</style>