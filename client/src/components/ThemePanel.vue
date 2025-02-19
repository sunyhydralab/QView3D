<script setup lang="ts">
import { ref, watch, watchEffect, onMounted, onBeforeUnmount } from 'vue'
import { Vue3ColorPicker } from '@cyhnkckali/vue3-color-picker'
import { vOnClickOutside } from '@vueuse/components'
import '@/assets/base.css'

const prefersDarkScheme = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

// Create a function to update the theme based on the preference
const updateTheme = () => {
  prefersDarkScheme.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  revertColors() // Call your function to revert colors based on the new preference
}

// Set up the media query listener
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

const primary = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary')
)
const primaryFont = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-text')
)
const secondary = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary')
)
const secondaryFont = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-font')
)
const background = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-background')
)
const backgroundFont = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-background-font')
)

const primaryTemp = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-primary')
)
const primaryFontTemp = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-text')
)
const secondaryTemp = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary')
)
const secondaryFontTemp = ref<string>(
  getComputedStyle(document.documentElement, null).getPropertyValue('--color-secondary-font')
)
const isDarkMode = ref(false)

const showPrimaryColorPicker = ref(false)
const showSecondaryColorPicker = ref(false)

function hidePrimaryColorPicker() {
  showPrimaryColorPicker.value = false
}

function hideSecondaryColorPicker() {
  showSecondaryColorPicker.value = false
}

interface ThemeSettings {
  primary: string
  secondary: string
  backgroundColor: string
  primaryFont: string
  secondaryFont: string
  backgroundFont: string
}

const themeSettings = ref<ThemeSettings | null>()

function saveThemeSettings() {
  themeSettings.value = {
    primary: primary.value,
    secondary: secondary.value,
    backgroundColor: background.value,
    primaryFont: primaryFont.value,
    secondaryFont: secondaryFont.value,
    backgroundFont: backgroundFont.value
  }

  localStorage.setItem('themeSettings', JSON.stringify(themeSettings.value))
}

