<script setup lang="ts">
import "./assets/base.css"
import 'bootstrap/dist/js/bootstrap.bundle'
import {RouterView} from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import ThemePanel from '@/components/ThemePanel.vue'
import {onMounted, nextTick, watch} from 'vue';
import {
    setupPortRepairSocket,
    setupErrorSocket,
    setupJobStatusSocket,
    setupPauseFeedbackSocket,
    setupProgressSocket,
    setupQueueSocket,
    setupReleaseSocket,
    setupStatusSocket,
    setupTempSocket,
    setupGCodeViewerSocket,
    setupExtrusionSocket,
    setupCurrentLayerHeightSocket,
    setupMaxLayerHeightSocket
} from '@/model/sockets';
import {useRetrievePrintersInfo, printers} from '@/model/ports';
import {setupTimeSocket, isLoading} from '@/model/jobs';
import SettingsPanel from "@/components/SettingsPanel.vue";

const { retrieveInfo } = useRetrievePrintersInfo();

onMounted(async () => {
    printers.value = await retrieveInfo()

    // sockets
    setupStatusSocket(printers)
    setupQueueSocket(printers)
    setupProgressSocket(printers)
    setupJobStatusSocket(printers)
    setupErrorSocket(printers)
    setupTimeSocket(printers)
    setupTempSocket(printers)
    setupGCodeViewerSocket(printers)
    setupPauseFeedbackSocket(printers) //not sure if needed
    setupReleaseSocket(printers)
    setupPortRepairSocket(printers)
    setupExtrusionSocket(printers)
    setupMaxLayerHeightSocket(printers)
    setupCurrentLayerHeightSocket(printers)
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
    <ThemePanel/>
    <SettingsPanel/>
</template>

<style scoped></style>