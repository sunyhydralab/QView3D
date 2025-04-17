<script setup>
import { reactive } from 'vue';
import { Fabricator } from '@/models/Fabricator';

// Represents a fabricator object
const fabricator = ref(Fabricator | null);

// Represents the formData bject
const formData = reactive({
    name: '',
    description: '',
    model: 'Default Model'
});

// Function to set fabricator data from formData
const setFabricatorData = (formData) => {
    fabricator.value = new Fabricator(formData.name, formData.description, formData.model, date.now());
};

// Function to handle form submission
const handleSubmit = () => {
    setFabricatorData();
    console.log('Fabricator data:', fabricator.value);
};
</script>

<template>
    <div class="mx-auto p-6 rounded-lg shadow-md">
        <div class="max-w-md mx-auto">
            <form @submit.prevent="handleSubmit" class="space-y-4">
                <!-- Name Input -->
                <div class="space-y-1">
                    <label for="name" class="block text-sm font-medium text-gray-700">Device Name</label>
                    <input id="name" v-model="formData.name" type="text"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Name your device" />
                </div>

                <!-- Description Input -->
                <div class="space-y-1">
                    <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
                    <textarea id="description" v-model="formData.description" rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Enter description"></textarea>
                </div>

                <!-- Model Input (Disabled) -->
                <div class="space-y-1">
                    <label for="model" class="block text-sm font-medium text-gray-700">Model</label>
                    <input id="model" v-model="formData.model" type="text"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100 cursor-not-allowed"
                        disabled />
                </div>
                <button type="submit"
                    class="w-full bg-accent-primary hover:bg-accent-primary-dark text-white py-2 px-4 rounded-md transition duration-300">
                    Submit
                </button>
            </form>
        </div>
    </div>
</template>
