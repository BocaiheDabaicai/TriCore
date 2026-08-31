<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import { AGENT_NAMES } from '../stores/chat'

const props = defineProps({
  message: { type: Object, required: true },
})

const html = computed(() => marked.parse(props.message.content || '思考中…'))
</script>

<template>
  <div class="msg-row" :class="message.role">
    <div class="bubble">
      <div v-if="message.role === 'assistant' && message.agent" class="msg-tag">
        {{ AGENT_NAMES[message.agent] || message.agent }}
        <span v-if="!message.done">回答中…</span>
      </div>
      <div v-if="message.role === 'assistant'" class="md" v-html="html"></div>
      <div v-else class="plain">{{ message.content }}</div>
      <div v-if="message.sources && message.sources.length" class="msg-sources">
        参考：{{ message.sources.map((s) => s.title).join('、') }}
      </div>
    </div>
  </div>
</template>
