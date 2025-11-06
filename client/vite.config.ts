import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(async () => {
  const plugins = [vue()]
  
  // Conditionally import devtools only in dev mode to avoid localStorage issues during build
  // Skip during build commands to prevent localStorage access errors
  const isBuild = process.env.npm_lifecycle_event === 'build' || 
                  process.env.npm_lifecycle_event === 'build-only' ||
                  process.env.NODE_ENV === 'production'
  
  if (!isBuild) {
    try {
      const vueDevTools = (await import('vite-plugin-vue-devtools')).default
      plugins.push(vueDevTools())
    } catch {
      // Silently fail if devtools can't be loaded (e.g., during build)
    }
  }
  
  return {
    plugins,
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
  }
})
