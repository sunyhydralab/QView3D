import { setModeToSystem } from './composables/useMode'
import { setupSockets } from '@/composables/useWebSockets.ts'
import { retrieveRegisteredFabricators } from '@/models/fabricator.ts'
import './assets/base.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import '@fortawesome/fontawesome-free/css/all.css';
import { connectSocket } from './services/socket'

// Set the mode on app start
setModeToSystem()

// Initialize socket connection
connectSocket()

// Setup WebSockets
setupSockets(await retrieveRegisteredFabricators())

const app = createApp(App)
app.use(router)
app.mount('#app')
