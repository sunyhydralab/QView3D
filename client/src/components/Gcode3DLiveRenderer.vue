<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import { GCodeRenderer } from "@/model/gcodeRenderer";

const props = defineProps({
  gcode: Array<string> || undefined,
  initialArcSegments: { type: Number, default: 400 },
});

// Reference to the rendering container
const rendererContainer = ref<HTMLDivElement | null>(null);
// Reference to the GCodeRenderer instance
const renderer = ref<GCodeRenderer | null>(null);
// Arc smoothness value (reactive)
const arcSegments = ref<number>(props.initialArcSegments);

/** Initialize the GCodeRenderer on component mount. */
onMounted(() => {
  if (rendererContainer.value) {
    // Create the GCodeRenderer instance
    renderer.value = new GCodeRenderer(rendererContainer.value, {
      arcSegments: arcSegments.value,
      extrusionColor: 0x7561A9,
      //backgroundColor: 0x000000,
      //buildVolume: {x: 250, y: 210, z: 220},
      travelColor: 0x32CD32,
      //lineWidth: 1,
      //lineHeight: 1,
      //extrusionWidth: 1,
      //renderExtrusion: true,
      renderTravel: false,
      //renderTubes: false,
    });
    if (props.gcode) renderer.value.parseGCode(props.gcode);
  }
});

/** Clean up the GCodeRenderer on component unmount. */
onUnmounted(() => {
  if (renderer.value) {
    renderer.value.clearScene();
    renderer.value = null;
  }
});

/** Watch for changes in the GCode prop and re-render the scene.*/
watch(
    () => props.gcode!,
    (newGCode: Array<string>) => {
      if (renderer.value) {
        renderer.value.clearScene();
        renderer.value.parseGCode(newGCode);
      }
    }
);

watch(
    () => props.gcode!.length,
    () => {
      if (renderer.value) {
        renderer.value.clearScene();
        renderer.value.parseGCode(props.gcode!);
      }
    }
)

/** Update arc smoothness dynamically when the slider is adjusted.*/
const updateArcSmoothness = (): void => {
  if (renderer.value) {
    renderer.value.setArcSegments(arcSegments.value);
    if (props.gcode) renderer.value.parseGCode(props.gcode);
  }
};
</script>

<template>
  <div class="gcode-renderer">
    <!-- Canvas for rendering -->
    <div id="renderer-container" ref="rendererContainer" class="renderer-container"></div>

    <!-- Controls for adjusting arc smoothness -->
    <div class="controls">
      <label for="arcSegments">Arc Smoothness: {{ arcSegments }}</label>
      <input
        id="arcSegments"
        type="range"
        min="10"
        max="800"
        step="10"
        v-model="arcSegments"
        @input="updateArcSmoothness"
      />
    </div>
  </div>
</template>

<style scoped>
.gcode-renderer {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.renderer-container {
  width: 100%;
  height: 400px;
  position: relative;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

input[type="range"] {
  width: 100%;
}
</style>
