<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { fabricatorList, retrieveRegisteredFabricators } from '../models/fabricator'
import QueueList from '../components/QueueList.vue'
import NoPrinterRobot from '../components/NoPrinterRobot.vue'

async function fetchFabricators() {
  fabricatorList.value = await retrieveRegisteredFabricators()
}

onMounted(async () => {
  if (!sessionStorage.getItem('reloaded')) {
    sessionStorage.setItem('reloaded', 'true')
    window.location.reload()
  } else {
    sessionStorage.removeItem('reloaded')
    fetchFabricators()
  }
})
</script>

<template>
  <div class="pt-12">
    <QueueList v-for="fabricator in fabricatorList" :key="fabricator.id" :fabricator="fabricator" />
    <NoPrinterRobot v-if="fabricatorList.length === 0" />
  </div>
</template>
