<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { type Fabricator, getPorts, retrievePrinters } from '@/models/fabricator';

const connectedFabricatorList = ref<Fabricator[]>([]);
const selectedDevice = ref<Fabricator | null>(null);

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
  connectedFabricatorList.value = await getPorts();
});
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
  <!-- Select Device -->
  <div>
    <label for="deviceSelect" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Select a Device</label>
    <select id="deviceSelect" v-model="selectedDevice"
      class="block w-full px-4 py-2 bg-light-primary-light border-light-primary-dark rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light"
      required>
      <option disabled value="">Select a device</option>
      <option v-for="fabricator in connectedFabricatorList" :key="fabricator.device.dbID" :value="fabricator">
        {{ fabricator.description }}
      </option>
    </select>
  </div>

  <!-- Device Name -->
  <div class="space-y-1">
    <label for="name" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Device Name</label>
    <input id="name" type="text"
      class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light"
      placeholder="Name your device" />
  </div>

  <!-- Description
  <div class="space-y-1">
    <label for="description" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Description</label>
    <textarea id="description" rows="3"
      class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light"
      placeholder="Enter description"></textarea>
  </div> -->

  <!-- Model (Disabled) -->
  <div class="space-y-1">
    <label for="model" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Model</label>
    <input id="model" type="text"
      class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100 cursor-not-allowed"
      disabled :placeholder="selectedDevice?.description"/>
  </div>

  <!-- Submit Button -->
  <button type="submit"
    class="w-full bg-accent-primary hover:bg-accent-primary-dark text-white py-2 px-4 rounded-md transition duration-300">
    Submit
  </button>
</div>

</template>