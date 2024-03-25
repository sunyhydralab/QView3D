<script setup lang="ts">
import { nextTick, onMounted, onActivated, onDeactivated, ref, toRef, watchEffect } from 'vue';
import { useGetFile, type Job } from '@/model/jobs';
import * as GCodePreview from 'gcode-preview';

const { getFile } = useGetFile();

const props = defineProps({
    job: Object as () => Job
})
const job = toRef(props, 'job');

// Create a ref for the canvas
const canvas = ref<HTMLCanvasElement | null>(null);

let preview: GCodePreview.WebGLPreview | null = null;

onMounted(async () => {
    const modal = document.getElementById('gcodeLiveViewModal');
    if (!modal) {
        console.error('Modal element is not available');
        return;
    }

    const gcodeFile = await getFile(props.job!);
    if (!gcodeFile) {
        console.error('Failed to get the file');
        return;
    }

    const fileReader = new FileReader();
    fileReader.onload = function (event) {
        if (event.target === null || typeof event.target.result !== 'string') {
            console.error('Failed to load the file content');
            return;
        }

        const fileContent = event.target.result;
        const lines = fileContent.split('\n');
        const commandLines = lines.filter(line => line.trim() && !line.startsWith(";"));

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
                    try {
                        if (job.value?.gcode_num) {
                            // proccess gcode of command lines from 0 to job.value.gcode
                            preview?.processGCode(commandLines.slice(0, job.value.gcode_num));
                        }
                    } catch (error) {
                        console.error('Failed to process GCode:', error);
                    }
                } else {
                    console.error('Canvas element is not available in showGCode');
                }
            }
        });

        watchEffect(() => {
            if (job.value?.gcode_num && preview) {
                try {
                    // process gcode of command line that is job.value.gcode
                    preview.processGCode(commandLines[job.value.gcode_num]);
                } catch (error) {
                    console.error('Failed to process GCode:', error);
                }
            }
        });

        modal.addEventListener('hidden.bs.modal', () => {
            // Clean up when the modal is hidden
            preview?.clear();
            if(job.value){
                job.value.file = new File([], "");
            }
        });
    };
    fileReader.readAsText(gcodeFile);
});
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