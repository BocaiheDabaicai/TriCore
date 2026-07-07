import { defineConfig } from '@rsbuild/core'
import { pluginVue } from '@rsbuild/plugin-vue'

export default defineConfig({
  plugins: [pluginVue()],
  source: {
    entry: {
      index: './src/main.ts',
    },
    include: [
      /node_modules[\\/]@ant-design[\\/]icons-vue/,
    ],
  },
  resolve: {
    alias: {
      '@': './src',
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  output: {
    assetPrefix: '/',
  },
})
