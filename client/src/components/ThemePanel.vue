<script setup lang="ts">
import { ref, watch, watchEffect, onMounted } from 'vue';
import { ColorPicker } from "vue3-colorpicker";
import "vue3-colorpicker/style.css";
import "@/assets/base.css";

const primary = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary'));
const primaryFont = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-text'));
const secondary = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary'));
const secondaryFont = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-font'));


const primaryTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary'));
const primaryFontTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-text'));
const gradientColorPrimary = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");
const secondaryTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary'));
const secondaryFontTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-font'));
const gradientColorSuccess = ref("linear-gradient(0deg, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, 1) 100%)");

const uploadedFontFace = ref<FontFace | null>(null);
const uploadedFontFaceTemp = ref<FontFace | null>(null);
const fontFileName = ref(null);

const backgroundColor = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-background'));

interface ThemeSettings {
  primary: string;
  secondary: string;
  backgroundColor: string;
  primaryFont: string;
  secondaryFont: string;
}

const themeSettings = ref<ThemeSettings | null>();

const saveThemeSettings = () => {
  themeSettings.value = {
    primary: primary.value,
    secondary: secondary.value,
    backgroundColor: backgroundColor.value,
    primaryFont: primaryFont.value,
    secondaryFont: secondaryFont.value
  }

  localStorage.setItem('themeSettings', JSON.stringify(themeSettings.value));
};

const loadThemeSettings = () => {
  const savedThemeSettings = localStorage.getItem('themeSettings');
  if (savedThemeSettings) {
    themeSettings.value = JSON.parse(savedThemeSettings);

    if (themeSettings.value) {
        primary.value = themeSettings.value.primary;
        primaryFont.value = themeSettings.value.primaryFont;
        secondary.value = themeSettings.value.secondary;
        secondaryFont.value = themeSettings.value.secondaryFont;
        backgroundColor.value = themeSettings.value.backgroundColor;
    }
  } else {
    themeSettings.value = {
        primary: primary.value,
        secondary: secondary.value,
        backgroundColor: backgroundColor.value,
        primaryFont: primaryFont.value,
        secondaryFont: secondaryFont.value
    }
  }
  saveColors();
};

const revertColors = () => {
    primary.value = getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary-reversion');
    secondary.value = getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-reversion');
    backgroundColor.value = getComputedStyle(document.documentElement, null).getPropertyValue('--color-background-reversion');
    primaryFont.value = fontColor(primaryTemp.value);
    successFont.value = fontColor(successTemp.value);
    saveColors();
};

const saveColors = () => {
    //primary.value = primaryTemp.value;
    primaryFont.value = fontColor(primary.value);
    //secondary.value = secondaryTemp.value;
    secondaryFont.value = fontColor(secondary.value);

    document.documentElement.style.setProperty('--color-text', primaryFont.value);
    document.documentElement.style.setProperty('--color-secondary-font', secondaryFont.value);
    document.documentElement.style.setProperty('--main-background-color', backgroundColor.value);

    document.documentElement.style.setProperty('--color-background', backgroundColor.value);

    document.documentElement.style.setProperty('--color-primary', primary.value);
    document.documentElement.style.setProperty('--bs-pagination-bg', primary.value);
    let darkenedColor = newShade(primary.value, -10);
    document.documentElement.style.setProperty('--color-primary-hover', darkenedColor);
    let darkenedColor2 = newShade(primary.value, -20);
    document.documentElement.style.setProperty('--color-primary-active', darkenedColor2);
    let lightenedColor = newShade(primary.value, 25);
    document.documentElement.style.setProperty('--color-primary-disabled', lightenedColor);

    document.documentElement.style.setProperty('--color-secondary', secondary.value);
    let darkenedColorSuccess = newShade(success.value, -10);
    document.documentElement.style.setProperty('--color-success-hover', darkenedColorSuccess);
    let darkenedColor2Success = newShade(success.value, -20);
    document.documentElement.style.setProperty('--color-success-active', darkenedColor2Success);
    let lightenedColorSuccess = newShade(success.value, 25);
    document.documentElement.style.setProperty('--color-success-disabled', lightenedColorSuccess);
    
    // save in localstorage
    saveThemeSettings();
};

