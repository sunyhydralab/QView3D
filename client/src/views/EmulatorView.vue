<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '@/models/api';
import { DEBUG_MODE } from '@/composables/useIPSettings';
import { addToast } from '@/components/Toast.vue';

const router = useRouter();
const loading = ref(false);
const emulators = ref<any[]>([]);
const showCreateModal = ref(false);

// Form data for new emulator
const newEmulator = ref({
  name: '',
  model: 'Prusa MK4',
  description: ''
});

// Available printer models
const printerModels = [
  { value: 'Prusa MK4', label: 'Prusa MK4', icon: 'fas fa-cube' },
  { value: 'Prusa Mini', label: 'Prusa Mini', icon: 'fas fa-cube' },
  { value: 'Ender 3', label: 'Creality Ender 3', icon: 'fas fa-cube' },
  { value: 'Ender 3 Pro', label: 'Creality Ender 3 Pro', icon: 'fas fa-cube' },
  { value: 'CR-10', label: 'Creality CR-10', icon: 'fas fa-cube' },
  { value: 'Generic', label: 'Generic Printer', icon: 'fas fa-cube' }
];

// Check if debug mode is enabled
onMounted(async () => {
  if (!DEBUG_MODE.value) {
    addToast('Debug mode is required to access the emulator', 'warning');
    router.push('/');
    return;
  }
  await loadEmulators();
});

// Load list of emulators
const loadEmulators = async () => {
  loading.value = true;
  try {
    const response = await api('api/emulator/list', undefined, 'GET');
    if (response && response.emulators) {
      emulators.value = response.emulators;
    } else {
      emulators.value = [];
    }
  } catch (error) {
    console.error('Error loading emulators:', error);
    addToast('Failed to load emulators', 'error');
    emulators.value = [];
  } finally {
    loading.value = false;
  }
};

// Open create modal
const openCreateModal = () => {
  newEmulator.value = {
    name: '',
    model: 'Prusa MK4',
    description: ''
  };
  showCreateModal.value = true;
};

// Create emulator
const createEmulator = async () => {
  if (!newEmulator.value.name.trim()) {
    addToast('Please enter a name for the emulator', 'warning');
    return;
  }

  loading.value = true;

  try {
    const response = await api('startemulator', {
      model: newEmulator.value.model,
      config: {
        name: newEmulator.value.name,
        description: newEmulator.value.description || 'Virtual Printer for Testing',
        hwid: 'EMU-' + Math.floor(Math.random() * 10000)
      }
    }, 'POST');

    if (!response.success && !response.emulator_id) {
      throw new Error('Failed to create emulator');
    }

    addToast(`Emulator "${newEmulator.value.name}" created successfully`, 'success');
    showCreateModal.value = false;
    await loadEmulators();
  } catch (error) {
    console.error('Error creating emulator:', error);
    addToast('Failed to create emulator', 'error');
  } finally {
    loading.value = false;
  }
};

// Delete emulator
const deleteEmulator = async (emulatorId: string | number) => {
  if (!confirm('Are you sure you want to delete this emulator?')) {
    return;
  }

  loading.value = true;

  try {
    const response = await api(`api/emulator/delete/${emulatorId}`, undefined, 'DELETE');

    if (response && response.success !== false) {
      addToast('Emulator deleted successfully', 'success');
      await loadEmulators();
    } else {
      throw new Error(response?.error || 'Failed to delete emulator');
    }
  } catch (error) {
    console.error('Error deleting emulator:', error);
    addToast('Failed to delete emulator', 'error');
  } finally {
    loading.value = false;
  }
};

