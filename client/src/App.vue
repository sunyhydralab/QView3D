<script setup lang="ts">
import 'bootstrap/dist/js/bootstrap.bundle'
import { RouterView, useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import { onMounted, watchEffect } from 'vue';
import { setupPortRepairSocket, setupCanPauseSocket, setupErrorSocket, setupJobStatusSocket, setupPauseFeedbackSocket, setupProgressSocket, setupQueueSocket, setupReleaseSocket, setupStatusSocket, setupTempSocket } from './model/sockets';
import { useRetrievePrintersInfo, printers } from './model/ports';
import { setupTimeSocket } from './model/jobs';

const { retrieveInfo } = useRetrievePrintersInfo();
const route = useRoute();

onMounted(async () => {
  printers.value = await retrieveInfo()

  // sockets
  setupStatusSocket(printers)
  setupQueueSocket(printers)
  setupProgressSocket(printers)
  setupJobStatusSocket(printers)
  setupErrorSocket(printers)
  setupTimeSocket(printers)
  setupTempSocket(printers)
  // setupGCodeViewerSocket(printers.value)
  // setupCanPauseSocket(printers) //not sure if needed
  setupPauseFeedbackSocket(printers) //not sure if needed
  setupReleaseSocket(printers)
  setupPortRepairSocket(printers)
})

// watchEffect(async () => {
//   if (route.fullPath) {
//   printers.value = await retrieveInfo()
//   }
// })

</script>

<template>
  <nav>
    <NavBar />
  </nav>
  <div class="">
    <RouterView />
  </div>
</template>

<style scoped></style>