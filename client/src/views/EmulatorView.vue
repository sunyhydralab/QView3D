<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '@/models/api';
import { DEBUG_MODE } from '@/composables/useIPSettings';
import { addToast } from '@/components/Toast.vue';

const router = useRouter();
const isActive = ref(false);
const loading = ref(false);
const emulatorName = ref('Virtual Printer');

// Check if debug mode is enabled
onMounted(() => {
  if (!DEBUG_MODE.value) {
    addToast('Debug mode is required to access the emulator', 'warning');
    router.push('/');
  }
});

// Start and register emulator in one action
const startEmulator = async () => {
  loading.value = true;

  try {
    // Start the emulator
    const startResponse = await api('startemulator', 'POST', {
      model: 'Prusa MK4',
      config: {
        name: emulatorName.value,
        description: 'Virtual Printer for Testing',
        hwid: 'EMU-' + Math.floor(Math.random() * 10000)
      }
    });

    if (!startResponse.success) {
      throw new Error('Failed to start emulator');
    }

    // Register the emulator as a fabricator
    const registerResponse = await api('registeremulator', 'POST', {
      model: 'Prusa MK4',
      config: {
        name: emulatorName.value,
        port: startResponse.port
      }
    });

    if (registerResponse.success) {
      isActive.value = true;
      addToast(`${emulatorName.value} started and registered successfully`, 'success');
    }
  } catch (error) {
    console.error('Error starting emulator:', error);
    addToast('Failed to start emulator', 'error');
  } finally {
    loading.value = false;
  }
};

// Stop emulator
const stopEmulator = async () => {
  loading.value = true;

  try {
    await api('disconnectemulator', 'POST', {
      printerConfig: {}
    });

    isActive.value = false;
    addToast('Emulator stopped successfully', 'info');
  } catch (error) {
    console.error('Error stopping emulator:', error);
    addToast('Failed to stop emulator', 'error');
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-light-primary via-white to-light-primary dark:from-dark-primary-dark dark:via-dark-primary dark:to-dark-primary-light transition-colors duration-300">
    <div class="container mx-auto px-4 py-12">
      <div class="max-w-2xl mx-auto">
        <!-- Header -->
        <div class="text-center mb-12">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-accent-primary to-accent-primary-light mb-4">
            <i class="fas fa-microchip text-4xl text-white"></i>
          </div>
          <h1 class="text-4xl font-bold bg-gradient-to-r from-accent-primary via-accent-primary-light to-accent-secondary bg-clip-text text-transparent mb-2">
            Virtual Emulator
          </h1>
          <p class="text-gray-600 dark:text-gray-400">
            Test the system without physical hardware
          </p>
        </div>

        <!-- Main Card -->
        <div class="bg-white dark:bg-dark-primary-light rounded-2xl shadow-xl overflow-hidden">
          <!-- Status Banner -->
          <div
            class="px-8 py-6 transition-colors duration-300"
            :class="isActive
              ? 'bg-gradient-to-r from-green-500 to-green-600'
              : 'bg-gradient-to-r from-gray-500 to-gray-600'"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="relative">
                  <div
                    class="w-4 h-4 rounded-full"
                    :class="isActive ? 'bg-white animate-pulse' : 'bg-white/50'"
                  ></div>
                </div>
                <div>
                  <div class="text-white/80 text-sm">Status</div>
                  <div class="text-white font-semibold text-lg">
                    {{ isActive ? 'Active' : 'Inactive' }}
                  </div>
                </div>
              </div>
              <i
                class="text-4xl text-white/80"
                :class="isActive ? 'fas fa-check-circle' : 'fas fa-power-off'"
              ></i>
            </div>
          </div>

          <!-- Content -->
          <div class="p-8 space-y-6">
            <!-- Name Input -->
            <div v-if="!isActive">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Emulator Name
              </label>
              <input
                v-model="emulatorName"
                type="text"
                placeholder="Enter a name for the virtual printer"
                class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                :disabled="loading"
              />
            </div>

            <!-- Info Box -->
            <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
              <div class="flex items-start space-x-3">
                <i class="fas fa-info-circle text-blue-600 dark:text-blue-400 mt-0.5"></i>
                <div class="text-sm text-blue-900 dark:text-blue-200">
                  <p class="font-medium mb-1">What does this do?</p>
                  <ul class="list-disc list-inside space-y-1 text-blue-800 dark:text-blue-300">
                    <li>Creates a virtual 3D printer</li>
                    <li>Appears on Dashboard with other printers</li>
                    <li>Can receive and process jobs</li>
                    <li>Perfect for testing without hardware</li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-3">
              <button
                v-if="!isActive"
                @click="startEmulator"
                :disabled="loading || !emulatorName.trim()"
                class="flex-1 group relative px-6 py-4 rounded-xl font-medium text-white overflow-hidden shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <div class="absolute inset-0 bg-gradient-to-r from-accent-primary to-accent-primary-light group-hover:from-accent-primary-dark group-hover:to-accent-primary transition-all duration-200"></div>
                <div class="relative flex items-center justify-center space-x-2">
                  <i v-if="loading" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-play"></i>
                  <span>{{ loading ? 'Starting...' : 'Start & Register' }}</span>
                </div>
              </button>

              <button
                v-else
                @click="stopEmulator"
                :disabled="loading"
                class="flex-1 group relative px-6 py-4 rounded-xl font-medium text-white overflow-hidden shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <div class="absolute inset-0 bg-gradient-to-r from-red-500 to-red-600 group-hover:from-red-600 group-hover:to-red-700 transition-all duration-200"></div>
                <div class="relative flex items-center justify-center space-x-2">
                  <i v-if="loading" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-stop"></i>
                  <span>{{ loading ? 'Stopping...' : 'Stop Emulator' }}</span>
                </div>
              </button>

              <button
                v-if="isActive"
                @click="router.push('/')"
                class="px-6 py-4 rounded-xl font-medium bg-gray-100 dark:bg-dark-primary text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-primary-dark transition-colors"
              >
                <i class="fas fa-home mr-2"></i>
                Dashboard
              </button>
            </div>

            <!-- Debug Notice -->
            <div class="text-center text-sm text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-dark-primary">
              <i class="fas fa-code mr-1"></i>
              Debug mode is enabled
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
