<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useGetFile, type Job } from '@/model/jobs';
import * as GCodePreview from 'gcode-preview';

const { getFile } = useGetFile();

const props = defineProps({
  job: Object as () => Job,
  file: Object as () => File
});

const file = () => {
  if (props.file) {
    return props.file;
  } else if (props.job) {
    return getFile(props.job);
  } else {
    return null;
  }
};

const modal = document.getElementById('gcodeImageModal');
const canvas = ref<HTMLCanvasElement | null>(null);
let preview: GCodePreview.WebGLPreview | null = null;

const renderTravel = ref(true); // Ref to control renderTravel dynamically

const processGCodeCommand = (gcode: string) => {
  try {
    // Dynamically process G-code and determine if renderTravel should be enabled
    if (gcode.includes('G0') || gcode.includes('G1')) {
      renderTravel.value = true; // Enable renderTravel for movement commands
    } else {
      renderTravel.value = false; // Disable for other commands
    }
    if (preview) {
      preview.renderTravel = renderTravel.value;
    }
  } catch (error) {
    console.error('Error processing GCode command. Reverting to default renderTravel:', error);

    // Ensure proper fallback
    renderTravel.value = true;
    if (preview) {
      preview.renderTravel = true;
    }
  }
};

onMounted(async () => {
  if (!modal) {
    console.error('Modal element is not available');
    return;
  }

  if (canvas.value) {
    try {
      preview = GCodePreview.init({
        canvas: canvas.value,
        extrusionColor: getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color').trim() || '#7561A9',
        backgroundColor: 'black',
        buildVolume: { x: 250, y: 210, z: 220 },
        travelColor: 'limegreen',
        renderExtrusion: true,
        renderTravel: renderTravel.value,
      });

      preview.camera.position.set(-200, 232, 200);
      preview.camera.lookAt(0, 0, 0);

      const fileValue = await file();
      if (fileValue) {
        const gcode = await fileToString(fileValue);

        try {
          // Process and render G-code with timeout
          const commands = gcode.split('\n');
          for (const command of commands) {
            setTimeout(() => {
              processGCodeCommand(command); // Update renderTravel dynamically
              preview?.processGCode(command);
            }, 2000);
          }
        } catch (error) {
          console.error('Failed to process GCode:', error);

          // Reset to original behavior on failure
          renderTravel.value = true;
          if (preview) {
            preview.renderTravel = true;
            preview.processGCode(gcode); // Fallback to processing entire file
          }
        }
      }
    } catch (error) {
      console.error('Error initializing GCodePreview:', error);

      // Fallback logic if initialization fails
      renderTravel.value = true;
      if (preview) {
        preview.renderTravel = true;
      }
    }
  }

  modal.addEventListener('hidden.bs.modal', () => {
    // Clean up when the modal is hidden
    if (preview) {
      preview.processGCode('');
      preview.clear();
      preview = null;
    }
  });
});

onUnmounted(() => {
  if (preview) {
    preview.processGCode('');
    preview.clear();
    preview = null;
  }
});

const fileToString = (file: File | undefined) => {
  if (!file) {
    console.error('File is not available');
    return '';
  }

  const reader = new FileReader();
  reader.readAsText(file);
  return new Promise<string>((resolve, reject) => {
    reader.onload = () => {
      resolve(reader.result as string);
    };
    reader.onerror = (error) => {
      reject(error);
    };
  });
};
</script>

<template>
  <canvas ref="canvas"></canvas>
</template>

<style scoped>
canvas {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
