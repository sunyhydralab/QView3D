<script setup lang="ts">
import { ref, onUnmounted } from 'vue';

const emit = defineEmits(['button-held'])

let progress = ref(0)
let interval: NodeJS.Timeout | null = null

const props = defineProps({
    color: String,
    disabled: Number
})

const disabled = props.disabled

onUnmounted(() => {
    if (interval) clearInterval(interval);
});

const startProgress = () => {
    interval = setInterval(() => {
        if (progress.value < 100) {
            progress.value += 1;
        } else {
            if (interval) clearInterval(interval);
        }
        if (progress.value === 100) {
            stopProgress()
            emit('button-held');
        }
    }, 10); // Speed of the progress
};

const stopProgress = () => {
    if (interval) clearInterval(interval);
    progress.value = 0;
};
</script>

<template>
    <div class="cont">
        <button :class="['btn hold-btn', 'btn-' + props.color]" @mousedown="startProgress" @mouseup="stopProgress"
            @mouseleave="stopProgress" style="box-sizing: border-box;">
            <slot></slot>
            <div class="progress-bar-container" :style="{ backgroundColor: `var(--${props.color}-light)` }">
                <div class="progress-bar"
                    :style="{ width: `${progress}%`, backgroundColor: `var(--${props.color}-dark)` }"></div>
            </div>
        </button>
    </div>
</template>

<style scoped>
.cont {
    position: relative;
    display: inline-block;
    opacity: 1;
}

.progress-bar-container {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 5px;
    border-radius: 0 0 5px 5px;
    border-top: 1px solid #f5f5f6;
    background-color: var(--primary-light);
    overflow: hidden;
}

.hold-btn {
    /* Your styles here */
    width: 100%; /* Add this line */
    box-sizing: border-box; /* Add this line */
}

.progress-bar {
    width: 100%; /* Add this line */
    box-sizing: border-box; /* Add this line */
    height: 100%;
    background-color: var(--primary-dark);
    border-radius: 0 0 5px 5px;
    overflow: hidden;
    width: 0;
}
</style>