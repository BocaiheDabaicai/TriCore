import { defineStore } from 'pinia'
import { fetchCatalog, preselectDocs, streamChat } from '../api/chat'

// Agent 名称映射：消息上显示"哪个 Agent 回答的"
export const AGENT_NAMES = { knowledge: '企业知识问答', general: '通用对话' }

// 从 axios 错误里取后端 detail（没有就退回原始 message）
function errText(e) {
  return e.response?.data?.detail || e.message
}

// 聊天状态（Options 写法）：state 放数据、actions 放方法，结构分区直观
// 和 setup 写法对外暴露的东西完全一样，组件不用改
export const useChatStore = defineStore('chat', {
  // state：数据 —— 必须是函数返回对象（每个使用方各拿一份，互不共享）
  state: () => ({
    messages: [],      // [{ role, content, agent, sources, retrieval, done, error }]（error 非空 = 这条回答失败，可重试）
    sessionId: null,   // 后端 meta 事件下发，后续提问带上（多轮对话）
    history: [],       // 兜底对话的历史（后端不存，前端记最近的传过去）
    loading: false,
    draft: '',         // 输入框草稿（放 store 是因为「AI 预选」要拿当前问题）

    // 「指定文档」面板
    panelOpen: false,
    catalog: [],         // 知识目录 [{id, title, category, kind, keywords}]
    catalogError: '',
    selectedIds: [],     // 勾选的文档 id；非空 = 指定文档模式（随会话延续）
    preselecting: false,
    preselectError: '',
  }),

  getters: {
    // 按分类分组给面板渲染：[{ category, items: [...] }]
    groupedCatalog(state) {
      const groups = {}
      for (const it of state.catalog) {
        const key = it.category || '未分类'
        if (!groups[key]) groups[key] = []
        groups[key].push(it)
      }
      return Object.entries(groups).map(([category, items]) => ({ category, items }))
    },
  },

  // actions：修改数据的方法（同步异步都行），用 this 访问 state
  // 注意：必须是普通函数写法，不能用箭头函数（箭头函数拿不到 this）
  actions: {
    async sendQuestion(question, { appendUser = true } = {}) {
      this.loading = true
      if (appendUser) this.messages.push({ role: 'user', content: question })
      this.messages.push({ role: 'assistant', content: '', agent: '', sources: [], done: false, error: '' })
      // 取回数组里刚 push 的那条 —— 这样拿到的是响应式代理，改它界面才跟着变
      const assistantMsg = this.messages[this.messages.length - 1]
      const selected = this.selectedIds.length ? [...this.selectedIds] : null

      try {
        // 逐个消费 SSE 事件，不用管底层是 fetch 还是 axios
        for await (const { event, data } of streamChat(question, this.sessionId, this.history, selected)) {
          if (event === 'meta') {
            // 第一个 meta 是调度信息，第二个 meta（kb-agent 透传）带来源/检索方式
            if (data.agent) assistantMsg.agent = data.agent
            if (data.session_id) this.sessionId = data.session_id
            if (data.sources) assistantMsg.sources = data.sources
            if (data.retrieval_method) assistantMsg.retrieval = data.retrieval_method
          } else if (event === 'delta') {
            assistantMsg.content += data.text || ''
          } else if (event === 'done') {
            assistantMsg.done = true
            if (data.answer_source === 'knowledge') assistantMsg.agent = 'knowledge'
          } else if (event === 'error') {
            // 错误挂在消息的独立字段上（不拼进正文——拼进去渲染出来像回答的一部分）
            assistantMsg.error = data.message || '服务返回错误'
          }
        }
      } catch (e) {
        assistantMsg.error = '连接中断：' + e.message
      }

      assistantMsg.done = true
      // 只留最近 10 条有内容的对话，作为兜底对话的历史传给后端（出错的半截回答不带进历史）
      this.history = this.messages
        .filter((m) => m.content && !m.error)
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))
      this.loading = false
    },

    // 重试最后一条失败的回答：去掉失败气泡（用户问题保留），按原问题再问一次
    async retry() {
      if (this.loading) return
      const last = this.messages[this.messages.length - 1]
      if (!last || last.role !== 'assistant' || !last.error) return
      const question = [...this.messages].reverse().find((m) => m.role === 'user')?.content
      if (!question) return
      this.messages.pop()
      await this.sendQuestion(question, { appendUser: false })
    },

    // 新对话：清空消息、会话与上下文（勾选的指定文档保留，可在作用域条一键清除）
    newSession() {
      if (this.loading) return
      this.messages = []
      this.sessionId = null
      this.history = []
    },

    // ---- 指定文档面板 ----

    async togglePanel() {
      this.panelOpen = !this.panelOpen
      if (!this.panelOpen) return
      if (!this.catalog.length) await this.loadCatalog()
      // 面板刚打开、还没勾选、输入框已有问题 → 让 AI 先预选一版
      if (this.draft.trim() && !this.selectedIds.length) await this.runPreselect()
    },

    async loadCatalog() {
      this.catalogError = ''
      try {
        this.catalog = (await fetchCatalog()).data
      } catch (e) {
        this.catalogError = '目录加载失败：' + errText(e)
      }
    },

    async runPreselect() {
      const question = this.draft.trim()
      if (!question || this.preselecting) return
      this.preselecting = true
      this.preselectError = ''
      try {
        const resp = await preselectDocs(question)
        this.selectedIds = resp.data?.ids || []
        if (!this.selectedIds.length) this.preselectError = 'AI 没找到相关文档，可自行勾选'
      } catch (e) {
        this.preselectError = 'AI 预选失败：' + errText(e)
      } finally {
        this.preselecting = false
      }
    },

    toggleSelect(id) {
      const i = this.selectedIds.indexOf(id)
      if (i >= 0) this.selectedIds.splice(i, 1)
      else this.selectedIds.push(id)
    },

    // 分类级全选 / 全不选：该分类全选中了就取消，否则补全
    toggleGroup(ids) {
      const allSelected = ids.every((id) => this.selectedIds.includes(id))
      if (allSelected) this.selectedIds = this.selectedIds.filter((id) => !ids.includes(id))
      else this.selectedIds = [...new Set([...this.selectedIds, ...ids])]
    },

    clearSelection() {
      this.selectedIds = []
      this.preselectError = ''
    },
  },
})
