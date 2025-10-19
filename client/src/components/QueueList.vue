<script setup lang="ts">
import { type Fabricator } from '../models/fabricator'
import { removeJob, moveJobInQueue } from '../models/job'
import { ref, computed } from 'vue'
import FilterForm from './FilterForm.vue'

const props = defineProps<{ fabricator: Fabricator }>()
const currentFabricator = props.fabricator

const allJobs = ref(currentFabricator.queue || [])
const showDetails = ref(true)
const draggedJob = ref<any>(null)
const dragOverIndex = ref<number | null>(null)

// Filter state for queue
const activeFilters = ref<{
  model?: string
  status?: string
  searchTerm?: string
}>({})

// Handle filter changes
const handleFilterChange = (filters: any) => {
  activeFilters.value = filters
}

// Filter jobs based on active filters
const filteredJobs = computed(() => {
  let jobs = [...allJobs.value]

  // Filter by search term (job name or ticket)
  if (activeFilters.value.searchTerm) {
    const searchLower = activeFilters.value.searchTerm.toLowerCase()
    jobs = jobs.filter(job => {
      const jobName = job?.name || ''
      const ticketId = job?.td_id?.toString() || ''
      const fileName = job?.file_name_original || ''
      return jobName.toLowerCase().includes(searchLower) ||
             ticketId.toLowerCase().includes(searchLower) ||
             fileName.toLowerCase().includes(searchLower)
    })
  }

  // Filter by status
  if (activeFilters.value.status) {
    jobs = jobs.filter(job => {
      const status = job?.status || 'pending'
      return status.toLowerCase() === activeFilters.value.status!.toLowerCase()
    })
  }

  return jobs
})

const deleteJob = async (jobId: number) => {
  if (!confirm('Are you sure you want to remove this job from the queue?')) {
    return
  }

  try {
    await removeJob([jobId])

    if (allJobs.value) {
      const jobIndex = allJobs.value.findIndex((job) => job.id === jobId)
      if (jobIndex !== -1) {
        allJobs.value.splice(jobIndex, 1)
      }
    }
  } catch (error) {
    console.error('Failed to remove job:', error)
    alert('Failed to remove job from queue')
  }
}

const toggleDetails = () => {
  showDetails.value = !showDetails.value
}

const onDeleteClick = (jobId: number) => {
  deleteJob(jobId)
}

// Drag and drop functions
const handleDragStart = (event: DragEvent, job: any, index: number) => {
  draggedJob.value = { job, index }
  event.dataTransfer!.effectAllowed = 'move'
  event.dataTransfer!.setData('text/html', '') // Required for Firefox
}

const handleDragOver = (event: DragEvent, index: number) => {
  event.preventDefault()
  dragOverIndex.value = index
}

const handleDragLeave = () => {
  dragOverIndex.value = null
}

const handleDrop = async (event: DragEvent, dropIndex: number) => {
  event.preventDefault()
  dragOverIndex.value = null

  if (!draggedJob.value) return

  const { job, index: dragIndex } = draggedJob.value

  if (dragIndex !== dropIndex) {
    // Remove from old position
    allJobs.value.splice(dragIndex, 1)

    // Insert at new position
    allJobs.value.splice(dropIndex, 0, job)

    // Update backend
    try {
      const jobIds = allJobs.value.map(j => j.id)
      await moveJobInQueue(currentFabricator.id, jobIds)
    } catch (error) {
      console.error('Failed to update queue order:', error)
      // Revert on failure
      allJobs.value.splice(dropIndex, 1)
      allJobs.value.splice(dragIndex, 0, job)
      alert('Failed to update queue order')
    }
  }

  draggedJob.value = null
}

const handleDragEnd = () => {
  draggedJob.value = null
  dragOverIndex.value = null
}

// Move job up in queue
const moveJobUp = async (index: number) => {
  if (index === 0) return

  const job = filteredJobs.value[index]
  const actualIndex = allJobs.value.findIndex(j => j.id === job.id)

  if (actualIndex > 0) {
    // Swap positions
    [allJobs.value[actualIndex - 1], allJobs.value[actualIndex]] =
    [allJobs.value[actualIndex], allJobs.value[actualIndex - 1]]

    // Update backend
    try {
      const jobIds = allJobs.value.map(j => j.id)
      await moveJobInQueue(currentFabricator.id, jobIds)
    } catch (error) {
      console.error('Failed to move job up:', error)
      // Revert on failure
      [allJobs.value[actualIndex - 1], allJobs.value[actualIndex]] =
      [allJobs.value[actualIndex], allJobs.value[actualIndex - 1]]
    }
  }
}

// Move job down in queue
const moveJobDown = async (index: number) => {
  if (index === filteredJobs.value.length - 1) return

  const job = filteredJobs.value[index]
  const actualIndex = allJobs.value.findIndex(j => j.id === job.id)

  if (actualIndex < allJobs.value.length - 1) {
    // Swap positions
    [allJobs.value[actualIndex], allJobs.value[actualIndex + 1]] =
    [allJobs.value[actualIndex + 1], allJobs.value[actualIndex]]

    // Update backend
    try {
      const jobIds = allJobs.value.map(j => j.id)
      await moveJobInQueue(currentFabricator.id, jobIds)
    } catch (error) {
      console.error('Failed to move job down:', error)
      // Revert on failure
      [allJobs.value[actualIndex], allJobs.value[actualIndex + 1]] =
      [allJobs.value[actualIndex + 1], allJobs.value[actualIndex]]
    }
  }
}