watchEffect(() => {
    if (primaryTemp.value !== primary.value || secondaryTemp.value !== secondary.value) {
        primaryFontTemp.value = fontColor(primaryTemp.value);
        secondaryFontTemp.value = fontColor(secondaryTemp.value);

        document.documentElement.style.setProperty('--bs-primary-font-color-temp', primaryFontTemp.value);
        document.documentElement.style.setProperty('--bs-success-font-color-temp', secondaryFontTemp.value);

        document.documentElement.style.setProperty('--color-background', backgroundColor.value);

        document.documentElement.style.setProperty('--bs-primary-color-temp', primaryTemp.value);
        let darkenedColor = newShade(primaryTemp.value, -10);
        document.documentElement.style.setProperty('--bs-primary-color-hover-temp', darkenedColor);
        let darkenedColor2 = newShade(primaryTemp.value, -20);
        document.documentElement.style.setProperty('--bs-primary-color-active-temp', darkenedColor2);
        let lightenedColor = newShade(primaryTemp.value, 25);
        document.documentElement.style.setProperty('--bs-primary-color-disabled-temp', lightenedColor);

        document.documentElement.style.setProperty('--bs-success-color-temp', secondaryTemp.value);
        let darkenedColorSuccess = newShade(secondaryTemp.value, -10);
        document.documentElement.style.setProperty('--bs-success-color-hover-temp', darkenedColorSuccess);
        let darkenedColor2Success = newShade(secondaryTemp.value, -20);
        document.documentElement.style.setProperty('--bs-success-color-active-temp', darkenedColor2Success);
        let lightenedColorSuccess = newShade(secondaryTemp.value, 25);
        document.documentElement.style.setProperty('--bs-success-color-disabled-temp', lightenedColorSuccess);
    }
});

