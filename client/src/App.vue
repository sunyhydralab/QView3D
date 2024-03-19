<script setup lang="ts">
import 'bootstrap/dist/js/bootstrap.bundle'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import { onMounted } from 'vue';
import { setupCanPauseSocket, setupErrorSocket, setupJobStatusSocket, setupPauseFeedbackSocket, setupProgressSocket, setupQueueSocket, setupReleaseSocket, setupStatusSocket, setupTempSocket } from './model/sockets';
import { useRetrievePrintersInfo, printers } from './model/ports';
import { setupTimeSocket } from './model/jobs';

const { retrieveInfo } = useRetrievePrintersInfo();

onMounted(async () => {
  printers.value = await retrieveInfo()

  // sockets
  setupStatusSocket(printers)
  setupQueueSocket(printers)
  setupProgressSocket(printers.value)
  setupJobStatusSocket(printers.value)
  setupErrorSocket(printers)
  setupTimeSocket(printers.value)
  setupTempSocket(printers)
  // setupGCodeViewerSocket(printers.value)
  // setupCanPauseSocket(printers) //not sure if needed
  setupPauseFeedbackSocket(printers) //not sure if needed
  setupReleaseSocket(printers.value)
})
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