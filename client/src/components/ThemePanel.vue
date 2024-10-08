<script setup lang="ts">
import {ref, watch, watchEffect, onMounted, onBeforeUnmount} from 'vue';
import {Vue3ColorPicker} from '@cyhnkckali/vue3-color-picker';
import {vOnClickOutside} from '@vueuse/components'
import "@/assets/base.css";

const prefersDarkScheme = ref(window.matchMedia('(prefers-color-scheme: dark)').matches);

// Create a function to update the theme based on the preference
const updateTheme = () => {
    prefersDarkScheme.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
    revertColors(); // Call your function to revert colors based on the new preference
};

// Set up the media query listener
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

const primary = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary'));
const primaryFont = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-text'));
const secondary = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary'));
const secondaryFont = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-font'));
const background = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-background'));
const backgroundFont = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-background-font'));

const primaryTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary'));
const primaryFontTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-text'));
const secondaryTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary'));
const secondaryFontTemp = ref<string>(getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-font'));

const uploadedFontFace = ref<FontFace | null>(null);
const uploadedFontFaceTemp = ref<FontFace | null>(null);
const fontFileName = ref(null);


const showPrimaryColorPicker = ref(false);
const showSecondaryColorPicker = ref(false);
const showBackgroundColorPicker = ref(false);

function hidePrimaryColorPicker() {
    showPrimaryColorPicker.value = false;
}

function hideSecondaryColorPicker() {
    showSecondaryColorPicker.value = false;
}

function hideBackgroundColorPicker() {
    showBackgroundColorPicker.value = false;
}

interface ThemeSettings {
    primary: string;
    secondary: string;
    backgroundColor: string;
    primaryFont: string;
    secondaryFont: string;
    backgroundFont: string;
}

const themeSettings = ref<ThemeSettings | null>();

function saveThemeSettings() {
    themeSettings.value = {
        primary: primary.value,
        secondary: secondary.value,
        backgroundColor: background.value,
        primaryFont: primaryFont.value,
        secondaryFont: secondaryFont.value,
        backgroundFont: backgroundFont.value
    }

    localStorage.setItem('themeSettings', JSON.stringify(themeSettings.value));
}

function loadThemeSettings() {
    const savedThemeSettings = localStorage.getItem('themeSettings');
    if (savedThemeSettings) {
        themeSettings.value = JSON.parse(savedThemeSettings);

        if (themeSettings.value) {
            primary.value = themeSettings.value.primary;
            primaryFont.value = themeSettings.value.primaryFont;
            secondary.value = themeSettings.value.secondary;
            secondaryFont.value = themeSettings.value.secondaryFont;
            background.value = themeSettings.value.backgroundColor;
            backgroundFont.value = themeSettings.value.backgroundColor;
        }
    } else {
        themeSettings.value = {
            primary: primary.value,
            secondary: secondary.value,
            backgroundColor: background.value,
            primaryFont: primaryFont.value,
            secondaryFont: secondaryFont.value,
            backgroundFont: backgroundFont.value
        }
    }
    saveColors();
}

function revertColors() {
    primary.value = getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary-reversion');
    secondary.value = getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-reversion');
    background.value = getComputedStyle(document.documentElement, null).getPropertyValue('--color-background-reversion');
    saveColors();
}

function saveColors() {
    primaryFont.value = fontColor(primary.value);
    secondaryFont.value = fontColor(secondary.value);
    backgroundFont.value = fontColor(background.value);
    document.documentElement.style.setProperty('--color-primary-font', primaryFont.value);
    document.documentElement.style.setProperty('--color-secondary-font', secondaryFont.value);
    document.documentElement.style.setProperty('--color-background-font', backgroundFont.value);
    document.documentElement.style.setProperty('--color-background', background.value);
    document.documentElement.style.setProperty('--color-background-soft-dark', newShade(background.value, 10));
    document.documentElement.style.setProperty('--color-background-mute-dark', newShade(background.value, 20));
    document.documentElement.style.setProperty('--color-background-soft-light', newShade(background.value, -10));
    document.documentElement.style.setProperty('--color-background-mute-light', newShade(background.value, -20));
    document.documentElement.style.setProperty('--color-primary', primary.value);
    document.documentElement.style.setProperty('--color-primary-hover-light', newShade(primary.value, 10));
    document.documentElement.style.setProperty('--color-primary-hover-dark', newShade(primary.value, -10));
    document.documentElement.style.setProperty('--color-primary-active-light', newShade(primary.value, 20));
    document.documentElement.style.setProperty('--color-primary-active-dark', newShade(primary.value, -20));
    document.documentElement.style.setProperty('--color-primary-disabled-light', newShade(primary.value, -25));
    document.documentElement.style.setProperty('--color-primary-disabled-dark', newShade(primary.value, 25));
    document.documentElement.style.setProperty('--color-secondary', secondary.value);
    document.documentElement.style.setProperty('--color-secondary-hover-light', newShade(secondary.value, 10));
    document.documentElement.style.setProperty('--color-secondary-active-light', newShade(secondary.value, 20));
    document.documentElement.style.setProperty('--color-secondary-disabled-light', newShade(secondary.value, -25));
    document.documentElement.style.setProperty('--color-secondary-hover-dark', newShade(secondary.value, -10));
    document.documentElement.style.setProperty('--color-secondary-active-dark', newShade(secondary.value, -20));
    document.documentElement.style.setProperty('--color-secondary-disabled-dark', newShade(secondary.value, 25));

    document.documentElement.style.setProperty('--bs-pagination-bg', primary.value);
    // save in localstorage
    saveThemeSettings();
}

watchEffect(() => {
    if (primaryTemp.value !== primary.value || secondaryTemp.value !== secondary.value) {
        primaryFontTemp.value = fontColor(primaryTemp.value);
        secondaryFontTemp.value = fontColor(secondaryTemp.value);

        document.documentElement.style.setProperty('--color-primary-font-temp', primaryFontTemp.value);
        document.documentElement.style.setProperty('--color-secondary-font-temp', secondaryFontTemp.value);

        document.documentElement.style.setProperty('--color-background', background.value);

        document.documentElement.style.setProperty('--color-primary-temp', primaryTemp.value);
        document.documentElement.style.setProperty('--color-primary-hover-temp', newShade(primaryTemp.value, -10));
        document.documentElement.style.setProperty('--color-primary-active-temp', newShade(primaryTemp.value, -20));
        document.documentElement.style.setProperty('--color-primary-disabled-temp', newShade(primaryTemp.value, 25));

        document.documentElement.style.setProperty('--color-secondary-temp', secondaryTemp.value);
        document.documentElement.style.setProperty('--color-secondary-hover-temp', newShade(secondaryTemp.value, -10));
        document.documentElement.style.setProperty('--color-secondary-active-temp', newShade(secondaryTemp.value, -20));
        document.documentElement.style.setProperty('--color-secondary-disabled-temp', newShade(secondaryTemp.value, 25));
    }
});

const newShade = (rgb: string, magnitude: number): string => {
    // Extract the individual red, green, and blue color values
    const rgbValuesStrings = ref<string>();
    const rgbValues = ref<number[]>(new Array(4));
    if (rgb.startsWith("rgb(")) {
        rgb = rgb.replace("rgb(", "rgba(");
        rgb = rgb.replace(")", ", 1)");
    }
    if (rgb.startsWith("rgba(")) {
        // Extract the individual red, green, blue and alpha color values
        if (rgb.match(/\d+/g) !== null) {
            rgbValuesStrings.value = rgb.match(/\d+/g);
        } else {
            throw new Error('Invalid RGB color');
        }
    } else {
        if (rgb.match(/\w\w+/g) !== null) {
            rgbValuesStrings.value = rgb.match(/\w\w/g);
        } else {
            throw new Error('Invalid RGB color');
        }
    }
    for (let i = 0; i < rgbValuesStrings.value.length; i++) {
        rgbValues.value[i] = parseInt(rgbValuesStrings.value[i], 16);
    }
    if (!rgbValues.value) {
        throw new Error('Invalid RGB color');
    }
    if (rgbValues.value.length !== 4) {
        console.error(rgbValues.value);
        throw new Error('Invalid RGB color');
    }

    // Adjust color brightness
    rgbValues.value[0] = Math.round(Math.min(Math.max(0, rgbValues.value[0] + (rgbValues.value[0] * magnitude / 100)), 255));
    rgbValues.value[1] = Math.round(Math.min(Math.max(0, rgbValues.value[1] + (rgbValues.value[1] * magnitude / 100)), 255));
    rgbValues.value[2] = Math.round(Math.min(Math.max(0, rgbValues.value[2] + (rgbValues.value[2] * magnitude / 100)), 255));
    rgbValues.value[3] = Math.min(Math.max(0, rgbValues.value[3] + (rgbValues.value[3] * magnitude / 100)), 1);
    // Return the new color in RGB format
    return `rgba(${rgbValues.value[0]}, ${rgbValues.value[1]}, ${rgbValues.value[2]}, ${rgbValues.value[3]})`;
};

const brightness = (rgb: string) => {
    const rgbValuesStrings = ref<string>();
    const rgbValues = ref<number[]>(new Array(4));
    if (rgb.startsWith("rgb(")) {
        rgb = rgb.replace("rgb(", "rgba(");
        rgb = rgb.replace(")", ", 1)");
    }
    if (rgb.startsWith("rgba(")) {
        // Extract the individual red, green, blue and alpha color values
        if (rgb.match(/\d+/g) !== null) {
            rgbValuesStrings.value = rgb.match(/\d+/g);
            for (let i = 0; i < rgbValuesStrings.value.length; i++) {
                rgbValues.value[i] = parseInt(rgbValuesStrings.value[i]);
            }
        } else {
            throw new Error('Invalid RGB color');
        }
    } else {
        if (rgb.startsWith("#")) {
            rgb = rgb.replace("#", "");
        }
        if (rgb.match(/\w\w+/g) !== null) {
            rgbValuesStrings.value = rgb.match(/\w\w/g);
            for (let i = 0; i < rgbValuesStrings.value.length; i++) {
                rgbValues.value[i] = parseInt(rgbValuesStrings.value[i], 16);
            }
        } else {
            throw new Error('Invalid RGB color');
        }
    }
    return Math.round(((rgbValues.value[0] * 299) + (rgbValues.value[1] * 587) + (rgbValues.value[2] * 114)) / 1000);
}

const fontColor = (rgb: string) => {
    const bright = brightness(rgb);
    console.log("rgb", rgb, "brightness", bright);
    return bright < 155 ? getComputedStyle(document.documentElement, null).getPropertyValue('--vt-c-text-dark-1') : getComputedStyle(document.documentElement, null).getPropertyValue('--vt-c-text-light-1');
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
    // Add the media query listener here
    mediaQuery.addEventListener('change', updateTheme);
});

