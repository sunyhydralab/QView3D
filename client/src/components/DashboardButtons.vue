<script setup lang="ts">
import { ref, type Ref } from 'vue'
import SubmitJobModal from './SubmitJobModal.vue'
import { FabricatorStatus, updateFabricatorStatus, startPrintAPI, type Fabricator, releaseJob } from '../models/fabricator'
import { type Job } from '../models/job'
import { addToast } from './Toast.vue'

const { currentFabricator } = defineProps<{
  currentFabricator: Fabricator
}>()

const isSubmitModalOpen = ref(false)
const isOnline = ref(currentFabricator.status === FabricatorStatus.TurnOnline)

const isPrinting = ref(false)
const isPaused = ref(false)

if (currentFabricator.queue != undefined) {
  if (currentFabricator.queue[0] != undefined){
    if (currentFabricator.queue[0].status != undefined) {
      if (currentFabricator.queue[0].status === FabricatorStatus.Printing) {
        isPrinting.value = true
        isOnline.value = true
      } else if (currentFabricator.queue[0].status === FabricatorStatus.PausePrint) {
        isPaused.value = true
        isOnline.value = true
      }
    }
  }
}

// Debounce used to prevent the user from updating the printer status when another update is currently being done
const updatingFabricatorStatus: Ref<boolean> = ref(false)

// A debounce used to prevent the user from clicking the Turn Online button multiple times
const turningOnline: Ref<boolean> = ref(false)
function turnOnline() {
  if (!turningOnline.value && !updatingFabricatorStatus.value) {
    turningOnline.value = true
    updatingFabricatorStatus.value = true

    // Turn the fabricator online
    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.TurnOnline)
        .then(() => {
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
  if (!turningOffline.value && !updatingFabricatorStatus.value) {
    turningOffline.value = true
    updatingFabricatorStatus.value = true

    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.TurnOffline)
        .then(() => {
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
  if (!startingPrint.value && !updatingFabricatorStatus.value) {
    startingPrint.value = true
    const jobQueue: Job[] | undefined = currentFabricator.queue

    if (jobQueue == undefined) {
      startingPrint.value = false
      addToast("The fabricator is currently doing something, please wait", "info")
    }
    if (jobQueue!.length == 0) {
      startingPrint.value = false
      addToast("This fabricator has no queue", "error")
    }
    const latestJob: Job = jobQueue![0]
    if (currentFabricator.id == undefined) {
      startingPrint.value = false
      addToast("This fabricator has no ID", "error")
    }
    addToast('Preparing print', 'info')
    startPrintAPI(latestJob.id, currentFabricator.id!)
      .then(() => {
        addToast('Starting print', 'success')
        startingPrint.value = false
        isPrinting.value = true
        isPaused.value = false
      })
  }
}
// Debounce used to prevent the user from clicking the Stop button multiple times
const stoppingPrint: Ref<boolean> = ref(false)
function stopPrint() {
  if (!stoppingPrint.value && !updatingFabricatorStatus.value) {
    stoppingPrint.value = true
    updatingFabricatorStatus.value = true

    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.TurnOffline)
        .then(() => {
          stoppingPrint.value = false
          updatingFabricatorStatus.value = false
          isPrinting.value = false
          isPaused.value = false
        })
    }
  }
}

// Debounce used to prevent a user from pressing the Pause button while the printer is pausing
const isPausingPrinter: Ref<boolean> = ref(false)
function pausePrint() {
  if (!isPausingPrinter.value && !updatingFabricatorStatus.value) {
    isPausingPrinter.value = true
    updatingFabricatorStatus.value = true
    addToast("Attempting to pause printer", "info")

    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.PausePrint)
        .then(() => {
          addToast("Paused printer", "success")
          isPausingPrinter.value = false
          updatingFabricatorStatus.value = false
          isPaused.value = true
        })
    }
  }

}

// Debounce used to prevent a user form pressing the Unpause button while the printer is unpausing
const isUnPausingPrinter: Ref<boolean> = ref(false)
function unpausePrint() {
  if (!isUnPausingPrinter.value && !updatingFabricatorStatus.value) {
    isUnPausingPrinter.value = true
    updatingFabricatorStatus.value = true
    addToast("Attempting to unpause printer", "info")

    if (currentFabricator.id != undefined) {
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.Printing)
        .then(() => {
          addToast("Unpaused printer", 'success')

          isUnPausingPrinter.value = false
          updatingFabricatorStatus.value = false
          isPaused.value = false
        })
    }
  }
}

// Debounce used to prevent the user from pressing the rerun job multiple times
// const isReruningJob: Ref<boolean> = ref(false)
// function rerunJob() {
//   if (isReruningJob.value === false && updatingFabricatorStatus.value === false) {
//     isReruningJob.value = true
//
//     addToast("Attempting to rerun job", "info")
//     if (currentFabricator.id != undefined) {
//       if (currentFabricator.queue != undefined) {
//         if (currentFabricator.queue[0] != undefined) {
//           releaseJob(currentFabricator.queue[0], 2, currentFabricator.id)
//             .then(response => {
//               isReruningJob.value = true
//
//               isPrinting.value = true
//               isPaused.value = false
//
//               addToast("Reruning previous job", "success")
//             })
//
//         } else {
//           isReruningJob.value = false
//         }
//       } else {
//         isReruningJob.value = false
//       }
//     } else {
//       isReruningJob.value = false
//     }
//
//   }
// }

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
    <button v-else-if="isOnline" @click="stopPrint" class="btn-danger">Stop/Complete</button>

    <!-- Pause / Unpause Toggle -->
    <button v-if="!isPaused && isPrinting" @click="pausePrint" class="btn-secondary">Pause</button>
    <button v-else-if="isPrinting" @click="unpausePrint" class="btn-primary">Unpause</button>

    <!-- Rerun
    <button class="btn-secondary" v-if="!isPrinting && isOnline" @click="rerunJob">
      Rerun Job
    </button> -->
  </div>
  <SubmitJobModal v-if="isSubmitModalOpen" @close="toggleSubmitModal" />
</template>

<style scoped></style>
