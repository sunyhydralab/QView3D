<script setup lang="ts">
import { ref, watch } from 'vue';
import { API_IP_ADDRESS, DEBUG_MODE, updateAPIAddress, updateDebugMode } from '@/composables/useIPSettings.ts';
import Button from '@/components/Button.vue'

const serverIP = ref<string>(API_IP_ADDRESS.value);
const debugMode = ref<boolean>(DEBUG_MODE.value);
const isOpen = ref(false);

interface ServerStatus {
  online: boolean;
  checking: boolean;
  backend?: string;
  url?: string;
  server_status?: any;
}

// Server status
const serverStatus = ref<ServerStatus>({
  online: false,
  checking: false
});

const isDetecting = ref(false);

// Watch for panel open and check server status if debug mode is enabled
watch(isOpen, (newValue) => {
  if (newValue && debugMode.value) {
    checkServerStatus();
  }
});

const togglePanel = () => {
  isOpen.value = !isOpen.value;
};

// Check server status (only available in debug mode)
async function checkServerStatus() {
  if (!debugMode.value) return;

  isDetecting.value = true;
  serverStatus.value.checking = true;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const response = await fetch(`http://${serverIP.value}:8002/api/middleware/health?debug=true`, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      serverStatus.value.online = true;
      serverStatus.value.backend = data.server_backend;
      serverStatus.value.url = data.server_url;
      serverStatus.value.server_status = data.server_status;
    } else {
      serverStatus.value.online = false;
    }
  } catch {
    serverStatus.value.online = false;
  }

  serverStatus.value.checking = false;
  isDetecting.value = false;
}

const saveSettings = async () => {
  if (serverIP.value !== API_IP_ADDRESS.value) {
    updateAPIAddress(serverIP.value);
  }
  if (debugMode.value !== DEBUG_MODE.value) {
    updateDebugMode(debugMode.value);
  }

  console.log(`Server IP: ${serverIP.value}, Debug Mode: ${debugMode.value}`);
  alert('Settings saved!');
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

          <!-- Server Status Section (Debug Mode Only) -->
          <div v-if="debugMode" class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="block text-sm font-medium dark:text-light-primary-dark">Server Status:</label>
              <Button
                @click="checkServerStatus"
                :disabled="isDetecting"
                class="text-xs px-3 py-1"
              >
                <i v-if="isDetecting" class="fas fa-spinner fa-spin mr-1"></i>
                <i v-else class="fas fa-sync mr-1"></i>
                {{ isDetecting ? 'Checking...' : 'Check' }}
              </Button>
            </div>

            <!-- Server Status Display -->
            <div class="bg-gray-50 dark:bg-dark-primary-light rounded-lg p-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <!-- Status Indicator -->
                  <div class="relative">
                    <div
                      v-if="serverStatus.checking"
                      class="w-3 h-3 rounded-full bg-yellow-400 animate-pulse"
                      title="Checking..."
                    ></div>
                    <div
                      v-else
                      :class="[
                        'w-3 h-3 rounded-full',
                        serverStatus.online ? 'bg-green-500' : 'bg-red-500'
                      ]"
                      :title="serverStatus.online ? 'Online' : 'Offline'"
                    ></div>
                  </div>
                  <div>
                    <span class="text-sm font-medium dark:text-light-primary">
                      {{ serverStatus.backend || 'Server' }}
                    </span>
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      {{ serverStatus.url || 'Unknown' }}
                    </p>
                  </div>
                </div>
                <span class="text-xs font-medium" :class="serverStatus.online ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                  {{ serverStatus.online ? 'Online' : 'Offline' }}
                </span>
              </div>
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