onBeforeUnmount(() => {
    mediaQuery.removeEventListener('change', updateTheme);
});

</script>

<template>
    <div class="offcanvas offcanvas-end" tabindex="-1" id="themeOffcanvas" aria-labelledby="themeOffcanvasLabel">
        <div class="offcanvas-header">
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
                        <div class="color-box" :style="{ backgroundColor: primary }"
                             @click="showPrimaryColorPicker = true"></div>
                        <div class="color-picker-wrapper" v-if="showPrimaryColorPicker"
                             v-on-click-outside="hidePrimaryColorPicker">
                            <Vue3ColorPicker v-model="primary" mode="solid"
                                             :showPickerMode="false" :theme="prefersDarkScheme ? 'dark' : 'light'"
                                             :showColorList="true" :showEyeDrop="true" class="color-picker"/>
                        </div>
                    </div>
                    <div class="color-picker-container">
                        <label for="secondaryColorPicker">Secondary Color</label>
                        <div class="color-box" :style="{ backgroundColor: secondary }"
                             @click="showSecondaryColorPicker = true"></div>
                        <div class="color-picker-wrapper" v-if="showSecondaryColorPicker"
                             v-on-click-outside="hideSecondaryColorPicker">
                            <Vue3ColorPicker v-model="secondary" mode="solid"
                                             :showPickerMode="false" :theme="prefersDarkScheme ? 'dark' : 'light'"
                                             :showColorList="true" :showEyeDrop="true" class="color-picker"/>
                        </div>
                    </div>
                    <div class="color-picker-container">
                        <label for="backgroundColorPicker">Background Color</label>
                        <div class="color-box" :style="{ backgroundColor: background }"
                             @click="showBackgroundColorPicker = true"></div>
                        <div class="color-picker-wrapper" v-if="showBackgroundColorPicker"
                             v-on-click-outside="hideBackgroundColorPicker">
                            <Vue3ColorPicker v-model="background" mode="solid"
                                             :showPickerMode="false" :theme="prefersDarkScheme ? 'dark' : 'light'"
                                             :showColorList="true" :showEyeDrop="true" class="color-picker"/>
                        </div>
                    </div>
                </div>
                <div class="card-footer d-flex justify-content-between">
                    <button class="btn"
                            :class="{ 'btn-primary-temp': primaryTemp !== primary, 'btn-primary': primaryTemp === primary }"
                            @click="revertColors">Revert
                    </button>
                    <button class="btn"
                            :class="{ 'btn-secondary-temp': secondaryTemp !== secondary, 'btn-secondary': secondaryTemp === secondary }"
                            @click="saveColors">Save
                    </button>
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
                    <button class="btn btn-secondary" @click="saveFont" v-bind:disabled="!fontFileName">Save
                    </button>
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

.ellipsis {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.color-box {
    width: 50px;
    height: 20px;
    border: 1px solid var(--color-border);
    cursor: pointer;
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
    border: 1px solid var(--color-border);
    width: 300px;
}

.color-picker-wrapper {
    position: absolute;
    z-index: 1050;
    background-color: var(--color-background-mute);
    color: var(--color-background-font);
    border: 1px solid var(--color-border);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    top: 0
}

.card-body {
    margin-bottom: 0;
}

.card {
    color: var(--color-background-font);
    background-color: var(--color-background);
    border: 1px solid var(--color-modal-background-inverted);
}

.card-header,
.card-footer {
}

label.form-control {
    border: 1px solid var(--color-border);
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


a:hover {
    color: var(--color-text);
}

a:active {
    color: var(--color-text) !important;
}

.dp__theme_light {
    --dp-primary-color: var(--color-primary) !important;
    --dp-primary-disabled-color: var(--color-primary-disabled) !important;
    --dp-primary-text-color: var(--color-primary-font) !important;
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
    color: var(--color-primary-font);
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
    color: var(--color-primary-font);
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

.fas, .fa-classic, .fa-solid, .far, .fa-regular {
    font-family: 'Font Awesome 6 Free', serif;
}
</style>