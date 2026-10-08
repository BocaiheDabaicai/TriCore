import { defineStore } from 'pinia'

// 全局轻提示：操作成功 / 失败后弹一下，几秒自动消失
// Options 写法（与项目习惯一致）；任何组件都能调用，展示由 App.vue 里的 ToastHost 统一负责
let nextId = 1

export const useToastStore = defineStore('toast', {
  state: () => ({
    items: [],   // { id, message, type: 'success' | 'error' }
  }),
  actions: {
    show(message, type = 'success') {
      const id = nextId++
      this.items.push({ id, message, type })
      setTimeout(() => this.remove(id), 2600)
    },
    success(message) {
      this.show(message, 'success')
    },
    error(message) {
      this.show(message, 'error')
    },
    remove(id) {
      this.items = this.items.filter((t) => t.id !== id)
    },
  },
})
