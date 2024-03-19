<script setup lang="ts">
import { nextTick, onMounted, onActivated, onDeactivated, ref, toRef } from 'vue';
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

// Create a ref for the canvas
const canvas = ref<HTMLCanvasElement | null>(null);

let preview: GCodePreview.WebGLPreview | null = null;

onMounted(async () => {
    const modal = document.getElementById('gcodeImageModal');
    if (!modal) {
        console.error('Modal element is not available');
        return;
    }

    // console.log("FILE NAME: ", file.value.name)

    modal.addEventListener('shown.bs.modal', async () => {
        // Initialize the GCodePreview and show the GCode when the modal is shown
        if (canvas.value) {
            preview = GCodePreview.init({
                canvas: canvas.value,
                extrusionColor: 'hotpink',
                backgroundColor: 'black',
                buildVolume: { x: 250, y: 210, z: 220, r: 0, i: 0, j: 0 },
            });

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
                } else {
                    console.error('File is not available');
                }
            } else {
                console.error('Canvas element is not available in showGCode');
            }
        }
    });

    modal.addEventListener('hidden.bs.modal', () => {
        // Clean up when the modal is hidden
        preview?.clear();
    });
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