<script setup lang="ts">
import GCodePreview from "@/components/GCodePreview.vue"
import { ref } from 'vue'

const isPrinting = ref(false)
const isPaused = ref(false)
const isOnline = ref(false)
const showDetails = ref(false)

function toggleDetails() {
  showDetails.value = !showDetails.value
}
</script>

<template>
    <!-- Developer Note: This is simply a beginning setup. Subject to change eventually. -->
  <div class="container mx-auto mt-3">
    <!-- Main Table -->
    <table class="min-w-full">
      <thead>
        <tr class="bg-light-primary-light dark:bg-dark-primary-light">
          <th class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">ID</th>
          <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Printer</th>
          <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Job Name</th>
          <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">File Name</th>
          <th class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Options</th>
          <th class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Progress</th>
          <th
            class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Options</th>
        </tr>
      </thead>
      <tbody>
        <tr class="text-center">
          <td class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">1</td>
          <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">mk4</td>
          <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">example</td>
          <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">example.gcode</td>
          <td class="w-36 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">
            <div class="flex flex-wrap gap-2">
              <!-- Functions will be added to these buttons when implemented. -->
              <!-- Turn Offline -->
              <button class="btn-blue" 
                v-if="!isOnline"
                @click="isOnline = true">
                Turn Online
              </button>
              <button class="btn-danger"
                v-else
                @click="isOnline = false; isPrinting = false">
                Turn Offline
              </button>

              <!-- Submit Job -->
              <button class="btn-regular">
                Submit Job
              </button>

              <!-- Printing -->
              <button
                v-if="!isPrinting && isOnline"
                @click="isPrinting = true"
                class="btn-regular"
              >
                Start Print
              </button>
              <button
                v-else-if="isOnline"
                @click="isPrinting = false"
                class="btn-danger"
              >
                Stop
              </button>

              <!-- Pause / Unpause Toggle -->
              <button
                v-if="!isPaused && isPrinting"
                @click="isPaused = true"
                class="btn-regular"
              >
                Pause
              </button>
              <button
                v-else-if="isPrinting"
                @click="isPaused = false"
                class="btn-regular"
              >
                Unpause
              </button>

              <!-- Note: this will be updated when we have access to the queue -->
              <!-- Rerun -->
              <button class="btn-blue"
                v-if="!isPrinting && isOnline"
                @click="isPrinting=true">
                Rerun Job
              </button> 
            </div>
          </td>
          <td class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">
            <div class="relative w-full rounded-full h-4 overflow-hidden dark:bg-dark-primary">
              <!-- Progress fill bar -->
                  <div class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-500 ease-in-out"
                      :style="{ width: '60%' }"
                  ></div>
              <!-- Overlayed percentage -->
              <div class="absolute inset-0 flex items-center justify-center text-xs font-medium text-black dark:text-white">
              {{ '60%' }}
              </div>
            </div>
          </td>
          <td class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2 cursor-pointer" @click="toggleDetails">
            <i class="mx-3" :class="['fas', showDetails ? 'fa-caret-up' : 'fa-caret-down']"></i>
            <i class="fa-solid mx-3 fa-ellipsis-vertical"></i> <!-- Currently doesn't do anything, will be for more actions -->
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Transition wrapper for animation -->
    <transition name="dropdown" mode="out-in">
      <div v-if="showDetails" key="details">
        <!-- Second Table -->
        <table
          class="min-w-full border border-light-primary dark:border-dark-primary dark:text-light-primary mt-4"
        >
          <thead>
            <tr class="bg-light-primary-light dark:bg-dark-primary-light">
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Layer</th>
              <th class="w-20 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Filament</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Nozzle</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Bed</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Elapsed</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Remaining</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Total</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">ETA</th>
            </tr>
          </thead>
          <tbody>
            <tr class="text-center align-middle">
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">0</td>
              <td class="w-20 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">PLA</td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">0</td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">0</td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00</td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00</td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00</td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00</td>
            </tr>
          </tbody>
        </table>

        <!-- Console & Viewer -->
        <div class="flex mt-4">
          <div class="bg-light-primary-light dark:bg-dark-primary-light w-1/3 dark:text-light-primary p-2">
            <p class="text-black dark:text-white">Console (Placeholder)</p>
          </div>
          <div class="bg-light-primary-light dark:bg-dark-primary-light w-2/3 dark:text-light-primary p-2">
            <GCodePreview />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
.dropdown-enter-to,
.dropdown-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.btn-regular {
  @apply rounded-md w-32 py-2 text-white font-semibold bg-accent-primary hover:bg-purple-400 transition-all duration-300;
}

.btn-danger {
  @apply rounded-md w-32 py-2 text-white font-semibold bg-red-400 hover:bg-red-300 transition-all duration-300;
}

.btn-blue {
  @apply rounded-md w-32 py-2 text-white font-semibold bg-accent-secondary hover:from-green-200 hover:bg-accent-secondary-light transition-all duration-300;
}
</style>