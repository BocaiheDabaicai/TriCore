import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5176,
    // 端口被占直接报错，不自动换端口——manager 按固定端口探活，换了端口它找不到
    strictPort: true,
    // 固定绑 IPv4：Vite 默认只绑 IPv6 的 localhost([::1])，manager 探 127.0.0.1 会连不上
    host: '127.0.0.1',
    proxy: {
      // 只代理 RPA 后端一个服务：操作台是它的专属界面，不像管理端要管一整个集群
      '/api': { target: 'http://localhost:8004', changeOrigin: true },
    },
  },
})
