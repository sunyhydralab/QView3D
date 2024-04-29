<script setup lang="ts">
import 'bootstrap/dist/js/bootstrap.bundle'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import ThemePanel from './components/ThemePanel.vue'
import { onMounted, nextTick, watch } from 'vue';
import { setupPortRepairSocket, setupErrorSocket, setupJobStatusSocket, setupPauseFeedbackSocket, setupProgressSocket, setupQueueSocket, setupReleaseSocket, setupStatusSocket, setupTempSocket, setupGCodeViewerSocket, setupExtrusionSocket, setupCurrentLayerHeightSocket, setupMaxLayerHeightSocket } from './model/sockets';
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
  setupMaxLayerHeightSocket(printers)
  setupCurrentLayerHeightSocket(printers)

  nextTick(() => {
    updateColors()
  })
})

const updateColors = () => {
  var primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color');
  var successColor = getComputedStyle(document.documentElement).getPropertyValue('--bs-success-color');

  var cls1Elements = document.querySelectorAll('.cls-1');
  cls1Elements.forEach(function(element) {
    (element as HTMLElement).style.fill = primaryColor;
  });

  var cls2Elements = document.querySelectorAll('.cls-2');
  cls2Elements.forEach(function(element) {
    (element as HTMLElement).style.fill = successColor;
  });
}

watch(() => getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color'), updateColors);
watch(() => getComputedStyle(document.documentElement).getPropertyValue('--bs-success-color'), updateColors);
</script>

<template>
  <nav style="padding-bottom: 2.5rem;">
    <NavBar />
  </nav>
  <div class="">
    <RouterView />
  </div>
  <ThemePanel />
</template>

<style scoped></style>