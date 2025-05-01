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
let layers: string[][] = [] // Store layers for layer-based rendering

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
        // Initialize the GCode preview with improved settings
        preview = GCodePreview.init({
          canvas: gcodeCanvas.value,
          extrusionColor: 'turquoise',
          backgroundColor: 'black',
          buildVolume: { x: 250, y: 210, z: 220 },
          travelColor: 'limegreen', // Changed to limegreen for better visibility
          lineWidth: 1.5,          // Increased for better visibility
          lineHeight: 1.5,         // Increased for better visibility
          extrusionWidth: 1.0,     // Increased for better visibility
          renderExtrusion: true,
          renderTravel: true,      // Enabled travel lines by default
          renderTubes: true
        });
        
        // Set the camera position explicitly for better view
        if (preview && preview.camera) {
          preview.camera.position.set(-200, 232, 200);
          preview.camera.lookAt(0, 0, 0);
        }
        
        // If we have a file already, process it
        if (props.file) {
          processFile(props.file);
        }
      }
      
      // Setup socket listeners for gcode updates if we have a job ID
      if (props.jobId) {
        setupGcodeSocketListeners(props.jobId);
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

// Function to extract layers from GCode
function extractLayers(gcode: string): string[][] {
  const lines = gcode.split('\n');
  return lines.reduce((layers, line) => {
    // Check for layer change markers - using common formats
    if (line.includes(";LAYER_CHANGE") || line.includes(";LAYER:") || line.includes(";Z:")) {
      layers.push([]);
    }
    if (layers.length > 0) {
      layers[layers.length - 1].push(line);
    } else {
      // Start a default layer if none exists yet
      layers.push([line]);
    }
    return layers;
  }, [] as string[][]);
}

// Process a file from scratch
async function processFile(file: File) {
  const reader = new FileReader();
  reader.onload = (event) => {
    gcodeString.value = event.target?.result as string;
    console.log(`Loaded GCode file with ${gcodeString.value.split('\n').length} lines`);
    
    // Extract layers for potential layer-based rendering
    layers = extractLayers(gcodeString.value);
    console.log(`Identified ${layers.length} layers in the GCode file`);
    
    if (preview && gcodeString.value) {
      if (isLivePreview.value) {
        processGCodeProgressively(gcodeString.value);
      } else {
        processStaticGCode(gcodeString.value);
      }
    }
  };
  reader.readAsText(file);
}

// Process the entire GCode file at once for static display with improved approach
function processStaticGCode(gcode: string) {
  if (!preview) return;
  
  console.log(`Processing static GCode file with ${gcode.split('\n').length} lines`);
  
  // Clear previous content
  preview.clear();
  
  // Set the camera position explicitly before each render
  if (preview.camera) {
    preview.camera.position.set(-200, 232, 200);
    preview.camera.lookAt(0, 0, 0);
  }
  
  try {
    // Process the entire gcode at once
    preview.processGCode(gcode);
    console.log("Static GCode rendering complete");
  } catch (error) {
    console.error("Error rendering static GCode:", error);
    // Try fallback render if primary fails
    try {
      // Process without renderTravel if the first attempt failed
      if (preview) {
        preview.renderTravel = false;
        preview.processGCode(gcode);
        preview.renderTravel = true; // Reset to default
      }
    } catch (fallbackError) {
      console.error("Fallback rendering also failed:", fallbackError);
    }
  }
}

// Process G-code command by command with visual feedback - improved approach
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
    
    // For live mode, process progressively with improved approach
    preview.clear();
    
    // Set camera position
    if (preview.camera) {
      preview.camera.position.set(-200, 232, 200);
      preview.camera.lookAt(0, 0, 0);
    }
    
    // First process the entire file at low detail for a quick preview
    console.log("Processing initial quick preview...");
    preview.renderTravel = false; // Disable travel lines for speed
    preview.processGCode(gcode);
    preview.renderTravel = true;  // Re-enable for detailed pass
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // If we have layers, process layer by layer for better organization
    if (layers.length > 0) {
      console.log(`Processing ${layers.length} layers progressively...`);
      
      for (let i = 0; i < layers.length; i++) {
        if (!isLivePreview.value) {
          // If switched to static mode during processing, stop progressive rendering
          processStaticGCode(gcode);
          break;
        }
        
        // Process an entire layer at once
        const layerGcode = layers[i].join('\n');
        preview.processGCode(layerGcode);
        
        // Pause briefly between layers for visual effect
        if (i % 5 === 0) {
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      }
    } else {
      // Fallback to line-by-line processing if no layers detected
      const commands = gcode.split('\n').filter(cmd => !cmd.trim().startsWith(';'));
      console.log(`Processing ${commands.length} commands progressively...`);
      
      // Process in larger chunks for better performance
      for (let i = 0; i < commands.length; i += 20) {
        if (!isLivePreview.value) {
          processStaticGCode(gcode);
          break;
        }
        
        const endIdx = Math.min(i + 20, commands.length);
        const chunk = commands.slice(i, endIdx).join('\n');
        preview.processGCode(chunk);
        
        // Only pause occasionally
        if (i % 100 === 0) {
          await new Promise(resolve => setTimeout(resolve, 10));
        }
      }
    }
    
    console.log("Progressive rendering complete");
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
  isLivePreview.value = !isLivePreview.value;
  emit('toggle-live-preview', isLivePreview.value);
  
  if (!isLivePreview.value && socketCleanup) {
    // If turning off live preview, clean up socket listeners
    socketCleanup();
    socketCleanup = null;
    
    // Process the whole file at once in static mode
    if (gcodeString.value && preview) {
      processStaticGCode(gcodeString.value);
    }
  } else if (isLivePreview.value && props.jobId) {
    // If turning on live preview, set up socket listeners
    setupGcodeSocketListeners(props.jobId);
    
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
    socketCleanup();
  }
  
  // Only set up listeners if we're in live preview mode
  if (!isLivePreview.value) return;
  
  console.log(`Setting up socket listeners for job ID: ${jobId}`);
  
  // Listen for gcode line updates
  const removeGcodeUpdateListener = onSocketEvent<{
    jobId: number; 
    gcodeLineNumber: number; 
    gcodeData?: string;
    current_layer_height?: number;
  }>('gcode_progress_update', (data) => {
    // Only process updates for our job
    if (data.jobId !== jobId) return;
    
    if (data.gcodeData && preview) {
      console.log(`Received gcode update for line ${data.gcodeLineNumber}`);
      // If we received new gcode data, accumulate it
      gcodeString.value += data.gcodeData + '\n';
      
      // Update occasionally to avoid too many renders
      if (data.gcodeLineNumber % 20 === 0 || data.current_layer_height) {
        // If we have layer information, try to render up to the current layer
        if (data.current_layer_height && layers.length > 0) {
          const currentLayerIndex = layers.findIndex(
            layer => layer.some(line => line.includes(`;Z:${data.current_layer_height}`))
          );
          
          if (currentLayerIndex !== -1) {
            preview.clear();
            const layersToRender = layers.slice(0, currentLayerIndex + 1).flat();
            preview.processGCode(layersToRender.join('\n'));
          } else {
            // Fallback if layer not found
            preview.processGCode(gcodeString.value);
          }
        } else {
          // Standard update if no layer info
          preview.processGCode(gcodeString.value);
        }
      }
    }
  });
  
  // Listen for gcode complete updates
  const removeGcodeCompleteListener = onSocketEvent<{jobId: number; gcodeComplete: boolean}>('gcode_complete', (data) => {
    // Only process updates for our job
    if (data.jobId !== jobId) return;
    
    if (data.gcodeComplete && preview) {
      console.log('GCode processing complete, rendering final result');
      // When gcode is complete, do a final update
      preview.processGCode(gcodeString.value);
      addToast('3D preview completed', 'success');
    }
  });
  
  // Store cleanup function
  socketCleanup = () => {
    removeGcodeUpdateListener();
    removeGcodeCompleteListener();
  };
}

// Watch for the file changes and load G-Code string
watch(() => props.file, (newFile) => {
  if (newFile && gcodeCanvas.value) {
    console.log(`Processing new file: ${newFile.name}`);
    processFile(newFile);
  } else {
    console.log("Missing required data for file processing:", { 
      file: !!newFile, 
      preview: !!preview, 
      canvas: !!gcodeCanvas.value 
    });
  }
});

// Watch for job ID changes to update socket listeners
watch(() => props.jobId, (newJobId) => {
  if (newJobId) {
    console.log(`Job ID changed to ${newJobId}, setting up socket listeners`);
    setupGcodeSocketListeners(newJobId);
  } else if (socketCleanup) {
    socketCleanup();
    socketCleanup = null;
  }
});

onBeforeUnmount(() => {
  // Improved cleanup
  if (preview) {
    try {
      // Empty the scene first
      preview.processGCode('');
      preview.clear();
      // Reset preview
      preview = null;
    } catch (error) {
      console.error("Error during cleanup:", error);
    }
  }
  
  // Clean up socket listeners
  if (socketCleanup) {
    socketCleanup();
    socketCleanup = null;
  }
  
  // Clear any stored data
  gcodeString.value = '';
  layers = [];
});
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
