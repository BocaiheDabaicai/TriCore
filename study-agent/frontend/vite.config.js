import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5175,
    strictPort: true,      // 端口被占直接报错，不自动换端口（manager 按固定端口探活，与另两个前端一致）
    host: '127.0.0.1',     // 固定 IPv4，避免 manager 探活探不到（Vite 默认只绑 IPv6 的 localhost）
    // /api 代理到研读助手后端（8003）——后端就绪后启用，现在数据在 src/api/readings.js 里是静态的
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8003',
        changeOrigin: true,
      },
    },
  },
})
