<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <Navbar />
  <RouterView class="min-h-screen h-full bg-light-primary dark:bg-dark-primary"/>
</template>
