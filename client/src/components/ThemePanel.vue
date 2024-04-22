<script setup lang="ts">
import { ref, watch, watchEffect } from 'vue';
import { ColorPicker } from "vue3-colorpicker";
import "vue3-colorpicker/style.css";

const primary = ref<string>("rgb(117, 97, 169)");
const primaryFont = ref<string>("white");
const success = ref<string>("rgb(96, 174, 174)");
const successFont = ref<string>("white");

const primaryTemp = ref<string>("rgb(117, 97, 169)");
const primaryFontTemp = ref<string>("white");
const gradientColorPrimary = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");
const successTemp = ref<string>("rgb(96, 174, 174)");
const successFontTemp = ref<string>("white");
const gradientColorSuccess = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");

const uploadedFontFace = ref<FontFace | null>(null);
const uploadedFontFaceTemp = ref<FontFace | null>(null);
const fontFileName = ref(null);

const revertColors = () => {
    primaryTemp.value = "rgb(117, 97, 169)";
    successTemp.value = "rgb(96, 174, 174)";
    primaryFontTemp.value = fontColor(primaryTemp.value);
    successFontTemp.value = fontColor(successTemp.value);

    saveColors();
};

const saveColors = () => {
    primary.value = primaryTemp.value;
    primaryFont.value = fontColor(primary.value);
    success.value = successTemp.value;
    successFont.value = fontColor(success.value);

    document.documentElement.style.setProperty('--bs-primary-font-color', primaryFont.value);
    document.documentElement.style.setProperty('--bs-success-font-color', successFont.value);

    document.documentElement.style.setProperty('--bs-primary-color', primary.value);
    document.documentElement.style.setProperty('--bs-pagination-bg', primary.value);
    let darkenedColor = newShade(primary.value, -10);
    document.documentElement.style.setProperty('--bs-primary-color-hover', darkenedColor);
    let darkenedColor2 = newShade(primary.value, -20);
    document.documentElement.style.setProperty('--bs-primary-color-active', darkenedColor2);
    let lightenedColor = newShade(primary.value, 25);
    document.documentElement.style.setProperty('--bs-primary-color-disabled', lightenedColor);

    document.documentElement.style.setProperty('--bs-success-color', success.value);
    let darkenedColorSuccess = newShade(success.value, -10);
    document.documentElement.style.setProperty('--bs-success-color-hover', darkenedColorSuccess);
    let darkenedColor2Success = newShade(success.value, -20);
    document.documentElement.style.setProperty('--bs-success-color-active', darkenedColor2Success);
    let lightenedColorSuccess = newShade(success.value, 25);
    document.documentElement.style.setProperty('--bs-success-color-disabled', lightenedColorSuccess);
};

watchEffect(() => {
    if (primaryTemp.value !== primary.value || successTemp.value !== success.value) {
        primaryFontTemp.value = fontColor(primaryTemp.value);
        successFontTemp.value = fontColor(successTemp.value);

        document.documentElement.style.setProperty('--bs-primary-font-color-temp', primaryFontTemp.value);
        document.documentElement.style.setProperty('--bs-success-font-color-temp', successFontTemp.value);

        document.documentElement.style.setProperty('--bs-primary-color-temp', primaryTemp.value);
        let darkenedColor = newShade(primaryTemp.value, -10);
        document.documentElement.style.setProperty('--bs-primary-color-hover-temp', darkenedColor);
        let darkenedColor2 = newShade(primaryTemp.value, -20);
        document.documentElement.style.setProperty('--bs-primary-color-active-temp', darkenedColor2);
        let lightenedColor = newShade(primaryTemp.value, 25);
        document.documentElement.style.setProperty('--bs-primary-color-disabled-temp', lightenedColor);

        document.documentElement.style.setProperty('--bs-success-color-temp', successTemp.value);
        let darkenedColorSuccess = newShade(successTemp.value, -10);
        document.documentElement.style.setProperty('--bs-success-color-hover-temp', darkenedColorSuccess);
        let darkenedColor2Success = newShade(successTemp.value, -20);
        document.documentElement.style.setProperty('--bs-success-color-active-temp', darkenedColor2Success);
        let lightenedColorSuccess = newShade(successTemp.value, 25);
        document.documentElement.style.setProperty('--bs-success-color-disabled-temp', lightenedColorSuccess);
    }
});

const newShade = (rgb: string, magnitude: number): string => {
    // Extract the individual red, green, and blue color values
    let rgbValues = rgb.match(/\d+/g);

    if (!rgbValues) {
        throw new Error('Invalid RGB color');
    }

    let [r, g, b] = rgbValues.map(Number);

    // Adjust color brightness
    r = Math.round(Math.min(Math.max(0, r + (r * magnitude / 100)), 255));
    g = Math.round(Math.min(Math.max(0, g + (g * magnitude / 100)), 255));
    b = Math.round(Math.min(Math.max(0, b + (b * magnitude / 100)), 255));

    // Return the new color in RGB format
    return `rgb(${r}, ${g}, ${b})`;
};

