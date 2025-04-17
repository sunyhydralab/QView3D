<script setup lang="ts">
import * as GCodePreview from 'gcode-preview'
import { ref } from 'vue'

const showDetails = ref(false)

function toggleDetails() {
  showDetails.value = !showDetails.value
}
</script>

<template>
    <!-- Developer Note: This is simply a beginning setup. Subject to change eventually. -->
  <div class="container mx-auto">
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
          <td class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">
            <i class="fas fa-cog"></i>
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
            <i :class="['fas', showDetails ? 'fa-caret-up' : 'fa-caret-down']"></i>
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
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Layer</th>
              <th class="w-20 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Filament</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Nozzle</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Bed</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Elapsed</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Remaining</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">Total</th>
              <th class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2">ETA</th>
            </tr>
          </thead>
          <tbody>
            <tr class="text-center align-middle">
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
              <td class="w-20 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
              <td class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"></td>
            </tr>
          </tbody>
        </table>

        <!-- Console & Viewer -->
        <div class="flex mt-4">
          <div class="w-1/3 dark:text-light-primary p-2">
            <p class="text-light-primary">Console (Placeholder)</p>
          </div>
          <div class="w-2/3 dark:text-light-primary p-2">
            <p class="text-light-primary">Viewer (Placeholder)</p>
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
</style>
