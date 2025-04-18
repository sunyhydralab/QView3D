<script setup lang="ts">
import GCodePreview from "@/components/GCodePreview.vue"
import { ref } from 'vue'
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
            <i class="fa-solid mx-3 fa-ellipsis-vertical"></i> <!-- Currently doesn't do anything, will be for more actions -->
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
</style>