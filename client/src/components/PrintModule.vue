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
  <div class="container mx-auto mt-3 px-2 md:px-0">
    <!-- Main Printer Status Table - Responsive Design -->
    <div class="overflow-x-auto">
      <!-- Mobile Card View (visible only on small screens) -->
      <div class="block md:hidden">
        <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow mb-4 p-4">
          <div class="flex justify-between mb-2">
            <div>
              <span class="font-bold">ID: 1</span>
            </div>
            <div>
              <button @click="toggleDetails" class="p-1">
                <i class="fas" :class="showDetails ? 'fa-caret-up' : 'fa-caret-down'"></i>
              </button>
            </div>
          </div>

          <div class="flex flex-col mb-2">
            <div class="py-1"><span class="font-semibold">Printer:</span> mk4</div>
            <div class="py-1"><span class="font-semibold">Job:</span> example</div>
            <div class="py-1"><span class="font-semibold">File:</span> example.gcode</div>
          </div>

          <!-- Progress Bar -->
          <div class="mb-4">
            <div class="relative w-full rounded-full h-4 overflow-hidden dark:bg-dark-primary">
              <div
                class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-500 ease-in-out"
                style="width: 60%"></div>
              <div
                class="absolute inset-0 flex items-center justify-center text-xs font-medium text-black dark:text-white">
                60%
              </div>
            </div>
          </div>

          <!-- Controls -->
          <div class="flex flex-wrap gap-2 justify-center">
            <!-- Turn Offline -->
            <button class="btn-secondary" v-if="!isOnline" @click="isOnline = true">
              Turn Online
            </button>
            <button class="btn-danger" v-else @click="isOnline = false; isPrinting = false">
              Turn Offline
            </button>

            <!-- Submit Job -->
            <button class="btn-primary">
              Submit Job
            </button>

            <!-- Printing -->
            <button v-if="!isPrinting && isOnline" @click="isPrinting = true" class="btn-primary">
              Start Print
            </button>
            <button v-else-if="isOnline" @click="isPrinting = false" class="btn-danger">
              Stop
            </button>

            <!-- Pause / Unpause Toggle -->
            <button v-if="!isPaused && isPrinting" @click="isPaused = true" class="btn-secondary">
              Pause
            </button>
            <button v-else-if="isPrinting" @click="isPaused = false" class="btn-primary">
              Unpause
            </button>

            <!-- Rerun -->
            <button class="btn-secondary" v-if="!isPrinting && isOnline" @click="isPrinting = true">
              Rerun Job
            </button>
          </div>
        </div>
      </div>

      <!-- Desktop Table (visible only on medium screens and up) -->
      <table class="hidden md:table min-w-full border-collapse">
        <thead>
          <tr class="bg-light-primary-light dark:bg-dark-primary-light">
            <th class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">ID</th>
            <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Printer
            </th>
            <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Job Name
            </th>
            <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">File Name
            </th>
            <th class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Controls
            </th>
            <th class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Progress
            </th>
            <th class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Details
            </th>
          </tr>
        </thead>
        <tbody>
          <tr class="text-center">
            <td class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">1</td>
            <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">mk4</td>
            <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">example
            </td>
            <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">
              example.gcode</td>
            <td class="w-36 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">
              <!-- Controls -->
              <div class="flex flex-wrap gap-2">
                <!-- Turn Offline -->
                <button class="btn-secondary" v-if="!isOnline" @click="isOnline = true">
                  Turn Online
                </button>
                <button class="btn-danger" v-else @click="isOnline = false; isPrinting = false">
                  Turn Offline
                </button>

                <!-- Submit Job -->
                <button class="btn-primary">
                  Submit Job
                </button>

                <!-- Printing -->
                <button v-if="!isPrinting && isOnline" @click="isPrinting = true" class="btn-primary">
                  Start Print
                </button>
                <button v-else-if="isOnline" @click="isPrinting = false" class="btn-danger">
                  Stop
                </button>

                <!-- Pause / Unpause Toggle -->
                <button v-if="!isPaused && isPrinting" @click="isPaused = true" class="btn-secondary">
                  Pause
                </button>
                <button v-else-if="isPrinting" @click="isPaused = false" class="btn-primary">
                  Unpause
                </button>

                <!-- Rerun -->
                <button class="btn-secondary" v-if="!isPrinting && isOnline" @click="isPrinting = true">
                  Rerun Job
                </button>
              </div>
            </td>
            <!-- Progress Bar -->
            <td class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">
              <div class="relative w-full rounded-full h-4 overflow-hidden dark:bg-dark-primary">
                <div
                  class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-500 ease-in-out"
                  style="width: 60%"></div>
                <div
                  class="absolute inset-0 flex items-center justify-center text-xs font-medium text-black dark:text-white">
                  60%
                </div>
              </div>
            </td>
            <td
              class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2 cursor-pointer"
              @click="toggleDetails">
              <div class="flex justify-center items-center">
                <i class="fas" :class="showDetails ? 'fa-caret-up' : 'fa-caret-down'"></i>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Details Section (conditionally displayed) -->
    <transition name="dropdown">
      <div v-if="showDetails" key="details">
        <!-- Mobile Details View -->
        <div class="block md:hidden mt-2">
          <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg p-4">
            <h3 class="font-bold mb-3">Print Details</h3>

            <div class="grid grid-cols-2 gap-3 mb-4">
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">Layer</div>
                <div>0</div>
              </div>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">Filament</div>
                <div>PLA</div>
              </div>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">Nozzle</div>
                <div>0</div>
              </div>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">Bed</div>
                <div>0</div>
              </div>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">Elapsed</div>
                <div>00:00</div>
              </div>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">Remaining</div>
                <div>00:00</div>
              </div>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">Total</div>
                <div>00:00</div>
              </div>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                <div class="text-xs font-medium">ETA</div>
                <div>00:00</div>
              </div>
            </div>

            <div class="mb-4">
              <h4 class="font-medium mb-2">Console</h4>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary rounded p-2 h-24 overflow-y-auto">
                <p class="text-black dark:text-white">Console (Placeholder)</p>
              </div>
            </div>

            <div>
              <h4 class="font-medium mb-2">Preview</h4>
              <div class="bg-light-primary-ultralight dark:bg-dark-primary rounded p-2">
                <GCodePreview />
              </div>
            </div>
          </div>
        </div>

        <!-- Desktop Details View -->
        <div class="hidden md:block">
          <!-- Print Details Table -->
          <table class="min-w-full border border-light-primary dark:border-dark-primary dark:text-light-primary mt-4">
            <thead>
              <tr class="bg-light-primary-light dark:bg-dark-primary-light">
                <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Layer
                </th>
                <th class="w-20 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">
                  Filament
                </th>
                <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Nozzle
                </th>
                <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Bed
                </th>
                <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">
                  Elapsed
                </th>
                <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">
                  Remaining
                </th>
                <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">Total
                </th>
                <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">ETA
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="text-center align-middle">
                <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">0</td>
                <td class="w-20 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">PLA
                </td>
                <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">0</td>
                <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">0</td>
                <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00
                </td>
                <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00
                </td>
                <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00
                </td>
                <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1">00:00
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Console & Viewer Section -->
          <div class="flex mt-4">
            <div class="bg-light-primary-light dark:bg-dark-primary-light w-1/3 dark:text-light-primary p-2">
              <p class="text-black dark:text-white">Console (Placeholder)</p>
            </div>
            <div class="bg-light-primary-light dark:bg-dark-primary-light w-2/3 dark:text-light-primary p-2">
              <GCodePreview />
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style>
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
</style>