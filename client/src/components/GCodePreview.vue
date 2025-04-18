<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import * as GCodePreview from 'gcode-preview'

const gcodeCanvas = ref<HTMLCanvasElement | null>(null)
let preview: ReturnType<typeof GCodePreview.init> | null = null

onMounted(() => {
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

    const gcode = 'G0 X0 Y0 Z0.2\nG1 X42 Y42 E10'
    preview.processGCode(gcode)
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
