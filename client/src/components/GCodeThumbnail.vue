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
const canvas = ref<HTMLCanvasElement | undefined>(undefined);
let preview: GCodePreview.WebGLPreview | null = null;

const thumbnailSrc = ref<string | null>(null);

onMounted(async () => {
    if (!modal) {
        console.error('Modal element is not available');
        return;
    }

    preview = GCodePreview.init({
        canvas: canvas.value,
    });

    const fileValue = await file();
    if (fileValue) {
        const gcode = await fileToString(fileValue);
        try {
            // Extract the thumbnail from the metadata
            const { metadata } = preview.parser.parseGCode(gcode);
            console.debug('GCode metadata:', metadata);
            let thumbnailData = null;
            if (metadata.thumbnails) {
                if(metadata.thumbnails['640x480']) thumbnailData = metadata.thumbnails['640x480'];
                else if(metadata.thumbnails['320x240']) thumbnailData = metadata.thumbnails['320x240'];
                else if(metadata.thumbnails['160x120']) thumbnailData = metadata.thumbnails['160x120'];
                else thumbnailData = metadata.thumbnails[Object.keys(metadata.thumbnails)[0]];
                thumbnailSrc.value = thumbnailData.src;
            }
        } catch (error) {
            console.error('Failed to process GCode:', error);
        }
    }

    modal.addEventListener('hidden.bs.modal', () => {
        // Clean up when the modal is hidden
        preview?.processGCode('');
        preview?.clear();
        preview = null;
        thumbnailSrc.value = null;
    });
});

onUnmounted(() => {
    preview?.processGCode('');
    preview?.clear();
    preview = null;
    thumbnailSrc.value = null;
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
    <canvas v-show="false" style="display: hidden" ref="canvas"></canvas>
    <img v-if="thumbnailSrc" :src="thumbnailSrc" alt="GCode Thumbnail" />
    <div v-else>This file doesn't have a thumbnail attached, you can check the viewer instead!</div>
</template>

<style scoped>
img {
    max-width: 500px;
    max-height: 500px;
    display: block;
    margin: auto;
}
</style>