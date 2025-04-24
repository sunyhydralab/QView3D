<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <nav class="fixed top-0 left-0 right-0 z-50shadow-md">
    <Navbar />
  </nav>
  <RouterView class="pt-20 px-10 min-h-screen h-full"/>
</template>
