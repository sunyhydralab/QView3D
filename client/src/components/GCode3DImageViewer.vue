<script setup lang="ts">
import { nextTick, onMounted, onActivated, onDeactivated, ref, toRef, onUnmounted } from 'vue';
import { useGetFile, type Job } from '@/model/jobs';
import * as GCodePreview from 'gcode-preview';

const { getFile } = useGetFile();

const props = defineProps({
    job: Object as () => Job,
    file: Object as () => File
})

const file = () => {
    if (props.file) {
        return props.file
    } else if (props.job) {
        return getFile(props.job)
    } else {
        return null
    }
}

const modal = document.getElementById('gcodeImageModal');

// Create a ref for the canvas
const canvas = ref<HTMLCanvasElement | null>(null);
let preview: GCodePreview.WebGLPreview | null = null;

onMounted(async () => {
    if (!modal) {
        console.error('Modal element is not available');
        return;
    }

    if (canvas.value) {
        preview = GCodePreview.init({
            canvas: canvas.value,
            extrusionColor: getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color').trim() || '#7561A9',
            backgroundColor: 'black',
            // @ts-ignore
            buildVolume: { x: 250, y: 210, z: 220, r: 0, i: 0, j: 0 },
        });

        preview.camera.position.set(0, 410, 365);
        preview.camera.lookAt(0, 0, 0);

        if (canvas.value) {
            // job.file to string
            const fileValue = await file();
            if (fileValue) {
                const gcode = await fileToString(fileValue);

                try {
                    preview?.processGCode(gcode); // MAIN LINE
                } catch (error) {
                    console.error('Failed to process GCode:', error);
                }
            }
        }
    }

    modal.addEventListener('hidden.bs.modal', () => {
        // Clean up when the modal is hidden
        preview?.processGCode('');
        preview?.clear();
        preview = null;
    });
});

onUnmounted(() => {
    preview?.processGCode('');
    preview?.clear();
    preview = null;
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