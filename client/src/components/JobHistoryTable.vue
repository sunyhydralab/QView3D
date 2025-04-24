<script setup lang="ts">
import { ref, onMounted } from 'vue'
import FilterForm from '@/components/FilterForm.vue'
import { getAllJobs } from '@/models/job'

// Reactive array to hold all jobs
const allJobs = ref<Job[]>([])

// Load all jobs when component is mounted
onMounted(async () => {
  allJobs.value = await getAllJobs()
  console.log('Loaded jobs:', allJobs.value.length)  // Debugging
})
</script>

<template>
  <transition name="slide-down" appear>
    <div class="container mx-auto px-4 sm:px-8">
      <div class="py-6">
        <FilterForm />
        <div class="-mx-4 sm:-mx-8 px-4 sm:px-8 py-3 overflow-x-auto">
          <div class="inline-block min-w-full shadow">
            <table class="min-w-full leading-normal">
              <thead>
                <tr>
                  <th
                    class="w-48 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Job Name
                  </th>
                  <th
                    class="w-12 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Ticket
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
                    Elasped Time
                  </th>
                  <th
                    class="w-12 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                <!-- Developer Note: for the condition below, the length of all jobs (even if empty) is 2 for some reason. This is why it checks allJobs.length > 2. -->
                <!-- Needs testing. -->
                <tr v-if="allJobs.length > 2" v-for="job in allJobs" :key="job.id">
                  <td
                    class="w-48 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p
                      class="w-48 text-dark-primary dark:text-light-primary whitespace-no-wrap truncate"
                    >
                      {{ job.name }}
                    </p>
                  </td>
                  <td
                    class="w-12 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.td_id }}
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.printerid }}
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.printer }}
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.date }} {{ job.time_started }}
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      {{ job.job_client?.elapsed_time ?? '-' }}
                    </p>
                  </td>
                  <td
                    class="w-12 px-3 py-3 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm align-center"
                  >
                    <div class="flex flex-col items-start space-y-1">
                      <!-- Statuses subject to change -->
                      <span
                        v-if="job.status === 'Done'"
                        class="relative inline-block w-20 text-center px-3 py-1 font-semibold leading-tight"
                      >
                        <span
                          aria-hidden
                          class="absolute inset-0 bg-accent-primary-light rounded-full"
                        ></span>
                        <span class="text-white dark:text-dark-primary-dark relative">Done</span>
                      </span>
                      <span
                        v-else-if="job.status === 'Printing'"
                        class="relative inline-block w-20 text-center px-3 py-1 font-semibold leading-tight"
                      >
                        <span
                          aria-hidden
                          class="absolute inset-0 bg-accent-secondary-light rounded-full"
                        ></span>
                        <span class="text-white dark:text-dark-primary-dark relative"
                          >Printing</span
                        >
                      </span>
                      <span
                        v-else-if="job.status === 'Error'"
                        class="relative inline-block w-20 text-center px-3 py-1 font-semibold leading-tight"
                      >
                        <span aria-hidden class="absolute inset-0 bg-red-300 rounded-full"></span>
                        <span class="text-white dark:text-dark-primary-dark relative">Error</span>
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div
              class="px-5 py-5 bg-light-primary-light dark:bg-dark-primary-light border-t flex flex-col xs:flex-row items-center xs:justify-between"
            >
              <span class="text-xs xs:text-sm text-dark-primary dark:text-light-primary">
                1 of 1
              </span>

              <!-- TODO: Pagniation -->
              <div class="inline-flex mt-2 xs:mt-0">
                <button
                  class="text-sm bg-light-primary-dark dark:bg-dark-primary hover:bg-light-primary dark:hover:bg-dark-primary text-dark-primary dark:text-light-primary font-semibold py-2 px-4 rounded-l border-r"
                >
                  Prev
                </button>
                <button
                  class="text-sm bg-light-primary-dark dark:bg-dark-primary hover:bg-light-primary dark:hover:bg-dark-primary-light text-dark-primary dark:text-light-primary font-semibold py-2 px-4 rounded-r"
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
  width: 30rem; /* Set a fixed width for the column */
}
</style>
