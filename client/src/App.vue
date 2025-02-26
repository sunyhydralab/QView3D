<script setup lang="ts">
import 'bootstrap/dist/js/bootstrap.bundle'
import '@cyhnkckali/vue3-color-picker/dist/style.css'
import "@/assets/main.css"
import { RouterView } from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import { onMounted, ref} from 'vue';
import {setupSockets} from '@/model/sockets';
import {useRetrievePrintersInfo, printers} from '@/model/ports';
import {setupTimeSocket} from '@/model/jobs';
import FooterComponent from './components/FooterComponent.vue'
import {watch} from 'vue';
import IsLoading from './components/IsLoading.vue'

const { retrieveInfo } = useRetrievePrintersInfo();
const isLoading = ref(true)

onMounted(async () => {
  printers.value = await retrieveInfo()

  // sockets
  setupSockets(printers.value)
  setupTimeSocket(printers.value)
})

// For updating the frontend when information on the printer changes
watch(printers, (updatedPrinter) => {
  if (updatedPrinter) {
    setupSockets(printers.value)
    setupTimeSocket(printers.value)
  }
})
</script>

<template>
    <IsLoading v-if="isLoading" />
    <nav style="padding-bottom: 2.5rem;">
        <NavBar/>
    </nav>
    <div class="">
        <RouterView/>
    </div>
    <FooterComponent/>
</template>

<style scoped></style>