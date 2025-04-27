<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { fabricatorList, retrieveRegisteredFabricators, type Fabricator } from '@/models/fabricator'
import { autoQueue, addJobToQueue } from '@/models/job'

const emit = defineEmits<{
  (e: 'close'): void
}>()

// Load fabricators when modal is mounted
onMounted(() => {
  retrieveRegisteredFabricators()
})

// File Upload Handling
const selectedFile = ref<File | null>(null)
const fileName = ref("No file selected.")
const quantity = ref(1)
const ticketId = ref(0)
const jobName = ref("")

// Save the selected file and updating the file and job names.
const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] as File
  fileName.value = selectedFile.value.name
  if (jobName.value === "")
    jobName.value = selectedFile.value.name
}

// Submits the selected file by auto-queuing it or assigning it to selected fabricators' queues, then resets the form
const submitJob = async () => {
  const job = new FormData()
  if (selectedFile.value) {
    try {
      setJob(job)
      if (!anySelected.value) {
        // If no fabricator is selected, auto queue the job
        await autoQueue(job)
      }
      else {
        // for every fabricator that is registered, if that fabricator is selected, then add the job to the fabricator's queue
        for (const fabricator of fabricatorList.value) {
          if (fabricator.isSelected) {
            job.set('printerid', (fabricator.id?.toString() ?? ''))
            // add as many jobs as the quantity
            for (let i = 0; i < quantity.value; i++) {
              await addJobToQueue(job)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error submitting job:', error)
    }
    resetForm()
    console.log('Job submitted:', job)
  }
}

// Reset the form
const resetForm = () => {
  selectedFile.value = null
  fileName.value = "No file selected."
  quantity.value = 1
  ticketId.value = 0
  jobName.value = ""
}

// Set the job data to be sent to the server.
const setJob = (job: FormData) => {
  job.append('file', selectedFile.value as File)
  job.append('name', jobName.value as string)
  job.append('td_id', ticketId.value.toString())
  job.append('quantity', quantity.value.toString())
  job.append('favorite', 'false')
  job.append('priority', '0')
  job.append('filament', 'PLA')
  console.log('Set job data:', job)
}

// Toggles the isSelected state of a selected Fabricator
const toggleFabricator = (selectedFabricator: Fabricator) => {
  selectedFabricator.isSelected = !selectedFabricator.isSelected
}

// Toggle all fabricators as selected or deselected based on current selection state.
const toggleSelectAll = () => {
  const shouldSelect = !allSelected.value;

  for (const fabricator of fabricatorList.value) {
    fabricator.isSelected = shouldSelect;
  }
}

// Checks if any fabricator is selected, returns true if at least one is.
const anySelected = computed(() =>
  fabricatorList.value.some((fabricator) => fabricator.isSelected)
)

// Checks if all fabricators are selected, returns true if they all are.
const allSelected = computed(() =>
  fabricatorList.value.every((fabricator) => fabricator.isSelected)
)
</script>

<template>
  <!-- Modal Overlay -->
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
    @click.self="emit('close')">
    <div class="bg-light-primary dark:bg-dark-primary-light rounded-lg shadow-lg max-w-md w-full mx-4 animate-fade-in">
      <!-- Header -->
      <div class="p-4 flex justify-between items-center">
        <h3 class="text-lg font-medium text-black dark:text-white">Submit Job</h3>
        <button @click="emit('close')"
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd" />
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="p-4 space-y-5">
        <!-- Fabricator Selection -->
        <div class="space-y-2">
          <h4 class="text-md font-medium text-center text-gray-700 dark:text-gray-300">Select Fabricator</h4>
          <div class="flex justify-center">
            <button @click="toggleSelectAll"
              class="px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-accent-primary-dark">
              {{ allSelected ? 'Deselect All' : 'Select All' }}
            </button>
          </div>

          <!-- Grid of fabricator buttons -->
          <div class="grid grid-cols-2 md:grid-cols-3 gap-2 p-2">
            <button v-for="fabricator in fabricatorList" :key="fabricator.id" type="button"
              class="px-3 py-2 rounded-md text-center text-sm font-medium transition-all duration-200 relative" :class="[fabricator.isSelected
                ? 'bg-accent-secondary text-white hover:bg-accent-secondary-dark font-bold shadow-lg transform scale-105'
                : 'bg-accent-secondary text-white hover:bg-accent-secondary-dark opacity-50'
              ]" @click="toggleFabricator(fabricator)">
              <div class="flex items-center justify-center space-x-1">
                <span v-if="fabricator.isSelected" class="absolute -left-1 -top-1 bg-white rounded-full p-1 shadow-md">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-500" viewBox="0 0 20 20"
                    fill="currentColor">
                    <path fill-rule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clip-rule="evenodd" />
                  </svg>
                </span>
                <span class="truncate">{{ fabricator.name }}</span>
              </div>
            </button>
          </div>

          <!-- File Upload -->
          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Upload your .gcode file
              <span class="text-red-500 ml-1">*</span>
            </label>

            <div class="flex items-center space-x-2">
              <!-- Browse Button -->
              <label
                class="cursor-pointer bg-accent-primary text-white px-4 py-2 rounded-md hover:bg-accent-primary-dark flex-shrink-0">
                Browse
                <input type="file" accept=".gcode" class="hidden" @change="handleFileUpload" />
              </label>

              <!-- File name preview -->
              <div class="flex-1 min-w-0 px-3 py-2 bg-gray-100 dark:bg-dark-primary rounded-md flex items-center">
                <span class="text-gray-500 dark:text-gray-400 truncate">{{ fileName }}</span>
              </div>

              <!-- Image Button -->
              <button type="button"
                class="bg-accent-primary hover:bg-accent-primary-dark py-2 px-3 rounded-md flex-shrink-0">
                <i class="fa-regular fa-image text-white"></i>
              </button>
            </div>
          </div>

          <!-- Quantity Input -->
          <div>
            <label for="quantity" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Quantity</label>
            <input id="quantity" type="number" min="1" v-model="quantity"
              class="bg-light-primary-light dark:bg-dark-primary w-full px-3 py-2 rounded-md text-gray-700 dark:text-light-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary" />
          </div>

          <!-- Ticket ID -->
          <div>
            <label for="ticketId" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Ticket ID</label>
            <input id="ticketId" type="number" min="0" v-model="ticketId"
              class="bg-light-primary-light dark:bg-dark-primary w-full px-3 py-2 rounded-md text-gray-700 dark:text-light-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary" />
          </div>

          <!-- Job Name -->
          <div>
            <label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Name<span
                class="text-red-500 ml-1">*</span></label>
            <input id="name" type="text" required placeholder="Enter job name" v-model="jobName"
              class="bg-light-primary-light dark:bg-dark-primary w-full px-3 py-2 rounded-md text-gray-700 dark:text-light-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary" />
          </div>

          <!-- No Fabricator Message -->
          <p v-if="!anySelected" class="text-[11px] text-center text-gray-500 dark:text-gray-400">
            <span class="text-red-400">No fabricator selected</span>, job will be <span
              class="text-accent-primary-light">auto queued</span> to fabricator with least jobs
          </p>

          <!-- Footer -->
          <div class="flex justify-end">
            <button type="button"
              class="px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-accent-primary-dark disabled:bg-accent-primary-light disabled:cursor-not-allowed"
              :disabled="!selectedFile" @click="submitJob">Submit</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
