<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
</script>

<template>
      <nav>
        <NavBar />
      </nav>
      <div class="">
      <RouterView />
    </div>
</template>

<style scoped>
</style>
