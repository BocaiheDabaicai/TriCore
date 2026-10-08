import { defineStore } from 'pinia'

// 全局确认弹窗：任何页面 `if (!(await confirm({...}))) return` 即可，确定得 true、取消得 false
// 弹窗本体是 App.vue 里的 ConfirmHost；resolver 放在 store 外面（被 promise 包着的函数不需要响应式）
let resolver = null

export const useConfirmStore = defineStore('confirm', {
  state: () => ({
    open: false,
    title: '确认操作',
    message: '',
    confirmText: '确定',
    cancelText: '取消',
    danger: false,   // 危险操作 → 确定按钮显示红色
  }),
  actions: {
    confirm({ title, message, confirmText = '确定', cancelText = '取消', danger = false } = {}) {
      this.title = title || '确认操作'
      this.message = message || ''
      this.confirmText = confirmText
      this.cancelText = cancelText
      this.danger = danger
      this.open = true
      return new Promise((resolve) => { resolver = resolve })
    },
    // 弹窗两个按钮的唯一出口
    answer(result) {
      this.open = false
      const fn = resolver
      resolver = null
      fn && fn(result)
    },
  },
})
