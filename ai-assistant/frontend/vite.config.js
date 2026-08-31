import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 开发环境代理：前端请求 /api/... 由 Vite 转发给 ai-assistant（8001 端口）
    // 好处：前端代码里只写相对路径，不用管后端地址，也没有跨域（CORS）问题
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