const newShade = (rgb: string, magnitude: number): string => {
    // Extract the individual red, green, and blue color values
    const rgbValues = ref<string[] | Number[]>();
    if (rgb.startsWith("rgb(")) {
        rgb = rgb.replace("rgb(", "rgba(");
        rgb = rgb.replace(")", ", 1)");
    }
    if (rgb.startsWith("rgba(")) {
        // Extract the individual red, green, blue and alpha color values
        rgbValues.value = rgb.match(/\d+/g);
    } else {
        regbValues.value = rgb.match(/\w\w/g);
        for (let i = 0; i < rgbValues.value.length; i++) {
            rgbValues.value[i] = parseInt(rgbValues[i], 16);
        }
    }
    console.log(rgb, rgbValues.value);
    if (rgbValues.value.length !== 4) {
        throw new Error('Invalid RGB color');
    }

    // Adjust color brightness
    rgbValues.value[0] = Math.round(Math.min(Math.max(0, r + (r * magnitude / 100)), 255));
    rgbValues.value[1] = Math.round(Math.min(Math.max(0, g + (g * magnitude / 100)), 255));
    rgbValues.value[2] = Math.round(Math.min(Math.max(0, b + (b * magnitude / 100)), 255));
    rgbValues.value[3] = Math.min(Math.max(0, a + (a * magnitude / 100)), 1);
    console.log(rgbValues.value);
    // Return the new color in RGB format
    return `rgb(${rgbValues.value[0]}, ${rgbValues.value[1]}, ${rgbValues.value[2]}, ${rgbValues.value[3]})`;
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

onMounted(() => {
    loadThemeSettings();
});
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
                        <color-picker id="primaryPicker" v-model:pureColor="primary"
                            v-model:gradientColor="primary" class="color-picker" />
                    </div>
                    <div class="color-picker-container">
                        <label for="secondaryColorPicker">Secondary Color</label>
                        <color-picker id="secondaryPicker" v-model:pureColor="secondary"
                            v-model:gradientColor="secondary" class="color-picker" />
                    </div>
                    <div class="color-picker-container">
                        <label for="backgroundColorPicker">Background Color</label>
                        <color-picker id="backgroundColorPicker" v-model:pureColor="backgroundColor"
                                      v-model:gradientColor="backgroundColor" class="color-picker"/>
                    </div>
                </div>
                <div class="card-footer d-flex justify-content-between">
                    <button class="btn"
                            :class="{ 'btn-primary-temp': primaryTemp !== primary, 'btn-primary': primaryTemp === primary }"
                            @click="revertColors">Revert
                    </button>
                    <button class="btn"
                        :class="{ 'btn-success-temp': secondaryTemp !== secondary, 'btn-success': secondaryTemp === secondary }"
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
.offcanvas-body {
    background-color: var(--color-modal-background);
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
    color: var(--color-text);
    background-color: var(--color-border-invert);
    margin-bottom: 0;
}

.card {
    border: 1px solid var(--color-modal-background-inverted);
    overflow: hidden;
}

.card-header,
.card-footer {
    color: var(--color-text);
    background-color: var(--color-border-invert);
}
label.form-control{
    background-color: var(--color-modal-background);
    color: var(--color-text);
    border: 1px solid var(--color-border);
}
</style>

<style>
.btn-primary {
    --bs-btn-color: var(--color-text);
    --bs-btn-bg: var(--color-primary);
    --bs-btn-border-color: var(--color-primary);
    --bs-btn-hover-color: var(--color-text);
    --bs-btn-hover-bg: var(--color-primary-hover);
    --bs-btn-hover-border-color: var(--color-primary-hover);
    --bs-btn-focus-shadow-rgb: 49, 132, 253;
    --bs-btn-active-color: var(--color-text);
    --bs-btn-active-bg: var(--color-primary-active);
    --bs-btn-active-border-color: var(--color-primary-active);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--color-text);
    --bs-btn-disabled-bg: var(--color-primary-disabled);
    --bs-btn-disabled-border-color: var(--color-primary-disabled);
}

.btn-primary-temp {
    --bs-btn-color: var(--color-text);
    --bs-btn-bg: var(--color-primary);
    --bs-btn-border-color: var(--color-primary);
    --bs-btn-hover-color: var(--color-text);
    --bs-btn-hover-bg: var(--color-primary-hover);
    --bs-btn-hover-border-color: var(--color-primary-hover);
    --bs-btn-focus-shadow-rgb: 49, 132, 253;
    --bs-btn-active-color: var(--color-text);
    --bs-btn-active-bg: var(--color-primary-active);
    --bs-btn-active-border-color: var(--color-primary-active);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--color-text);
    --bs-btn-disabled-bg: var(--color-primary-disabled);
    --bs-btn-disabled-border-color: var(--color-primary-disabled);
}

.btn-success {
    --bs-btn-color: var(--color-secondary-font);
    --bs-btn-bg: var(--color-secondary);
    --bs-btn-border-color: var(--color-secondary);
    --bs-btn-hover-color: var(--color-secondary-font);
    --bs-btn-hover-bg: var(--color-secondary-hover);
    --bs-btn-hover-border-color: var(--color-secondary-hover);
    --bs-btn-focus-shadow-rgb: 49, 132, 253;
    --bs-btn-active-color: var(--color-secondary-font);
    --bs-btn-active-bg: var(--color-secondary-active);
    --bs-btn-active-border-color: var(--color-secondary-active);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--color-secondary-font);
    --bs-btn-disabled-bg: var(--color-secondary-disabled);
    --bs-btn-disabled-border-color: var(--color-secondary-disabled);
}

