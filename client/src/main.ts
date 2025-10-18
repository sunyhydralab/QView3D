import { setModeToSystem } from './composables/useMode'
import { setupSockets } from '@/composables/useWebSockets.ts'
import { retrieveRegisteredFabricators } from '@/models/fabricator.ts'
import './assets/base.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import '@fortawesome/fontawesome-free/css/all.css';
import { connectSocket } from './services/socket'

async function initializeApp() {
  // Set the mode on app start
  setModeToSystem()

  // Initialize socket connection
  connectSocket()

  // Setup WebSockets with await inside async function
  const fabricators = await retrieveRegisteredFabricators()
  setupSockets(fabricators)

  // Create and mount the app
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
}

// Call the async initialization function
initializeApp().catch((error) => {
  console.error('Failed to initialize app:', error)
})
