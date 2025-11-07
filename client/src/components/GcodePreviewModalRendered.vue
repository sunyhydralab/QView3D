<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useGCodeViewer } from '@/composables/useGCodeViewer'

const props = defineProps<{ file: File | null }>()
const emit = defineEmits(['close'])
const canvas = ref<HTMLCanvasElement | null>(null)

// Use the composable for shared functionality
const {
  initPreview: initGCodePreview,
  preprocessGCodeForZOffset,
  stripGCodeComments
} = useGCodeViewer()

let preview: ReturnType<typeof initGCodePreview> = null

// Command-by-command animation rendering
async function initAnimatedPreview(file: File) {
  if (!canvas.value) return

  // Initialize with consistent configuration
  preview = initGCodePreview(canvas.value, {
    extrusionColor: '#7561A9',  // Custom color for this viewer
    renderTravel: true  // Show travel moves in animation
  })

  if (!preview) {
    console.error('Failed to initialize GCode preview')
    return
  }

  // Read and preprocess the file
  const text = await file.text()
  const strippedCommands = stripGCodeComments(text)

  // Apply Z-offset correction for proper positioning
  const correctedGCode = preprocessGCodeForZOffset(strippedCommands)
  const commands = correctedGCode.split('\n').filter(cmd => cmd.length > 0)

  console.log(`[Animated Preview] Processing ${commands.length} commands with animation`)

  // Process command-by-command for visual animation effect
  for (const cmd of commands) {
    preview.processGCode(cmd)
    // Pause between commands for visual effect (30ms per command)
    await new Promise(r => setTimeout(r, 30))
  }

  console.log('[Animated Preview] Animation complete')
}

onMounted(async () => {
  // wait for the canvas to actually exist
  await nextTick()
  if (props.file) {
    await initAnimatedPreview(props.file)
  }
})

watch(
  () => props.file,
  async file => {
    if (file) {
      // again wait for any DOM updates (just in case)
      await nextTick()
      await initAnimatedPreview(file)
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
