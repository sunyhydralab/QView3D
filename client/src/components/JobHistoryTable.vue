<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import FilterForm from './FilterForm.vue'
import { getAllJobs, type Job } from '@/models/job'

// Reactive array to hold all jobs
const allJobs = ref<Job[]>([])

// Filter state
const activeFilters = ref<{
  model?: string
  status?: string
  searchTerm?: string
  dateRange?: { start: Date | null; end: Date | null }
}>({})

// Load all jobs when component is mounted
onMounted(async () => {
  try {
    const jobs = await getAllJobs()

    if (Array.isArray(jobs)) {
      allJobs.value = jobs
    } else if (jobs && Array.isArray(jobs[0])) {
      allJobs.value = jobs[0]
    } else {
      allJobs.value = []
    }

    console.log('Loaded jobs:', allJobs.value.length)
  } catch (error) {
    console.error('Failed to load jobs:', error)
    allJobs.value = []
  }
})

// Handle filter changes from FilterForm
const handleFilterChange = (filters: any) => {
  activeFilters.value = filters
  currentPage.value = 1 // Reset to first page when filters change
}

// Filter jobs based on active filters
const filteredJobs = computed(() => {
  let jobs = [...allJobs.value]

  // Filter by printer model
  if (activeFilters.value.model) {
    jobs = jobs.filter(job => {
      const printerName = job.printer_name || ''
      return printerName.toLowerCase().includes(activeFilters.value.model!.toLowerCase())
    })
  }

  // Filter by status
  if (activeFilters.value.status) {
    jobs = jobs.filter(job => {
      const status = job.status || ''
      return status.toLowerCase() === activeFilters.value.status!.toLowerCase()
    })
  }

  // Filter by search term (job name)
  if (activeFilters.value.searchTerm) {
    const searchLower = activeFilters.value.searchTerm.toLowerCase()
    jobs = jobs.filter(job => {
      const jobName = job.name || ''
      const ticketId = job.td_id?.toString() || ''
      return jobName.toLowerCase().includes(searchLower) ||
             ticketId.toLowerCase().includes(searchLower)
    })
  }

  // Filter by date range
  if (activeFilters.value.dateRange) {
    const { start, end } = activeFilters.value.dateRange

    jobs = jobs.filter(job => {
      const jobDate = job.date ? new Date(job.date) : null
      if (!jobDate) return false

      if (start && end) {
        return jobDate >= start && jobDate <= end
      } else if (start) {
        return jobDate >= start
      } else if (end) {
        return jobDate <= end
      }
      return true
    })
  }

  return jobs
})

const jobsPerPage = 20
const currentPage = ref(1)

// Grabs the jobs that are between the set start and end.
const paginatedJobs = computed(() => {
  const start = (currentPage.value - 1) * jobsPerPage
  const end = start + jobsPerPage
  return filteredJobs.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(filteredJobs.value.length / jobsPerPage))

// Calculates current range of entries
const currentRange = computed(() => {
  if (filteredJobs.value.length === 0) return 'No results'

  const start = (currentPage.value - 1) * jobsPerPage + 1
  const end = Math.min(currentPage.value * jobsPerPage, filteredJobs.value.length)
  return `Showing ${start}-${end} of ${filteredJobs.value.length} jobs`
})

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}

const goToPrevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

// Format date for display
const formatDate = (date: string | null) => {
  if (!date) return '-'

  try {
    const d = new Date(date)
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString()
  } catch {
    return date
  }
}

// Format elapsed time
const formatElapsedTime = (seconds: number | null) => {
  if (!seconds) return '00:00'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
}

// Get status color
const getStatusColor = (status: string | null) => {
  switch(status?.toLowerCase()) {
    case 'completed':
      return 'text-green-600 dark:text-green-400'
    case 'failed':
    case 'canceled':
      return 'text-red-600 dark:text-red-400'
    case 'printing':
      return 'text-blue-600 dark:text-blue-400'
    case 'paused':
      return 'text-yellow-600 dark:text-yellow-400'
    default:
      return 'text-gray-600 dark:text-gray-400'
  }
}
</script>

