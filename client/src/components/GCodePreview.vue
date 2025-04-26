<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref, nextTick } from 'vue'
import * as GCodePreview from 'gcode-preview'

const gcodeString = ref('')
const props = defineProps<{ file: File | null }>()
const gcodeCanvas = ref<HTMLCanvasElement | null>(null)
let preview: ReturnType<typeof GCodePreview.init> | null = null

onMounted(() => {
  nextTick(() => {
    if (gcodeCanvas.value) {
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
        renderTubes: true,
      })
    }
  })
})


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


onBeforeUnmount(() => {
  if (preview) {
    preview.clear()
  }
})
</script>

<template>
  <div class="gcode-container">
    <canvas ref="gcodeCanvas"></canvas>
  </div>
</template>

<style scoped>
.gcode-container {
  width: 100%;
  height: 100%;
  position: relative;
}

canvas {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
