import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

// 与另两个前端同款结构：main.js 只负责装配（pinia + router），布局在 App.vue
createApp(App).use(createPinia()).use(router).mount('#app')
