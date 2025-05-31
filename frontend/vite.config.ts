// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 代理所有 /api 开头的请求到后端
      '/api': 'http://localhost:8000'
    }
  }
})
