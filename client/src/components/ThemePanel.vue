<script setup lang="ts">
import { ref, watch } from 'vue';
import { ColorPicker } from "vue3-colorpicker";
import "vue3-colorpicker/style.css";

const primary = ref<string>("#7561a9");
const success = ref<string>("#60AEAE");

const primaryTemp = ref<string>("7561a9");
const gradientColorPrimary = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");
const successTemp = ref<string>("60AEAE");
const gradientColorSuccess = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");

const revertColors = () => {
    primaryTemp.value = "#7561a9";
    successTemp.value = "#60AEAE";
    saveColors();
};

const saveColors = () => {
    primary.value = primaryTemp.value;
    success.value = successTemp.value;
    console.log(primary.value, success.value);

    document.documentElement.style.setProperty('--bs-primary-color', primary.value);
    document.documentElement.style.setProperty('--bs-pagination-bg', primary.value);
    let darkenedColor = newShade(primary.value, -20);
    console.log(darkenedColor);
    document.documentElement.style.setProperty('--bs-primary-color-hover', darkenedColor);
    let darkenedColor2 = newShade(primary.value, -40);
    document.documentElement.style.setProperty('--bs-primary-color-active', darkenedColor2);
    let lightenedColor = newShade(primary.value, 20);
    document.documentElement.style.setProperty('--bs-primary-color-disabled', lightenedColor);

    document.documentElement.style.setProperty('--bs-success-color', success.value);
    let darkenedColorSuccess = newShade(success.value, -20);
    document.documentElement.style.setProperty('--bs-success-color-hover', darkenedColorSuccess);
    let darkenedColor2Success = newShade(success.value, -40);
    document.documentElement.style.setProperty('--bs-success-color-active', darkenedColor2Success);
    let lightenedColorSuccess = newShade(success.value, 20);
    document.documentElement.style.setProperty('--bs-success-color-disabled', lightenedColorSuccess);
};

const newShade = (hexColor: string, magnitude: number) => {
    hexColor = hexColor.replace(`#`, ``);
    const decimalColor = parseInt(hexColor, 16);

    let r = ((decimalColor >> 16) & 0xff) + magnitude;
    r = r > 255 ? 255 : r < 0 ? 0 : r;

    let g = ((decimalColor >> 8) & 0xff) + magnitude;
    g = g > 255 ? 255 : g < 0 ? 0 : g;

    let b = (decimalColor & 0xff) + magnitude;
    b = b > 255 ? 255 : b < 0 ? 0 : b;

    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
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
                    <button class="btn btn-primary" @click="revertColors">Revert</button>
                    <button class="btn btn-success" @click="saveColors">Save</button>
                </div>
            </div>
            <div class="card">
                <div class="card-header text-center">
                    <h5 class="card-title">Font</h5>
                </div>
                <div class="card-body">
                </div>
                <div class="card-footer d-flex justify-content-between">
                    <button class="btn btn-primary" @click="revertColors">Revert</button>
                    <button class="btn btn-success" @click="saveColors">Save</button>
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
    --bs-btn-color: #fff;
    --bs-btn-bg: var(--bs-primary-color, #7561a9);
    --bs-btn-border-color: var(--bs-primary-color, #7561a9);
    --bs-btn-hover-color: #fff;
    --bs-btn-hover-bg: var(--bs-primary-color-hover, #5e548e);
    --bs-btn-hover-border-color: var(--bs-primary-color-hover, #5e548e);
    --bs-btn-focus-shadow-rgb: 49, 132, 253;
    --bs-btn-active-color: #fff;
    --bs-btn-active-bg: var(--bs-primary-color-active, #51457c);
    --bs-btn-active-border-color: var(--bs-primary-color-active, #51457c);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: #fff;
    --bs-btn-disabled-bg: var(--bs-primary-color-disabled, #9681ca);
    --bs-btn-disabled-border-color: var(--bs-primary-color-disabled, #9681ca);
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

.btn-success {
    --bs-btn-color: #fff;
    --bs-btn-bg: var(--bs-success-color, #60aeae);
    --bs-btn-border-color: #60aeae;
    --bs-btn-hover-color: #fff;
    --bs-btn-hover-bg: var(--bs-success-color-hover, #4a8e8b);
    --bs-btn-hover-border-color: var(--bs-success-color-hover, #4a8e8b);
    --bs-btn-focus-shadow-rgb: 60, 153, 110;
    --bs-btn-active-color: #fff;
    --bs-btn-active-bg: var(--bs-success-color-active, #3e7776);
    --bs-btn-active-border-color: #3e7776;
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: #fff;
    --bs-btn-disabled-bg: var(--bs-success-color-disabled, #88d3d3);
    --bs-btn-disabled-border-color: var(--bs-success-color-disabled, #88d3d3);
}

.btn-link {
    text-decoration: none !important;
}

.pagination {
    --bs-pagination-padding-x: 0.75rem;
    --bs-pagination-padding-y: 0.375rem;
    --bs-pagination-font-size: 1rem;
    --bs-pagination-color: #fff;
    --bs-pagination-bg: var(--bs-primary-color, #7561a9);
    --bs-pagination-border-width: var(--bs-border-width);
    --bs-pagination-border-color: #929292;
    --bs-pagination-border-radius: var(--bs-border-radius);
    --bs-pagination-hover-color: #fff;
    --bs-pagination-hover-bg: var(--bs-primary-color-hover, #5e548e);
    --bs-pagination-hover-border-color: #929292;
    --bs-pagination-focus-color: #fff;
    --bs-pagination-focus-bg: var(--bs-primary-color-hover, #5e548e);
    --bs-pagination-focus-box-shadow: 0 0 0 0.25rem rgba(49, 132, 253, 0.25);
    --bs-pagination-active-color: #fff;
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
}

a,
.btn-link {
    color: var(--bs-primary-color, #7561a9);
}

a:hover,
.btn-link:hover {
    color: var(--bs-primary-color-hover, #5e548e);
}
</style>