import { setModeToSystem } from './composables/useMode'
import { setupSockets } from '@/composables/useWebSockets.ts'
import { retrieveRegisteredFabricators } from '@/models/fabricator.ts'
import { migratePortSettings } from '@/utils/portMigration'
import { API_PORT } from '@/composables/useIPSettings'
import './assets/base.css'
import './assets/styles/global.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import '@fortawesome/fontawesome-free/css/all.css';
import { connectSocket } from './services/socket'

async function initializeApp() {
  // Run migration first to ensure correct settings
  migratePortSettings();

  console.log(`Initializing app with API port: ${API_PORT.value}`)

  // Set the mode on app start
  setModeToSystem()

  // Initialize socket connection
  connectSocket()

  // Setup socket event listeners (once during app initialization)
  setupSockets()

  // Fetch initial fabricator data
  await retrieveRegisteredFabricators()

  // Create and mount the app
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
}

// Call the async initialization function
initializeApp().catch((error) => {
  console.error('Failed to initialize app:', error)
})
