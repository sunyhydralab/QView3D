<!--TODO: Whenever the database is wiped, so should the localStorage for connectedFabricatorList-->

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  type Fabricator,
  fabricatorList,
  getConnectedFabricators,
  registerFabricator,
  retrieveRegisteredFabricators,
} from '@/models/fabricator'
import FabricatorCard from '@/components/RegisteredFabricatorCard.vue'
import { addToast } from '../components/Toast.vue'

// all connected fabricators
const connectedFabricatorList = ref<Fabricator[]>([])

// the selected fabricator from the dropdown
const selectedFabricator = ref<Fabricator | null>(null)

// the user submitted name for the fabricator
const customName = ref<string | null>(null)

// fetch the list of connected ports from backend and automatically load them into the form dropdown
onMounted(async () => {
  // get the filtered list of connected fabricators from local storage
  const previousConnectedFabricatorList = localStorage.getItem('connectedFabricatorList')
  // if the list exists in local storage, use it; otherwise, fetch from the server
  if (previousConnectedFabricatorList) {
    connectedFabricatorList.value = JSON.parse(previousConnectedFabricatorList)
    console.log('Loaded connectedFabricatorList from localStorage')
  } else {
    connectedFabricatorList.value = await getConnectedFabricators()
    console.log('Loaded connectedFabricatorList from server')
  }

  // get the list of registered fabricators from the server
  await retrieveRegisteredFabricators()
  console.log('Loaded fabricatorList from server')
})

// update the list of connected Fabricators but filter out the registered ones
async function refreshFabricatorList() {
  const updatedList = await getConnectedFabricators()
  // filter out fabricators that have already been registered
  connectedFabricatorList.value = updatedList.filter((fabricator: Fabricator) => {
    // checks if the fabricator is registered and already has a name by it's serialPort id
    const isRegisteredFabricator = searchFabricatorById(fabricator.device.serialPort) // TODO Change how we uniquely identify printers

    // returns true if the fabricator is not registered
    return !isRegisteredFabricator
  })
}

// Handle fabricator deletion
async function handleFabricatorDeleted(id: number) {
  console.log(`Fabricator with ID ${id} deleted`);
  // Refresh the list of registered fabricators
  fabricatorList.value = await retrieveRegisteredFabricators();
}

// helper function to search by fabricatorList.value serialPort id
function searchFabricatorById(id: string) {
  return fabricatorList.value.find((fabricator: Fabricator) => {
    return fabricator.device.serialPort === id // TODO Change how we uniquely identify printers
  })
}

async function handleSubmit() {
  // register the selected fabricator with the custom name
  if (selectedFabricator.value && customName.value) {
    selectedFabricator.value.name = customName.value
    console.log('Selected Fabricator:', selectedFabricator.value)
    await registerFabricator(selectedFabricator.value)

    // update fabricatorList when a new fabricator is registered
    fabricatorList.value = await retrieveRegisteredFabricators()
    console.log('Registered Fabricators:', fabricatorList.value)

    // filter out fabricators that have already been registered
    connectedFabricatorList.value = connectedFabricatorList.value.filter((fabricator: Fabricator) => {
      return !fabricator.name
    })
    console.log('Connected Fabricators:', connectedFabricatorList.value)

    // save the updated list to localStorage
    localStorage.setItem('connectedFabricatorList', JSON.stringify(connectedFabricatorList.value))
    console.log('Saved connectedFabricatorList to localStorage')

    // reset the form
    selectedFabricator.value = null
    customName.value = null
    console.log('Form reset')
  } else {
    addToast("Please add a custom name to this fabricator", "info")
  }
}

</script>

<template>
  <transition name="slide-down" appear>
    <div class="container mx-auto pt-10 px-4">
      <h1 class="text-2xl font-semibold mb-6 text-center md:text-left text-gray-800 dark:text-gray-200">
        Printer Registration
      </h1>
      
      <div class="flex flex-wrap justify-center items-start">
        <!-- Registration form -->
        <div class="md:w-1/3 mx-auto max-w-md space-y-5 mb-10"> 
          <div class="p-6 bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-md transition-all duration-300 hover:shadow-lg">
            <!-- Select Fabricator -->
            <div class="mb-4">
              <label
                for="fabricatorSelect"
                class="block mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200"
                >Select a Printer</label
              >
              <div class="flex items-center">
                <select
                  id="fabricatorSelect"
                  v-model="selectedFabricator"
                  class="block w-full p-3 bg-light-primary dark:bg-dark-primary border border-light-primary-dark dark:border-dark-primary-dark rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-accent-primary text-gray-800 dark:text-white"
                  required
                >
                  <option v-if="connectedFabricatorList.length > 0" disabled value="">
                    Select a printer
                  </option>
                  <option v-else disabled value="">All connected printers have been registered</option>
                  <option
                    v-for="fabricator in connectedFabricatorList"
                    :key="fabricator.device.dbID"
                    :value="fabricator"
                  >
                    {{ fabricator.description }}
                  </option>
                </select>
                <div class="ml-2">
                  <!-- Refresh Button -->
                  <button
                    type="button"
                    class="flex items-center justify-center w-10 h-10 bg-accent-primary hover:bg-accent-primary-dark text-white rounded-md transition-all duration-300 transform hover:scale-105"
                    @click="refreshFabricatorList"
                  >
                    <i class="fas fa-sync-alt"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- Fabricator Name -->
            <div class="mb-4">
              <label for="name" class="block mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200"
                >Printer Name</label
              >
              <input
                id="name"
                type="text"
                class="w-full p-3 border border-light-primary-dark dark:border-dark-primary-dark rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-accent-primary bg-light-primary dark:bg-dark-primary text-gray-800 dark:text-white"
                v-model="customName"
                placeholder="Enter a name for your printer"
              />
            </div>

            <!-- Model (Disabled) -->
            <div class="mb-5">
              <label for="model" class="block mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200"
                >Model</label
              >
              <input
                id="model"
                type="text"
                class="w-full p-3 border border-light-primary-dark dark:border-dark-primary-dark rounded-md shadow-sm bg-light-primary-dark dark:bg-dark-primary-dark text-gray-500 dark:text-gray-400 cursor-not-allowed"
                disabled
                :placeholder="selectedFabricator?.description || 'Printer model'"
              />
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              class="w-full bg-accent-primary hover:bg-accent-primary-dark text-white py-3 px-4 rounded-md transition-all duration-300 transform hover:scale-[1.02] disabled:bg-accent-primary-light disabled:hover:scale-100 disabled:cursor-not-allowed"
              :disabled="!selectedFabricator || !customName"
              @click="handleSubmit"
            >
              Register Printer
            </button>
          </div>
        </div>
        
        <!-- Registered printers grid -->
        <div v-if="fabricatorList.length > 0" class="md:w-2/3">
          <h2 class="text-xl font-medium mb-4 text-gray-800 dark:text-gray-200">Registered Printers</h2>
          <div class="flex flex-wrap justify-center md:justify-start">
            <FabricatorCard
              v-for="fabricator in fabricatorList"
              :key="fabricator.id"
              :id="fabricator.id || 0"
              :name="fabricator.name || ''"
              :model="fabricator.description"
              :date="fabricator.date ? fabricator.date : ''"
              :hwid="fabricator.hwid"
              @deleted="handleFabricatorDeleted"
            />
          </div>
        </div>
        
        <!-- No printers registered message -->
        <div v-else class="w-full text-center py-10">
          <p class="text-gray-500 dark:text-gray-400">No printers are currently registered. Connect a printer and register it using the form.</p>
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
</style>
