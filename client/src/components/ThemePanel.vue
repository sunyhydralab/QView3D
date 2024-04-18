<script setup lang="ts">
import { ref } from 'vue';
import { ColorPicker } from "vue3-colorpicker";
import "vue3-colorpicker/style.css";

const primary = ref<string>("7561a9");
const gradientColorPrimary = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");
const secondary = ref<string>("60AEAE");
const gradientColorSecondary = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");

</script>

<template>
    <div class="offcanvas offcanvas-end" tabindex="-1" id="themeOffcanvas" aria-labelledby="themeOffcanvasLabel" style="background-color: #b9b9b9;">
        <div class="offcanvas-header" style="background-color: #484848; color: #dbdbdb;">
            <h5 id="themeOffcanvasLabel">Theme Settings</h5>
            <button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        </div>
        <div class="offcanvas-body">
            <div class="color-picker-container">
                <label for="primaryColorPicker">Primary Color</label>
                <color-picker id="primaryColorPicker" v-model:pureColor="primary"
                    v-model:gradientColor="gradientColorPrimary" class="color-picker" />
            </div>
            <div class="color-picker-container">
                <label for="secondaryColorPicker">Secondary Color</label>
                <color-picker id="secondaryColorPicker" v-model:pureColor="secondary"
                    v-model:gradientColor="gradientColorSecondary" class="color-picker" />
            </div>
        </div>
    </div>

    <div class="position-fixed bottom-0 end-0 m-3">
        <button class="btn btn-primary" data-bs-toggle="offcanvas" data-bs-target="#themeOffcanvas">
            <i class="fas fa-palette"></i> <!-- Font Awesome icon -->
        </button>
    </div>
</template>

<style scoped>
.color-picker-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 20px;
}

.color-picker-container label {
    margin-bottom: 10px;
    font-size: 20px;
}

.color-picker-container .color-picker {
    width: 300px;
    height: 300px;
}
</style>