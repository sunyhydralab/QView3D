<script setup lang="ts">
import { ref, onUnmounted } from 'vue';
import { useMoveHead, type Device } from '@/model/ports';

const { move } = useMoveHead();

const props = defineProps({
    speed: Number,
    num: Number,
    selectedDevice: Object as () => Device | null
})
const num = ref(props.num)
const selectedDevice = ref(props.selectedDevice)

onUnmounted(() => {
    if (interval) clearInterval(interval);
});

let progress = ref(0)
let interval: NodeJS.Timeout | null = null

const startProgress = () => {
    interval = setInterval(() => {
        if (progress.value < 100) {
            progress.value += 1;
        } else {
            if (interval) clearInterval(interval);
            // Perform the button click action here
        }
        if (progress.value === 100) {
            // perform function here
            if (props.num !== undefined) {
                performAction()
            }
            stopProgress()
        }
    }, props.speed); // Speed of the progress
};

const stopProgress = () => {
    if (interval) clearInterval(interval);
    progress.value = 0;
};

const performAction = async () => {
    if (num.value == 1) {
        await doMove(selectedDevice.value as Device)
    } else if (num.value == 2) {

    }
}

const doMove = async (printer: Device) => {
    await move(printer.device)
}
</script>

<template>
    <button type="button" class="btn btn-secondary" @mousedown="startProgress" @mouseup="stopProgress"
        @mouseleave="stopProgress" style="box-sizing: border-box;">
        <slot></slot>
        <div class="progress-bar-container">
            <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
        </div>
    </button>
</template>

<style scoped>
.progress-bar-container {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 5px;
    border-radius: 0 0 5px 5px;
    border-top: 1px solid #f5f5f6;
    background-color: #b8d4ff;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background-color: #007bff;
    border-radius: 0 0 5px 5px;
    overflow: hidden;
    width: 0;
}
</style>