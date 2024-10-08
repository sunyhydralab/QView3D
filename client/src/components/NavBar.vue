<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue';
import {useRoute} from 'vue-router';
import {api, socket, API_PORT, API_IP_ADDRESS} from '@/model/myFetch';

const route = useRoute();

const isSubmitRoute = computed(() => route.path.startsWith('/submit'));

const clientVersion = import.meta.env.VITE_CLIENT_VERSION as string;
const serverVersion = ref<string | null>(null);
const ping = ref<number | null>(null);

async function refreshServerConnection() {
    try {
        serverVersion.value = await api('serverVersion');
    } catch (e) {
        console.error('Failed to connect to server');
        serverVersion.value = null;
        ping.value = null;
    }

    socket.value.on('connect', () => {
        console.log('Connected to socket');
        measurePing();
    });

    socket.value.on('disconnect', () => {
        ping.value = null;
    });
}

async function measurePing() {
    const startTime = Date.now();
    socket.value.emit('ping');

    socket.value.once('pong', () => {
        ping.value = Date.now() - startTime;
    });

}

onMounted(async () => {
    await refreshServerConnection();
    setInterval(measurePing, 10000);
});

watch([API_IP_ADDRESS, API_PORT], async () => {
    await refreshServerConnection();
});
</script>

<template>
    <div style="position: sticky; top: 0;">
        <nav class="navbar navbar-expand-lg thick">
            <div class="navbar-brand">
                <router-link to="/" class="navbar-brand">
                    <img class="logo" src="../assets/QView3D.svg" alt="QView3D Logo">
                </router-link>
                <div class="client-version">v{{ clientVersion }} (v{{ serverVersion }}-serv)</div>
                <div class="ping">Ping: {{ ping }} ms</div>
            </div>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                    aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse justify-content-end" id="navbarNav" style="padding-right: 1rem;">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <router-link to="/" class="nav-link" active-class="active-tab">HOME</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/queue" class="nav-link" active-class="active-tab">QUEUES</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/registration" class="nav-link" active-class="active-tab">REGISTRATION
                        </router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/submit" class="nav-link" :class="{ 'active-tab': isSubmitRoute }">SUBMIT JOB
                        </router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/history" class="nav-link" active-class="active-tab">JOB HISTORY</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/error" class="nav-link" active-class="active-tab">ERROR LOG</router-link>
                    </li>
                </ul>
            </div>
        </nav>
    </div>
</template>

<style scoped>

.logo {
    height: 100px;
    position: relative;
    right: 60px;
    margin-bottom: -2rem;
    margin-top: -1rem;;
}

.navbar {
    background: var(--color-background-mute);
}
.nav-link {
    font-size: 1.2em;
    font-weight: bold;
    color: var(--color-nav-text);
    padding-right: 1.5rem !important;
}

.nav-link:hover {
    color: var(--color-nav-text-hover);
}


.form-check {
    padding-right: 20px;
}

.btn {
    margin-right: 3%;
}

.navbar-brand,
.navbar-dropdown {
    margin-left: 2%;
}

.thick {
    border-bottom: 2px solid var(--color-background-soft);
    box-shadow: 0 2px 6px -2px var(--vt-c-black);
}

.active-tab {
    color: var(--color-nav-text-active) !important;
    font-weight: bolder;
}

body {
    margin: 0;
    padding: 0;
}

.client-version {
    font-size: 0.65em;
    color: var(--color-background-font);
    margin-top: 0.5rem;
    text-align: center;
    position: relative;
    right: 60px;
}

.ping {
    font-size: 0.65em;
    color: var(--color-background-font);
    margin-top: 0.5rem;
    text-align: center;
    position: relative;
    right: 60px;
}
</style>