<script setup lang="ts">
import { ref, watch } from 'vue';
import { API_IP_ADDRESS, API_PORT, DEBUG_MODE, updateAPIAddress, updateAPIPort, updateDebugMode } from '@/composables/useIPSettings.ts';
import Button from '@/components/Button.vue'

const serverIP = ref<string>(API_IP_ADDRESS.value);
const serverPort = ref<string>(API_PORT.value);
const debugMode = ref<boolean>(DEBUG_MODE.value);
const isOpen = ref(false);

interface ServerStatus {
  name: string;
  port: string;
  online: boolean;
  checking: boolean;
  service?: string;
}

// Server type options with status tracking
const serverTypes = ref<ServerStatus[]>([
  { name: 'Middleware (Hybrid)', port: '3500', online: false, checking: false },
  { name: 'Python Backend', port: '8000', online: false, checking: false },
  { name: 'JavaScript Backend', port: '3001', online: false, checking: false }
]);

const selectedServerType = ref(
  serverTypes.value.find(s => s.port === serverPort.value) || serverTypes.value[0]
);

const isDetecting = ref(false);

// Watch for server type changes and update port
watch(selectedServerType, (newType) => {
  serverPort.value = newType.port;
});

// Watch for panel open and auto-detect servers
watch(isOpen, (newValue) => {
  if (newValue) {
    detectServers();
  }
});

const togglePanel = () => {
  isOpen.value = !isOpen.value;
};

// Check if a server is online by pinging its health endpoint
async function checkServerHealth(ip: string, port: string): Promise<{ online: boolean; service?: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout

    const response = await fetch(`http://${ip}:${port}/health`, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      return {
        online: true,
        service: data.service || data.middleware || 'unknown'
      };
    }
    return { online: false };
  } catch {
    return { online: false };
  }
}

// Detect all available servers
async function detectServers() {
  isDetecting.value = true;

  // Set all servers to checking state
  serverTypes.value.forEach(server => {
    server.checking = true;
  });

  // Check each server in parallel
  const checks = serverTypes.value.map(async (server) => {
    const result = await checkServerHealth(serverIP.value, server.port);
    server.online = result.online;
    server.service = result.service;
    server.checking = false;
  });

  await Promise.all(checks);
  isDetecting.value = false;

  // Auto-select the first online server if current selection is offline
  if (!selectedServerType.value.online) {
    const firstOnline = serverTypes.value.find(s => s.online);
    if (firstOnline) {
      selectedServerType.value = firstOnline;
    }
  }
}

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
          <!-- Server Detection Section -->
          <div v-if="debugMode" class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="block text-sm font-medium dark:text-light-primary-dark">Server Detection:</label>
              <Button
                @click="detectServers"
                :disabled="isDetecting"
                class="text-xs px-3 py-1"
              >
                <i v-if="isDetecting" class="fas fa-spinner fa-spin mr-1"></i>
                <i v-else class="fas fa-sync mr-1"></i>
                {{ isDetecting ? 'Detecting...' : 'Detect' }}
              </Button>
            </div>

            <!-- Server Status Indicators -->
            <div class="bg-gray-50 dark:bg-dark-primary-light rounded-lg p-3 space-y-2">
              <div v-for="server in serverTypes" :key="server.port" class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <!-- Status Indicator -->
                  <div class="relative">
                    <div
                      v-if="server.checking"
                      class="w-3 h-3 rounded-full bg-yellow-400 animate-pulse"
                      title="Checking..."
                    ></div>
                    <div
                      v-else
                      :class="[
                        'w-3 h-3 rounded-full',
                        server.online ? 'bg-green-500' : 'bg-red-500'
                      ]"
                      :title="server.online ? 'Online' : 'Offline'"
                    ></div>
                  </div>
                  <span class="text-sm dark:text-light-primary">
                    {{ server.name }}
                  </span>
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  :{{ server.port }}
                </span>
              </div>
            </div>

            <!-- Server Type Selector -->
            <div>
              <label for="serverType" class="block text-sm font-medium dark:text-light-primary-dark mb-2">Select Server:</label>
              <select
                id="serverType"
                v-model="selectedServerType"
                class="input-style mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-dark-primary-dark dark:text-light-primary"
              >
                <option v-for="type in serverTypes" :key="type.port" :value="type">
                  {{ type.name }} (Port {{ type.port }})
                  <template v-if="type.online"> - Online</template>
                </option>
              </select>
            </div>
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
