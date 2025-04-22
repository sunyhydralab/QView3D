<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { type Fabricator, getConnectedFabricators, registerFabricator } from '@/models/fabricator';

// all connected fabricators
const connectedFabricatorList = ref<Fabricator[]>([]);

// the selected fabricator from the dropdown
const selectedFabricator = ref<Fabricator | null>(null);

// the user submitted name for the fabricator
const customName = ref<string | null>(null);

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
  connectedFabricatorList.value = await getConnectedFabricators();
});

async function handleSubmit() {
  if(selectedFabricator.value && customName.value) {
    selectedFabricator.value.name = customName.value;
    console.log('Selected Fabricator:', selectedFabricator.value);
    await registerFabricator(selectedFabricator.value);
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
  <!-- Select Fabricator -->
  <div>
    <label for="fabricatorSelect" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Select a Fabricator</label>
    <select id="fabricatorSelect" v-model="selectedFabricator"
      class="block w-full px-4 py-2 bg-light-primary-light border-light-primary-dark rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light"
      required>
      <option disabled value="">Select a fabricator</option>
      <option v-for="fabricator in connectedFabricatorList" :key="fabricator.device.dbID" :value="fabricator">
        {{ fabricator.description }}
      </option>
    </select>
  </div>

  <!-- Fabricator Name -->
  <div class="space-y-1">
    <label for="name" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Fabricator Name</label>
    <input id="name" type="text"
      class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light"
      v-model="customName" placeholder="Name your fabricator" />
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
      disabled :placeholder="selectedFabricator?.description"/>
  </div>

  <!-- Submit Button -->
  <button type="submit"
    class="w-full bg-accent-primary hover:bg-accent-primary-dark text-white py-2 px-4 rounded-md transition duration-300 disabled:bg-accent-primary-light disabled:cursor-not-allowed" :disabled="!selectedFabricator"
    :onclick="handleSubmit">
    Submit
  </button>
</div>

</template>