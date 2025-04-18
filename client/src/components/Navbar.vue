<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import ToggleMode from '@/components/ToggleMode.vue';

// State for mobile menu
const isOpen = ref(false);

const navigationItems = ref([
    { name: 'Dashboard', route: '/' },
    { name: 'Registration', route: '/register' },
    { name: 'Queues', route: '/queue' },
    { name: 'Job History', route: '/history' },
    { name: 'Logger', route: '/errors' },
]);

// Get current route
const route = useRoute();

// Function to check if route is active
const isActive = (path: string) => {
    return route.path === path;
};

// Close mobile menu when window is resized
onMounted(() => {
    const handleResize = () => {
        if (window.innerWidth >= 1024 && isOpen.value) {
            isOpen.value = false;
        }
    };

    window.addEventListener('resize', handleResize);

    return () => {
        window.removeEventListener('resize', handleResize);
    };
});
</script>

<template>
    <nav class="bg-white drop-shadow-sm shadow-lg dark:bg-dark-primary-light text-white">
        <div class="mx-auto pl-2 pr-4 sm:pr-6 lg:pr-8">
            <div class="flex h-16 items-center justify-between">
                <div class="flex items-center space-x-6">
                    <!-- Logo -->
                    <div className="flex-shrink-0 flex items-center">
                        <router-link to="/">
                            <img class="h-12 w-auto" src="@/assets/images/QView3Dlogo.png" alt="Logo" />
                        </router-link>
                    </div>
                </div>

                <!-- Navigation Links-->
                <div class="hidden mx-5 mb-3 lg:flex lg:items-center">
                    <div class="flex space-x-8">
                        <router-link v-for="(item, index) in navigationItems" :key="index" :to="item.route" :class="[
                            'inline-flex items-center px-1 pt-1 border-b-2 text-xl font-semibold transition-colors duration-200 ease-in-out',
                            isActive(item.route)
                                ? 'border-b-2 border-[#7561A9] text-[#7E66B9]'
                                : 'border-transparent text-gray-700 hover:text-[#7561A9] hover:border-gray-500 dark:hover:border-white dark:text-white'
                        ]" aria-current="page">
                            {{ item.name }}
                        </router-link>
                    </div>
                </div>

                <!-- Toggle Mode and Mobile Menu Button -->
                <div class="flex items-center ml-auto">
                    <!-- Toggle always visible -->
                    <ToggleMode class="mr-3" />

                    <!-- Divider Line -->
                    <div class="lg:hidden h-8 w-px bg-gray-300 mr-3"></div>

                    <!-- Mobile menu button -->
                    <div class="lg:hidden">
                        <button @click="isOpen = !isOpen"
                            class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-[#7561A9] hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-[#7561A9]"
                            :aria-expanded="isOpen">
                            <span class="sr-only">Open main menu</span>
                            <!-- If menu is opened, show X icon -->
                            <svg v-if="isOpen" class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none"
                                viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            <!-- If menu is closed, show hamburger icon -->
                            <svg v-else class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none"
                                viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Mobile menu dropdown -->
        <div v-if="isOpen" class="lg:hidden">
            <div class="pt-2 pb-3 space-y-1">
                <router-link v-for="(item, index) in navigationItems" :key="index" :to="item.route" :class="[
                    'block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors duration-200 ease-in-out',
                    isActive(item.route)
                        ? 'border-[#7561A9] text-[#7E66B9] bg-purple-50 dark:bg-gray-700 dark:hover:bg-gray-700'
                        : 'border-transparent text-gray-800 hover:bg-purple-50 hover:border-gray-300 hover:text-[#7E66B9] dark:text-gray-100 dark:hover:bg-gray-700'
                ]">
                    {{ item.name }}
                </router-link>
            </div>
        </div>
    </nav>
</template>

<style scoped></style>