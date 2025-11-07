import { ref, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'
import { API_URL } from '@/composables/useIPSettings'
import { addToast } from '@/components/Toast.vue'

// Create a reactive socket instance reference
export const socket = ref<Socket | null>(null)
export const isConnected = ref(false)

// Connect to the socket server - returns a Promise that resolves when connected
export function connectSocket(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (socket.value && socket.value.connected) {
      console.log('Socket already connected')
      resolve()
      return
    }

    console.log(`Attempting socket connection to ${API_URL.value}`)

    // Create the socket connection with improved resilience
    socket.value = io(API_URL.value, {
      reconnectionAttempts: 3,
      reconnectionDelay: 2000,
      reconnectionDelayMax: 10000,
      timeout: 10000,
      transports: ['websocket', 'polling'], // Try both transports
    })

    // Connection events
    socket.value.off('connect')
    socket.value.on('connect', () => {
      console.log('Socket connected:', socket.value?.id)
      isConnected.value = true
      addToast('Connected to server', 'success')
      resolve() // Resolve the promise when connected
    })

    // Handle connection error
    socket.value.off('connect_error')
    socket.value.once('connect_error', (error) => {
      console.error('Socket connection error:', error)
      addToast(`Connection error: ${error.message}`, 'error')
      reject(error) // Reject the promise on connection error
    })

    socket.value.off('disconnect')
    socket.value.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason)
      isConnected.value = false
      addToast('Disconnected from server', 'warning')
    })

    socket.value.on('connect_error', (error) => {
      console.error('Socket connection error:', error)
      addToast(`Connection error: ${error.message}`, 'error')
    })

    socket.value.off('reconnect_attempt')
    socket.value.on('reconnect_attempt', (attemptNumber) => {
      console.log(`Socket reconnection attempt ${attemptNumber}`)
      addToast(`Reconnecting to server (attempt ${attemptNumber})`, 'info')
    })

    socket.value.off('reconnect_failed')
    socket.value.on('reconnect_failed', () => {
      console.error('Socket reconnection failed')
      addToast('Failed to reconnect to server', 'error')
    })

    // Add a timeout for initial connection
    setTimeout(() => {
      if (!isConnected.value) {
        reject(new Error('Socket connection timeout'))
      }
    }, 10000) // 10 second timeout
  })
}

// Disconnect from the socket server
export function disconnectSocket() {
  if (socket.value) {
    socket.value.disconnect()
    socket.value = null
    isConnected.value = false
  }
}

// Custom composable to use socket in components
export function useSocket() {
  // Connect when component is mounted (no need to await here since app already connects)
  connectSocket().catch(error => {
    console.error('Failed to connect socket in useSocket:', error)
  })

  // Disconnect when component is unmounted
  onUnmounted(() => {
    // Don't disconnect the shared socket when component unmounts
    // The socket should stay connected for the entire app lifecycle
  })

  return {
    socket,
    isConnected,
  }
}

// Generic event subscription helper
export function onSocketEvent<T>(event: string, callback: (data: T) => void) {
  // Ensure socket is connected
  if (!socket.value) {
    console.warn(`Socket not connected when setting up listener for '${event}'. Attempting to connect...`)
    connectSocket().catch(error => {
      console.error(`Failed to connect socket for event '${event}':`, error)
    })
  }

  // Set up the event listener if socket exists
  if (socket.value) {
    socket.value.off(event) // Remove any existing listeners for the event
    socket.value.on(event, callback)
  }

  // Return unsubscribe function
  return () => {
    socket.value?.off(event, callback)
  }
}

// Generic event emitter helper
export function emitSocketEvent<T>(event: string, data?: T) {
  if (!socket.value) {
    connectSocket()
  }
  
  socket.value?.emit(event, data)
}
