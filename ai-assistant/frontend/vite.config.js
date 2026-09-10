import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,      // 端口被占时直接报错，不自动换端口——manager 按固定端口探活，换端口就“失联”了
    host: '127.0.0.1',     // 默认只绑 IPv6 的 localhost（[::1]），manager 探 127.0.0.1 连不上；固定 IPv4 与后端一致
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
