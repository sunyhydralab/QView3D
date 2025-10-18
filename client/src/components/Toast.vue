<script lang="ts">
import { ref } from 'vue'

export interface ToastMessage {
  id: number
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  duration?: number
}

// Create a global toast messages array that can be accessed from any component
export const toastMessages = ref<ToastMessage[]>([])

// Counter to generate unique IDs for toast messages
let toastCounter = 0

// Add a new toast message
export function addToast(
  message: string,
  type: 'success' | 'error' | 'info' | 'warning' = 'info',
  duration = 5000
) {
  const id = toastCounter++
  toastMessages.value.push({
    id,
    type,
    message,
    duration
  })

  // Auto-remove the toast after the specified duration
  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  return id
}

// Remove a toast message by ID
export function removeToast(id: number) {
  const index = toastMessages.value.findIndex(toast => toast.id === id)
  if (index !== -1) {
    toastMessages.value.splice(index, 1)
  }
}

// Clear all toast messages
export function clearToasts() {
  toastMessages.value = []
}
</script>

<script setup lang="ts">
// Component setup code - no exports here
</script>

<template>
  <div class="fixed top-24 right-4 z-50 flex flex-col gap-2 max-w-md">
    <div
      v-for="toast in toastMessages"
      :key="toast.id"
      class="toast-notification rounded-md shadow-lg overflow-hidden flex transition-all duration-300 transform animate-slide-in"
      :class="{
        'bg-green-50 dark:bg-green-900': toast.type === 'success',
        'bg-red-50 dark:bg-red-900': toast.type === 'error',
        'bg-blue-50 dark:bg-blue-900': toast.type === 'info',
        'bg-yellow-50 dark:bg-yellow-900': toast.type === 'warning'
      }"
    >
      <!-- Icon based on toast type -->
      <div
        class="flex items-center justify-center w-12"
        :class="{
          'bg-green-500 text-white': toast.type === 'success',
          'bg-red-500 text-white': toast.type === 'error',
          'bg-blue-500 text-white': toast.type === 'info',
          'bg-yellow-500 text-white': toast.type === 'warning'
        }"
      >
        <i
          class="fas"
          :class="{
            'fa-check-circle': toast.type === 'success',
            'fa-exclamation-circle': toast.type === 'error',
            'fa-info-circle': toast.type === 'info',
            'fa-exclamation-triangle': toast.type === 'warning'
          }"
        ></i>
      </div>

      <!-- Toast content -->
      <div class="flex-1 p-3 flex items-center">
        <p
          class="text-sm"
          :class="{
            'text-green-800 dark:text-green-100': toast.type === 'success',
            'text-red-800 dark:text-red-100': toast.type === 'error',
            'text-blue-800 dark:text-blue-100': toast.type === 'info',
            'text-yellow-800 dark:text-yellow-100': toast.type === 'warning'
          }"
        >
          {{ toast.message }}
        </p>
      </div>

      <!-- Close button -->
      <button
        @click="removeToast(toast.id)"
        class="p-2 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-gray-100"
      >
        <i class="fas fa-times"></i>
      </button>
    </div>
  </div>
</template>

<style scoped>
.toast-notification {
  max-width: 24rem;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slideIn 0.3s ease-out forwards;
}
</style>