.btn-success-temp {
    --bs-btn-color: var(--color-secondary-font);
    --bs-btn-bg: var(--color-secondary);
    --bs-btn-border-color: var(--color-secondary);
    --bs-btn-hover-color: var(--color-secondary-font);
    --bs-btn-hover-bg: var(--color-primary-hover);
    --bs-btn-hover-border-color: var(--color-secondary-hover);
    --bs-btn-focus-shadow-rgb: 49, 132, 253;
    --bs-btn-active-color: var(--color-secondary-font);
    --bs-btn-active-bg: var(--color-secondary-active);
    --bs-btn-active-border-color: var(--color-secondary-active);
    --bs-btn-active-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    --bs-btn-disabled-color: var(--color-secondary-font);
    --bs-btn-disabled-bg: var(--color-secondary-disabled);
    --bs-btn-disabled-border-color: var(--color-secondary-disabled);
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
    --bs-pagination-color: var(--color-text);
    --bs-pagination-bg: var(--color-primary);
    --bs-pagination-border-width: var(--bs-border-width);
    --bs-pagination-border-color: #929292;
    --bs-pagination-border-radius: var(--bs-border-radius);
    --bs-pagination-hover-color: var(--color-text);
    --bs-pagination-hover-bg: var(--color-primary-hover);
    --bs-pagination-hover-border-color: #929292;
    --bs-pagination-focus-color: var(--color-text);
    --bs-pagination-focus-bg: var(--color-primary-hover);
    --bs-pagination-focus-box-shadow: 0 0 0 0.25rem rgba(49, 132, 253, 0.25);
    --bs-pagination-active-color: var(--color-text);
    --bs-pagination-active-bg: var(--color-primary-active);
    --bs-pagination-active-border-color: #929292;
    --bs-pagination-disabled-color: #525252;
    --bs-pagination-disabled-bg: #d8d8d8;
    --bs-pagination-disabled-border-color: #929292;
    list-style: none;
}

.progress {
    --bs-progress-bar-bg: var(--color-primary, #7561a9);
    --bs-progress-bg: #d8d8d8;
    border: 1px solid #b9b9b9;
}

.alert {
    --bs-alert-border: 1px solid #ad6060;
    --bs-alert-bg: #e4b6b6;
}

input[type='checkbox']:checked,
input[type='radio']:checked {
    background-color: var(--color-secondary) !important;
    border-color: var(--color-secondary) !important;
}

.dropdown-menu li a:active,
.dropdown-item:active,
.dropdown-submenu .dropdown-item:active {
    background-color: var(--color-primary);
    color: var(--color-text);
}

a {
    color: var(--color-text);
}

.btn-link, .routerLink {
    color: var(--color-primary);
}

a:hover {
    color: var(--color-text);
}

.btn-link:hover, .routerLink:hover {
    color: var(--color-primary-hover);
}

a:active {
    color: var(--color-text) !important;
}

.btn-link:active, .routerLink:active {
    color: var(--color-primary-active) !important;
}

.dp__theme_light {
    --dp-primary-color: var(--color-primary) !important;
    --dp-primary-disabled-color: var(--color-primary-disabled) !important;
    --dp-primary-text-color: var(--color-text) !important;
}

.dp__action_cancel,
.dp__action_cancel:hover {
    color: #484848 !important;
    border: 1px solid #484848 !important;
}

.nav-link:not(.active-tab):hover {
    color: var(--color-primary);
}

.current-page {
    background-color: var(--color-primary);
    color: white;
    padding: 5px;
    display: inline-block;
    border-right: 2px solid var(--color-primary);
    border-bottom: 2px solid var(--color-primary);
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
    background-color: var(--color-primary);
    color: #dbdbdb;
}

.d-flex.align-items-center .fas.fa-star {
    color: var(--color-secondary);
}

*,
input {
    font-family: var(--user-font, 'Public Sans'), sans-serif;
}

.dp__action_button {
    font-family: var(--user-font, 'Public Sans'), sans-serif !important;
}
</style>