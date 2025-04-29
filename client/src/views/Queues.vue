<script setup lang="ts">
import { onMounted } from 'vue'
import { fabricatorList, retrieveRegisteredFabricators } from '../models/fabricator'
import QueueList from '../components/QueueList.vue'
import NoPrinterRobot from '../components/NoPrinterRobot.vue'

async function fetchFabricators() {
  fabricatorList.value = await retrieveRegisteredFabricators()
}

onMounted(async () => {await fetchFabricators()})
</script>

<template>
  <div class="pt-12">
    <QueueList v-for="fabricator in fabricatorList" :key="fabricator.id" :fabricator="fabricator" />
    <NoPrinterRobot v-if="fabricatorList.length === 0" />
  </div>
</template>
