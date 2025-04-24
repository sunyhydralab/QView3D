<script setup lang="ts">
import { ref } from 'vue';
import { API_IP_ADDRESS, API_PORT, updateAPIAddress, updateAPIPort } from '@/composables/useIPSettings.ts';
import Button from '@/components/Button.vue'

const serverIP = ref<string>(API_IP_ADDRESS.value);
const serverPort = ref<string>(API_PORT.value);
const isOpen = ref(false);

const togglePanel = () => {
  isOpen.value = !isOpen.value;
};

const saveSettings = () => {
  if (serverIP.value !== API_IP_ADDRESS.value) {
    updateAPIAddress(serverIP.value);
  }
  if (serverPort.value !== API_PORT.value) {
    updateAPIPort(serverPort.value);
  }
  console.log(`Server IP: ${serverIP.value}, Server Port: ${serverPort.value}`);
  isOpen.value = false;
  window.location.reload()
};
</script>

<template>
  <div>
    <!-- Trigger Button -->
    <div class="fixed bottom-4 right-4 z-50">
      <Button @click="togglePanel">
        <i class="fas fa-gear"></i>
      </Button>
    </div>

    <!-- Overlay -->
    <div
      v-if="isOpen"
      @click="togglePanel"
      class="fixed inset-0 bg-black bg-opacity-50 z-40"
    ></div>

    <!-- Slide-in Panel -->
    <div
      :class="[
        'fixed top-0 right-0 h-full w-80 bg-white dark:bg-dark-primary shadow-xl z-50 transform transition-transform duration-300 ease-in-out',
        isOpen ? 'translate-x-0' : 'translate-x-full'
      ]"
    >
      <div class="flex justify-between items-center p-4 border-b">
        <h2 class="text-lg font-semibold dark:text-light-primary">Server Settings</h2>
        <button @click="togglePanel" class="dark:text-light-primary-dark ">&times;</button>
      </div>
      <div class="p-4">
        <form @submit.prevent="saveSettings" class="space-y-4 ">
          <div>
            <label for="ip" class="block text-sm font-medium dark:text-light-primary-dark">Server IP:</label>
            <input
              type="text"
              id="ip"
              v-model="serverIP"
              required
              class="input-style mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label for="port" class="block text-sm font-medium dark:text-light-primary-dark">Server Port:</label>
            <input
              type="number"
              id="port"
              v-model="serverPort"
              required
              class="input-style mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <Button @click="saveSettings" class="w-full">
            Save
          </Button>
        </form>
      </div>
    </div>
  </div>
</template>
