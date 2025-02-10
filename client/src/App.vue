<script setup lang="ts">
import 'bootstrap/dist/js/bootstrap.bundle'
import '@cyhnkckali/vue3-color-picker/dist/style.css'
import "@/assets/main.css"
import { RouterView } from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import { onMounted } from 'vue';
import {setupSockets} from '@/model/sockets';
import {useRetrievePrintersInfo, printers} from '@/model/ports';
import {isLoading, setupTimeSocket} from '@/model/jobs';
import FooterComponent from './components/FooterComponent.vue'

const { retrieveInfo } = useRetrievePrintersInfo();

onMounted(async () => {
  printers.value = await retrieveInfo()

  // sockets
  setupSockets(printers.value)
  setupTimeSocket(printers.value)
})
</script>

<template>
    <transition name="fade">
        <div v-if="isLoading" class="modal fade show d-block" id="loadingModal" tabindex="-1"
             aria-labelledby="loadingModalLabel" aria-hidden="true"
             style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100%; height: 100%; overflow-y: hidden;">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-body d-flex justify-content-center align-items-center"
                     style="user-select: none; position: relative;">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </div>
        </div>
    </transition>

    <nav style="padding-bottom: 2.5rem;">
        <NavBar/>
    </nav>
    <div class="">
        <RouterView/>
    </div>
    <FooterComponent/>
</template>

<style scoped></style>