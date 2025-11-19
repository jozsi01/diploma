import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'


// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools()
  ],
  server: {
    proxy: {
      // forward any request starting with /api to your backend
      '/api': {
        target: 'http://localhost:5000', // your backend URL
        changeOrigin: true,
        secure: false, // only if your backend is HTTP
        // optional: rewrite path if backend doesn't use /api prefix
        // rewrite: (path) => path.replace(/^\/api/, '')
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
