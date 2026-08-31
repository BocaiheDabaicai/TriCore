import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

// pinia：全局状态管理 —— 组件之间共享数据不用再层层传 props
createApp(App).use(createPinia()).mount('#app')
