<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { type Fabricator, FabricatorList, getPorts, retrievePrinters } from '@/models/fabricator';

const FabricatorList = ref<Fabricator[]>([]); 
// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
    FabricatorList.value = await getPorts();
    console.log(FabricatorList.value);
});
</script>

<template>
</template>