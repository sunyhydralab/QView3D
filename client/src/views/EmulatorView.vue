<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { api } from '@/models/api';
import { onSocketEvent, emitSocketEvent } from '@/services/socket';
import { addToast } from '@/components/Toast.vue';

// Define interfaces for socket event data
interface EmulatorStatusData {
  status: string;
  message?: string;
}

interface EmulatorTemperatureData {
  extruder?: number;
  bed?: number;
  targetExtruder?: number;
  targetBed?: number;
}

interface EmulatorRegistrationData {
  name?: string;
  id?: number;
}

// Emulator State
const isConnected = ref(false);
const isRegistered = ref(false);
const loading = ref(false);
const selectedPrinterType = ref('Prusa MK4');
const emulatorStatus = ref('Offline');
const statusMessage = ref('');
const temperatureData = reactive({
  extruder: 25,
  bed: 25,
  targetExtruder: 0,
  targetBed: 0
});

// Available printer models based on printeremu/data/printers.json
const printerModels = [
  { value: 'Prusa MK4', label: 'Prusa MK4' }, // ID: 1
  { value: 'Ender 3', label: 'Ender 3' }      // ID: 2
];

// Printer configuration
const printerConfig = reactive({
  name: 'Emulator Printer',
  port: 'EMU001',
  description: 'Virtual 3D Printer',
  hwid: 'EMU-' + Math.floor(Math.random() * 10000)
});

// Temperature control
const extruderTemp = ref(0);
const bedTemp = ref(0);

// Track registered event unsubscribe functions
const unsubscribers = ref<(() => void)[]>([]);

// Setup socket listeners for emulator updates
onMounted(() => {
  setupSocketListeners();

  // Ensure cleanup of event handlers when component is unmounted
  return () => {
    cleanupSocketListeners();
  };
});

// Clean up socket listeners to prevent duplicates
function cleanupSocketListeners() {
  // Execute all unsubscribe functions
  unsubscribers.value.forEach(unsubscribe => unsubscribe());
  unsubscribers.value = [];
  console.log('All socket event listeners cleaned up');
}

function setupSocketListeners() {
  // Clean up any existing listeners first
  cleanupSocketListeners();

  // Listen for emulator status updates
  const statusUnsubscribe = onSocketEvent<EmulatorStatusData>('emulator_status', (data) => {
    emulatorStatus.value = data.status;
    if (data.message) {
      statusMessage.value = data.message;
    }

    // If the status changed, show a toast notification
    addToast(`Emulator status: ${data.status}`, data.status === 'Error' ? 'error' : 'info');
  });
  unsubscribers.value.push(statusUnsubscribe);

  // Listen for temperature updates
  const tempUnsubscribe = onSocketEvent<EmulatorTemperatureData>('emulator_temperature', (data) => {
    if (data.extruder !== undefined) temperatureData.extruder = data.extruder;
    if (data.bed !== undefined) temperatureData.bed = data.bed;
    if (data.targetExtruder !== undefined) temperatureData.targetExtruder = data.targetExtruder;
    if (data.targetBed !== undefined) temperatureData.targetBed = data.targetBed;
  });
  unsubscribers.value.push(tempUnsubscribe);

  // Listen for registration status
  const regUnsubscribe = onSocketEvent<EmulatorRegistrationData>('emulator_registered', (data) => {
    isRegistered.value = true;
    addToast(`Emulator registered as ${data.name || 'Virtual Printer'}`, 'success');
  });
  unsubscribers.value.push(regUnsubscribe);
  
  console.log('Socket event listeners set up successfully');
}

// Update the printer configuration based on selected model
watch(selectedPrinterType, (newValue) => {
  switch(newValue) {
    case 'Prusa MK3':
      printerConfig.description = 'Prusa MK3 Virtual Printer';
      break;
    case 'Prusa MK4':
      printerConfig.description = 'Prusa MK4 Virtual Printer';
      break;
    case 'Prusa MK4S':
      printerConfig.description = 'Prusa MK4S Virtual Printer';
      break;
    case 'Ender 3':
      printerConfig.description = 'Ender 3 Virtual Printer';
      break;
  }
});

