<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { EditorView, keymap, drawSelection, placeholder } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'
import { markdown } from '@codemirror/lang-markdown'

// Markdown 编辑器（CodeMirror 6）：输入时按语法实时着色（标题 / 加粗 / 列表 / 引用 / 代码块）
// 用法同 v-model：值变化通过 update:modelValue 抛给父组件
const props = defineProps({ modelValue: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue'])

const host = ref(null)
let view = null

// 外观主题：贴近 daisyUI 浅色风格（行高、内边距、光标聚焦不描边）
const MD_THEME = EditorView.theme({
  '&': { height: '100%', fontSize: '14px', color: '#1f2937' },
  '&.cm-focused': { outline: 'none' },
  '.cm-scroller': { fontFamily: 'inherit', lineHeight: '1.8', overflow: 'auto' },
  '.cm-content': { padding: '12px 0' },
  '.cm-line': { padding: '0 14px' },
  '.cm-placeholder': { color: '#9ca3af' },
})

onMounted(() => {
  view = new EditorView({
    parent: host.value,
    doc: props.modelValue,
    extensions: [
      history(),                                  // 撤销/重做
      drawSelection(),                            // 原生选区绘制
      keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),   // Tab 缩进 / Shift+Tab 取消缩进
      markdown(),                                 // Markdown 语法树（着色的依据）
      syntaxHighlighting(defaultHighlightStyle),  // 用默认高亮样式上色
      placeholder('写笔记…（支持 Markdown：# 标题、**加粗**、- 列表）'),
      EditorView.lineWrapping,                    // 长行自动折行，不横向滚动
      MD_THEME,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) emit('update:modelValue', update.state.doc.toString())
      }),
    ],
  })
})

// 外部改值（以后"继续编辑"载入旧笔记）时，同步进编辑器
watch(
  () => props.modelValue,
  (val) => {
    if (!view || val === view.state.doc.toString()) return
    view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: val } })
  },
)

onBeforeUnmount(() => view?.destroy())
</script>

<template>
  <div
    ref="host"
    class="flex-1 min-h-0 rounded-lg border border-base-300 bg-base-100 overflow-hidden
           focus-within:border-primary transition-colors"
  ></div>
</template>
