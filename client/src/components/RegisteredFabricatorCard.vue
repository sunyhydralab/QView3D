<script setup lang="ts">
import { defineProps } from 'vue';

interface FabricatorProps {
    name: string;
    model: string;
    date: string | Date;
}

const props = defineProps<FabricatorProps>();
</script>

<template>
    <div
        class="my-10 mx-10 block max-w-sm bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700">
        <!-- Purple header section with name -->
        <div class="p-4 bg-accent-primary rounded-t-lg">
            <p class="text-2xl font-bold tracking-tight text-white">{{ name }}</p>
        </div>

        <!-- Content section -->
        <div class="p-4">
            <p class="font-normal text-gray-700 dark:text-gray-400">Model: {{ model }}</p>
            <p class="font-normal text-gray-700 dark:text-gray-400">Date Registered: {{ date }}</p>
        </div>
    </div>
</template>