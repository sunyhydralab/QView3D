<script setup lang="ts">
import { ref, type Ref } from 'vue'
import SubmitJobModal from './SubmitJobModal.vue'
import { FabricatorStatus, updateFabricatorStatus, startPrintAPI, type Fabricator } from '../models/fabricator'
import { type Job } from '../models/job'
import { addToast } from './Toast.vue'

const isSubmitModalOpen = ref(false)
const isOnline = ref(false)
const isPrinting = ref(false)
const isPaused = ref(false)

const { currentFabricator } = defineProps<{
  currentFabricator: Fabricator
}>()

// Debounce used to prevent the user from updating the printer status when another update is currently being done
const updatingFabricatorStatus: Ref<boolean> = ref(false)

// A debounce used to prevent the user from clicking the Turn Online button multiple times
const turningOnline: Ref<boolean> = ref(false)
function turnOnline() {
  if (turningOnline.value === false && updatingFabricatorStatus.value === false) {
    turningOnline.value = true
    updatingFabricatorStatus.value = true
    
    // Turn the fabricator online
    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.TurnOnline)
        .then(response => {
          // When the Fabricator has been turned online, update the following booleans:
          turningOnline.value = false
          isOnline.value = true
          updatingFabricatorStatus.value = false
        })
    }
  }

}

// Debounce used to prevent the user from clicking the Turn Offline button multiple times
const turningOffline: Ref<boolean> = ref(false)
function turnOffline() {
  if (turningOffline.value === false && updatingFabricatorStatus.value === false) {
    turningOffline.value = true
    updatingFabricatorStatus.value = true

    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.TurnOffline)
        .then(response => {
          turningOffline.value = false
          updatingFabricatorStatus.value = false
          isOnline.value = false
          isPrinting.value = false
          isPaused.value = false
        })
    }
  }
}

// Debounce used to prevent the user from clicking the Start Print button
const startingPrint: Ref<boolean> = ref(false)
function startPrint() {
  if (startingPrint.value === false && updatingFabricatorStatus.value === false) {
    startingPrint.value = true
    const jobQueue: Job[] | undefined = currentFabricator.queue

    if (jobQueue != undefined) {
      if (jobQueue.length > 0) {
        const latestJob: Job = jobQueue[0]
        if (currentFabricator.id != undefined) {
          addToast("Preparing print", "info")
          startPrintAPI(latestJob.id, currentFabricator.id)
          .then(response => {
            addToast("Starting print", "success")
            
            startingPrint.value = false
            isPrinting.value = true
            isPaused.value = false
          })
        } else {
          startingPrint.value = false
          addToast("This fabricator has no ID", "error")
        }
      } else {
        startingPrint.value = false
        addToast("This fabricator has no queue", "error")
      }
    } else {
      startingPrint.value = false
      addToast("The fabricator is currently doing something, please wait", "info")
    }

  }
}

// Debounce used to prevent the user from clicking the Stop button multiple times
const stoppingPrint: Ref<boolean> = ref(false)
function stopPrint() {
  if (stoppingPrint.value === false && updatingFabricatorStatus.value === false) {
    stoppingPrint.value = true
    updatingFabricatorStatus.value = true

    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.TurnOffline)
        .then(response => {
          stoppingPrint.value = false
          updatingFabricatorStatus.value = false
          isPrinting.value = false
          isPaused.value = false
        })
    }
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
  <div class="flex flex-wrap gap-1.5 justify-center">
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
