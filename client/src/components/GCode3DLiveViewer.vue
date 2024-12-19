<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { type Device } from '@/model/ports';
import * as GCodePreview from 'gcode-preview';
import { withConsoleSuppression } from '@/model/gcodeWorker';

const figuredOutWorkers = false;

const props = defineProps<{ device: Device }>();

const canvas = ref<HTMLCanvasElement | undefined>(undefined);
let preview: GCodePreview.WebGLPreview | null = null;
let worker: Worker | null = null;

// Initialize rendering logic on mount
onMounted(async () => {
  if (!canvas.value) {
    console.error('Canvas not found');
    return;
  }

  // Rendering settings
  const settings = {
    extrusionColor: getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() || '#7561A9',
    backgroundColor: 'black',
    buildVolume: { x: 250, y: 210, z: 220 },
    travelColor: 'limegreen',
    lineWidth: 0.8,
    lineHeight: 0.4,
    extrusionWidth: 0.8,
    renderExtrusion: true,
    renderTravel: false,
    renderTubes: false,
    initialCameraPosition: [-200, 232, 200],
  };

  // Initialize worker or preview
  if (figuredOutWorkers) {
    const offscreen: OffscreenCanvas = canvas.value.transferControlToOffscreen();
    worker = new Worker(new URL('@/model/gcodeWorker.ts', import.meta.url), { type: 'module' });
    worker.onmessage = (event) => {
      const { type, error } = event.data;
      if (type === 'error') console.error('Worker Error:', error);
    };
    worker.postMessage(
      {
        type: 'init',
        payload: {
          canvas: offscreen,
          ...settings,
        },
      },
      [offscreen]
    );
  } else {
    if (preview) {
      preview.clear();
    }
    const oldDebug = console.debug;
    const oldInfo = console.info;
    console.debug = () => {};
    preview = GCodePreview.init({
      canvas: canvas.value,
      ...settings,
    });
    preview.camera.lookAt(0, 0, 0);
    console.debug = oldDebug;
    console.info = oldInfo;
  }

  // Function to render GCode lines
  const renderGCode = (gcode: string) => {
    if (figuredOutWorkers) {
      worker?.postMessage({
        type: 'render',
        payload: { gcode },
      });
    } else if (preview) {
      if (preview.renderTubes) withConsoleSuppression(() => preview!.processGCode(gcode));
      else preview.processGCode(gcode);
    }
  };

  // Watch for changes to GCode lines
  watch(
    () => props.device?.gcodeLines,
    (newGCodeLines) => {
      if (figuredOutWorkers) {
          worker?.postMessage({ type: 'clear' });
        } else {
          preview?.clear();
          preview?.render();
        }
      if (!newGCodeLines || newGCodeLines.length === 0) {
        // Clear existing render data
        return
      }
      // Render all lines
      newGCodeLines.forEach((line) => renderGCode(line));
    },
    { immediate: true }
  );

  // Watch for additional lines being added
  watch(
    () => props.device?.gcodeLines?.length,
    () => {
      if (!props.device.gcodeLines ) return;
      renderGCode(props.device.gcodeLines.slice(-1)[0]);
    }
  );
});

// Clean up resources on unmount
onUnmounted(() => {
  if (worker) {
    worker.terminate();
    worker = null;
  }
  if (preview) {
    preview.clear();
    preview = null;
  }
});
</script>

<template>
  <canvas ref="canvas"></canvas>
</template>

<style scoped>
canvas {
  width: 100%;
  height: 400px;
  display: block;
}
</style>
