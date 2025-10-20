<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../models/api'

// Props and emits
const props = defineProps<{
  filterType?: 'jobs' | 'queue'
}>()

const emit = defineEmits<{
  'filter-change': [filters: {
    model?: string
    status?: string
    searchTerm?: string
    dateRange?: { start: Date | null; end: Date | null }
  }]
}>()

// State
const showFilters = ref(false)
const printerModels = ref<string[]>([])
const selectedModel = ref('All')
const selectedStatus = ref('All')
const searchTerm = ref('')
const showDatePicker = ref(false)
const dateRange = ref<{ start: Date | null; end: Date | null }>({
  start: null,
  end: null
})

// Status options based on filter type
const statusOptions = computed(() => {
  if (props.filterType === 'queue') {
    return ['All', 'Pending', 'Printing', 'Paused']
  }
  return ['All', 'Completed', 'Canceled', 'Failed', 'Printing']
})

// Fetch printer models from backend
const fetchPrinterModels = async () => {
  try {
    const response = await api('api/fabricators/models', undefined, 'GET')
    printerModels.value = ['All', ...(response?.models || [])]
  } catch (error) {
    console.error('Failed to fetch printer models:', error)
    // Fallback models if API fails
    printerModels.value = ['All', 'Prusa MK3', 'Prusa MK4', 'Ender 3', 'MakerBot']
  }
}

// Toggle filters
const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

// Toggle date picker
const toggleDatePicker = () => {
  showDatePicker.value = !showDatePicker.value
}

// Clear date range
const clearDateRange = () => {
  dateRange.value = { start: null, end: null }
  showDatePicker.value = false
}

// Format date for display
const formatDate = (date: Date | null) => {
  if (!date) return ''
  return date.toLocaleDateString()
}

// Date range display text
const dateRangeText = computed(() => {
  const { start, end } = dateRange.value
  if (!start && !end) return ''
  if (start && end) {
    return `${formatDate(start)} - ${formatDate(end)}`
  }
  if (start) return `From ${formatDate(start)}`
  if (end) return `Until ${formatDate(end)}`
  return ''
})

// Emit filter changes
const emitFilterChange = () => {
  emit('filter-change', {
    model: selectedModel.value === 'All' ? undefined : selectedModel.value,
    status: selectedStatus.value === 'All' ? undefined : selectedStatus.value,
    searchTerm: searchTerm.value || undefined,
    dateRange: (dateRange.value.start || dateRange.value.end) ? dateRange.value : undefined
  })
}

// Watch for filter changes
watch([selectedModel, selectedStatus, searchTerm, dateRange], () => {
  emitFilterChange()
}, { deep: true })

// Fetch models on mount
onMounted(() => {
  fetchPrinterModels()
})
</script>

