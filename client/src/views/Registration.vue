<!--TODO: Whenever the database is wiped, so should the localStorage for connectedFabricatorList-->

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
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

// animation states
const formSubmitted = ref(false)
const isRotating = ref(false) // Changed from isRefreshing to isRotating for consistency with card

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
  // Trigger rotation animation
  triggerRotation()

  const updatedList = await getConnectedFabricators()
  // filter out fabricators that have already been registered
  connectedFabricatorList.value = updatedList.filter((fabricator: Fabricator) => {
    // checks if the fabricator is registered and already has a name by it's serialPort id
    const isRegisteredFabricator = searchFabricatorById(fabricator.device.serialPort) // TODO Change how we uniquely identify printers

    // returns true if the fabricator is not registered
    return !isRegisteredFabricator
  })
}

// Function to handle refresh button click and enable rotation - reused from card component
function triggerRotation() {
  if (!isRotating.value) {
    isRotating.value = true
    setTimeout(() => {
      isRotating.value = false
    }, 800) // Duration of one full rotation
  }
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

    formSubmitted.value = true
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

    // reset animation state
    setTimeout(() => {
      formSubmitted.value = false
    }, 1000)
  }
}
// Handle fabricator deletion
async function handleFabricatorDeleted(id: number) {
  console.log(`Fabricator with ID ${id} deleted and page has been refreshed`);
  // Refresh the list of registered fabricators
  fabricatorList.value = await retrieveRegisteredFabricators();
}
</script>

