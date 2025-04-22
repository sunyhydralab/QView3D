<script setup lang="ts">
interface FabricatorProps {
    name: string;
    model: string;
    date: string | Date;
}

const props = defineProps<FabricatorProps>();
</script>

<template>
    <div
        class="my-10 mx-10 block max-w-sm bg-white rounded-lg shadow-sm dark:bg-light-primary-light">
        <!-- Purple header section with name -->
        <div class="p-4 bg-accent-primary rounded-t-lg">
            <p class="text-2xl font-bold tracking-tight text-white">{{ name }}</p>
        </div>

        <!-- Content section -->
        <div class="p-4">
            <p class="font-normal text-gray-700 dark:text-black">Model: {{ model }}</p>
            <p class="font-normal text-gray-700 dark:text-black">Date Registered: {{ date }}</p>
        </div>
    </div>
</template>