const brightness = (rgb: string) => {
    let rgbValues = rgb.match(/\d+/g);

    if (!rgbValues) {
        throw new Error('Invalid RGB color');
    }

    let [r, g, b] = rgbValues.map(Number);

    return Math.round(((r * 299) + (g * 587) + (b * 114)) / 1000);
}

const fontColor = (rgb: string) => {
    return brightness(rgb) > 155 ? 'black' : 'white';
}

const handleFontUpload = (event: any) => {
    let file = event.target.files[0];
    fontFileName.value = file.name;
    let reader = new FileReader();

    reader.onloadend = () => {
        if (reader.result) {
            let fontFace = new FontFace('userFontTemp', reader.result as ArrayBuffer);
            fontFace.load().then((loadedFace) => {
                uploadedFontFaceTemp.value = loadedFace;
                // Set the CSS variable here for the preview
                document.documentElement.style.setProperty('--user-font-temp', 'userFontTemp');
            });
        }
    };

    reader.readAsArrayBuffer(file);
};

const saveFont = () => {
    if (uploadedFontFaceTemp.value) {
        uploadedFontFace.value = uploadedFontFaceTemp.value;
        document.fonts.add(uploadedFontFace.value); // Add the font to document.fonts here
        document.documentElement.style.setProperty('--user-font', 'userFontTemp'); // Set the CSS variable here
        // Reset the temporary CSS variable
        document.documentElement.style.setProperty('--user-font-temp', 'Public Sans');
        uploadedFontFaceTemp.value = null;
        fontFileName.value = null;
    }
};

const triggerFileInput = () => {
    const fileInput = document.getElementById('fontFile') as HTMLInputElement;
    fileInput.click();
}

const revertFont = () => {
    document.documentElement.style.removeProperty('--user-font');
    uploadedFontFaceTemp.value = null;
    uploadedFontFace.value = null;
    fontFileName.value = null;
};

</script>

<template>
    <div class="offcanvas offcanvas-end" tabindex="-1" id="themeOffcanvas" aria-labelledby="themeOffcanvasLabel"
        style="background-color: #b9b9b9;">
        <div class="offcanvas-header" style="background-color: #484848; color: #dbdbdb;">
            <h5 id="themeOffcanvasLabel">Theme Settings</h5>
            <button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        </div>
        <div class="offcanvas-body">
            <div class="card mb-3">
                <div class="card-header text-center">
                    <h5 class="card-title">Color</h5>
                </div>
                <div class="card-body">
                    <div class="color-picker-container mb-3">
                        <label for="primaryColorPicker">Primary Color</label>
                        <color-picker id="primaryColorPicker" v-model:pureColor="primaryTemp"
                            v-model:gradientColor="gradientColorPrimary" class="color-picker" />
                    </div>
                    <div class="color-picker-container">
                        <label for="secondaryColorPicker">Secondary Color</label>
                        <color-picker id="secondaryColorPicker" v-model:pureColor="successTemp"
                            v-model:gradientColor="gradientColorSuccess" class="color-picker" />
                    </div>
                </div>
                <div class="card-footer d-flex justify-content-between">
                    <button class="btn"
                        :class="{ 'btn-primary-temp': primaryTemp !== primary, 'btn-primary': primaryTemp === primary }"
                        @click="revertColors">Revert</button>
                    <button class="btn"
                        :class="{ 'btn-success-temp': successTemp !== success, 'btn-success': successTemp === success }"
                        @click="saveColors">Save</button>
                </div>
            </div>
            <div class="card">
                <div class="card-header text-center">
                    <h5 class="card-title">Font</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label for="fontFile" class="form-label">Upload your .ttf file</label>
                        <input ref="fontFileInput" @change="handleFontUpload" style="display: none;" type="file"
                            id="fontFile" name="fontFile" accept=".ttf">
                        <div class="input-group">
                            <button type="button" @click="triggerFileInput" class="btn btn-primary">Browse</button>
                            <label class="form-control" style="width: 220px;">
                                <div v-if="fontFileName" class="ellipsis" style="width: 200px;"> {{ fontFileName }}
                                </div>
                                <div v-else>No font selected.</div>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="card-footer d-flex justify-content-between">
                    <button class="btn btn-primary" @click="revertFont">Revert</button>
                    <button class="btn btn-success" @click="saveFont" v-bind:disabled="!fontFileName">Save</button>
                </div>
            </div>
        </div>
    </div>

    <div class="position-fixed bottom-0 end-0 m-3">
        <button class="btn btn-primary" data-bs-toggle="offcanvas" data-bs-target="#themeOffcanvas">
            <i class="fas fa-palette"></i>
        </button>
    </div>
