<script setup lang="ts">
import {ref} from 'vue';
import {API_IP_ADDRESS, API_PORT, setServerIP, setServerPort} from '@/model/myFetch';

const serverIP = ref<string>(API_IP_ADDRESS.value ?? '127.0.0.1');
const serverPort = ref<number>(Number(API_PORT.value ?? 8000));

const saveSettings = () => {
    setServerIP(serverIP.value);
    setServerPort(serverPort.value);
    console.log(`Server IP: ${serverIP.value}, Server Port: ${serverPort.value}`);
};
</script>

<template>
    <div>
        <div class="offcanvas offcanvas-end" tabindex="-1" id="settingsOffcanvas">
            <div class="offcanvas-header">
                <h5 class="offcanvas-title">Server Settings</h5>
                <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
            </div>
            <div class="offcanvas-body">
                <form @submit.prevent="saveSettings">
                    <div class="form-group">
                        <label for="ip">Server IP:</label>
                        <input type="text" id="ip" v-model="serverIP" required/>
                    </div>
                    <div class="form-group">
                        <label for="port">Server Port:</label>
                        <input type="number" id="port" v-model="serverPort" required/>
                    </div>
                    <button type="submit" class="btn btn-secondary">Save</button>
                </form>
            </div>
        </div>
    </div>

    <div class="position-fixed end-0 m-3" style="bottom:3rem">
        <button class="btn btn-secondary" data-bs-toggle="offcanvas" data-bs-target="#settingsOffcanvas">
            <i class="fas fa-gear"></i>
        </button>
    </div>
</template>

<style scoped>
.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
}

input {
    width: 100%;
    padding: 8px;
    border: 1px solid var(--color-border);
    border-radius: 4px;
}
</style>