<script setup lang="ts">
import { type Fabricator } from '../models/fabricator'
import { removeJob } from '../models/job'
import { ref } from 'vue'

const props = defineProps<{ fabricator: Fabricator }>()
const currentFabricator = props.fabricator
const allJobs = currentFabricator.queue
const showDetails = ref(false)

const deleteJob = async (jobId: number) => {
  await removeJob([jobId])
  allJobs.splice(
    allJobs.findIndex((job) => job.id === jobId),
    1,
  )
}

function toggleDetails() {
  showDetails.value = !showDetails.value
}

function onDeleteClick(jobId: number) {
  deleteJob(jobId)
}
</script>

<template>
  <!-- Developer Note: This is simply a beginning setup. Subject to change eventually. -->
  <div class="container mx-auto mt-3">
    <!-- Main Table -->
    <table class="min-w-full">
      <thead>
        <tr class="bg-light-primary-light dark:bg-dark-primary-light">
          <th
            class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            TID
          </th>
          <th
            class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            {{ currentFabricator.name }}
          </th>
          <th
            class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            Job Name
          </th>
          <th
            class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            File Name
          </th>
          <th
            class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            Progress
          </th>
          <th
            class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-1"
          >
            <div class="flex justify-center items-center cursor-pointer" @click="toggleDetails">
              <i class="fas" :class="showDetails ? 'fa-caret-up' : 'fa-caret-down'"></i>
            </div>
          </th>
        </tr>
      </thead>
      <transition name="expand">
        <tbody v-if="showDetails">
          <tr v-for="job in allJobs" class="text-center" :key="job.id">
            <td
              class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              {{ job.td_id }}
            </td>
            <td
              class="w-48 whitespace-no-wrap truncate border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              {{ currentFabricator.description }}
            </td>
            <td
              class="w-48 whitespace-no-wrap truncate border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              {{ job?.name ?? '-' }}
            </td>
            <td
              class="w-48 whitespace-no-wrap truncate border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              {{ job?.file_name_original ?? '-' }}
            </td>
            <td
              class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              <div class="relative w-full rounded-full h-4 overflow-hidden dark:bg-dark-primary">
                <!-- Progress fill bar -->
                <div
                  class="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-500 ease-in-out"
                  :style="{ width: job?.progress != null ? job.progress + '%' : '0%' }"
                ></div>
                <!-- Overlayed percentage -->
                <div
                  class="absolute inset-0 flex items-center justify-center text-xs font-medium text-black dark:text-white"
                >
                  {{ job?.progress != null ? job.progress + '%' : '0%' }}
                </div>
              </div>
            </td>
            <td
              class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2 text-center align-middle"
            >
              <div class="flex items-center justify-center">
                <button
                  class="w-10 h-10 bg-red-500 hover:bg-red-600 text-white rounded flex items-center justify-center"
                  @click="onDeleteClick(job.id)"
                >
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
            </td>
          </tr></tbody
      ></transition>
    </table>
  </div>
</template>

<style scoped>
.expand-enter-active, .expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
}
.expand-enter-to, .expand-leave-from {
  max-height: 1000px;
  opacity: 1;
}
.w-48 {
  max-width: 15rem;
  min-width: 15rem;
}
</style>
