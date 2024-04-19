<script setup lang="ts">
import 'bootstrap/dist/js/bootstrap.bundle'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import ThemePanel from './components/ThemePanel.vue' // Import the ThemePanel component
import { onMounted } from 'vue';
import { setupPortRepairSocket, setupErrorSocket, setupJobStatusSocket, setupPauseFeedbackSocket, setupProgressSocket, setupQueueSocket, setupReleaseSocket, setupStatusSocket, setupTempSocket, setupGCodeViewerSocket, setupExtrusionSocket } from './model/sockets';
import { useRetrievePrintersInfo, printers } from './model/ports';
import { setupTimeSocket } from './model/jobs';

const { retrieveInfo } = useRetrievePrintersInfo();

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
  setupGCodeViewerSocket(printers)
  setupPauseFeedbackSocket(printers) //not sure if needed
  setupReleaseSocket(printers)
  setupPortRepairSocket(printers)
  setupExtrusionSocket(printers)
})

</script>

<template>
  <nav style="padding-bottom: 2.5rem;">
    <NavBar />
  </nav>
  <div class="">
    <RouterView />
  </div>
  <ThemePanel /> <!-- Add the ThemePanel component here -->
</template>

<style scoped></style>