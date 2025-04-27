import { setModeToSystem } from './composables/useMode'
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

const app = createApp(App)
app.use(router)
app.mount('#app')
