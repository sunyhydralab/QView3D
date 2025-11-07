<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref, nextTick } from 'vue'
import * as GCodePreview from 'gcode-preview'
import { onSocketEvent, socket } from '@/services/socket'
import { addToast } from '@/components/Toast.vue'
import { isDark } from '@/composables/useMode'
import { API_URL } from '@/composables/useIPSettings'

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

// Fetch G-code file from API if file is not provided but jobId is available
async function fetchJobFile(jobId: number): Promise<void> {
  if (!preview || !gcodeCanvas.value) {
    console.log("Preview or canvas not ready, waiting...");
    return;
  }

  try {
    console.log(`Fetching G-code file for job ID: ${jobId}`);

    // Try direct backend URL since middleware routing is having issues
    const backendUrl = 'http://localhost:8000';
    console.log(`Trying direct backend: ${backendUrl}/getfile?jobid=${jobId}`);

    const response = await fetch(`${backendUrl}/getfile?jobid=${jobId}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (data.file) {
      console.log(`Loaded G-code file from API with ${data.file.split('\n').length} lines`);
      gcodeString.value = data.file;
      
      // Extract layers for potential layer-based rendering
      layers = extractLayers(gcodeString.value);
      console.log(`Identified ${layers.length} layers in the GCode file`);
      
      // Process the G-code directly
      if (isLivePreview.value) {
        processGCodeProgressively(gcodeString.value);
      } else {
        processStaticGCode(gcodeString.value);
      }
    } else {
      console.error("No file data in API response");
      addToast('Failed to load G-code file from job', 'error');
    }
  } catch (error) {
    console.error("Error fetching job file:", error);
    addToast(`Failed to load G-code file: ${error}`, 'error');
  }
}

onMounted(() => {
  nextTick(() => {
    withoutConsoleWarnings(() => {
      if (gcodeCanvas.value) {
        console.log("Initializing GCode preview...");
        
        // Ensure canvas has dimensions
        const canvasWidth = gcodeCanvas.value.clientWidth || 800;
        const canvasHeight = gcodeCanvas.value.clientHeight || 600;
        gcodeCanvas.value.width = canvasWidth;
        gcodeCanvas.value.height = canvasHeight;
        console.log(`Canvas dimensions: ${canvasWidth}x${canvasHeight}`);
        
        // Initialize the GCode preview with correct settings according to docs
        try {
          preview = GCodePreview.init({
            canvas: gcodeCanvas.value,
            extrusionColor: 'turquoise',
            backgroundColor: 'black',
            buildVolume: { x: 250, y: 210, z: 220 },  // Standard print bed size
            travelColor: 'limegreen',
            renderTubes: true,  // Use tube geometry for better visuals
            // Note: The library doesn't support all the properties we were using
            // Removed unsupported properties: lineWidth, lineHeight, extrusionWidth,
            // renderExtrusion, renderTravel, minLayerThreshold, initialCameraPosition
          });
          console.log("GCode preview initialized successfully");
        } catch (error) {
          console.error("Failed to initialize GCode preview:", error);
          addToast(`Failed to initialize 3D viewer: ${error}`, 'error');
          return;
        }

        // The library handles camera positioning automatically
        
        // If we have a file already, process it
        if (props.file) {
          processFile(props.file);
        } else if (props.jobId) {
          // If no file but we have a jobId, fetch the file from API
          fetchJobFile(props.jobId);
        }
      } else {
        console.error("Canvas element not found!");
        addToast('3D viewer canvas not found', 'error');
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

/**
 * Preprocess GCode to fix Z-axis offset issues
 * This ensures the model sits on the bed instead of floating
 */
function preprocessGCodeForZOffset(gcode: string): string {
  const lines = gcode.split('\n');
  let minZ = Infinity;

  // First pass: find the minimum Z value in the entire file
  lines.forEach(line => {
    const zMatch = line.match(/Z(-?\d*\.?\d+)/);
    if (zMatch) {
      const zValue = parseFloat(zMatch[1]);
      if (!isNaN(zValue) && zValue < minZ) {
        minZ = zValue;
      }
    }
  });

  // If we found a minimum Z value and it's positive, adjust all Z values
  if (minZ !== Infinity && minZ > 0.1) { // Only adjust if Z is significantly above 0
    console.log(`Adjusting Z-axis offset: shifting all Z values down by ${minZ}mm`);

    return lines.map(line => {
      // Only adjust lines with Z values
      const zMatch = line.match(/Z(-?\d*\.?\d+)/);
      if (zMatch) {
        const originalZ = parseFloat(zMatch[1]);
        const adjustedZ = (originalZ - minZ).toFixed(3);
        return line.replace(/Z(-?\d*\.?\d+)/, `Z${adjustedZ}`);
      }
      return line;
    }).join('\n');
  }

  return gcode; // Return original if no adjustment needed
}

// Process the entire GCode file at once for static display
function processStaticGCode(gcode: string) {
  if (!preview) {
    console.error("GCode preview not initialized!");
    addToast('GCode preview not initialized', 'error');
    return;
  }

  console.log(`Processing static GCode file with ${gcode.split('\n').length} lines`);

  try {
    // Clear previous content
    preview.clear();

    // Apply Z-offset correction to prevent floating
    const correctedGCode = preprocessGCodeForZOffset(gcode);

    // Process the corrected gcode
    preview.processGCode(correctedGCode);

    // Render the scene after processing
    preview.render();

    console.log("Static GCode rendering complete");
    addToast('3D preview loaded successfully', 'success');
  } catch (error) {
    console.error("Error rendering static GCode:", error);
    addToast(`3D preview error: ${error}`, 'error');
  }
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

    // For live mode, simulate progressive rendering
    preview.clear();

    // Apply Z-offset correction first
    const correctedGCode = preprocessGCodeForZOffset(gcode);

    // Extract layers for progressive rendering
    const layers = extractLayers(correctedGCode);

    if (layers.length > 0) {
      console.log(`Processing ${layers.length} layers progressively...`);

      // Build up the gcode progressively
      let accumulatedGCode = '';

      for (let i = 0; i < layers.length; i++) {
        if (!isLivePreview.value) {
          // If switched to static mode, render everything
          processStaticGCode(gcode);
          break;
        }

        // Accumulate layers
        accumulatedGCode += layers[i].join('\n') + '\n';

        // Clear and re-render with accumulated gcode
        preview.clear();
        preview.processGCode(accumulatedGCode);
        preview.render();

        // Pause between layer groups for visual effect
        if (i % 10 === 0 && i > 0) {
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      }
    } else {
      // No layers detected, just process the whole file
      preview.processGCode(gcode);
      preview.render();
    }

    console.log("Progressive rendering complete");
  } catch (error) {
    console.error('Error in progressive processing:', error);
    // Fallback to static rendering
    processStaticGCode(gcode);
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
    // If turning on live preview, clear canvas and start fresh
    if (preview) {
      preview.clear();
      gcodeString.value = '';  // Clear accumulated gcode
      console.log('[GCode Live Preview] Switched to live mode - waiting for printer updates');
    }

    // Set up socket listeners for real-time updates
    setupGcodeSocketListeners(props.jobId);
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

  // Request accumulated gcode buffer for jobs already in progress
  const requestBufferListener = onSocketEvent<{
    job_id: number;
    gcode_buffer: string;
    progress: number;
  }>('gcode_buffer_response', (data) => {
    if (data.job_id !== jobId) return;

    if (data.gcode_buffer && preview && isLivePreview.value) {
      console.log(`[GCode Live Preview] Received buffer with ${data.progress.toFixed(1)}% progress`);
      gcodeString.value = data.gcode_buffer;

      // Clear and process the accumulated buffer with Z-offset correction
      try {
        preview.clear();

        // Apply Z-offset correction to prevent floating
        const correctedBuffer = preprocessGCodeForZOffset(data.gcode_buffer);

        // Camera position already set via initialCameraPosition, just ensure lookAt
        if (preview.camera) {
          preview.camera.lookAt(0, 0, 0);
        }

        preview.processGCode(correctedBuffer);
      } catch (error) {
        console.error('Error processing gcode buffer:', error);
      }
    }
  });

  // Request the buffer immediately after setting up listener
  socket.value.emit('request_gcode_buffer', { job_id: jobId });

  // Listen for gcode line updates
  // TODO: Future improvement - implement true live preview that shows actual printer position
  // Current implementation processes chunks incrementally but may have rendering issues
  // Consider: 1) M114 position tracking, 2) Progressive geometry building, 3) Buffer vs execution tracking
  const removeGcodeUpdateListener = onSocketEvent<{
    job_id: number;
    fabricator_id: number;
    line_number: number;
    total_lines: number;
    progress: number;
    current_layer_height: number;
    gcode_chunk: string;
  }>('gcode_progress_update', (data) => {
    // Only process updates for our job
    if (data.job_id !== jobId) return;

    if (data.gcode_chunk && preview && isLivePreview.value) {
      console.log(`[GCode Live Preview] Progress: ${data.progress.toFixed(1)}% (${data.line_number}/${data.total_lines} lines, layer: ${data.current_layer_height})`);

      // Accumulate the gcode data
      gcodeString.value += data.gcode_chunk + '\n';

      // Process the new chunk incrementally with proper Z-offset
      try {
        // Extract Z value from the chunk to maintain continuity
        const zMatch = data.gcode_chunk.match(/Z(-?\d*\.?\d+)/);
        if (zMatch) {
          // Find minimum Z from the start of the print to apply consistent offset
          const lines = gcodeString.value.split('\n');
          let minZ = Infinity;

          lines.forEach((line: string) => {
            const match = line.match(/Z(-?\d*\.?\d+)/);
            if (match) {
              const z = parseFloat(match[1]);
              if (!isNaN(z) && z < minZ) minZ = z;
            }
          });

          // Apply the same offset to the new chunk
          let correctedChunk = data.gcode_chunk;
          if (minZ !== Infinity && minZ > 0) {
            const originalZ = parseFloat(zMatch[1]);
            const adjustedZ = (originalZ - minZ).toFixed(3);
            correctedChunk = data.gcode_chunk.replace(/Z(-?\d*\.?\d+)/, `Z${adjustedZ}`);
          }

          preview.processGCode(correctedChunk);
        } else {
          // No Z value in chunk, process as-is
          preview.processGCode(data.gcode_chunk);
        }
      } catch (error) {
        console.error('Error processing gcode chunk:', error);
      }
    }
  });
  
  // Listen for gcode complete updates
  const removeGcodeCompleteListener = onSocketEvent<{
    job_id: number;
    fabricator_id: number;
    gcode_complete: boolean;
  }>('gcode_complete', (data) => {
    // Only process updates for our job
    if (data.job_id !== jobId) return;

    if (data.gcode_complete && preview) {
      console.log('[GCode Live Preview] Print complete - preview finalized');
      addToast('Live 3D preview completed', 'success');
    }
  });
  
  // Store cleanup function
  socketCleanup = () => {
    requestBufferListener();
    removeGcodeUpdateListener();
    removeGcodeCompleteListener();
  };
}

// Watch for the file changes and load G-Code string
watch(() => props.file, (newFile: File | undefined) => {
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

// Watch for jobId changes - if file is not available, fetch it from API
watch([() => props.jobId, () => props.file, () => preview], ([jobId, file, previewInstance]) => {
  // Only fetch if we have a jobId, no file, and preview is ready
  if (jobId && !file && previewInstance && gcodeCanvas.value) {
    console.log(`Job ID ${jobId} provided but no file - fetching from API`);
    fetchJobFile(jobId);
  }
}, { immediate: true });

// Watch for job ID changes to update socket listeners
watch(() => props.jobId, (newJobId: number | undefined) => {
  if (newJobId) {
    console.log(`Job ID changed to ${newJobId}, setting up socket listeners`);

    // Clear canvas and gcode buffer for new job in live preview mode
    if (isLivePreview.value && preview) {
      preview.clear();
      gcodeString.value = '';
      console.log('[GCode Live Preview] New job started - canvas cleared');
    }

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
