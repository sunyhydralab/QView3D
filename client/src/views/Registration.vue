<script setup lang="ts">
import { reactive, ref } from 'vue';
import { type Fabricator, registerFabricator, getFabricatorDetails, getFabricatorList } from '@/models/fabricator';


// Properly typed ref
const fabricator = ref<Fabricator | null>(null);

// Typed reactive formData
const formData = reactive({
  name: '',
  description: ''
});

// Function to handle form submission
const handleSubmit = () => {
  fabricator.value = registerFabricator({
    customName: formData.name,
    description: formData.description,
    date: Date.now()
  })
  console.log('Fabricator data:', getFabricatorDetails(fabricator.value),getFabricatorList());
};
</script>

<template>
  <div class="mx-auto p-6 rounded-lg shadow-md">
    <div class="max-w-md mx-auto">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Name Input -->
        <div class="space-y-1">
          <label for="name" class="block text-sm font-medium text-gray-700">Device Name</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Name your device"
          />
        </div>
        <!-- Description Input -->
        <div class="space-y-1">
          <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            id="description"
            v-model="formData.description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter description"
          ></textarea>
        </div>
        <!-- Model Input (Disabled) -->
        <div class="space-y-1">
          <label for="model" class="block text-sm font-medium text-gray-700">Model</label>
          <input
            id="model"
            v-model="formData.model"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100 cursor-not-allowed"
            disabled
          />
        </div>
        <button
          type="submit"
          class="w-full bg-accent-primary hover:bg-accent-primary-dark text-white py-2 px-4 rounded-md transition duration-300"
        >
          Submit
        </button>
      </form>
    </div>
  </div>
</template>