// Get status badge color
const getStatusColor = (status: string) => {
  switch (status?.toLowerCase()) {
    case 'active':
    case 'online':
    case 'running':
      return 'bg-green-500';
    case 'inactive':
    case 'offline':
    case 'stopped':
      return 'bg-gray-500';
    case 'error':
    case 'failed':
      return 'bg-red-500';
    default:
      return 'bg-yellow-500';
  }
};
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-light-primary via-white to-light-primary dark:from-dark-primary-dark dark:via-dark-primary dark:to-dark-primary-light transition-colors duration-300">
    <div class="container mx-auto px-4 py-12">
      <div class="max-w-6xl mx-auto">
        <!-- Header -->
        <div class="flex justify-between items-center mb-12">
          <div>
            <div class="flex items-center space-x-4">
              <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-accent-primary to-accent-primary-light">
                <i class="fas fa-microchip text-3xl text-white"></i>
              </div>
              <div>
                <h1 class="text-4xl font-bold bg-gradient-to-r from-accent-primary via-accent-primary-light to-accent-secondary bg-clip-text text-transparent">
                  Virtual Emulators
                </h1>
                <p class="text-gray-600 dark:text-gray-400 mt-1">
                  Create and manage virtual 3D printers for testing
                </p>
              </div>
            </div>
          </div>
          <button
            @click="openCreateModal"
            :disabled="loading"
            class="group relative px-6 py-3 rounded-xl font-medium text-white overflow-hidden shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-accent-primary to-accent-primary-light group-hover:from-accent-primary-dark group-hover:to-accent-primary transition-all duration-200"></div>
            <div class="relative flex items-center space-x-2">
              <i class="fas fa-plus"></i>
              <span>Create Emulator</span>
            </div>
          </button>
        </div>

        <!-- Info Box -->
        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 mb-8">
          <div class="flex items-start space-x-3">
            <i class="fas fa-info-circle text-blue-600 dark:text-blue-400 mt-0.5"></i>
            <div class="text-sm text-blue-900 dark:text-blue-200">
              <p class="font-medium mb-1">Virtual Emulators</p>
              <ul class="list-disc list-inside space-y-1 text-blue-800 dark:text-blue-300">
                <li>Create multiple virtual printers for testing</li>
                <li>Choose from different printer models (Prusa, Ender, etc.)</li>
                <li>Emulators appear on Dashboard alongside physical printers</li>
                <li>Perfect for development and testing without hardware</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading && emulators.length === 0" class="text-center py-12">
          <i class="fas fa-spinner fa-spin text-4xl text-accent-primary mb-4"></i>
          <p class="text-gray-600 dark:text-gray-400">Loading emulators...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="!loading && emulators.length === 0" class="text-center py-12">
          <div class="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gray-100 dark:bg-dark-primary mb-4">
            <i class="fas fa-microchip text-5xl text-gray-400 dark:text-gray-600"></i>
          </div>
          <h3 class="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-2">No Emulators Yet</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-6">Create your first virtual printer to get started</p>
          <button
            @click="openCreateModal"
            class="inline-flex items-center space-x-2 px-6 py-3 rounded-xl font-medium text-white bg-gradient-to-r from-accent-primary to-accent-primary-light hover:from-accent-primary-dark hover:to-accent-primary transition-all"
          >
            <i class="fas fa-plus"></i>
            <span>Create First Emulator</span>
          </button>
        </div>

        <!-- Emulators Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="emulator in emulators"
            :key="emulator.id"
            class="bg-white dark:bg-dark-primary-light rounded-2xl shadow-xl overflow-hidden hover:shadow-2xl transition-shadow duration-300"
          >
            <!-- Status Header -->
            <div class="px-6 py-4 bg-gradient-to-r from-gray-600 to-gray-700">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="relative">
                    <div
                      class="w-3 h-3 rounded-full"
                      :class="getStatusColor(emulator.status)"
                    ></div>
                    <div
                      v-if="emulator.status === 'active' || emulator.status === 'online'"
                      class="absolute inset-0 w-3 h-3 rounded-full animate-ping"
                      :class="getStatusColor(emulator.status)"
                    ></div>
                  </div>
                  <span class="text-white text-sm font-medium">
                    {{ emulator.status || 'Unknown' }}
                  </span>
                </div>
                <i class="fas fa-microchip text-white/80"></i>
              </div>
            </div>

            <!-- Content -->
            <div class="p-6">
              <h3 class="text-xl font-bold text-dark-primary dark:text-light-primary-light mb-2">
                {{ emulator.name || 'Unnamed Emulator' }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {{ emulator.model || 'Unknown Model' }}
              </p>

              <div v-if="emulator.description" class="text-sm text-gray-700 dark:text-gray-300 mb-4">
                {{ emulator.description }}
              </div>

              <div class="space-y-2 mb-4">
                <div v-if="emulator.hwid" class="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <i class="fas fa-fingerprint w-5"></i>
                  <span>{{ emulator.hwid }}</span>
                </div>
                <div v-if="emulator.id" class="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <i class="fas fa-hashtag w-5"></i>
                  <span>ID: {{ emulator.id }}</span>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex gap-2">
                <button
                  @click="deleteEmulator(emulator.id)"
                  :disabled="loading"
                  class="flex-1 px-4 py-2 rounded-xl font-medium text-white bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  <i class="fas fa-trash mr-2"></i>
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Debug Notice -->
        <div class="text-center text-sm text-gray-500 dark:text-gray-400 mt-8 pt-8 border-t border-gray-200 dark:border-dark-primary">
          <i class="fas fa-code mr-1"></i>
          Debug mode is enabled
        </div>
      </div>
    </div>

    <!-- Create Emulator Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showCreateModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          @click.self="showCreateModal = false"
        >
          <div
            class="relative w-full max-w-md bg-white dark:bg-dark-primary-light rounded-2xl shadow-2xl transform transition-all overflow-hidden"
            @click.stop
          >
            <!-- Header -->
            <div class="px-6 py-4 bg-gradient-to-r from-accent-primary to-accent-primary-light">
              <button
                @click="showCreateModal = false"
                class="absolute top-4 right-4 p-2 rounded-lg text-white hover:bg-white/20 transition-colors"
              >
                <i class="fas fa-times text-xl"></i>
              </button>
              <h2 class="text-2xl font-bold text-white">Create New Emulator</h2>
              <p class="text-white/80 mt-1">Configure your virtual printer</p>
            </div>

            <!-- Form -->
            <form @submit.prevent="createEmulator" class="p-6 space-y-4">
              <!-- Name -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Emulator Name *
                </label>
                <input
                  v-model="newEmulator.name"
                  type="text"
                  required
                  placeholder="e.g., Test Printer 1"
                  class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                  :disabled="loading"
                />
              </div>

              <!-- Model Selection -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Printer Model *
                </label>
                <select
                  v-model="newEmulator.model"
                  required
                  class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                  :disabled="loading"
                >
                  <option v-for="model in printerModels" :key="model.value" :value="model.value">
                    {{ model.label }}
                  </option>
                </select>
              </div>

              <!-- Description -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  v-model="newEmulator.description"
                  rows="3"
                  placeholder="Optional description for this emulator"
                  class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20 resize-none"
                  :disabled="loading"
                />
              </div>

              <!-- Action Buttons -->
              <div class="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  @click="showCreateModal = false"
                  :disabled="loading"
                  class="px-6 py-3 rounded-xl font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-dark-primary hover:bg-gray-200 dark:hover:bg-dark-primary-dark transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="loading || !newEmulator.name.trim()"
                  class="group relative px-6 py-3 rounded-xl font-medium text-white overflow-hidden shadow-lg hover:shadow-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  <div class="absolute inset-0 bg-gradient-to-r from-accent-primary to-accent-primary-light group-hover:from-accent-primary-dark group-hover:to-accent-primary transition-all duration-200"></div>
                  <div class="relative flex items-center space-x-2">
                    <i v-if="loading" class="fas fa-spinner fa-spin"></i>
                    <i v-else class="fas fa-plus"></i>
                    <span>{{ loading ? 'Creating...' : 'Create Emulator' }}</span>
                  </div>
                </button>
              </div>
            </form>
          </div>
        </div>
      </Transition>
    </Teleport>
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

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .relative {
  transform: scale(0.9) translateY(-20px);
}

.modal-leave-to .relative {
  transform: scale(0.95) translateY(10px);
}
</style>
