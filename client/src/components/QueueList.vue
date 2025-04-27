<script setup lang="ts">
import { type Fabricator } from '../models/fabricator'
import { removeJob } from '../models/job';
import { defineEmits } from 'vue'

const props = defineProps<{ fabricator: Fabricator }>()
const currentFabricator = props.fabricator
const allJobs = currentFabricator.queue

const emit = defineEmits(['jobDeleted'])

const deleteJob = async (jobId : number) => {
  await removeJob([jobId])
  emit('jobDeleted') // Tell the parent component to refresh
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
            ID
          </th>
          <th
            class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            Printer
          </th>
          <th
            class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            Job Name
          </th>
          <th
            class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            File Name
          </th>
          <th
            class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            Progress
          </th>
          <th
            class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            Options
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="job in allJobs" class="text-center" :key="job.id">
          <td
            class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
          >
            {{ currentFabricator.id }}
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
            class="w-40 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
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
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.w-48 {
  width: 20rem; /* Set a fixed width for the column */
}
</style>
