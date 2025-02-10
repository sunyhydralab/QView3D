<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import ThemePanel from './ThemePanel.vue'
import SettingsPanel from './SettingsPanel.vue'
import { api, socket, API_PORT, API_IP_ADDRESS } from '@/model/myFetch'

const clientVersion = import.meta.env.VITE_CLIENT_VERSION as string
const serverVersion = ref<string | null>(null)
const ping = ref<number | null>(null)

async function refreshServerConnection() {
  try {
    serverVersion.value = await api('serverVersion')
  } catch (e) {
    console.error('Failed to connect to server')
    serverVersion.value = null
    ping.value = null
  }

  socket.value.on('connect', () => {
    console.debug('Connected to socket')
    measurePing()
  })

  socket.value.on('disconnect', () => {
    ping.value = null
  })
}

async function measurePing() {
  const startTime = Date.now()
  socket.value.emit('ping')

  socket.value.once('pong', () => {
    ping.value = Date.now() - startTime
  })
}

onMounted(async () => {
  await refreshServerConnection()
  setInterval(measurePing, 10000)
})

watch([API_IP_ADDRESS, API_PORT], async () => {
  await refreshServerConnection()
})
</script>

<template>
  <!-- A footer to display the SettingsPanel and ThemePanel components in one file -->
  <div class="client-version">v{{ clientVersion }} (v{{ serverVersion }}-serv)</div>
  <div class="ping">Ping: {{ ping }} ms</div>

  <ThemePanel />
  <SettingsPanel />
</template>

<style scoped>
.client-version {
  font-size: 0.9em;
  color: var(--color-nav-text);
  position: fixed;
  bottom: 1rem;
  left: 1rem;
  text-align: left;
  margin: 0;
}
.ping {
  font-size: 0.9em;
  color: var(--color-nav-text);
  position: fixed;
  bottom: 2.2rem; /
  left: 1rem;
  text-align: left;
  margin: 0;
}

.ping {
  margin-top: 0.3rem; /* Adds space between the version and ping */
}
</style>