// Connect to the emulator
const connectEmulator = async () => {
  loading.value = true;
  statusMessage.value = 'Connecting to emulator...';
  
  try {
    // First, let's check if we need to start the emulator
    await api('startemulator', {
      model: selectedPrinterType.value,
      config: printerConfig
    }, 'POST');
    
    isConnected.value = true;
    emulatorStatus.value = 'Connected';
    statusMessage.value = 'Emulator connected successfully';
    addToast('Emulator connected successfully', 'success');
  } catch (error) {
    console.error('Error connecting to emulator:', error);
    statusMessage.value = 'Failed to connect to emulator';
    addToast('Failed to connect to emulator', 'error');
  } finally {
    loading.value = false;
  }
};

// Disconnect from the emulator
const disconnectEmulator = async () => {
  loading.value = true;
  statusMessage.value = 'Disconnecting from emulator...';
  
  try {
    const response = await api('disconnectemulator', { 
      printerConfig: printerConfig
    }, 'POST');
    
    if (response && response.message) {
      statusMessage.value = response.message;
      isConnected.value = false;
      isRegistered.value = false;
      emulatorStatus.value = 'Offline';
      addToast('Emulator disconnected successfully', 'info');
    } else if (response && response.error) {
      statusMessage.value = response.error;
      addToast(`Error: ${response.error}`, 'error');
    }
  } catch (error) {
    console.error('Error disconnecting emulator:', error);
    statusMessage.value = 'Error disconnecting emulator';
    addToast('Error disconnecting emulator', 'error');
  } finally {
    loading.value = false;
  }
};

// Register the printer with the system
const registerPrinter = async () => {
  loading.value = true;
  statusMessage.value = 'Registering emulator with the system...';
  
  try {
    const response = await api('registeremulator', { 
      model: selectedPrinterType.value,
      config: printerConfig
    }, 'POST');
    
    if (response && response.message) {
      statusMessage.value = response.message;
      isRegistered.value = true;
      addToast('Emulator registered successfully', 'success');
    } else if (response && response.error) {
      statusMessage.value = response.error;
      addToast(`Error: ${response.error}`, 'error');
    }
  } catch (error) {
    console.error('Error registering emulator:', error);
    statusMessage.value = 'Error registering emulator';
    addToast('Error registering emulator', 'error');
  } finally {
    loading.value = false;
  }
};

// Set the temperature of the printer
const setTemperature = async () => {
  try {
    await api('setemulatortemperature', {
      extruder: extruderTemp.value,
      bed: bedTemp.value
    }, 'POST');
    
    addToast(`Target temperatures set: Extruder ${extruderTemp.value}°C, Bed ${bedTemp.value}°C`, 'success');
  } catch (error) {
    console.error('Error setting temperature:', error);
    addToast('Failed to set temperature', 'error');
  }
};

// Generate a gcode test
const runGCodeTest = async () => {
  if (!isRegistered.value) {
    addToast('Printer must be registered before running a test', 'warning');
    return;
  }
  
  try {
    await api('runemulatortest', {
      type: 'simple_move'
    }, 'POST');
    addToast('G-code test started', 'info');
  } catch (error) {
    console.error('Error running G-code test:', error);
    addToast('Failed to run G-code test', 'error');
  }
};

// Reset the emulator state
const resetEmulator = async () => {
  try {
    await api('resetemulator', {}, 'POST');
    emulatorStatus.value = 'Reset';
    statusMessage.value = 'Emulator has been reset';
    temperatureData.extruder = 25;
    temperatureData.bed = 25;
    temperatureData.targetExtruder = 0;
    temperatureData.targetBed = 0;
    addToast('Emulator reset successfully', 'success');
  } catch (error) {
    console.error('Error resetting emulator:', error);
    addToast('Failed to reset emulator', 'error');
  }
};
</script>