function loadThemeSettings() {
  const savedThemeSettings = localStorage.getItem('themeSettings')
  if (savedThemeSettings) {
    themeSettings.value = JSON.parse(savedThemeSettings)

    if (themeSettings.value) {
      primary.value = themeSettings.value.primary
      primaryFont.value = themeSettings.value.primaryFont
      secondary.value = themeSettings.value.secondary
      secondaryFont.value = themeSettings.value.secondaryFont
      background.value = themeSettings.value.backgroundColor
      backgroundFont.value = themeSettings.value.backgroundColor
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
  saveColors()
}

function revertColors() {
  primary.value = getComputedStyle(document.documentElement, null).getPropertyValue(
    '--color-primary-reversion'
  )
  secondary.value = getComputedStyle(document.documentElement, null).getPropertyValue(
    '--color-secondary-reversion'
  )
  background.value = getComputedStyle(document.documentElement, null).getPropertyValue(
    '--color-background-reversion'
  )
  saveColors()
}

function saveColors() {
  primaryFont.value = fontColor(primary.value)
  secondaryFont.value = fontColor(secondary.value)
  backgroundFont.value = fontColor(background.value)
  document.documentElement.style.setProperty('--color-primary-font', primaryFont.value)
  document.documentElement.style.setProperty('--color-secondary-font', secondaryFont.value)
  document.documentElement.style.setProperty('--color-background-font', backgroundFont.value)
  document.documentElement.style.setProperty('--color-background', background.value)
  document.documentElement.style.setProperty(
    '--color-background-soft-dark',
    newShade(background.value, 10)
  )
  document.documentElement.style.setProperty(
    '--color-background-mute-dark',
    newShade(background.value, 20)
  )
  document.documentElement.style.setProperty(
    '--color-background-soft-light',
    newShade(background.value, -10)
  )
  document.documentElement.style.setProperty(
    '--color-background-mute-light',
    newShade(background.value, -20)
  )
  document.documentElement.style.setProperty('--color-primary', primary.value)
  document.documentElement.style.setProperty(
    '--color-primary-hover-light',
    newShade(primary.value, 10)
  )
  document.documentElement.style.setProperty(
    '--color-primary-hover-dark',
    newShade(primary.value, -10)
  )
  document.documentElement.style.setProperty(
    '--color-primary-active-light',
    newShade(primary.value, 20)
  )
  document.documentElement.style.setProperty(
    '--color-primary-active-dark',
    newShade(primary.value, -20)
  )
  document.documentElement.style.setProperty(
    '--color-primary-disabled-light',
    newShade(primary.value, -25)
  )
  document.documentElement.style.setProperty(
    '--color-primary-disabled-dark',
    newShade(primary.value, 25)
  )
  document.documentElement.style.setProperty('--color-secondary', secondary.value)
  document.documentElement.style.setProperty(
    '--color-secondary-hover-light',
    newShade(secondary.value, 10)
  )
  document.documentElement.style.setProperty(
    '--color-secondary-active-light',
    newShade(secondary.value, 20)
  )
  document.documentElement.style.setProperty(
    '--color-secondary-disabled-light',
    newShade(secondary.value, -25)
  )
  document.documentElement.style.setProperty(
    '--color-secondary-hover-dark',
    newShade(secondary.value, -10)
  )
  document.documentElement.style.setProperty(
    '--color-secondary-active-dark',
    newShade(secondary.value, -20)
  )
  document.documentElement.style.setProperty(
    '--color-secondary-disabled-dark',
    newShade(secondary.value, 25)
  )

  document.documentElement.style.setProperty('--bs-pagination-bg', primary.value)
  // save in localstorage
  saveThemeSettings()
}

watchEffect(() => {
  if (primaryTemp.value !== primary.value || secondaryTemp.value !== secondary.value) {
    primaryFontTemp.value = fontColor(primaryTemp.value)
    secondaryFontTemp.value = fontColor(secondaryTemp.value)

    document.documentElement.style.setProperty('--color-primary-font-temp', primaryFontTemp.value)
    document.documentElement.style.setProperty(
      '--color-secondary-font-temp',
      secondaryFontTemp.value
    )

    document.documentElement.style.setProperty('--color-background', background.value)

    document.documentElement.style.setProperty('--color-primary-temp', primaryTemp.value)
    document.documentElement.style.setProperty(
      '--color-primary-hover-temp',
      newShade(primaryTemp.value, -10)
    )
    document.documentElement.style.setProperty(
      '--color-primary-active-temp',
      newShade(primaryTemp.value, -20)
    )
    document.documentElement.style.setProperty(
      '--color-primary-disabled-temp',
      newShade(primaryTemp.value, 25)
    )

    document.documentElement.style.setProperty('--color-secondary-temp', secondaryTemp.value)
    document.documentElement.style.setProperty(
      '--color-secondary-hover-temp',
      newShade(secondaryTemp.value, -10)
    )
    document.documentElement.style.setProperty(
      '--color-secondary-active-temp',
      newShade(secondaryTemp.value, -20)
    )
    document.documentElement.style.setProperty(
      '--color-secondary-disabled-temp',
      newShade(secondaryTemp.value, 25)
    )
  }
})

const newShade = (rgb: string, magnitude: number): string => {
  const rgbValuesStrings = ref<string[]>([])
  const rgbValues = ref<number[]>(new Array(4).fill(0)) // Initialize with zeros

  if (rgb.startsWith('rgb(')) {
    rgb = rgb.replace('rgb(', 'rgba(')
    rgb = rgb.replace(')', ', 1)')
  }

  if (rgb.startsWith('rgba(')) {
    // Extract the individual red, green, blue, and alpha color values
    const matched = rgb.match(/\d+/g) // Match RGB(A) values
    if (matched !== null) {
      rgbValuesStrings.value = matched
    } else {
      throw new Error('Invalid RGB color')
    }
  } else {
    const matched = rgb.match(/\w\w/g) // Match hex values
    if (matched !== null) {
      rgbValuesStrings.value = matched
    } else {
      throw new Error('Invalid RGB color')
    }
  }

  // Parse the RGB(A) values
  for (let i = 0; i < rgbValuesStrings.value.length; i++) {
    rgbValues.value[i] = parseInt(rgbValuesStrings.value[i], 16)
  }

  // Adjust color brightness
  rgbValues.value[0] = Math.round(
    Math.min(Math.max(0, rgbValues.value[0] + (rgbValues.value[0] * magnitude) / 100), 255)
  )
  rgbValues.value[1] = Math.round(
    Math.min(Math.max(0, rgbValues.value[1] + (rgbValues.value[1] * magnitude) / 100), 255)
  )
  rgbValues.value[2] = Math.round(
    Math.min(Math.max(0, rgbValues.value[2] + (rgbValues.value[2] * magnitude) / 100), 255)
  )
  rgbValues.value[3] = Math.min(
    Math.max(0, rgbValues.value[3] + (rgbValues.value[3] * magnitude) / 100),
    1
  )

  // Return the new color in RGBA format
  return `rgba(${rgbValues.value[0]}, ${rgbValues.value[1]}, ${rgbValues.value[2]}, ${rgbValues.value[3]})`
}

const brightness = (rgb: string) => {
  const rgbValuesStrings = ref<string[]>([])
  const rgbValues = ref<number[]>(new Array(4).fill(0))

  if (rgb.startsWith('rgb(')) {
    rgb = rgb.replace('rgb(', 'rgba(')
    rgb = rgb.replace(')', ', 1)')
  }

  if (rgb.startsWith('rgba(')) {
    // Extract the individual red, green, blue, and alpha color values
    const matched = rgb.match(/\d+/g)
    if (matched !== null) {
      rgbValuesStrings.value = matched // Safe to assign, no null
      for (let i = 0; i < rgbValuesStrings.value.length; i++) {
        rgbValues.value[i] = parseInt(rgbValuesStrings.value[i])
      }
    } else {
      throw new Error('Invalid RGB color')
    }
  } else {
    if (rgb.startsWith('#')) {
      rgb = rgb.replace('#', '')
    }
    const matched = rgb.match(/\w\w/g)
    if (matched !== null) {
      rgbValuesStrings.value = matched // Safe to assign, no null
      for (let i = 0; i < rgbValuesStrings.value.length; i++) {
        rgbValues.value[i] = parseInt(rgbValuesStrings.value[i], 16)
      }
    } else {
      throw new Error('Invalid RGB color')
    }
  }

  return Math.round(
    (rgbValues.value[0] * 299 + rgbValues.value[1] * 587 + rgbValues.value[2] * 114) / 1000
  )
}

const fontColor = (rgb: string) => {
  const bright = brightness(rgb)
  return bright < 155
    ? getComputedStyle(document.documentElement, null).getPropertyValue('--vt-c-text-dark-1')
    : getComputedStyle(document.documentElement, null).getPropertyValue('--vt-c-text-light-1')
}

onMounted(() => {
  loadThemeSettings()
  // Add the media query listener here
  mediaQuery.addEventListener('change', updateTheme)
})

onBeforeUnmount(() => {
  mediaQuery.removeEventListener('change', updateTheme)
})

watch(isDarkMode, (newValue) => {
  background.value = newValue ? '#1a1a1a' : '#E7E7E7'
  document.body.style.backgroundColor = newValue ? '#1a1a1a' : '#E7E7E7'
  document.body.style.color = newValue ? '#ffffff' : '#000000'
  saveColors()
})
</script>

<template>
  <div
    class="offcanvas offcanvas-end"
    tabindex="-1"
    id="themeOffcanvas"
    aria-labelledby="themeOffcanvasLabel"
  >
    <div class="offcanvas-header">
      <h5 id="themeOffcanvasLabel">Theme Settings</h5>
      <button
        type="button"
        class="btn-close text-reset"
        data-bs-dismiss="offcanvas"
        aria-label="Close"
      ></button>
    </div>
    <div class="offcanvas-body">
      <div class="card mb-3">
        <div class="card-header text-center">
          <h5 class="card-title">Color</h5>
        </div>
        <div class="card-body">
          <div class="color-picker-container mb-3">
            <label for="primaryColorPicker">Primary Color</label>
            <div
              class="color-box"
              :style="{ backgroundColor: primary }"
              @click="showPrimaryColorPicker = true"
            ></div>
            <div
              class="color-picker-wrapper"
              v-if="showPrimaryColorPicker"
              v-on-click-outside="hidePrimaryColorPicker"
            >
              <Vue3ColorPicker
                v-model="primary"
                mode="solid"
                :showPickerMode="false"
                :theme="prefersDarkScheme ? 'dark' : 'light'"
                :showColorList="true"
                :showEyeDrop="true"
                class="color-picker"
              />
            </div>
          </div>
          <div class="color-picker-container">
            <label for="secondaryColorPicker">Secondary Color</label>
            <div
              class="color-box"
              :style="{ backgroundColor: secondary }"
              @click="showSecondaryColorPicker = true"
            ></div>
            <div
              class="color-picker-wrapper"
              v-if="showSecondaryColorPicker"
              v-on-click-outside="hideSecondaryColorPicker"
            >
              <Vue3ColorPicker
                v-model="secondary"
                mode="solid"
                :showPickerMode="false"
                :theme="prefersDarkScheme ? 'dark' : 'light'"
                :showColorList="true"
                :showEyeDrop="true"
                class="color-picker"
              />
            </div>
          </div>
          <div class="color-picker-container">
            <label for="backgroundColorPicker">Background Color</label>
            <h2>
              <i
                :class="isDarkMode ? 'fa-regular fa-sun fa-xl' : 'fa-solid fa-sun fa-xl'"
                @click="isDarkMode = false"
              ></i>
              <i
                :class="isDarkMode ? 'fa-solid fa-moon fa-xl' : 'fa-regular fa-moon fa-xl'"
                @click="isDarkMode = true"
              ></i>
            </h2>
          </div>
        </div>
        <div class="card-footer d-flex justify-content-between">
          <button
            class="btn"
            :class="{
              'btn-primary-temp': primaryTemp !== primary,
              'btn-primary': primaryTemp === primary
            }"
            @click="revertColors"
          >
            Revert
          </button>
          <button
            class="btn"
            :class="{
              'btn-secondary-temp': secondaryTemp !== secondary,
              'btn-secondary': secondaryTemp === secondary
            }"
            @click="saveColors"
          >
            Save
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
  text-align: center;
  margin-top: 1.5rem;
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
  top: 0;
}

.card-body {
  margin-bottom: 0;
}

.card {
  color: var(--color-background-font);
  background-color: var(--color-background);
  border: 1px solid var(--color-modal-background-inverted);
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

.fas,
.fa-classic,
.fa-solid,
.far,
.fa-regular {
  font-family: 'Font Awesome 6 Free', serif;
}

h2 i {
  cursor: pointer;
  margin: 0 10px;
  margin-top: 1rem;
  transition: transform 0.2s ease-in-out;
}

h2 i:hover {
  transform: scale(1.1);
}
</style>
