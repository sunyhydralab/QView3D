<script setup lang="ts">
import { ref, type Ref } from 'vue'
import SubmitJobModal from './SubmitJobModal.vue'
import { FabricatorStatus, updateFabricatorStatus, type Fabricator } from '../models/fabricator'

const isSubmitModalOpen = ref(false)
const isOnline = ref(false)
const isPrinting = ref(false)
const isPaused = ref(false)

// By default, all operations will be sent to the fabricator with ID 1
const DEFAULT_FABRICATOR_ID: number = 1

const { currentFabricator } = defineProps<{
  currentFabricator: Fabricator
}>()

// Debounce used to prevent the user from updating the printer status when another update is currently being done
const updatingFabricatorStatus: Ref<boolean> = ref(false)

// A debounce used to prevent the user from clicking the Turn Online button multiple times
const turningOnline: Ref<boolean> = ref(false)
function turnOnline() {
  if (!turningOnline.value && !updatingFabricatorStatus.value) {
    turningOnline.value = true
    updatingFabricatorStatus.value = true
    
    // Turn the fabricator online
    updateFabricatorStatus(currentFabricator.id ?? DEFAULT_FABRICATOR_ID, FabricatorStatus.TurnOnline)
      .then(() => {
        // When the Fabricator has been turned online, update the following booleans:
        turningOnline.value = false
        isOnline.value = true
        updatingFabricatorStatus.value = false
      })
  }

}

// Debounce used to prevent the user from clicking the Turn Offline button multiple times
const turningOffline: Ref<boolean> = ref(false)
function turnOffline() {
  if (!turningOffline.value && !updatingFabricatorStatus.value) {
    turningOffline.value = true
    updatingFabricatorStatus.value = true

    updateFabricatorStatus(currentFabricator.id ?? DEFAULT_FABRICATOR_ID, FabricatorStatus.TurnOffline)
      .then(() => {
        turningOffline.value = false
        updatingFabricatorStatus.value = false
        isOnline.value = false
        isPrinting.value = false
        isPaused.value = false
      })
  }
}

function startPrint() {
  isPrinting.value = true
  isPaused.value = false
}

// Debounce used to prevent the user from clicking the Stop button multiple times
const stoppingPrint: Ref<boolean> = ref(false)
function stopPrint() {
  if (!stoppingPrint.value && !updatingFabricatorStatus.value) {
    stoppingPrint.value = true
    updatingFabricatorStatus.value = true

    updateFabricatorStatus(currentFabricator.id ?? DEFAULT_FABRICATOR_ID, FabricatorStatus.TurnOffline)
      .then(() => {
        stoppingPrint.value = false
        updatingFabricatorStatus.value = false
        isPrinting.value = false
        isPaused.value = false
      })
  }
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
