<script setup lang="ts">
import { api } from '@/model/ports';
import { ref } from 'vue';

const message = ref('');
const loading = ref(false);
const isRegistered = ref(false);

const registerPrinter = async () => {
    loading.value = true;
    message.value = '';

    try {
        const response = await api('api/registeremulator', { 'data': 'wow' }, 'POST');
        
        if (response && response.message) {
            message.value = response.message;
            isRegistered.value = true;
        } else if (response && response.error) {
            message.value = response.error;
        } else {
            message.value = 'Unknown response structure';
        }
    } catch (error) {
        message.value = 'Error registering emulator';
    } finally {
        loading.value = false;
    }
}

const disconnectPrinter = async () => {
    loading.value = true;
    message.value = '';

    try {
        const response = await api('api/disconnectemulator', { 'data': 'wow' }, 'POST');
        
        if (response && response.message) {
            message.value = response.message;
            isRegistered.value = false;
        } else if (response && response.error) {
            message.value = response.error;
        } else {
            message.value = 'Unknown response structure';
        }
    } catch (error) {
        message.value = 'Error disconnecting emulator';
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <div class="container mt-5">
        <!-- Heading Section -->
        <h1 class="text-center mb-4">Emulator Registration</h1>
        
        <!-- Card for the form -->
        <div class="card shadow-sm">
            <div class="card-body">
                <h5 class="card-title">Emulator Control</h5>
                <p class="card-text">
                    Click the button below to either register or disconnect the emulator.
                </p>
                
                <!-- Register Button (only visible if the printer is not registered) -->
                <div class="d-grid gap-2">
                    <button 
                        class="btn btn-primary" 
                        @click="registerPrinter"
                        :disabled="loading || isRegistered"
                    >
                        Register Emulator
                    </button>
                </div>
                
                <!-- Disconnect Button (only visible if the printer is registered) -->
                <div class="d-grid gap-2 mt-2">
                    <button 
                        class="btn btn-danger" 
                        @click="disconnectPrinter"
                        :disabled="loading || !isRegistered"
                    >
                        Disconnect Emulator
                    </button>
                </div>
                
                <!-- Loading Spinner -->
                <div v-if="loading" class="text-center my-3">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
                
                <!-- Message Section -->
                <div v-if="message" class="mt-3">
                    <div :class="['alert', message.startsWith('Error') ? 'alert-danger' : 'alert-success']" role="alert">
                        <strong>{{ message.startsWith('Error') ? 'Oops!' : 'Success!' }}</strong> {{ message }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* You can add additional custom styling here if needed */
</style>
