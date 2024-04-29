<script setup lang="ts">
import { nextTick, onMounted, onActivated, onDeactivated, ref, toRef, watch } from 'vue';
import { useGetFile, type Job } from '@/model/jobs';
import * as GCodePreview from 'gcode-preview';

const { getFile } = useGetFile();

const props = defineProps({
    job: Object as () => Job,
    file: Object as () => File,
    isImageVisible: Boolean,
})

const isImageVisible = toRef(props, 'isImageVisible');

const file = () => {
    if (props.file) {
        return props.file
    } else if (props.job) {
        return getFile(props.job)
    } else {
        return null
    }
}

const thumbnailSrc = ref<string | null>(null);
const canvas = ref<HTMLCanvasElement | undefined>(undefined);
let preview: GCodePreview.WebGLPreview | null = null;

const initializeViewer = async () => {
    preview = GCodePreview.init({
        canvas: canvas.value,
        extrusionColor: getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color').trim() || '#7561A9',
        backgroundColor: 'black',
        buildVolume: { x: 250, y: 210, z: 220, r: 0, i: 0, j: 0 },
    });

    const fileValue = await file();
    if (fileValue) {
        const gcode = await fileToString(fileValue);

        try {
            preview?.processGCode(gcode);
            const { metadata } = preview.parser.parseGCode(gcode);
            console.log('metadata:', metadata);
            if (metadata.thumbnails && metadata.thumbnails['640x480']) {
                const thumbnailData = metadata.thumbnails['640x480'];
                thumbnailSrc.value = thumbnailData.src;
            }
        }
        catch (error) {
            console.error('Failed to process GCode:', error);
        }
    }
}

onMounted(async () => {
    const modal = document.getElementById('gcodeImageModal');
    if (!modal) {
        console.error('Modal element is not available');
        return;
    }

    modal.addEventListener('shown.bs.modal', async () => {
        if (canvas.value) {
            await initializeViewer();
        }
    });

    modal.addEventListener('hidden.bs.modal', () => {
        preview?.clear();
        thumbnailSrc.value = null;
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
    <img v-if="thumbnailSrc && isImageVisible" :src="thumbnailSrc" alt="GCode Thumbnail" />
    <div v-else-if="isImageVisible">This file doesn't have a thumbnail attached, you can check the viewer instead!</div>
</template>

<style scoped>
.hidden-canvas{
    visibility: hidden;
}

img {
    max-width: 500px;
    max-height: 500px;
    display: block;
    margin: auto;
}
canvas {
    width: 100%;
    height: 100%;
    display: block;
}
</style>