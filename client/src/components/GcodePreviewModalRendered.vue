<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as GCodePreview from 'gcode-preview'

const props = defineProps<{ file: File | null }>()
const emit = defineEmits(['close'])
const canvas = ref<HTMLCanvasElement | null>(null)
let preview: GCodePreview.WebGLPreview | null = null

// helper to init (or re-init) preview once canvas exists
async function initPreview(file: File) {
  if (!canvas.value) return
  preview?.clear()

  preview = GCodePreview.init({
    canvas: canvas.value,
    extrusionColor: '#7561A9',
    backgroundColor: 'black',
    buildVolume: { x: 250, y: 210, z: 220 },
    travelColor: 'limegreen',
    lineWidth: 0.5,
    lineHeight: 0.5,
    extrusionWidth: 0.25,
    renderExtrusion: true,
    renderTravel: false,
    renderTubes: true,
  })

  preview.camera.position.set(-200, 232, 200)
  preview.camera.lookAt(0, 0, 0)

  const text = await file.text()
  const commands = text
    .split('\n')
    .filter(line => !line.trim().startsWith(';'))

  for (const cmd of commands) {
    preview.renderTravel = true
    preview.processGCode(cmd)
    // tiny pause so WebGL can catch up
    await new Promise(r => setTimeout(r, 30))
  }
}

onMounted(async () => {
  // wait for the canvas to actually exist
  await nextTick()
  if (props.file) {
    await initPreview(props.file)
  }
})

watch(
  () => props.file,
  async file => {
    if (file) {
      // again wait for any DOM updates (just in case)
      await nextTick()
      await initPreview(file)
    }
  },
)

onUnmounted(() => {
  preview?.clear()
})
</script>

<template>
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
    @click.self="emit('close')"
  >
    <div class="bg-white rounded-lg overflow-hidden w-[90vw] max-w-2xl h-[80vh] flex flex-col">
      <header class="flex justify-between items-center p-2 border-b">
        <h2 class="text-lg">G-code Preview</h2>
        <button @click="emit('close')" class="p-2 hover:bg-gray-200 rounded">✕</button>
      </header>
      <div class="flex-1">
        <canvas ref="canvas" class="w-full h-full block"></canvas>
      </div>
    </div>
  </div>
</template>