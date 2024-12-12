<script setup lang="ts">
import {ref, onMounted, onUnmounted, watch, type Ref} from 'vue';
import {type Device} from '@/model/ports';
import * as GCodePreview from 'gcode-preview';

const props = defineProps({
  device: Object as () => Device,
});

const canvas = ref<HTMLCanvasElement | null>(null);

const gcodeBuffer: Ref<Array<string>> = ref([] as Array<string>);

let preview: GCodePreview.WebGLPreview | null = null;
const originalConsoleWarn = console.warn;
const bufferSizeToRender = 50;

onMounted(async () => {
  if (canvas.value) {
    try {
        console.warn = () => {}; // Suppress warnings from gcode-preview
      preview = (GCodePreview.init({
        canvas: canvas.value,
        extrusionColor: getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() || '#7561A9',
        backgroundColor: 'black',
        buildVolume: {x: 250, y: 210, z: 220},
        travelColor: 'limegreen',
        lineWidth: 1,
        lineHeight: 1,
        extrusionWidth: 1,
        renderExtrusion: true,
        renderTravel: false,
        renderTubes: false,
      }));

      preview.camera.position.set(-200, 232, 200);
      preview.camera.lookAt(0, 0, 0);
      console.warn = originalConsoleWarn;

    } catch (error) {
      console.error('Error initializing GCodePreview:', error);
    }
  }
  if(preview?.renderTubes) {
    watch(() => props.device!.gcodeLines?.length, () => {
      gcodeBuffer.value.push(props.device!.gcodeLines![props.device!.gcodeLines!.length - 1]);
      if (gcodeBuffer.value?.length > bufferSizeToRender) {
        renderAllNoWarn(gcodeBuffer.value);
        gcodeBuffer.value = [];
      }
    });
    if (props.device!.gcodeLines) {
      renderAllNoWarn(props.device!.gcodeLines!);
    }
  } else {
    watch(() => props.device!.gcodeLines?.length, () => {
      gcodeBuffer.value.push(props.device!.gcodeLines![props.device!.gcodeLines!.length - 1]);
      if (gcodeBuffer.value?.length > bufferSizeToRender) {
        renderAll(gcodeBuffer.value);
        gcodeBuffer.value = [];
      }
    });
    if(props.device!.gcodeLines) {
      renderAll(props.device!.gcodeLines!);
    }
  }
});


function renderAll(gcode: string[]){
    preview?.processGCode(gcode);
}

function renderAllNoWarn(gcode: string[]){
    console.warn = () => {}; // Suppress warnings from gcode-preview
    preview?.processGCode(gcode);
    console.warn = originalConsoleWarn;
}

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