<script>
import * as GCodePreview from 'gcode-preview'

export default {
  name: 'GCodePreview',
  mounted() {
    // Initialize the GCodePreview
    this.preview = GCodePreview.init({
      canvas: this.$refs.gcodeCanvas,
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

    // Example GCode
    const gcode = 'G0 X0 Y0 Z0.2\nG1 X42 Y42 E10'
    this.preview.processGCode(gcode)
  },
  beforeDestroy() {
    // Clean up preview when the component is collapsed
    if (this.preview) {
      this.preview.clear()
    }
  },
}
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
