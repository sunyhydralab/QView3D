<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <div class="min-h-screen bg-light-primary dark:bg-dark-primary">
    <Navbar />
    <RouterView class="h-full"/>
  </div>
</template>

<style scoped></style>
