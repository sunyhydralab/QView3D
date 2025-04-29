<script setup lang="ts">
import { onMounted } from 'vue';
import { fabricatorList, retrieveRegisteredFabricators } from '@/models/fabricator'
import PrintModule from '@/components/PrintModule.vue'
import NoPrinterRobot from '@/components/NoPrinterRobot.vue'
// import router from '@/router';
// import { useRoute } from 'vue-router';

// const route = useRoute()

// // Hack
// setInterval(_ => {
//   router.push(route.path)
// }, 1000)

onMounted(async () => {
  retrieveRegisteredFabricators()
});
</script>

<template>
  <div class="pt-12">
    <PrintModule v-for="fabricator in fabricatorList" :key="fabricator.id" :fabricator="fabricator" />
    <NoPrinterRobot />
  </div>
</template>