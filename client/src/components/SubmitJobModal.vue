<script setup lang="ts">
import { ref } from 'vue'

// File handling refs - functionality to be implemented by you
const selectedFile = ref<File | null>(null)
const fileName = ref<string>("No file selected.")
const filamentDetected = ref<string | null>(null)
</script>

<template>
  <!-- Modal backdrop with blur and click-outside handling -->
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
    @click.self="$emit('close')">
    <!-- Modal container -->
    <div class="bg-light-primary dark:bg-dark-primary-light rounded-lg shadow-lg max-w-md w-full mx-4 animate-fade-in">
      <!-- Modal header -->
      <div class="p-4 flex justify-between items-center">
        <h3 class="text-lg font-medium text-black dark:text-white">Submit Job</h3>
        <button @click="$emit('close')"
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd" />
          </svg>
        </button>
      </div>

      <!-- Modal body -->
      <div class="p-4 space-y-5">
        <!-- Fabricator Selection -->
        <div class="space-y-2">
          <h4 class="text-sm font-medium text-center text-gray-700 dark:text-gray-300">Select Fabricator</h4>
          <div class="bg-gray-100 dark:bg-light-primary-light rounded-md p-2 space-y-1">
            <div class="flex items-center px-2 py-1">
              <input type="checkbox" id="select-all"
                class="mr-3 h-4 w-4 rounded border-gray-300 focus:ring-accent-primary-light">
              <label for="select-all" class="text-sm text-gray-700 dark:text-black">Select All</label>
            </div>
            <div class="border-b border-light-primary-dark dark:border-dark-primary-light"></div>
            <div class="flex items-center px-2 py-1">
              <input type="checkbox" id="mk4"
                class="mr-3 h-4 w-4 rounded border-gray-300 focus:ring-accent-primary-light">
              <label for="mk4" class="text-sm text-gray-700 dark:text-black">Some Fabricator</label>
            </div>
          </div>
          <p class="text-xs text-center text-gray-500 dark:text-gray-400">
            No fabricator selected, will <span class="text-accent-primary-light">auto queue</span>
          </p>
        </div>

        <!-- File Upload -->
        <div class="space-y-1">
          <div class="flex items-center">
            <label for="file-upload" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Upload your
              .gcode file<span class="text-red-500 ml-1">*</span></label>
          </div>
          <div class="flex space-x-2">
            <button type="button"
              class="px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-accent-primary-dark transition">
              Browse
            </button>
            <div class="flex-1 px-3 py-2 bg-gray-100 dark:bg-light-primary-light rounded-md flex items-center">
              <span class="text-gray-500 dark:text-gray-400 truncate">{{ fileName }}</span>
            </div>
            <button type="button" class="bg-accent-primary hover:bg-accent-primary-dark p-2 px-3 rounded-md">
              <i class="fa-regular fa-image text-white"></i>
            </button>
            <input ref="fileInput" type="file" accept=".gcode" class="hidden" />
          </div>
        </div>

        <!-- Quantity -->
        <div class="space-y-1">
          <label for="quantity" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Quantity</label>
          <div class="relative">
            <input id="quantity" type="number" min="1" value="1"
              class="w-full px-3 py-2 border border-gray-300 bg-gray-50 dark:bg-light-primary-light rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light" />
            <button type="button"
              class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
            </button>
          </div>
        </div>

        <!-- Ticket ID -->
        <div class="space-y-1">
          <label for="ticketId" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Ticket ID</label>
          <div class="relative">
            <input id="ticketId" type="number" min="0" value="0"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-light-primary-light rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light" />
            <button type="button"
              class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
            </button>
          </div>
        </div>

        <!-- Name -->
        <div class="space-y-1">
          <div class="flex items-center">
            <label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
            <span class="text-red-500 ml-1">*</span>
          </div>
          <input id="name" type="text" required
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-light-primary-light rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light dark:text-white"
            placeholder="Enter job name" />
        </div>
      </div>

      <!-- Modal footer -->
      <div class="border-t border-gray-200 dark:border-gray-700 p-4 flex justify-end">
        <button type="button"
          class="px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-accent-primary-dark transition disabled:opacity-50 disabled:cursor-not-allowed">
          Submit
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>