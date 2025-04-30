<script setup lang="ts">
import { type Ref, ref, onMounted, computed } from 'vue';
import { fabricatorList, retrieveRegisteredFabricators, type Fabricator } from '@/models/fabricator'
import { type Job } from '../models/job'
import NoPrinterRobot from '@/components/NoPrinterRobot.vue'
import DashboardButtons from '@/components/DashboardButtons.vue'
import GCodePreview from '../components/GCodePreview.vue'
import { isDark } from '@/composables/useMode'

// Dark mode tracking
const darkMode = computed(() => isDark());

onMounted(async () => {
  retrieveRegisteredFabricators()
});

// State tracking for UI
const detailsBools: Ref<boolean[]> = ref([])
const gcodeViewerVisible: Ref<boolean[]> = ref([])
const livePreviewStatus: Ref<boolean[]> = ref([])

// Toggle details panel for fabricator
function toggleDetails(currentFab: Fabricator): void {
  if (currentFab.id != undefined) {
    // Initialize if undefined
    if (detailsBools.value[currentFab.id] === undefined) {
      detailsBools.value[currentFab.id] = false
    }
    detailsBools.value[currentFab.id] = !detailsBools.value[currentFab.id]
  }
}

// Get details visibility state
function getDetails(currentFab: Fabricator): boolean {
  if (currentFab.id != undefined)
    return !!detailsBools.value[currentFab.id]
  else
    return false
}

// Toggle GCode viewer visibility
function toggleGCodeViewer(currentFab: Fabricator): void {
  if (currentFab.id != undefined) {
    // Initialize if undefined
    if (gcodeViewerVisible.value[currentFab.id] === undefined) {
      gcodeViewerVisible.value[currentFab.id] = false
    }
    gcodeViewerVisible.value[currentFab.id] = !gcodeViewerVisible.value[currentFab.id]
  }
}

// Get GCode viewer visibility state
function isGCodeViewerVisible(currentFab: Fabricator): boolean {
  if (currentFab.id != undefined)
    return !!gcodeViewerVisible.value[currentFab.id]
  else
    return false
}

// Handle live preview toggle from GCodePreview component
function handleLivePreviewToggle(isLive: boolean, fabricatorId = 0): void {
  livePreviewStatus.value[fabricatorId] = isLive
}

// Utility functions for jobs and progress
function getCurrentJob(fab: Fabricator): Job | undefined {
  return fab.queue?.[0]
}

function getProgress(job: Job | undefined): string {
  if (job != undefined) {
    const currentProgress: number | undefined = Math.ceil(job.progress)

    if (currentProgress != undefined) {
      return currentProgress + "%"
    } else {
      return "0%"
    }
  } else {
    return "0%"
  }
}
</script>