<template>
  <!-- Fixed z-index and animation to match other pages -->
  <div class="container mx-auto mt-5 p-4 animate-fadeDown transition-all duration-300 ease-in">
    <h1 class="text-3xl font-bold mb-6 text-center dark:text-light-primary">
      Printer Emulator
    </h1>
    
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Configuration Panel -->
      <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-lg p-6 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-1">
        <h2 class="text-xl font-semibold mb-4 dark:text-light-primary">Printer Configuration</h2>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2 dark:text-light-primary">Printer Model</label>
          <select 
            v-model="selectedPrinterType"
            class="w-full p-2 rounded border bg-light-primary dark:bg-dark-primary text-dark-primary dark:text-light-primary"
            :disabled="isConnected"
          >
            <option v-for="model in printerModels" :key="model.value" :value="model.value">
              {{ model.label }}
            </option>
          </select>
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2 dark:text-light-primary">Printer Name</label>
          <input 
            v-model="printerConfig.name"
            type="text"
            class="w-full p-2 rounded border bg-light-primary dark:bg-dark-primary text-dark-primary dark:text-light-primary"
            :disabled="isConnected"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2 dark:text-light-primary">Description</label>
          <input 
            v-model="printerConfig.description"
            type="text"
            class="w-full p-2 rounded border bg-light-primary dark:bg-dark-primary text-dark-primary dark:text-light-primary"
            :disabled="isConnected"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2 dark:text-light-primary">Hardware ID</label>
          <input 
            v-model="printerConfig.hwid"
            type="text"
            class="w-full p-2 rounded border bg-light-primary dark:bg-dark-primary text-dark-primary dark:text-light-primary"
            :disabled="isConnected"
          />
        </div>
        
        <div class="flex space-x-2">
          <button 
            @click="connectEmulator"
            class="bg-accent-primary text-white px-4 py-2 rounded-md hover:bg-accent-primary-dark flex-1"
            :disabled="isConnected || loading"
          >
            <span v-if="loading && !isConnected">Connecting...</span>
            <span v-else>Connect</span>
          </button>
          
          <button 
            @click="disconnectEmulator"
            class="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 flex-1"
            :disabled="!isConnected || loading"
          >
            <span v-if="loading && isConnected">Disconnecting...</span>
            <span v-else>Disconnect</span>
          </button>
        </div>
      </div>
      
      <!-- Status Panel -->
      <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-lg p-6 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-1">
        <h2 class="text-xl font-semibold mb-4 dark:text-light-primary">Emulator Status</h2>
        
        <div class="mb-4">
          <div class="flex items-center mb-2">
            <div class="font-medium dark:text-light-primary">Status:</div>
            <div class="ml-2 px-3 py-1 rounded-full text-sm" :class="{
              'bg-green-100 text-green-800': emulatorStatus === 'Online' || emulatorStatus === 'Connected',
              'bg-red-100 text-red-800': emulatorStatus === 'Offline' || emulatorStatus === 'Error',
              'bg-yellow-100 text-yellow-800': emulatorStatus === 'Busy' || emulatorStatus === 'Connecting',
              'bg-blue-100 text-blue-800': emulatorStatus === 'Reset'
            }">
              {{ emulatorStatus }}
            </div>
          </div>
          
          <div class="flex items-center mb-2">
            <div class="font-medium dark:text-light-primary">Connection:</div>
            <div class="ml-2 px-3 py-1 rounded-full text-sm" :class="{
              'bg-green-100 text-green-800': isConnected,
              'bg-red-100 text-red-800': !isConnected
            }">
              {{ isConnected ? 'Connected' : 'Disconnected' }}
            </div>
          </div>
          
          <div class="flex items-center mb-2">
            <div class="font-medium dark:text-light-primary">Registration:</div>
            <div class="ml-2 px-3 py-1 rounded-full text-sm" :class="{
              'bg-green-100 text-green-800': isRegistered,
              'bg-red-100 text-red-800': !isRegistered
            }">
              {{ isRegistered ? 'Registered' : 'Not Registered' }}
            </div>
          </div>
        </div>
        
        <div class="mb-4">
          <h3 class="font-medium mb-2 dark:text-light-primary">Temperature</h3>
          
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="bg-light-primary dark:bg-dark-primary p-3 rounded-lg">
              <div class="text-sm text-gray-500 dark:text-gray-400">Extruder</div>
              <div class="text-xl font-bold dark:text-light-primary">{{ temperatureData.extruder }}°C</div>
              <div class="text-xs text-gray-400 dark:text-gray-500">Target: {{ temperatureData.targetExtruder }}°C</div>
            </div>
            
            <div class="bg-light-primary dark:bg-dark-primary p-3 rounded-lg">
              <div class="text-sm text-gray-500 dark:text-gray-400">Bed</div>
              <div class="text-xl font-bold dark:text-light-primary">{{ temperatureData.bed }}°C</div>
              <div class="text-xs text-gray-400 dark:text-gray-500">Target: {{ temperatureData.targetBed }}°C</div>
            </div>
          </div>
        </div>
        
        <div v-if="statusMessage" class="mb-4 p-3 bg-light-primary dark:bg-dark-primary rounded-lg">
          <div class="text-sm font-medium dark:text-light-primary">Message:</div>
          <div class="text-gray-600 dark:text-gray-300">{{ statusMessage }}</div>
        </div>
        
        <div class="flex">
          <button 
            @click="registerPrinter"
            class="bg-accent-primary text-white px-4 py-2 rounded-md hover:bg-accent-primary-dark flex-1"
            :disabled="!isConnected || isRegistered || loading"
          >
            Register Printer
          </button>
        </div>
      </div>
      
      <!-- Control Panel -->
      <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-lg p-6 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-1">
        <h2 class="text-xl font-semibold mb-4 dark:text-light-primary">Printer Controls</h2>
        
        <div class="mb-4">
          <h3 class="font-medium mb-2 dark:text-light-primary">Temperature Control</h3>
          
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium mb-1 dark:text-light-primary">Extruder (°C)</label>
              <input 
                v-model="extruderTemp" 
                type="number" 
                min="0" 
                max="300"
                class="w-full p-2 rounded border bg-light-primary dark:bg-dark-primary text-dark-primary dark:text-light-primary"
                :disabled="!isConnected"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium mb-1 dark:text-light-primary">Bed (°C)</label>
              <input 
                v-model="bedTemp" 
                type="number" 
                min="0" 
                max="120"
                class="w-full p-2 rounded border bg-light-primary dark:bg-dark-primary text-dark-primary dark:text-light-primary"
                :disabled="!isConnected"
              />
            </div>
          </div>
          
          <button 
            @click="setTemperature"
            class="w-full bg-accent-primary text-white px-4 py-2 rounded-md hover:bg-accent-primary-dark mb-4"
            :disabled="!isConnected"
          >
            Set Temperature
          </button>
        </div>
        
        <div class="mb-4">
          <h3 class="font-medium mb-2 dark:text-light-primary">Test Commands</h3>
          
          <button 
            @click="runGCodeTest"
            class="w-full bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 mb-2"
            :disabled="!isRegistered"
          >
            Run G-code Test
          </button>
          
          <button 
            @click="resetEmulator"
            class="w-full bg-yellow-500 text-white px-4 py-2 rounded-md hover:bg-yellow-600"
            :disabled="!isConnected"
          >
            Reset Emulator
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Fixed animation to match other pages */
.animate-fadeDown {
  animation: fadeDown 0.5s ease-out forwards;
}

@keyframes fadeDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>