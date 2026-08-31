import { defineStore } from 'pinia'
import { streamChat } from '../api/chat'

// Agent 名称映射：消息上显示"哪个 Agent 回答的"
export const AGENT_NAMES = { knowledge: '企业知识问答', general: '通用对话' }

// 聊天状态（Options 写法）：state 放数据、actions 放方法，结构分区直观
// 和 setup 写法对外暴露的东西完全一样，组件不用改
export const useChatStore = defineStore('chat', {
  // state：数据 —— 必须是函数返回对象（每个使用方各拿一份，互不共享）
  state: () => ({
    messages: [],      // [{ role, content, agent, sources, done }]
    sessionId: null,   // 后端 meta 事件下发，后续提问带上（多轮对话）
    history: [],       // 兜底对话的历史（后端不存，前端记最近的传过去）
    loading: false,
  }),

  // actions：修改数据的方法（同步异步都行），用 this 访问 state
  // 注意：必须是普通函数写法，不能用箭头函数（箭头函数拿不到 this）
  actions: {
    async sendQuestion(question) {
      this.loading = true
      this.messages.push({ role: 'user', content: question })
      this.messages.push({ role: 'assistant', content: '', agent: '', sources: [], done: false })
      // 取回数组里刚 push 的那条 —— 这样拿到的是响应式代理，改它界面才跟着变
      const assistantMsg = this.messages[this.messages.length - 1]

      try {
        // 逐个消费 SSE 事件，不用管底层是 fetch 还是 axios
        for await (const { event, data } of streamChat(question, this.sessionId, this.history)) {
          if (event === 'meta') {
            // 第一个 meta 是调度信息，第二个 meta（kb-agent 透传）带来源
            if (data.agent) assistantMsg.agent = data.agent
            if (data.session_id) this.sessionId = data.session_id
            if (data.sources) assistantMsg.sources = data.sources
          } else if (event === 'delta') {
            assistantMsg.content += data.text || ''
          } else if (event === 'done') {
            assistantMsg.done = true
            if (data.answer_source === 'knowledge') assistantMsg.agent = 'knowledge'
          } else if (event === 'error') {
            assistantMsg.content += `\n\n（${data.message}）`
          }
        }
      } catch (e) {
        assistantMsg.content += `\n\n（连接中断：${e.message}）`
      }

      assistantMsg.done = true
      // 只留最近 10 条有内容的对话，作为兜底对话的历史传给后端
      this.history = this.messages
        .filter((m) => m.content)
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))
      this.loading = false
    },
  },
})
