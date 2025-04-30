<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref, nextTick } from 'vue'
import * as GCodePreview from 'gcode-preview'
import { onSocketEvent } from '@/services/socket'
import { addToast } from '@/components/Toast.vue'
import { isDark } from '@/composables/useMode'

const gcodeString = ref('')
const isLivePreview = ref(true)
const darkMode = isDark()

const props = defineProps<{
  file: File | null;
  jobId?: number;
}>()

const emit = defineEmits(['toggle-live-preview'])

const gcodeCanvas = ref<HTMLCanvasElement | null>(null)
const originalConsoleWarn = console.warn
const originalConsoleInfo = console.info
const originalConsoleDebug = console.debug
let preview: ReturnType<typeof GCodePreview.init> | null = null
let socketCleanup: (() => void) | null = null

onMounted(() => {
  nextTick(() => {
    withoutConsoleWarnings(() => {
      if (gcodeCanvas.value) {
        // Initialize the GCode preview
        preview = GCodePreview.init({
          canvas: gcodeCanvas.value,
          extrusionColor: 'turquoise',
          backgroundColor: 'black',
          buildVolume: { x: 250, y: 210, z: 220 },
          travelColor: 'purple',
          lineWidth: 0.5,
          lineHeight: 0.5,
          extrusionWidth: 0.25,
          renderExtrusion: true,
          renderTravel: false,
          renderTubes: true
        })
      }
      // Setup socket listeners for gcode updates if we have a job ID
      if (props.jobId) {
        setupGcodeSocketListeners(props.jobId)
      }
    })
  })
})

function withoutConsoleWarnings(fn: () => void) {
  console.warn = () => {}
  console.info = () => {}
  console.debug = () => {}
  fn()
  console.warn = originalConsoleWarn
  console.info = originalConsoleInfo
  console.debug = originalConsoleDebug
}

// Toggle live preview mode
function toggleLivePreview() {
  isLivePreview.value = !isLivePreview.value
  emit('toggle-live-preview', isLivePreview.value)
  
  if (!isLivePreview.value && socketCleanup) {
    // If turning off live preview, clean up socket listeners
    socketCleanup()
    socketCleanup = null
  } else if (isLivePreview.value && props.jobId) {
    // If turning on live preview, set up socket listeners
    setupGcodeSocketListeners(props.jobId)
  }
}

// Setup socket listeners for real-time gcode updates
function setupGcodeSocketListeners(jobId: number) {
  // Remove any existing listeners
  if (socketCleanup) {
    socketCleanup()
  }
  
  // Only set up listeners if we're in live preview mode
  if (!isLivePreview.value) return
  
  // Listen for gcode line updates
  const removeGcodeUpdateListener = onSocketEvent<{jobId: number; gcodeLineNumber: number; gcodeData?: string}>('gcode_progress_update', (data) => {
    // Only process updates for our job
    if (data.jobId !== jobId) return
    
    if (data.gcodeData && preview) {
      // If we received new gcode data, accumulate it and update the preview occasionally
      gcodeString.value += data.gcodeData + '\n'
      
      // Update occasionally to avoid too many renders
      if (data.gcodeLineNumber % 20 === 0) {
        preview.processGCode(gcodeString.value)
      }
    }
  })
  
  // Listen for gcode complete updates
  const removeGcodeCompleteListener = onSocketEvent<{jobId: number; gcodeComplete: boolean}>('gcode_complete', (data) => {
    // Only process updates for our job
    if (data.jobId !== jobId) return
    
    if (data.gcodeComplete && preview) {
      // When gcode is complete, do a final update
      preview.processGCode(gcodeString.value)
      addToast('3D preview completed', 'success')
    }
  })
  
  // Store cleanup function
  socketCleanup = () => {
    removeGcodeUpdateListener()
    removeGcodeCompleteListener()
  }
}

// Watch for the file changes and load G-Code string.
watch(() => props.file, (newFile) => {
  if (newFile && preview && gcodeCanvas.value) {
    const reader = new FileReader()
    reader.onload = (event) => {
      gcodeString.value = event.target?.result as string
      if (preview && gcodeString.value) {
        preview.clear()
        preview.processGCode(gcodeString.value)
      }
    }
    reader.readAsText(newFile)
  }
})

// Watch for job ID changes to update socket listeners
watch(() => props.jobId, (newJobId) => {
  if (newJobId) {
    setupGcodeSocketListeners(newJobId)
  } else if (socketCleanup) {
    socketCleanup()
    socketCleanup = null
  }
})

onBeforeUnmount(() => {
  // Clean up the preview
  if (preview) {
    preview.clear()
  }
  
  // Clean up socket listeners
  if (socketCleanup) {
    socketCleanup()
  }
})
</script>

<template>
  <div class="gcode-container">
    <div class="controls">
      <button 
        @click.stop="toggleLivePreview"
        class="control-btn"
        :title="isLivePreview ? 'Disable Live Updates' : 'Enable Live Updates'"
      >
        <i class="fas" :class="isLivePreview ? 'fa-wifi' : 'fa-wifi-slash'"></i>
        <span class="control-text">{{ isLivePreview ? 'Live' : 'Static' }}</span>
      </button>
    </div>
    <canvas ref="gcodeCanvas"></canvas>
  </div>
</template>

<style scoped>
.gcode-container {
  width: 100%;
  height: 100%;
  position: relative;
  min-height: 250px;
}

canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  display: flex;
  gap: 8px;
  transition: opacity 0.2s ease;
}

.control-btn {
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.control-btn:hover {
  background-color: rgba(0, 0, 0, 0.8);
}

.control-text {
  font-size: 0.75rem;
}
</style>
