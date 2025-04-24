<script setup lang="ts">
import FilterForm from '@/components/FilterForm.vue'
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
                    Completed at
                  </th>
                  <th
                    class="w-12 px-5 py-3 border-b border-dark-primary-light dark:border-light-primary text-left text-xs font-semibold text-dark-primary dark:text-light-primary bg-light-primary-dark dark:bg-dark-primary-light uppercase"
                  >
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td
                    class="w-48 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p
                      class="w-48 text-dark-primary dark:text-light-primary whitespace-no-wrap truncate"
                    >
                      mini_cube_or_some_super_long_name_to_test_ellipsis
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      Prusa MK4
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      Jan 21, 2020 12:50:01
                    </p>
                  </td>
                  <td
                    class="w-30 px-5 py-5 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm"
                  >
                    <p class="text-dark-primary dark:text-light-primary whitespace-no-wrap">
                      Jan 21, 2020 12:52:29
                    </p>
                  </td>
                  <td
                    class="w-12 px-3 py-3 border-b border-light-primary-dark dark:border-dark-primary-light bg-light-primary-light dark:bg-dark-primary-light text-sm align-top"
                  >
                    <div class="flex flex-col items-start space-y-1">
                      <span class="relative inline-block px-3 py-1 font-semibold leading-tight">
                        <span
                          aria-hidden
                          class="absolute inset-0 bg-accent-primary-light rounded-full"
                        ></span>
                        <span class="text-white dark:text-dark-primary-dark relative">Done</span>
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