<template>
  <transition name="slide-down" appear>
    <div class="container mx-auto px-4 sm:px-8">
      <div class="py-6">
        <!-- Filter Form with event handler -->
        <FilterForm
          filter-type="jobs"
          @filter-change="handleFilterChange"
        />

        <!-- Results summary -->
        <div v-if="activeFilters.searchTerm || activeFilters.model || activeFilters.status || activeFilters.dateRange"
             class="mt-3 mb-2 text-sm text-gray-600 dark:text-gray-400">
          <span v-if="filteredJobs.length === 0" class="text-red-600 dark:text-red-400">
            No jobs found matching your filters
          </span>
          <span v-else>
            Found {{ filteredJobs.length }} job{{ filteredJobs.length !== 1 ? 's' : '' }} matching your filters
          </span>
        </div>

        <div class="-mx-4 sm:-mx-8 px-4 sm:px-8 py-3 overflow-x-auto">
          <div class="inline-block min-w-full shadow">
            <table class="min-w-full leading-normal">
              <thead>
                <tr>
                  <th
                    class="w-12 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Ticket
                  </th>
                  <th
                    class="w-48 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Job Name
                  </th>
                  <th
                    class="w-30 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Printer ID
                  </th>
                  <th
                    class="w-30 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Printer
                  </th>
                  <th
                    class="w-30 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Started at
                  </th>
                  <th
                    class="w-30 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Elapsed Time
                  </th>
                  <th
                    class="w-12 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                <!-- Show message when no jobs -->
                <tr v-if="paginatedJobs.length === 0">
                  <td colspan="7" class="px-5 py-8 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-center">
                    <p class="text-gray-500 dark:text-gray-400">
                      {{ filteredJobs.length === 0 && (activeFilters.searchTerm || activeFilters.model || activeFilters.status)
                         ? 'No jobs match your search criteria'
                         : 'No jobs in history' }}
                    </p>
                  </td>
                </tr>

                <!-- Paginated jobs display -->
                <tr v-else v-for="job in paginatedJobs" :key="job.id">
                  <td
                    class="w-12 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.td_id || '-' }}
                    </p>
                  </td>
                  <td
                    class="w-48 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p
                      class="w-48 text-dark-primary dark:text-light-primary whitespace-no-wrap truncate"
                      :title="job.name"
                    >
                      {{ job.name || 'Unnamed Job' }}
                    </p>
                  </td>

                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.printerid || '-' }}
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.printer_name || 'Unknown' }}
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ formatDate(job.date) }}
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ formatElapsedTime(job.job_client?.elapsed_time || job.time_elapsed) }}
                    </p>
                  </td>
                  <td
                    class="w-12 px-3 py-3 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm align-center"
                  >
                    <p :class="getStatusColor(job.status)" class="font-medium whitespace-no-wrap">
                      {{ job.status || '-' }}
                    </p>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Pagination -->
            <div
              class="px-5 py-5 bg-light-primary-light dark:bg-dark-primary-light border-t flex flex-col xs:flex-row items-center xs:justify-between"
            >
              <span class="text-xs xs:text-sm text-dark-primary dark:text-light-primary">
                {{ currentRange }}
              </span>
              <div class="inline-flex mt-2 xs:mt-0">
                <button
                  :disabled="currentPage === 1 || filteredJobs.length === 0"
                  class="text-sm bg-light-primary-dark dark:bg-dark-primary hover:bg-light-primary dark:hover:bg-dark-primary-light text-dark-primary dark:text-light-primary font-semibold py-2 px-4 rounded-l border-r disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="goToPrevPage"
                >
                  Prev
                </button>
                <button
                  :disabled="currentPage === totalPages || filteredJobs.length === 0"
                  class="text-sm bg-light-primary-dark dark:bg-dark-primary hover:bg-light-primary dark:hover:bg-dark-primary-light text-dark-primary dark:text-light-primary font-semibold py-2 px-4 rounded-r disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="goToNextPage"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
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
.w-48 {
  width: 20rem; /* Set a fixed width for the column */
}
</style>