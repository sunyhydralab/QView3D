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


const observer = new MutationObserver(() => {
    const colorPrimary = getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary').trim();
    const colorSecondary = getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary').trim();

    const svgElementPrimary = document.getElementById('cls-1');

    if (svgElementPrimary) {
        svgElementPrimary.style.fill = colorPrimary;
    }

    const svgElementSecondary = document.getElementById('cls-2');

    if (svgElementSecondary) {
        svgElementSecondary.style.stroke = colorSecondary;
    }
});

observer.observe(document.documentElement, {attributes: true, attributeFilter: ['style']});

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
                    <svg id="Layer_1" xmlns="http://www.w3.org/2000/svg" viewBox="25 25 620 288">
                        <path class="cls-2"
                              d="M289.85,99.17l-25.61,74.4h-20.83l-25.61-74.4h23.17l5.42,19.98c2.55,9.25,6.16,24.34,7.55,31.46,1.38-7.12,5-22.11,7.55-31.46l5.42-19.98h22.96Z"/>
                        <path class="cls-2"
                              d="M317.07,104.27c0,5.85-4.57,9.46-11.16,9.46s-10.95-3.61-10.95-9.46c0-5.42,4.68-9.25,10.95-9.25,6.59,0,11.16,3.83,11.16,9.25ZM315.47,173.57h-19.13v-55.8h19.13v55.8Z"/>
                        <path class="cls-2"
                              d="M373.1,147.43c0,1.59,0,2.76-.11,3.72h-32.74c.64,6.17,4.25,8.93,9.46,8.93,4.89,0,8.93-1.06,14.46-3.93l7.33,12.22c-6.91,4.04-14.03,6.38-22.74,6.38-16.79,0-26.04-11.9-26.04-29.02,0-19.24,10.84-29.12,25.51-29.12s24.87,10.1,24.87,30.82ZM356.2,139.24c-.96-5.63-2.87-8.5-8.5-8.5-4.36,0-6.8,2.98-7.44,8.5h15.94Z"/>
                        <path class="cls-2"
                              d="M450.06,117.77l-15.73,55.8h-15.52l-2.34-11.37c-1.28-6.38-3.51-18.71-4.15-22.74-.74,4.04-2.87,16.26-4.25,22.96l-2.34,11.16h-15.09l-15.73-55.8h18.49l1.59,8.29c1.28,6.38,2.98,18.71,3.61,22.74.74-4.04,2.87-16.26,4.36-22.96l1.81-8.08h15.73l1.7,8.08c1.38,6.7,3.61,18.92,4.36,22.96.64-4.04,2.55-16.37,3.72-22.74l1.49-8.29h18.28Z"/>
                        <path class="cls-1"
                              d="M521.36,149.98c0,17.22-12.44,24.76-32.63,24.76-12.65,0-23.38-4.36-31.35-11.37l10.63-13.39c6.06,4.68,12.97,7.76,21.15,7.76,8.61,0,12.22-2.44,12.22-7.55s-2.98-7.12-10.52-7.12h-10.73v-16.05h9.57c6.48,0,8.61-1.38,8.61-6.27,0-3.93-2.98-6.06-10.31-6.06s-12.75,2.23-18.49,6.38l-9.78-13.39c6.91-5.31,15.84-9.67,28.8-9.67,17.86,0,29.76,5.63,29.76,21.36,0,8.18-4.78,12.12-9.89,14.56,6.91,1.59,12.97,6.59,12.97,16.05Z"/>
                        <path class="cls-1"
                              d="M592.08,135.95c0,27.95-13.82,37.63-40.18,37.63h-24.13v-74.4h26.04c23.38,0,38.26,8.82,38.26,36.77ZM570.92,136.27c0-13.71-4.36-19.45-17.22-19.45h-5.1v39.11h4.46c12.86,0,17.86-4.89,17.86-19.66Z"/>
                        <path class="cls-2"
                              d="M214.71,180.77l-11.61-15.26c6.4-7.47,10.27-17.16,10.27-27.76,0-23.59-19.13-42.72-42.72-42.72s-42.72,19.13-42.72,42.72,19.13,42.72,42.72,42.72c4.82,0,9.45-.81,13.78-2.28l11.07,14.79,19.21-12.2ZM189.45,140.34c1.35-.33,7.9,1.37,8.48,2.52.46.91-6.52,14.39-7.57,14.46-.95.06-6.56-4.32-6.9-5.53-.35-1.25,5.04-11.21,5.99-11.45ZM183.45,123.78c.5-1.3,5.63-5.72,6.9-5.53,1.01.15,8.11,13.56,7.57,14.46-.49.81-7.28,2.93-8.48,2.52-1.23-.42-6.34-10.53-5.99-11.45ZM162.55,111.22c.6-.83,15.77-.9,16.32,0,.49.81-.78,7.81-1.7,8.68-.94.89-12.27.73-12.92,0-.92-1.04-2.45-7.64-1.7-8.68ZM157.83,151.79c-.34,1.22-5.96,5.59-6.9,5.53-1.05-.07-8.03-13.55-7.57-14.46.57-1.15,7.13-2.85,8.48-2.52.95.23,6.35,10.2,5.99,11.45ZM151.84,135.23c-1.19.41-7.99-1.71-8.48-2.52-.54-.9,6.56-14.31,7.57-14.46,1.27-.18,6.4,4.24,6.9,5.53.35.91-4.77,11.02-5.99,11.45ZM178.87,164.27c-.55.9-15.72.83-16.32,0-.75-1.04.78-7.64,1.7-8.68.65-.73,11.98-.89,12.92,0,.92.87,2.19,7.87,1.7,8.68ZM170.64,146.43c-4.8,0-8.69-3.89-8.69-8.69s3.89-8.69,8.69-8.69,8.69,3.89,8.69,8.69-3.89,8.69-8.69,8.69Z"/>
                    </svg>
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
    color: var(--color-nav-text);
    margin-top: 0.5rem;
    text-align: center;
    position: relative;
    margin-left: -60px
}

.ping {
    font-size: 0.65em;
    color: var(--color-nav-text);

    text-align: center;
    position: relative;
    margin-left: -60px;
}

svg .cls-1 {
    fill: var(--color-primary);
    stroke: var(--color-primary-font)
}

svg .cls-2 {
    fill: var(--color-secondary);
    stroke: var(--color-secondary-font)
}

svg {
    width: 233px;
    height: 108px;
    margin-right: 10px;
    margin-top: -25px;
    margin-bottom: -48px;
    margin-left: -60px;
}
</style>