// Get job status badge color
const getStatusColor = (status: string | null) => {
  switch(status?.toLowerCase()) {
    case 'printing':
      return 'bg-blue-500'
    case 'paused':
      return 'bg-yellow-500'
    case 'pending':
      return 'bg-gray-500'
    default:
      return 'bg-gray-400'
  }
}
</script>

<template>
  <transition name="slide-down" appear>
    <div class="container mx-auto mt-3">
      <!-- Filter section for queue -->
      <div class="mb-3">
        <FilterForm
          filter-type="queue"
          @filter-change="handleFilterChange"
        />
      </div>

      <!-- Queue summary -->
      <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
        <span v-if="filteredJobs.length === 0 && allJobs.length > 0">
          No jobs match your filters
        </span>
        <span v-else>
          {{ filteredJobs.length }} job{{ filteredJobs.length !== 1 ? 's' : '' }} in queue
          <span v-if="activeFilters.searchTerm"> (filtered)</span>
        </span>
      </div>

      <!-- Main Table -->
      <table class="min-w-full">
        <thead>
          <tr class="bg-light-primary-light dark:bg-dark-primary-light">
            <th
              class="w-8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              #
            </th>
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
              class="w-20 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              Status
            </th>
            <th
              class="w-48 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              Progress
            </th>
            <th
              class="w-24 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
            >
              Actions
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
            <tr v-if="filteredJobs.length === 0" class="text-center">
              <td colspan="9" class="border border-light-primary dark:border-dark-primary dark:text-light-primary p-4">
                <span v-if="allJobs.length === 0">No jobs in queue</span>
                <span v-else>No jobs match your search criteria</span>
              </td>
            </tr>
            <tr
              v-else
              v-for="(job, index) in filteredJobs"
              class="text-center transition-all duration-200 hover:bg-light-primary-light dark:hover:bg-dark-primary-dark"
              :key="job.id"
              :class="{
                'bg-blue-50 dark:bg-blue-900/20': dragOverIndex === index,
                'opacity-50': draggedJob?.job.id === job.id
              }"
              draggable="true"
              @dragstart="handleDragStart($event, job, index)"
              @dragover="handleDragOver($event, index)"
              @dragleave="handleDragLeave"
              @drop="handleDrop($event, index)"
              @dragend="handleDragEnd"
            >
              <td
                class="w-8 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2 cursor-move"
              >
                {{ index + 1 }}
              </td>
              <td
                class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
              >
                {{ job.td_id || '-' }}
              </td>
              <td
                class="w-48 whitespace-no-wrap truncate border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
              >
                {{ currentFabricator.description || currentFabricator.name }}
              </td>
              <td
                class="w-48 whitespace-no-wrap truncate border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
                :title="job?.name"
              >
                {{ job?.name || '-' }}
              </td>
              <td
                class="w-48 whitespace-no-wrap truncate border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
                :title="job?.file_name_original"
              >
                {{ job?.file_name_original || '-' }}
              </td>
              <td
                class="w-20 border border-light-primary dark:border-dark-primary p-2"
              >
                <span
                  :class="getStatusColor(job?.status)"
                  class="text-white text-xs px-2 py-1 rounded"
                >
                  {{ job?.status || 'Pending' }}
                </span>
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
                    {{ job?.progress != null ? Math.ceil(job.progress) + '%' : '0%' }}
                  </div>
                </div>
              </td>
              <td
                class="w-24 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
              >
                <div class="flex items-center justify-center space-x-1">
                  <!-- Move up button -->
                  <button
                    :disabled="index === 0"
                    class="w-8 h-8 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded flex items-center justify-center"
                    @click="moveJobUp(index)"
                    title="Move up"
                  >
                    <i class="fa-solid fa-arrow-up text-xs"></i>
                  </button>
                  <!-- Move down button -->
                  <button
                    :disabled="index === filteredJobs.length - 1"
                    class="w-8 h-8 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded flex items-center justify-center"
                    @click="moveJobDown(index)"
                    title="Move down"
                  >
                    <i class="fa-solid fa-arrow-down text-xs"></i>
                  </button>
                  <!-- Delete button -->
                  <button
                    class="w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded flex items-center justify-center"
                    @click="onDeleteClick(job.id)"
                    title="Remove from queue"
                  >
                    <i class="fa-solid fa-trash text-xs"></i>
                  </button>
                </div>
              </td>
              <td
                class="w-12 border border-light-primary dark:border-dark-primary dark:text-light-primary p-2"
              >
                <i class="fa-solid fa-grip-vertical text-gray-400"></i>
              </td>
            </tr>
          </tbody>
        </transition>
      </table>

      <!-- Queue action buttons -->
      <div v-if="showDetails && filteredJobs.length > 0" class="mt-3 flex justify-end space-x-2">
        <button
          class="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded"
          @click="() => console.log('Pause all jobs')"
        >
          <i class="fa-solid fa-pause mr-2"></i>Pause Queue
        </button>
        <button
          class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded"
          @click="() => console.log('Start processing')"
        >
          <i class="fa-solid fa-play mr-2"></i>Start Processing
        </button>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
.expand-enter-to,
.expand-leave-from {
  max-height: 2000px;
  opacity: 1;
}
.w-48 {
  max-width: 15rem;
  min-width: 15rem;
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

/* Drag and drop cursor styles */
tr[draggable="true"] {
  cursor: move;
}

tr[draggable="true"]:active {
  cursor: grabbing;
}
</style>