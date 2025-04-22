TODO: Whenever the database is wiped, so should the localStorage for connectedFabricatorList

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { type Fabricator, FabricatorList, getConnectedFabricators, registerFabricator, retrieveRegisteredFabricators } from '@/models/fabricator';

// all connected fabricators
const connectedFabricatorList = ref<Fabricator[]>([]);

// the selected fabricator from the dropdown
const selectedFabricator = ref<Fabricator | null>(null);

// the user submitted name for the fabricator
const customName = ref<string | null>(null);

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
  // get the filtered list of connected fabricators from local storage
  const previousConnectedFabricatorList = localStorage.getItem('connectedFabricatorList');
  // if the list exists in local storage, use it; otherwise, fetch from the server
  if (previousConnectedFabricatorList) {
    connectedFabricatorList.value = JSON.parse(previousConnectedFabricatorList);
    console.log('Loaded connectedFabricatorList from localStorage');
  } else {
    connectedFabricatorList.value = await getConnectedFabricators();
    console.log('Loaded connectedFabricatorList from server');
  }
});

async function handleSubmit() {
  // register the selected fabricator with the custom name
  if (selectedFabricator.value && customName.value) {
    selectedFabricator.value.name = customName.value;
    console.log('Selected Fabricator:', selectedFabricator.value);
    await registerFabricator(selectedFabricator.value);
  }

  // update FabricatorList when a new fabricator is registered
  FabricatorList.value = await retrieveRegisteredFabricators();
  console.log('Registered Fabricators:', FabricatorList.value);

  // filter out fabricators that have already been registered
  connectedFabricatorList.value = connectedFabricatorList.value.filter((fabricator: Fabricator) => {
    return !fabricator.name;
  });
  console.log('Connected Fabricators:', connectedFabricatorList.value);

  // save the updated list to localStorage
  localStorage.setItem('connectedFabricatorList', JSON.stringify(connectedFabricatorList.value));
  console.log('Saved connectedFabricatorList to localStorage');

  // reset the form
  selectedFabricator.value = null;
  customName.value = null;

  console.log(FabricatorList.value[1].date);
}
</script>

<template>
  <div>
    <div class="mx-auto max-w-md space-y-4">
      <!-- Select Fabricator -->
      <div>
        <label for="fabricatorSelect" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Select a
          Fabricator</label>
        <select id="fabricatorSelect" v-model="selectedFabricator"
          class="block w-full px-4 py-2 bg-light-primary-light border-light-primary-dark rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light"
          required>
          <option v-if="connectedFabricatorList.length > 0" disabled value="">Select a fabricator</option>
          <option v-else disabled value="">All connected fabricators have been registered</option>
          <option v-for="fabricator in connectedFabricatorList" :key="fabricator.device.dbID" :value="fabricator">
            {{ fabricator.description }}
          </option>
        </select>
      </div>

      <!-- Fabricator Name -->
      <div class="space-y-1">
        <label for="name" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Fabricator
          Name</label>
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
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100 cursor-not-allowed" disabled
          :placeholder="selectedFabricator?.description" />
      </div>

      <!-- Submit Button -->
      <button type="submit"
        class="w-full bg-accent-primary hover:bg-accent-primary-dark text-white py-2 px-4 rounded-md transition duration-300 disabled:bg-accent-primary-light disabled:cursor-not-allowed"
        :disabled="!selectedFabricator" :onclick="handleSubmit">
        Submit
      </button>
    </div>
  </div>
</template>