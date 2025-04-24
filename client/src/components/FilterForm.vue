<script setup lang="ts">
import { ref } from 'vue'

const showFilters = ref(false) // State to manage filter visibility

const toggleFilters = () => {
  showFilters.value = !showFilters.value // Toggle filter visibility
}
</script>

<template>
  <div class="flex sm:flex-row flex-col">
    <button
      @click="toggleFilters"
      class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary px-3 py-2 mr-3 rounded-md transition-all duration-300"
    >
      <i class="fa-solid fa-filter"></i>
    </button>

    <transition name="filter-transition">
      <div v-if="showFilters" class="flex flex-row mb-1 sm:mb-0 transition-all duration-300">
        <div class="relative">
          <select
            class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary appearance-none h-full rounded-l block w-full py-2 px-4 pr-8 leading-tight focus:outline-none focus:bg-light-primary-light dark:focus:bg-dark-primary-light border-r-2"
          >
<<<<<<< HEAD
            <option>All</option>
=======
>>>>>>> origin/frontdev-rewrite-jobhistory
            <option>Prusa MK3</option>
            <option>Prusa MK4</option>
            <option>Ender 3</option>
          </select>
          <div
            class="text-dark-primary dark:text-light-primary pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700"
          >
            <i class="fa-solid fa-caret-down pr-1"></i>
          </div>
        </div>
        <div class="relative">
          <select
            class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary appearance-none h-full rounded-r sm:rounded-r-none block w-full py-2 px-4 pr-8 leading-tight focus:outline-none focus:bg-light-primary-light dark:focus:bg-dark-primary-light border-r-2"
          >
            <option>All</option>
            <option>Completed</option>
            <option>Canceled</option>
            <option>Printing</option>
          </select>
          <div
            class="text-dark-primary dark:text-light-primary pointer-events-none absolute inset-y-0 right-0 flex items-center px-2"
          >
            <i class="fa-solid fa-caret-down p-1"></i>
          </div>
        </div>

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
            placeholder="File Name"
            class="bg-light-primary-dark dark:bg-dark-primary-light text-dark-primary dark:text-light-primary appearance-none rounded-l sm:rounded-l-none sm:rounded-r-none block px-9 py-2 w-full h-full text-sm placeholder-gray-400 focus:bg-light-primary-light focus:placeholder-dark-primary-light dark:text-light-primary focus:text-gray-700 focus:outline-none"
          />

          <!-- Calendar Icon -->
          <div class="absolute inset-y-0 right-0 flex items-center pr-3 cursor-pointer">
            <i
              class="fa-solid fa-calendar-days text-dark-primary dark:text-light-primary text-base"
            ></i>
          </div>
        </div>
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
</style>