<template>
  <div class="flex flex-col md:flex-row h-full p-4 overflow-hidden">
    <!-- Registration Form -->
    <transition name="slide-in-left" appear>
      <div class="md:w-1/3 p-6 flex-shrink-0">
        <div class="max-w-md mx-auto space-y-6 my-6">
          <h2 class="text-2xl font-bold mb-6 text-dark-primary dark:text-light-primary">
            Register New Fabricator

          </h2>

          <!-- Select Fabricator -->
          <div class="space-y-2">
            <label for="fabricatorSelect" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-200">Select
              a Fabricator</label>
            <div class="flex items-center">
              <select id="fabricatorSelect" v-model="selectedFabricator"
                class="input-style block w-full px-4 py-3 bg-light-primary-light border-light-primary-dark rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light transition-all duration-300"
                required>
                <option v-if="connectedFabricatorList.length > 0" disabled value="">
                  Select a fabricator
                </option>
                <option v-else disabled value="">All connected fabricators have been registered</option>
                <option v-for="fabricator in connectedFabricatorList" :key="fabricator.device.dbID" :value="fabricator">
                  {{ fabricator.description }}
                </option>
              </select>
              <div class="ml-2">
                <!-- Refresh Button -->
                <button type="button"
                  class="h-full flex items-center justify-center bg-accent-primary hover:bg-accent-primary-dark text-white rounded-lg transition-all duration-300 p-2"
                  @click="refreshFabricatorList" :disabled="isRotating">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" class="w-7 h-7"
                    :class="{ 'rotating': isRotating }">
                    <path
                      d="M49.4835 63.8984L48.3355 61.1268L48.3355 61.1268L49.4835 63.8984ZM42.1844 62.7193C40.5382 62.9076 39.3565 64.3948 39.5448 66.0409C39.7332 67.687 41.2203 68.8687 42.8664 68.6804L42.1844 62.7193ZM42.8472 68.6826C44.4934 68.4954 45.6762 67.009 45.4889 65.3628C45.3017 63.7165 43.8154 62.5338 42.1691 62.721L42.8472 68.6826ZM42.0894 62.73C40.4425 62.9114 39.2546 64.3936 39.436 66.0405C39.6175 67.6874 41.0996 68.8753 42.7465 68.6939L42.0894 62.73ZM63.4835 49.8984L60.7119 48.7504L63.4835 49.8984ZM63.4835 30.0994L66.2551 28.9514L66.2551 28.9514L63.4835 30.0994ZM59.1619 18.7833C57.9443 17.6596 56.0463 17.7358 54.9227 18.9534C53.799 20.171 53.8752 22.069 55.0928 23.1926L59.1619 18.7833ZM48.3355 61.1268C46.3513 61.9487 44.2805 62.4795 42.1844 62.7193L42.8664 68.6804C45.5127 68.3776 48.1271 67.7075 50.6316 66.6701L48.3355 61.1268ZM42.1691 62.721C42.1426 62.7241 42.116 62.727 42.0894 62.73L42.7465 68.6939C42.7801 68.6902 42.8136 68.6864 42.8472 68.6826L42.1691 62.721ZM60.7119 48.7504C58.3908 54.3538 53.9389 58.8058 48.3355 61.1268L50.6316 66.6701C57.7052 63.7401 63.3251 58.1201 66.2551 51.0465L60.7119 48.7504ZM60.7119 31.2475C63.0329 36.851 63.0329 43.1469 60.7119 48.7504L66.2551 51.0465C69.1851 43.9729 69.1851 36.025 66.2551 28.9514L60.7119 31.2475ZM55.0928 23.1926C57.5044 25.4181 59.432 28.1577 60.7119 31.2475L66.2551 28.9514C64.6395 25.0509 62.2059 21.5923 59.1619 18.7833L55.0928 23.1926Z"
                      fill="#E5E7EB" />
                    <path
                      d="M42.418 56.5962L42.418 73.4038C42.418 75.0999 40.3673 75.9493 39.168 74.75L31.5393 67.1213C30.3677 65.9497 30.3677 64.0503 31.5393 62.8787L39.168 55.25C40.3673 54.0507 42.418 54.9001 42.418 56.5962Z"
                      fill="#E5E7EB" stroke="#E5E7EB" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
                    <path
                      d="M29.4931 16.1016L30.6411 18.8732L30.6411 18.8732L29.4931 16.1016ZM36.7922 17.2807C38.4383 17.0924 39.6201 15.6052 39.4317 13.9591C39.2434 12.313 37.7563 11.1313 36.1101 11.3196L36.7922 17.2807ZM36.1294 11.3174C34.4831 11.5046 33.3004 12.991 33.4876 14.6372C33.6749 16.2835 35.1612 17.4662 36.8074 17.279L36.1294 11.3174ZM36.8872 17.27C38.534 17.0886 39.722 15.6064 39.5405 13.9595C39.3591 12.3126 37.8769 11.1247 36.23 11.3061L36.8872 17.27ZM15.4931 30.1016L18.2647 31.2496L15.4931 30.1016ZM15.4931 49.9006L12.7214 51.0486L12.7214 51.0486L15.4931 49.9006ZM19.8147 61.2167C21.0323 62.3404 22.9303 62.2642 24.0539 61.0466C25.1776 59.829 25.1014 57.931 23.8838 56.8074L19.8147 61.2167ZM30.6411 18.8732C32.6253 18.0513 34.6961 17.5205 36.7922 17.2807L36.1101 11.3196C33.4639 11.6224 30.8495 12.2925 28.345 13.3299L30.6411 18.8732ZM36.8074 17.279C36.834 17.2759 36.8606 17.273 36.8872 17.27L36.23 11.3061C36.1965 11.3098 36.1629 11.3136 36.1294 11.3174L36.8074 17.279ZM18.2647 31.2496C20.5857 25.6462 25.0377 21.1942 30.6411 18.8732L28.345 13.3299C21.2714 16.2599 15.6514 21.8799 12.7214 28.9535L18.2647 31.2496ZM18.2647 48.7525C15.9437 43.149 15.9437 36.8531 18.2647 31.2496L12.7214 28.9535C9.79143 36.0271 9.79143 43.975 12.7214 51.0486L18.2647 48.7525ZM23.8838 56.8074C21.4722 54.5819 19.5445 51.8423 18.2647 48.7525L12.7214 51.0486C14.3371 54.9491 16.7707 58.4077 19.8147 61.2167L23.8838 56.8074Z"
                      fill="#E5E7EB" />
                    <path
                      d="M36.5586 23.4038L36.5586 6.59619C36.5586 4.90008 38.6093 4.05067 39.8086 5.25L47.4373 12.8787C48.6088 14.0503 48.6088 15.9497 47.4373 17.1213L39.8086 24.75C38.6093 25.9493 36.5586 25.0999 36.5586 23.4038Z"
                      fill="#E5E7EB" stroke="#E5E7EB" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Fabricator Name -->
          <div class="space-y-2">
            <label for="name" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-200">Fabricator
              Name</label>
            <input id="name" type="text"
              class="input-style w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:border-accent-primary-light focus:ring-accent-primary-light transition-all duration-300"
              v-model="customName" placeholder="Name your fabricator" />
          </div>

          <!-- Model -->
          <div class="space-y-2">
            <label for="model" class="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-200">Model</label>
            <input id="model" type="text"
              class="input-style w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-gray-100 cursor-not-allowed transition-all duration-300"
              disabled :placeholder="selectedFabricator?.description || 'Select a fabricator'" />
          </div>

          <!-- Submit Button -->
          <button type="submit"
            class="w-full bg-accent-primary hover:bg-accent-primary-dark text-white py-3 px-4 rounded-lg transition-all duration-300 disabled:bg-accent-primary-light disabled:cursor-not-allowed shadow-md hover:shadow-lg transform hover:translate-y-[-2px] active:translate-y-0 flex items-center justify-center"
            :class="{ 'animate-pulse disabled:cursor-not-allowed': formSubmitted }"
            :disabled="!selectedFabricator || !customName || formSubmitted" @click="handleSubmit">
            <span v-if="!formSubmitted">Register Fabricator</span>
            <div v-else class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none"
                viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                </path>
              </svg>
              <span>Processing...</span>
            </div>
          </button>
        </div>
      </div>
    </transition>

    <!-- Fabricator Cards List -->
    <transition name="fade-in" appear>
      <div class="md:w-2/3 mt-8 p-4 flex flex-col h-full">
        <h2 class="text-2xl font-bold mb-4 text-dark-primary dark:text-light-primary">
          Registered Fabricators
          <span v-if="fabricatorList.length > 0" class="text-accent-primary ml-2">
            ({{ fabricatorList.length }})
          </span>
        </h2>

        <!-- Scrollable container for fabricator cards -->
        <div class="flex-grow overflow-y-auto rounded-xl bg-light-primary-light dark:bg-dark-primary-light p-4 custom-scrollbar">
          <div v-if="fabricatorList.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <transition-group name="card-fade">
              <FabricatorCard v-for="(fabricator, index) in fabricatorList" :key="fabricator.id"
                :name="fabricator.name || ''" :model="fabricator.description"
                :date="fabricator.date ? fabricator.date : ''" :id="fabricator.id || 0"
                :style="{ animationDelay: `${index * 0.05}s` }" @deregistered="handleFabricatorDeleted" />
            </transition-group>
          </div>
          <div v-else class="flex items-center justify-center h-full">
            <p class="text-gray-500 dark:text-gray-400 text-center py-12">
              No fabricators registered yet. Register a fabricator to see it here.
            </p>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* Animations */
.slide-in-left-enter-active {
  transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.slide-in-left-enter-from {
  transform: translateX(-50px);
  opacity: 0;
}

.slide-in-left-enter-to {
  transform: translateX(0);
  opacity: 1;
}

.fade-in-enter-active {
  transition: all 0.6s ease;
}

.fade-in-enter-from {
  opacity: 0;
}

.fade-in-enter-to {
  opacity: 1;
}

.card-fade-enter-active,
.card-fade-leave-active {
  transition: all 0.4s ease;
}

.card-fade-enter-from,
.card-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Custom scrollbar */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 20px;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.7;
  }
}

.animate-pulse {
  animation: pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Rotation animation for refresh button */
@keyframes full-rotation {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.rotating {
  animation: full-rotation 0.8s cubic-bezier(0.4, 0.2, 0.2, 1) forwards;
}
</style>