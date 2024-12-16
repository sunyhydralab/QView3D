<script setup lang="ts">
import {ref, onMounted, onUnmounted, watch} from 'vue';
import {type Device} from '@/model/ports';
import * as GCodePreview from 'gcode-preview';

const props = defineProps<{ device: Device }>();

const canvas = ref<HTMLCanvasElement | undefined>(undefined);
let preview: GCodePreview.WebGLPreview | null = null;
let worker: Worker | null = null;

onMounted(async () => {
  if (!canvas.value) {
    console.error('Canvas not found');
    return;
  }
  worker = new Worker(new URL('@/model/gcodeWorker.ts', import.meta.url), {type: 'module'});
  worker.onmessage = (event) => {
    const {type, error} = event.data;
    if (type === 'error') console.error('Worker Error:', error);
  };

  const extrusionColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() || '#7561A9';
  const offscreen: OffscreenCanvas = canvas.value.transferControlToOffscreen();

  console.debug(offscreen)

  worker.postMessage({
    type: 'init',
    payload: {
      canvas: offscreen,
      extrusionColor: extrusionColor,
      backgroundColor: 'black',
      buildVolume: {x: 250, y: 210, z: 220},
      travelColor: 'limegreen',
      lineWidth: 1,
      lineHeight: 1,
      extrusionWidth: 1,
      renderExtrusion: true,
      renderTravel: false,
      renderTubes: false
    }
  }, [offscreen]);

  const renderGCode = (gcode: string) => {
    worker?.postMessage({
      type: 'render',
      payload: {gcode},
    });
  };

  watch(() => props.device?.gcodeLines?.length!, () => {
    renderGCode(props.device.gcodeLines!.slice(-1)[0]); // Render last 10 lines as a batch
  });


  const allLines = props.device?.gcodeLines;
  if (allLines) {
    for (let i = 0; i < allLines.length; i++) renderGCode(allLines[i]);
  }
});


onUnmounted(() => {
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