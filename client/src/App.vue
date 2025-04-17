<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <Navbar />
  <RouterView class="h-screen bg-gray-200 dark:bg-gray-900"/>
</template>

<style scoped></style>
