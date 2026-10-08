<script setup>
import { computed, ref } from 'vue'
import { marked } from 'marked'
import { AGENT_NAMES, useChatStore } from '../stores/chat'

const props = defineProps({
  message: { type: Object, required: true },
  isLast: { type: Boolean, default: false },   // 重试按钮只给最后一条失败的问答复用
})

const chat = useChatStore()

const html = computed(() => marked.parse(props.message.content || ''))

// 等待阶段：回答还没开始（没正文、没出错、没结束）时显示状态文案
const waiting = computed(
  () => props.message.role === 'assistant' && !props.message.done && !props.message.content && !props.message.error,
)
// meta 先到：agent 已定时能说出人在哪一步，还没到就笼统一点
const waitText = computed(() => (props.message.agent === 'knowledge' ? '正在检索知识库…' : '正在理解问题…'))

// 检索方式标记：让用户一眼看出这次回答用了哪条路径
const SCOPE_TAGS = { selected: '按指定文档回答', aggregate: '综合汇总回答' }
const scopeTag = computed(() => SCOPE_TAGS[props.message.retrieval] || '')

// 来源列表：综合汇总可能命中全库几十条，超过 4 条只显示前 3 条 + 总数（悬停看全部）
const sourceTitles = computed(() => (props.message.sources || []).map((s) => s.title))
const sourcesText = computed(() => {
  if (sourceTitles.value.length <= 4) return sourceTitles.value.join('、')
  return sourceTitles.value.slice(0, 3).join('、') + ` 等 ${sourceTitles.value.length} 条`
})

// 复制答案：点了短暂变成「已复制」
const copied = ref(false)
async function copy() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* 剪贴板不可用（非安全上下文等）时静默失败 */
  }
}
</script>

<template>
  <div class="msg-row" :class="message.role">
    <div class="bubble">
      <div v-if="message.role === 'assistant' && message.agent" class="msg-tag">
        {{ AGENT_NAMES[message.agent] || message.agent }}
        <span v-if="!message.done">回答中…</span>
      </div>

      <!-- 等待指示：跳动的三点 + 当前阶段，替代原来藏在正文里的「思考中…」 -->
      <div v-if="waiting" class="msg-wait">
        <span class="dots"><i></i><i></i><i></i></span>
        {{ waitText }}
      </div>

      <div v-if="message.role === 'assistant' && message.content" class="md" v-html="html"></div>
      <div v-else-if="message.role !== 'assistant'" class="plain">{{ message.content }}</div>

      <!-- 错误块：与回答正文分开显示，最后一条给重试 -->
      <div v-if="message.error" class="msg-error">
        <span>{{ message.error }}</span>
        <button v-if="isLast && !chat.loading" @click="chat.retry()">重试</button>
      </div>

      <div v-if="scopeTag" class="msg-scope">{{ scopeTag }}</div>
      <div v-if="sourceTitles.length" class="msg-sources" :title="sourceTitles.join('、')">
        参考：{{ sourcesText }}
      </div>

      <div v-if="message.role === 'assistant' && message.done && message.content" class="msg-actions">
        <button @click="copy">{{ copied ? '已复制' : '复制' }}</button>
      </div>
    </div>
  </div>
</template>
