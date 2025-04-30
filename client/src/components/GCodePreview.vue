<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref, nextTick } from 'vue'
import * as GCodePreview from 'gcode-preview'
import { onSocketEvent } from '@/services/socket'
import { addToast } from '@/components/Toast.vue'
import { isDark } from '@/composables/useMode'

const gcodeString = ref('')
const isLivePreview = ref(false) // Default to static mode
const darkMode = isDark()
const isProcessing = ref(false)

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
        console.log("Initializing GCode preview...");
        // Initialize the GCode preview
        preview = GCodePreview.init({
          canvas: gcodeCanvas.value,
          extrusionColor: 'turquoise',
          backgroundColor: 'black',
          buildVolume: { x: 250, y: 210, z: 220 },
          travelColor: 'purple',
          lineWidth: 1.0,  // Increased line width for better visibility
          lineHeight: 1.0,  // Increased line height
          extrusionWidth: 0.5,  // Increased extrusion width
          renderExtrusion: true,
          renderTravel: true,  // Show travel lines
          renderTubes: true
        })
        
        // If we have a file already, process it
        if (props.file) {
          const reader = new FileReader()
          reader.onload = (event) => {
            gcodeString.value = event.target?.result as string
            if (preview && gcodeString.value) {
              processStaticGCode(gcodeString.value);
            }
          }
          reader.readAsText(props.file)
        }
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

// Process the entire GCode file at once for static display
function processStaticGCode(gcode: string) {
  if (!preview) return;
  
  console.log(`Processing static GCode file with ${gcode.split('\n').length} lines`);
  preview.clear();
  preview.processGCode(gcode);
}

// Process G-code command by command with visual feedback
async function processGCodeProgressively(gcode: string) {
  if (!preview) return;
  isProcessing.value = true;
  
  try {
    // For static mode, just process the entire file at once
    if (!isLivePreview.value) {
      processStaticGCode(gcode);
      isProcessing.value = false;
      return;
    }
    
    // For live mode, process progressively
    preview.clear();
    const commands = gcode.split('\n').filter(cmd => !cmd.trim().startsWith(';'));
    console.log(`Processing ${commands.length} commands progressively...`);
    
    // First pass - process the entire file to get the model rendered quickly
    preview.processGCode(gcode);
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Then do the progressive rendering for animation effect
    for (let i = 0; i < commands.length; i += 10) {
      if (!isLivePreview.value) {
        // If switched to static mode during processing, stop progressive rendering
        processStaticGCode(gcode);
        break;
      }
      
      // Process a chunk of commands at once for better performance
      const endIdx = Math.min(i + 10, commands.length);
      const chunk = commands.slice(i, endIdx).join('\n');
      preview.processGCode(chunk);
      
      // Only pause occasionally to speed up rendering
      if (i % 100 === 0) {
        await new Promise(resolve => setTimeout(resolve, 5));
      }
    }
  } catch (error) {
    console.error('Error in progressive processing:', error);
    // Fallback to processing the entire file at once
    if (preview) {
      processStaticGCode(gcode);
    }
  }
  
  isProcessing.value = false;
}

// Toggle live preview mode
function toggleLivePreview() {
  isLivePreview.value = !isLivePreview.value
  emit('toggle-live-preview', isLivePreview.value)
  
  if (!isLivePreview.value && socketCleanup) {
    // If turning off live preview, clean up socket listeners
    socketCleanup()
    socketCleanup = null
    
    // Process the whole file at once in static mode
    if (gcodeString.value && preview) {
      processStaticGCode(gcodeString.value);
    }
  } else if (isLivePreview.value && props.jobId) {
    // If turning on live preview, set up socket listeners
    setupGcodeSocketListeners(props.jobId)
    
    // If we have gcode data and toggling to live preview, process it progressively
    if (gcodeString.value && preview) {
      processGCodeProgressively(gcodeString.value);
    }
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
  
  console.log(`Setting up socket listeners for job ID: ${jobId}`);
  
  // Listen for gcode line updates
  const removeGcodeUpdateListener = onSocketEvent<{jobId: number; gcodeLineNumber: number; gcodeData?: string}>('gcode_progress_update', (data) => {
    // Only process updates for our job
    if (data.jobId !== jobId) return
    
    if (data.gcodeData && preview) {
      console.log(`Received gcode update for line ${data.gcodeLineNumber}`);
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
      console.log('GCode processing complete, rendering final result');
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
    console.log(`Processing new file: ${newFile.name}`);
    const reader = new FileReader()
    reader.onload = (event) => {
      gcodeString.value = event.target?.result as string
      console.log(`Loaded GCode file with ${gcodeString.value.split('\n').length} lines`);
      
      if (preview && gcodeString.value) {
        if (isLivePreview.value) {
          // Process progressively in live mode
          processGCodeProgressively(gcodeString.value);
        } else {
          // Process all at once in static mode
          processStaticGCode(gcodeString.value);
        }
      }
    }
    reader.readAsText(newFile)
  } else {
    console.log("Missing required data for file processing:", { 
      file: !!newFile, 
      preview: !!preview, 
      canvas: !!gcodeCanvas.value 
    });
  }
})

// Watch for job ID changes to update socket listeners
watch(() => props.jobId, (newJobId) => {
  if (newJobId) {
    console.log(`Job ID changed to ${newJobId}, setting up socket listeners`);
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
        :title="isLivePreview ? 'Switch to Static Mode' : 'Switch to Live Mode'"
        :disabled="isProcessing"
      >
        <i class="fas" :class="isLivePreview ? 'fa-wifi' : 'fa-wifi-slash'"></i>
        <span class="control-text">{{ isLivePreview ? 'Live' : 'Static' }}</span>
        <span v-if="isProcessing" class="loading-indicator ml-1">
          <i class="fas fa-spinner fa-spin"></i>
        </span>
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
  z-index: 1000; /* Increased z-index to ensure visibility */
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

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-indicator {
  font-size: 0.8rem;
}

.ml-1 {
  margin-left: 0.25rem;
}

.control-text {
  font-size: 0.75rem;
}
</style>
