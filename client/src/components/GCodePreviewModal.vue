
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useGCodeViewer } from '@/composables/useGCodeViewer'

const props = defineProps<{ file: File | null }>()
const emit = defineEmits(['close'])
const canvas = ref<HTMLCanvasElement | null>(null)

// Use the composable for shared functionality
const {
  initPreview,
  processStaticGCode,
  stripGCodeComments
} = useGCodeViewer()

let preview: ReturnType<typeof initPreview> = null

async function initFullPreview(file: File) {
  if (!canvas.value) return

  // Initialize with consistent configuration
  preview = initPreview(canvas.value, {
    extrusionColor: '#7561A9',  // Custom color for this viewer
    renderTravel: false  // Disable travel lines for cleaner preview
  })

  if (!preview) {
    console.error('Failed to initialize GCode preview')
    return
  }

  // Read and process the file
  const raw = await file.text()
  const stripped = stripGCodeComments(raw)

  // Process with Z-offset correction for proper positioning
  processStaticGCode(preview, stripped)
}

onMounted(async () => {
  await nextTick()
  if (props.file) {
    await initFullPreview(props.file)
  }
})

watch(
  () => props.file,
  async file => {
    if (file) {
      await nextTick()
      await initFullPreview(file)
    }
  }
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
