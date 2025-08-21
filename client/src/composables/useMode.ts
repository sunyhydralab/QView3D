import { ref } from 'vue'

/*
Developer note:
You might be wondering, Why not use true or false instead of 'light' or 'dark'?
1. Readability + simplicity, it's easy to understand light and dark vs true and false
2. Scalability, what if you wanted to add a third theme or mode?
3. Compatibility, tailwind expects 'dark' or 'light' values
*/

// state for the mode
const mode = ref<'light' | 'dark'>('dark')

// get mode
export function isDark(): boolean {
  return mode.value === 'dark'
}

// set the mode and update mode on local storage
export function setMode(newMode: 'light' | 'dark'): void {
  mode.value = newMode
  document.documentElement.classList.toggle('dark', newMode === 'dark')
  localStorage.setItem('mode', newMode)
}

// toggle the mode between light and dark
export function toggleMode(): void {
  if (mode.value === 'dark') {
    setMode('light')
  } else {
    setMode('dark')
  }
}

// Use the last mode saved in localStorage or the OS preference
export function setModeToSystem(): void {
  const savedMode = localStorage.getItem('mode')
  if (savedMode) {
    setMode(savedMode as 'light' | 'dark')
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    setMode('dark')
  } else {
    setMode('light')
  }
}