</template>

<style scoped>
.form-control,
.list-group-item {
    background-color: #f4f4f4 !important;
    border-color: #484848 !important;
}

.ellipsis {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

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

.card-body {
    background-color: #cdcdcd;
    margin-bottom: 0;
}

.card {
    border: 1px solid #484848;
    overflow: hidden;
}

.card-header,
.card-footer {
    background-color: #9f9f9f;
}
</style>

<style>
.btn-primary {
    --bs-btn-color: var(--bs-primary-font-color, #fff);
    --bs-btn-bg: var(--bs-primary-color, #7561a9);
    --bs-btn-border-color: var(--bs-primary-color, #7561a9);
    --bs-btn-hover-color: var(--bs-primary-font-color, #fff);
    --bs-btn-hover-bg: var(--bs-primary-color-hover, #5e548e);
    --bs-btn-hover-border-color: var(--bs-primary-color-hover, #5e548e);
    --bs-btn-focus-shadow-rgb: 49, 132, 253;
    --bs-btn-active-color: var(--bs-primary-font-color, #fff);
    --bs-btn-active-bg: var(--bs-primary-color-active, #51457c);
    --bs-btn-active-border-color: var(--bs-primary-color-active, #51457c);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--bs-primary-font-color, #fff);
    --bs-btn-disabled-bg: var(--bs-primary-color-disabled, #9681ca);
    --bs-btn-disabled-border-color: var(--bs-primary-color-disabled, #9681ca);
}

.btn-primary-temp {
    --bs-btn-color: var(--bs-primary-font-color-temp, #fff);
    --bs-btn-bg: var(--bs-primary-color-temp, #7561a9);
    --bs-btn-border-color: var(--bs-primary-color-temp, #7561a9);
    --bs-btn-hover-color: var(--bs-primary-font-color-temp, #fff);
    --bs-btn-hover-bg: var(--bs-primary-color-hover-temp, #5e548e);
    --bs-btn-hover-border-color: var(--bs-primary-color-hover-temp, #5e548e);
    --bs-btn-focus-shadow-rgb: 49, 132, 253;
    --bs-btn-active-color: var(--bs-primary-font-color-temp, #fff);
    --bs-btn-active-bg: var(--bs-primary-color-active-temp, #51457c);
    --bs-btn-active-border-color: var(--bs-primary-color-active-temp, #51457c);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--bs-primary-font-color-temp, #fff);
    --bs-btn-disabled-bg: var(--bs-primary-color-disabled-temp, #9681ca);
    --bs-btn-disabled-border-color: var(--bs-primary-color-disabled-temp, #9681ca);
}

.btn-success {
    --bs-btn-color: var(--bs-success-font-color, #fff);
    --bs-btn-bg: var(--bs-success-color, #60aeae);
    --bs-btn-border-color: var(--bs-success-color, #60aeae);
    --bs-btn-hover-color: var(--bs-success-font-color, #fff);
    --bs-btn-hover-bg: var(--bs-success-color-hover, #4a8e8b);
    --bs-btn-hover-border-color: var(--bs-success-color-hover, #4a8e8b);
    --bs-btn-focus-shadow-rgb: 60, 153, 110;
    --bs-btn-active-color: var(--bs-success-font-color, #fff);
    --bs-btn-active-bg: var(--bs-success-color-active, #3e7776);
    --bs-btn-active-border-color: var(--bs-success-color-active, #3e7776);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--bs-success-font-color, #fff);
    --bs-btn-disabled-bg: var(--bs-success-color-disabled, #88d3d3);
    --bs-btn-disabled-border-color: var(--bs-success-color-disabled, #88d3d3);
}

.btn-success-temp {
    --bs-btn-color: var(--bs-success-font-color-temp, #fff);
    --bs-btn-bg: var(--bs-success-color-temp, #60aeae);
    --bs-btn-border-color: var(--bs-success-color-temp, #60aeae);
    --bs-btn-hover-color: var(--bs-success-font-color-temp, #fff);
    --bs-btn-hover-bg: var(--bs-success-color-hover-temp, #4a8e8b);
    --bs-btn-hover-border-color: var(--bs-success-color-hover-temp, #4a8e8b);
    --bs-btn-focus-shadow-rgb: 60, 153, 110;
    --bs-btn-active-color: var(--bs-success-font-color-temp, #fff);
    --bs-btn-active-bg: var(--bs-success-color-active-temp, #3e7776);
    --bs-btn-active-border-color: var(--bs-success-color-active-temp, #3e7776);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--bs-success-font-color-temp, #fff);
    --bs-btn-disabled-bg: var(--bs-success-color-disabled-temp, #88d3d3);
    --bs-btn-disabled-border-color: var(--bs-success-color-disabled-temp, #88d3d3);
}

.btn-danger {
    --bs-btn-color: #fff;
    --bs-btn-bg: #ad6060;
    --bs-btn-border-color: #ad6060;
    --bs-btn-hover-color: #fff;
    --bs-btn-hover-bg: #935252;
    --bs-btn-hover-border-color: #935252;
    --bs-btn-focus-shadow-rgb: 225, 83, 97;
    --bs-btn-active-color: #fff;
    --bs-btn-active-bg: #794343;
    --bs-btn-active-border-color: #794343;
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: #fff;
    --bs-btn-disabled-bg: #ad6060;
    --bs-btn-disabled-border-color: #ad6060;
}

.btn-link {
    text-decoration: none !important;
}

.pagination {
    --bs-pagination-padding-x: 0.75rem;
    --bs-pagination-padding-y: 0.375rem;
    --bs-pagination-font-size: 1rem;
    --bs-pagination-color: var(--bs-primary-font-color, #fff);
    --bs-pagination-bg: var(--bs-primary-color, #7561a9);
    --bs-pagination-border-width: var(--bs-border-width);
    --bs-pagination-border-color: #929292;
    --bs-pagination-border-radius: var(--bs-border-radius);
    --bs-pagination-hover-color: var(--bs-primary-font-color, #fff);
    --bs-pagination-hover-bg: var(--bs-primary-color-hover, #5e548e);
    --bs-pagination-hover-border-color: #929292;
    --bs-pagination-focus-color: var(--bs-primary-font-color, #fff);
    --bs-pagination-focus-bg: var(--bs-primary-color-hover, #5e548e);
    --bs-pagination-focus-box-shadow: 0 0 0 0.25rem rgba(49, 132, 253, 0.25);
    --bs-pagination-active-color: var(--bs-primary-font-color, #fff);
    --bs-pagination-active-bg: var(--bs-primary-color-active, #51457c);
    --bs-pagination-active-border-color: #929292;
    --bs-pagination-disabled-color: #525252;
    --bs-pagination-disabled-bg: #d8d8d8;
    --bs-pagination-disabled-border-color: #929292;
    list-style: none;
}

.progress {
    --bs-progress-bar-bg: var(--bs-primary-color, #7561a9);
    --bs-progress-bg: #d8d8d8;
    border: 1px solid #b9b9b9;
}

.alert {
    --bs-alert-border: 1px solid #ad6060;
    --bs-alert-bg: #e4b6b6;
}

input[type='checkbox']:checked,
input[type='radio']:checked {
    background-color: var(--bs-success-color, #60aeae) !important;
    border-color: var(--bs-success-color, #60aeae) !important;
}

.dropdown-menu li a:active,
.dropdown-item:active,
.dropdown-submenu .dropdown-item:active {
    background-color: var(--bs-primary-color, #7561a9);
    color: var(--bs-primary-font-color, #fff);
}

a,
.btn-link {
    color: var(--bs-primary-color, #7561a9);
}

a:hover,
.btn-link:hover {
    color: var(--bs-primary-color-hover, #5e548e);
}

a:active,
.btn-link:active {
    color: var(--bs-primary-color-active, #fff) !important;
}

.dp__theme_light {
    --dp-primary-color: var(--bs-primary-color, #7561a9) !important;
    --dp-primary-disabled-color: var(--bs-primary-color-disabled, #9681ca) !important;
    --dp-primary-text-color: var(--bs-primary-font-color, #fff) !important;
}

.dp__action_cancel,
.dp__action_cancel:hover {
    color: #484848 !important;
    border: 1px solid #484848 !important;
}

.nav-link:not(.active-tab):hover {
    color: var(--bs-primary-color, #7561a9);
}

.current-page {
    background-color: var(--bs-primary-color, #7561a9);
    color: white;
    padding: 5px;
    display: inline-block;
    border-right: 2px solid var(--bs-primary-color, #7561a9);
    border-bottom: 2px solid var(--bs-primary-color, #7561a9);
    border-bottom-right-radius: 5px;
    position: relative;
    z-index: 1;
    box-shadow: 0 2px 6px -2px #303035;
    padding-left: 15px;
    padding-right: 15px;
}

.header {
    padding-left: 10px;
    padding-right: 10px;
    padding-top: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
    background-color: var(--bs-primary-color, #7561a9);
    color: #dbdbdb;
}

.d-flex.align-items-center .fas.fa-star {
    color: var(--bs-success-color, #60aeae);
}

*,
input {
    font-family: var(--user-font, 'Public Sans'), sans-serif;
}

.dp__action_button {
    font-family: var(--user-font, 'Public Sans'), sans-serif !important;
}
</style>