<template>
  <div class="flex sm:flex-row flex-col">
    <button
      @click="toggleFilters"
      class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary px-3 py-2 mr-3 rounded-md transition-all duration-300 hover:bg-accent-primary"
    >
      <i class="fa-solid fa-filter"></i>
    </button>

    <transition name="filter-transition">
      <div v-if="showFilters" class="flex flex-row mb-1 sm:mb-0 transition-all duration-300">
        <!-- Printer Model Dropdown -->
        <div class="relative">
          <select
            v-model="selectedModel"
            class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary appearance-none h-full rounded-l block w-full py-2 px-4 pr-8 leading-tight focus:outline-none focus:bg-light-primary-light dark:focus:bg-dark-primary-light border-r-2"
          >
            <option v-for="model in printerModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
          <div
            class="text-dark-primary dark:text-light-primary pointer-events-none absolute inset-y-0 right-0 flex items-center px-2"
          >
            <i class="fa-solid fa-caret-down pr-1"></i>
          </div>
        </div>

        <!-- Status Dropdown -->
        <div class="relative">
          <select
            v-model="selectedStatus"
            class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary appearance-none h-full rounded-r sm:rounded-r-none block w-full py-2 px-4 pr-8 leading-tight focus:outline-none focus:bg-light-primary-light dark:focus:bg-dark-primary-light border-r-2"
          >
            <option v-for="status in statusOptions" :key="status" :value="status">
              {{ status }}
            </option>
          </select>
          <div
            class="text-dark-primary dark:text-light-primary pointer-events-none absolute inset-y-0 right-0 flex items-center px-2"
          >
            <i class="fa-solid fa-caret-down p-1"></i>
          </div>
        </div>

        <!-- Search Input with Date Picker -->
        <div class="block relative flex items-center">
          <!-- Search Icon -->
          <span class="absolute inset-y-0 left-0 flex items-center pl-2">
            <svg
              viewBox="0 0 24 24"
              class="text-dark-primary dark:text-light-primary h-4 w-4 fill-current text-gray-500"
            >
              <path
                d="M10 4a6 6 0 100 12 6 6 0 000-12zm-8 6a8 8 0 1114.32 4.906l5.387 5.387a1 1 0 01-1.414 1.414l-5.387-5.387A8 8 0 012 10z"
              ></path>
            </svg>
          </span>

          <!-- Search Input -->
          <input
            v-model="searchTerm"
            :placeholder="filterType === 'queue' ? 'Search queue...' : 'Job Name'"
            class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary appearance-none rounded-l sm:rounded-l-none sm:rounded-r-none block px-9 py-2 w-full h-full text-sm placeholder-dark-primary/50 dark:placeholder-light-primary/50 focus:bg-light-primary-light dark:focus:bg-dark-primary focus:text-dark-primary dark:focus:text-light-primary focus:outline-none"
          />

          <!-- Calendar Icon -->
          <div
            @click="toggleDatePicker"
            class="absolute inset-y-0 right-0 flex items-center pr-3 cursor-pointer hover:text-accent-primary"
          >
            <i
              class="fa-solid fa-calendar-days text-dark-primary dark:text-light-primary text-base"
            ></i>
          </div>
        </div>

        <!-- Date Range Picker (appears below when clicked) -->
        <transition name="date-picker-transition">
          <div
            v-if="showDatePicker"
            class="absolute top-full mt-2 right-0 bg-white dark:bg-dark-primary shadow-lg rounded-lg p-4 z-50"
          >
            <div class="flex flex-col space-y-2">
              <label class="text-sm font-medium text-dark-primary dark:text-light-primary">Date Range</label>
              <div class="flex space-x-2">
                <input
                  type="date"
                  v-model="dateRange.start"
                  class="px-2 py-1 border rounded dark:bg-dark-primary-light dark:text-light-primary"
                  placeholder="Start Date"
                />
                <span class="self-center">-</span>
                <input
                  type="date"
                  v-model="dateRange.end"
                  class="px-2 py-1 border rounded dark:bg-dark-primary-light dark:text-light-primary"
                  placeholder="End Date"
                />
              </div>
              <div class="flex justify-between">
                <button
                  @click="clearDateRange"
                  class="text-sm text-dark-primary hover:text-accent-primary dark:text-light-primary dark:hover:text-accent-primary-light"
                >
                  Clear
                </button>
                <button
                  @click="showDatePicker = false"
                  class="text-sm text-accent-primary hover:text-accent-primary-dark"
                >
                  Apply
                </button>
              </div>
              <div v-if="dateRangeText" class="text-xs text-dark-primary dark:text-light-primary">
                {{ dateRangeText }}
              </div>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.filter-transition-enter-active,
.filter-transition-leave-active {
  transition: all 0.3s ease;
}
.filter-transition-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.filter-transition-enter-to {
  opacity: 1;
  transform: translateX(0);
}
.filter-transition-leave-from {
  opacity: 1;
  transform: translateX(0);
}
.filter-transition-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.date-picker-transition-enter-active,
.date-picker-transition-leave-active {
  transition: all 0.2s ease;
}
.date-picker-transition-enter-from,
.date-picker-transition-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
.date-picker-transition-enter-to,
.date-picker-transition-leave-from {
  opacity: 1;
  transform: translateY(0);
}
</style>