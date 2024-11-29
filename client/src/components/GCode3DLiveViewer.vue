<script setup lang="ts">
import { nextTick, onMounted, onActivated, onDeactivated, ref, toRef, watchEffect, onUnmounted } from 'vue';
import { useGetFile, type Job } from '@/model/jobs';
import * as GCodePreview from 'gcode-preview';

const { getFile } = useGetFile();

const props = defineProps({
    job: Object as () => Job
})

const job = toRef(props, 'job');

const modal = document.getElementById('gcodeLiveViewModal');

// Create a ref for the canvas
const canvas = ref<HTMLCanvasElement | null>(null);
let preview: GCodePreview.WebGLPreview | null = null;
let layers: string[][] = [];

onMounted(async () => {
    if (!modal) {
        console.error('Modal element is not available');
        return;
    }

    const gcodeFile = await getFile(props.job!);
    if (!gcodeFile) {
        console.error('Failed to get the file');
        return;
    }

    const fileString = await fileToString(gcodeFile);
    const lines = fileString.split('\n');
    layers = lines.reduce((layers, line) => {
        if (line.startsWith(";LAYER_CHANGE")) {
            layers.push([]);
        }
        if (layers.length > 0) {
            layers[layers.length - 1].push(line as never);
        }
        return layers;
    }, [[]]);

    watchEffect(() => {
        if (job.value?.current_layer_height && preview) {
            try {
                // process gcode of layers up to current_layer_height
                const currentLayerIndex = layers.findIndex(layer => layer.includes(`;Z:${job.value!.current_layer_height}`));
                if (currentLayerIndex !== -1) {
                    preview.clear();
                    preview.processGCode(layers.slice(0, currentLayerIndex + 1).flat());
                }
            } catch (error) {
                console.error('Failed to process GCode:', error);
            }
        }
    });

    modal.addEventListener('shown.bs.modal', async () => {
        // Initialize the GCodePreview and show the GCode when the modal is shown
        if (canvas.value) {
            preview = GCodePreview.init({
                canvas: canvas.value,
                extrusionColor: getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim() || '#7561A9',
                backgroundColor: 'black',
                buildVolume: { x: 250, y: 210, z: 220 },
                lineWidth: 1,
                lineHeight: 1,
                extrusionWidth: 1,
                renderExtrusion: true,
                renderTubes: true,
            });

            preview.camera.position.set(-200, 232, 200);
            preview.camera.lookAt(0, 0, 0);

            if (job.value?.current_layer_height && preview) {
                try {
                    // process gcode of layers up to current_layer_height
                    const currentLayerIndex = layers.findIndex(layer => layer.includes(`;Z:${job.value!.current_layer_height}`));
                    if (currentLayerIndex !== -1) {
                        preview.clear();
                        const gcode = layers.slice(0, currentLayerIndex + 1).flat();
                        preview.processGCode(gcode);
                    }
                } catch (error) {
                    console.error('Failed to process GCode:', error);
                }
            }
        }
    });

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