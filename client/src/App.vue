<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <Navbar />
  <RouterView class="h-screen bg-light-primary dark:bg-dark-primary"/>
</template>

<style scoped></style>
