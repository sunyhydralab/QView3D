<script setup lang="ts">
import { ref } from 'vue'
import SubmitJobModal from './SubmitJobModal.vue'

const isSubmitModalOpen = ref(false)
const isOnline = ref(false)
const isPrinting = ref(false)
const isPaused = ref(false)

function turnOnline() {
  isOnline.value = true
}

function turnOffline() {
  isOnline.value = false
  isPrinting.value = false
  isPaused.value = false
}

function startPrint() {
  isPrinting.value = true
  isPaused.value = false
}

function stopPrint() {
  isPrinting.value = false
  isPaused.value = false
}

function pausePrint() {
  isPaused.value = true
}

function unpausePrint() {
  isPaused.value = false
}

function rerunJob() {
  isPrinting.value = true
  isPaused.value = false
}

function toggleSubmitModal() {
  isSubmitModalOpen.value = !isSubmitModalOpen.value
}
</script>

<template>
  <!-- Controls -->
  <div class="flex flex-wrap gap-2 justify-center">
    <!-- Turn Offline -->
    <button class="btn-secondary" v-if="!isOnline" @click="turnOnline">Turn Online</button>
    <button class="btn-danger" v-else @click="turnOffline">Turn Offline</button>

    <!-- Submit Job -->
    <button class="btn-primary" @click="toggleSubmitModal">Submit Job</button>

    <!-- Printing -->
    <button v-if="!isPrinting && isOnline" @click="startPrint" class="btn-primary">
      Start Print
    </button>
    <button v-else-if="isOnline" @click="stopPrint" class="btn-danger">Stop</button>

    <!-- Pause / Unpause Toggle -->
    <button v-if="!isPaused && isPrinting" @click="pausePrint" class="btn-secondary">Pause</button>
    <button v-else-if="isPrinting" @click="unpausePrint" class="btn-primary">Unpause</button>

    <!-- Rerun -->
    <button class="btn-secondary" v-if="!isPrinting && isOnline" @click="rerunJob">
      Rerun Job
    </button>
  </div>
  <SubmitJobModal v-if="isSubmitModalOpen" @close="toggleSubmitModal" />
</template>

<style scoped></style>
