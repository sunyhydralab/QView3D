<script setup lang="ts">
import 'bootstrap/dist/js/bootstrap.bundle'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import { onMounted } from 'vue';
import { setupErrorSocket, setupJobStatusSocket, setupProgressSocket, setupQueueSocket, setupStatusSocket, setupTempSocket, setupTimeSocket } from './model/sockets';
import { useRetrievePrintersInfo, printers } from './model/ports';

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