<script setup lang="ts">
import { ref, type Ref, computed } from 'vue'
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
const isCompleted = computed(() => {
  if (currentFabricator.status === FabricatorStatus.StopPrint) {
    return true
  } else if (currentFabricator.status === FabricatorStatus.Error) {
    return true
  } else if (currentFabricator.status === FabricatorStatus.CancelledPrint)
  return true
})

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

// debouncer for the release job button
const releaseJobDebouncer: Ref<boolean> = ref(false)
async function release(key?: number) {
  if (releaseJobDebouncer.value) return
  releaseJobDebouncer.value = true

  try {
    if (currentFabricator.queue == undefined) {
      addToast("The Queue is undefined.", "error")
      return
    }
    if (currentFabricator.queue![0] == undefined) {
      addToast("The Queue is empty.", "error")
      return
    }
    if (currentFabricator.id == undefined) {
      addToast("The fabricator ID is undefined.", "error")
      return
    }

    console.debug("release job api call")
    await releaseJob(currentFabricator.queue![0], currentFabricator.id!, key ?? 3)
      .then(response => {
        console.debug(response)
        if (key != 2) {
          currentFabricator.queue!.shift()
        }
        addToast('Released job', 'success')
      })
      .catch(error => {
        console.error(error)
        addToast('Error releasing job', 'error')
      })
  } catch (error) {
    console.error('Failed to release job:', error)
    addToast('Error releasing job', 'error')
  } finally {
    releaseJobDebouncer.value = false
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
        .catch(error => {
          console.error('Failed to turn fabricator online:', error)
          addToast('Error turning fabricator online', 'error')
        })
        .finally(() => {
          turningOnline.value = false
          updatingFabricatorStatus.value = false
        })
    } else {
      turningOnline.value = false
      updatingFabricatorStatus.value = false
      addToast('Fabricator ID is undefined', 'error')
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
        .catch(error => {
          console.error('Failed to turn fabricator offline:', error)
          addToast('Error turning fabricator offline', 'error')
        })
        .finally(() => {
          turningOffline.value = false
          updatingFabricatorStatus.value = false
        })
    } else {
      turningOffline.value = false
      updatingFabricatorStatus.value = false
      addToast('Fabricator ID is undefined', 'error')
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
      return
    }
    if (jobQueue!.length == 0) {
      startingPrint.value = false
      addToast("This fabricator has no queue", "error")
      return
    }
    const latestJob: Job = jobQueue![0]
    if (currentFabricator.id == undefined) {
      startingPrint.value = false
      addToast("This fabricator has no ID", "error")
      return
    }
    addToast('Preparing print', 'info')
    startPrintAPI(latestJob.id, currentFabricator.id!)
      .then(() => {
        addToast('Starting print', 'success')
        startingPrint.value = false
        isPrinting.value = true
        isPaused.value = false
      })
      .catch(error => {
        console.error('Failed to start print:', error)
        addToast('Error starting print', 'error')
        startingPrint.value = false
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
      updateFabricatorStatus(currentFabricator.id, FabricatorStatus.CancelledPrint)
        .then(() => {
          stoppingPrint.value = false
          updatingFabricatorStatus.value = false
          isPrinting.value = false
          isPaused.value = false
        })
        .catch(error => {
          console.error('Failed to stop print:', error)
          addToast('Error stopping print', 'error')
        })
        .finally(() => {
          stoppingPrint.value = false
          updatingFabricatorStatus.value = false
        })
    } else {
      stoppingPrint.value = false
      updatingFabricatorStatus.value = false
      addToast('Fabricator ID is undefined', 'error')
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
        .catch(error => {
          console.error('Failed to pause print:', error)
          addToast('Error pausing print', 'error')
        })
        .finally(() => {
          isPausingPrinter.value = false
          updatingFabricatorStatus.value = false
        })
    } else {
      isPausingPrinter.value = false
      updatingFabricatorStatus.value = false
      addToast('Fabricator ID is undefined', 'error')
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
        .catch(error => {
          console.error('Failed to unpause print:', error)
          addToast('Error unpausing print', 'error')
        })
        .finally(() => {
          isUnPausingPrinter.value = false
          updatingFabricatorStatus.value = false
        })
    } else {
      isUnPausingPrinter.value = false
      updatingFabricatorStatus.value = false
      addToast('Fabricator ID is undefined', 'error')
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
    <!-- Buttons for when the job is complete -->
    <button v-if="isCompleted" @click="release(1)" class="btn-secondary">Complete</button>
    <button v-if="isCompleted" @click="release(2)" class="btn-primary">Rerun Job</button>
    <button v-if="isCompleted" @click="release(3)" class="btn-danger">Job Error</button>
    <!-- Turn Offline -->
    <button class="btn-secondary" v-if="!isOnline" @click="turnOnline">Turn Online</button>
    <button class="btn-danger" v-else @click="turnOffline">Turn Offline</button>

    <!-- Submit Job -->
    <button v-if="!isCompleted" class="btn-primary" @click="toggleSubmitModal">Submit Job</button>

    <!-- Printing -->
    <button v-if="!isCompleted && !isPrinting && isOnline && ((currentFabricator.queue?.length ?? -1) > 0)" @click="startPrint" class="btn-primary">Start Print</button>
    <button v-else-if="!isCompleted && isPrinting && isOnline" @click="stopPrint" class="btn-danger">Stop/Complete</button>

    <!-- Pause / Unpause Toggle -->
    <button v-if="!isCompleted && !isPaused && isPrinting" @click="pausePrint" class="btn-secondary">Pause</button>
    <button v-else-if="!isCompleted && isPrinting" @click="unpausePrint" class="btn-primary">Unpause</button>
  </div>
  <SubmitJobModal v-if="isSubmitModalOpen" @close="toggleSubmitModal" />
</template>

<style scoped></style>