<template>
  <transition name="slide-down" appear>
    <div class="pt-12 mt-8">
      <div class="container mx-auto mt-3 px-2 md:px-0" v-for="currentFabricator in fabricatorList ">
        <!-- Main Printer Status Table -->
        <div class="overflow-x-auto w-full">
          <!-- Mobile Card View (visible only on small screens) -->
          <div class="block md:hidden">
            <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow mb-4 p-4">
              <div class="flex justify-between mb-2">
                <div>
                  <span class="font-bold text-gray-900 dark:text-white">ID: {{ currentFabricator.id }}</span>
                </div>
                <div>
                  <button @click="toggleDetails(currentFabricator)" class="p-1">
                    <i class="fas text-gray-600 dark:text-gray-300" :class="getDetails(currentFabricator) ? 'fa-caret-up' : 'fa-caret-down'"></i>
                  </button>
                </div>
              </div>

              <div class="flex flex-col mb-2">
                <div class="py-1">
                  <span class="font-semibold text-gray-800 dark:text-gray-200">Printer:</span> 
                  <span class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ currentFabricator.name }}</span>
                </div>
                <div class="py-1">
                  <span class="font-semibold text-gray-800 dark:text-gray-200">Job:</span> 
                  <span class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.name ?? 'N/A' }}</span>
                </div>
                <div class="py-1">
                  <span class="font-semibold text-gray-800 dark:text-gray-200">File:</span> 
                  <span class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.file_name_original ?? 'N/A' }}</span>
                </div>
              </div>

              <!-- Progress Bar -->
              <div class="mb-4">
                <div class="relative w-full rounded-full h-4 overflow-hidden dark:bg-dark-primary">
                  <div
                    class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-500 ease-in-out"
                    :style="{
                      width: getCurrentJob(currentFabricator)?.progress != null ? getCurrentJob(currentFabricator)?.progress + '%' : '0%',
                    }"
                  ></div>
                  <div
                    class="absolute inset-0 flex items-center justify-center text-xs font-medium text-black dark:text-white"
                  >
                    {{ getCurrentJob(currentFabricator)?.progress != null ? getCurrentJob(currentFabricator)?.progress + '%' : '0%' }}
                  </div>
                </div>
              </div>

              <!-- Controls -->
              <DashboardButtons :current-fabricator="currentFabricator"/>
            </div>
          </div>

          <!-- Desktop Table (visible only on medium screens and up) -->
          <table class="hidden md:table w-full table-fixed border-collapse text-sm">
            <thead>
              <tr class="bg-light-primary-light dark:bg-dark-primary-light">
                <th
                  class="w-[5%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  ID
                </th>
                <th
                  class="w-[10%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  Fabricator Name
                </th>
                <th
                  class="w-[15%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  Job Name
                </th>
                <th
                  class="w-[15%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  File Name
                </th>
                <th
                  class="w-[40%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  Controls
                </th>
                <th
                  class="w-[12%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  Progress
                </th>
                <th
                  class="w-[1.5%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  <span class="sr-only">Details</span>
                </th>
                <th
                  class="w-[1.5%] border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  <span class="sr-only">Viewer</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="text-center">
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  {{ currentFabricator.id }}
                </td>
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                    {{ currentFabricator.name }}
                  </div>
                </td>
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                    {{ getCurrentJob(currentFabricator)?.name ?? 'N/A' }}
                  </div>
                </td>
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                    {{ getCurrentJob(currentFabricator)?.file_name_original ?? 'N/A' }}
                  </div>
                </td>
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
                >
                  <!-- Controls -->
                  <DashboardButtons :current-fabricator="currentFabricator"/>
                </td>
                <!-- Progress Bar -->
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                >
                  <div class="relative w-full rounded-full h-4 overflow-hidden dark:bg-dark-primary">
                    <div
                      class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-500 ease-in-out"
                      :style="{
                        width: getProgress(getCurrentJob(currentFabricator)),
                      }"
                    ></div>
                    <div
                      class="absolute inset-0 flex items-center justify-center text-xs font-medium text-black dark:text-white"
                    >
                      {{ getProgress(getCurrentJob(currentFabricator)) }}
                    </div>
                  </div>
                </td>
                <!-- Info Toggle Button -->
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-1 cursor-pointer"
                  @click="toggleDetails(currentFabricator)"
                >
                  <div class="flex justify-center items-center">
                    <i class="fas text-gray-600 dark:text-gray-300" :class="getDetails(currentFabricator) ? 'fa-caret-up' : 'fa-caret-down'" title="Toggle Details"></i>
                  </div>
                </td>
                <!-- Viewer Toggle Button -->
                <td
                  class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-1 cursor-pointer"
                  @click="toggleGCodeViewer(currentFabricator)"
                >
                  <div class="flex justify-center items-center">
                    <i class="fas text-gray-600 dark:text-gray-300" :class="isGCodeViewerVisible(currentFabricator) ? 'fa-eye-slash' : 'fa-eye'" title="Toggle GCode Viewer"></i>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Details Section (conditionally displayed) -->
        <div class="hidden md:block">
          <transition name="dropdown">
            <!-- Print Details Panel -->
            <div v-if="getDetails(currentFabricator)" class="mt-1">
              <table
                class="w-full table-fixed border border-light-primary dark:border-dark-primary dark:text-light-primary text-sm"
              >
                <thead>
                  <tr class="bg-light-primary-light dark:bg-dark-primary-light">
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      Layer
                    </th>
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      Filament
                    </th>
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      Nozzle
                    </th>
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      Bed
                    </th>
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      Elapsed
                    </th>
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      Remaining
                    </th>
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      Total
                    </th>
                    <th
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      ETA
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="text-center align-middle">
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ getCurrentJob(currentFabricator)?.current_layer_height ?? 'N/A' }}
                      </div>
                    </td>
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ getCurrentJob(currentFabricator)?.filament ?? 'Idle' }}
                      </div>
                    </td>
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ currentFabricator.extruder_temp ? currentFabricator.extruder_temp + '°C' : 'Idle' }}
                      </div>
                    </td>
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ currentFabricator.bed_temp ? currentFabricator.bed_temp + '°C' : 'Idle' }}
                      </div>
                    </td>
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ getCurrentJob(currentFabricator)?.job_client?.elapsed_time ?? 'Idle' }}
                      </div>
                    </td>
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ getCurrentJob(currentFabricator)?.job_client?.remaining_time ?? 'Idle' }}
                      </div>
                    </td>
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ getCurrentJob(currentFabricator)?.job_client?.total_time ?? 'Idle' }}
                      </div>
                    </td>
                    <td
                      class="w-1/8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
                    >
                      <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ getCurrentJob(currentFabricator)?.job_client?.eta ?? 'Idle' }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </transition>
          
          <transition name="dropdown">
            <!-- Gcode Viewer Section -->
            <div v-if="isGCodeViewerVisible(currentFabricator)" class="flex mt-1 justify-center bg-black">
              <div class="bg-black w-full md:w-4/5 p-2">
                <GCodePreview
                  :file="getCurrentJob(currentFabricator)?.file ?? null"
                  :job-id="getCurrentJob(currentFabricator)?.id"
                  @toggle-live-preview="(isLive) => handleLivePreviewToggle(isLive, currentFabricator.id || 0)"
                />
              </div>
            </div>
          </transition>
        </div>

        <!-- Mobile Details View -->
        <div class="block md:hidden mt-2">
          <transition name="dropdown">
            <div v-if="getDetails(currentFabricator)" class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg p-4">
              <h3 class="font-bold mb-3 text-gray-900 dark:text-white">Print Details</h3>

              <div class="grid grid-cols-2 gap-3 mb-4">
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">Layer</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.current_layer_height ?? 'N/A' }}</div>
                </div>
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">Filament</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.filament ?? 'Idle' }}</div>
                </div>
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">Nozzle</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ currentFabricator?.extruder_temp ? currentFabricator.extruder_temp + '°C' : 'Idle' }}</div>
                </div>
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">Bed</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ currentFabricator?.bed_temp ? currentFabricator.bed_temp + '°C' : 'Idle' }}</div>
                </div>
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">Elapsed</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.job_client?.elapsed_time ?? 'Idle' }}</div>
                </div>
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">Remaining</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.job_client?.remaining_time ?? 'Idle' }}</div>
                </div>
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">Total</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.job_client?.total_time ?? 'Idle' }}</div>
                </div>
                <div class="bg-light-primary-ultralight dark:bg-dark-primary p-2 rounded">
                  <div class="text-xs font-medium text-gray-800 dark:text-gray-200">ETA</div>
                  <div class="overflow-hidden text-ellipsis text-gray-900 dark:text-white">{{ getCurrentJob(currentFabricator)?.job_client?.eta ?? 'Idle' }}</div>
                </div>
              </div>

              <!-- Viewer Toggle Button -->
              <button 
                @click="toggleGCodeViewer(currentFabricator)" 
                class="flex items-center gap-2 mb-3 py-1 px-3 bg-light-primary dark:bg-dark-primary rounded hover:bg-light-primary-dark dark:hover:bg-dark-primary-dark transition-colors"
              >
                <i class="fas text-gray-700 dark:text-gray-300" :class="isGCodeViewerVisible(currentFabricator) ? 'fa-eye-slash' : 'fa-eye'"></i>
                <span class="text-sm text-gray-700 dark:text-gray-300">{{ isGCodeViewerVisible(currentFabricator) ? 'Hide Preview' : 'Show Preview' }}</span>
              </button>

              <transition name="dropdown">
                <div v-if="isGCodeViewerVisible(currentFabricator)">
                  <div class="bg-black rounded p-2">
                    <GCodePreview
                      :file="getCurrentJob(currentFabricator)?.file ?? null"
                      :job-id="getCurrentJob(currentFabricator)?.id"
                      @toggle-live-preview="(isLive) => handleLivePreviewToggle(isLive, currentFabricator.id || 0)"
                    />
                  </div>
                </div>
              </transition>
            </div>
          </transition>
        </div>
      </div>
      <NoPrinterRobot />
    </div>
  </transition>
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

.slide-down-enter-active {
  transition: all 0.5s ease;
}
.slide-down-enter-from {
  transform: translateY(-50px);
  opacity: 0;
}
.slide-down-enter-to {
  transform: translateY(0);
  opacity: 1;
}

/* Fixed table styles */
table {
  table-layout: fixed;
  width: 100%;
  max-width: 100%;
}

td > div, th > div {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Ensure table doesn't expand beyond container */
.overflow-x-auto {
  max-width: 100%;
  scrollbar-width: thin;
}
</style>
