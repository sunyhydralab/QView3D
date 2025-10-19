<script setup lang="ts">
import { ref, watch } from 'vue';
import { API_IP_ADDRESS, API_PORT, DEBUG_MODE, updateAPIAddress, updateAPIPort, updateDebugMode } from '@/composables/useIPSettings.ts';
import Button from '@/components/Button.vue'

const serverIP = ref<string>(API_IP_ADDRESS.value);
const serverPort = ref<string>(API_PORT.value);
const debugMode = ref<boolean>(DEBUG_MODE.value);
const isOpen = ref(false);

// Server type options
const serverTypes = [
  { name: 'Middleware (Hybrid)', port: '3500' },
  { name: 'Python Backend', port: '8000' },
  { name: 'JavaScript Backend', port: '3001' }
];

const selectedServerType = ref(
  serverTypes.find(s => s.port === serverPort.value) || serverTypes[0]
);

// Watch for server type changes and update port
watch(selectedServerType, (newType) => {
  serverPort.value = newType.port;
});

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
  if (debugMode.value !== DEBUG_MODE.value) {
    updateDebugMode(debugMode.value);
  }
  console.log(`Server IP: ${serverIP.value}, Server Port: ${serverPort.value}, Debug Mode: ${debugMode.value}`);
  isOpen.value = false;
  window.location.reload()
};
</script>

<template>
  <div>
    <!-- Trigger Button -->
    <div class="fixed bottom-4 right-4 z-50">
      <Button @click="togglePanel">
        <i class="fas fa-gear py-2"></i>
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
          <!-- Server Type Selector - only shows in debug mode -->
          <div v-if="debugMode">
            <label for="serverType" class="block text-sm font-medium dark:text-light-primary-dark mb-2">Server Type:</label>
            <select
              id="serverType"
              v-model="selectedServerType"
              class="input-style mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-dark-primary-dark dark:text-light-primary"
            >
              <option v-for="type in serverTypes" :key="type.port" :value="type">
                {{ type.name }} (Port {{ type.port }})
              </option>
            </select>
          </div>

          <!-- Manual Port Input - shows when not in debug mode or for custom ports -->
          <div v-if="!debugMode">
            <label for="port" class="block text-sm font-medium dark:text-light-primary-dark">Server Port:</label>
            <input
              type="number"
              id="port"
              v-model="serverPort"
              required
              class="input-style mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <!-- Port Display when server type is selected -->
          <div v-else>
            <label class="block text-sm font-medium dark:text-light-primary-dark">Current Port:</label>
            <div class="mt-1 px-3 py-2 bg-gray-100 dark:bg-dark-primary-light rounded-md">
              <span class="text-sm dark:text-light-primary">{{ serverPort }}</span>
            </div>
          </div>
          <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-dark-primary-dark rounded-lg">
            <div>
              <label for="debug" class="block text-sm font-medium dark:text-light-primary-dark">Debug Mode</label>
              <p class="text-xs text-gray-500 dark:text-gray-400">Enable virtual emulator</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                id="debug"
                v-model="debugMode"
                class="sr-only peer"
              />
              <div class="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary/20 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-accent-primary"></div>
            </label>
          </div>
          <Button @click="saveSettings" class="w-full">
            Save
          </Button>
        </form>
      </div>
    </div>
  </div>
</template>
