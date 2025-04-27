import { ref, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'
import { API_URL } from '@/composables/useIPSettings'
import { addToast } from '@/components/Toast.vue'

// Create a reactive socket instance reference
export const socket = ref<Socket | null>(null)
export const isConnected = ref(false)

// Connect to the socket server
export function connectSocket() {
  if (socket.value && socket.value.connected) {
    console.log('Socket already connected')
    return
  }

  // Create the socket connection
  socket.value = io(API_URL.value, {
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 5000,
  })

  // Connection events
  socket.value.off('connect')
  socket.value.on('connect', () => {
    console.log('Socket connected:', socket.value?.id)
    isConnected.value = true
    addToast('Connected to server', 'success')
  })

  socket.value.off('disconnect')
  socket.value.on('disconnect', (reason) => {
    console.log('Socket disconnected:', reason)
    isConnected.value = false
    addToast('Disconnected from server', 'warning')
  })

  socket.value.off('connect_error')
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

  // Return cleanup function
  return () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
      isConnected.value = false
    }
  }
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
  // Connect when component is mounted
  const cleanup = connectSocket()

  // Disconnect when component is unmounted
  onUnmounted(() => {
    if (cleanup) {
      cleanup()
    }
  })

  return {
    socket,
    isConnected,
  }
}

// Generic event subscription helper
export function onSocketEvent<T>(event: string, callback: (data: T) => void) {
  if (!socket.value) {
    connectSocket()
  }

  socket.value?.off(event) // Remove any existing listeners for the event
  socket.value?.on(event, callback)
  
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
