import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5174,
    strictPort: true,      // 端口被占时直接报错，不自动换端口——manager 按固定端口探活，换端口就“失联”了
    host: '127.0.0.1',     // 默认只绑 IPv6 的 localhost（[::1]），manager 探 127.0.0.1 连不上；固定 IPv4 与后端一致
    // 与聊天端（frontend）同一模式：管理端也只调调度器，/api 代理到 ai-assistant（8001）
    // 管理数据走 8001 转发到各 Agent，前端不直连 Agent 服务
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      // 服务管理直连 manager（8002）：进程控制不能经 ai-assistant 转发
      '/ops': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ops/, ''),
      },
    },
  },
})
