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

const processGCodeCommand = (gcode: string) => {
  try {
    // Dynamically process G-code and determine if renderTravel should be enabled
    if (preview) {
      preview.renderTravel = true;
    }
  } catch (error) {
    console.error('Error processing GCode command. Reverting to default renderTravel:', error);

    // Ensure proper fallback
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
      preview = (GCodePreview.init({
        canvas: canvas.value,
        extrusionColor: getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color').trim() || '#7561A9',
        backgroundColor: 'black',
        buildVolume: {x: 250, y: 210, z: 220},
        travelColor: 'limegreen',
        lineWidth: 1,
        lineHeight: 1,
        extrusionWidth: 1,
        renderExtrusion: true,
        renderTravel: false,
        renderTubes: true,
      }));

      preview?.camera.position.set(-200, 232, 200);
      preview?.camera.lookAt(0, 0, 0);

      const fileValue = await file();
      if (fileValue) {
        const gcode = await fileToString(fileValue);

        try {
          // Process and render G-code with timeout
          let commands = gcode.split('\n');
          commands = commands.filter(command => !command.trim().startsWith(';'));
          for (const command of commands) {
            await new Promise(resolve => setTimeout(resolve, 150));
            processGCodeCommand(command); // Update renderTravel dynamically
            preview?.processGCode(command);
            // try {
            //
            // } catch (error: unknown) {
            //   if (error instanceof TypeError) {
            //     continue;
            //   }
            //   throw error;
            // }
          }
        } catch (error) {
          console.error('Failed to process GCode:', error);

          // Reset to original behavior on failure
          if (preview) {
            preview.renderTravel = true;
            preview?.processGCode(gcode); // Fallback to processing entire file
          }
        }
      }
    } catch (error) {
      console.error('Error initializing GCodePreview:', error);

      // Fallback logic if initialization fails
      if (preview) {
        preview.renderTravel = true;
      }
    }
  }

  modal.addEventListener('hidden.bs.modal', () => {
    // Clean up when the modal is hidden
    if (preview) {
      preview.clear();
      preview = null;
    }
  });
});

onUnmounted(() => {
  if (preview) {
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
