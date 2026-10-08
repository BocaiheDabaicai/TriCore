<script setup>
import { useChatStore } from '../stores/chat'

// 指定文档面板：左侧目录（分类 → 标题），勾选后由 AI 只用这几篇回答
// 默认由 AI 按当前问题预选，用户可增删；不勾选 = 全库问答（默认）
// 收起时宽度 0（外壳不变宽），展开是帘子拉开的效果——见 style.css 的 .doc-panel
const chat = useChatStore()
const KIND_LABELS = { policy: '制度', document: '文档', workflow: '流程' }

const groupIds = (group) => group.items.map((i) => i.id)
const allSelected = (group) => group.items.every((i) => chat.selectedIds.includes(i.id))
const someSelected = (group) => group.items.some((i) => chat.selectedIds.includes(i.id))
const selectedCount = (group) => group.items.filter((i) => chat.selectedIds.includes(i.id)).length
</script>

<template>
  <aside class="doc-panel" :class="{ open: chat.panelOpen }">
    <div class="doc-panel-inner">
      <div class="doc-panel-head">
        <div class="title">
          指定文档
          <span class="count" :class="{ active: chat.selectedIds.length }">
            {{ chat.selectedIds.length ? `已选 ${chat.selectedIds.length} 篇` : '未选 · 全库问答' }}
          </span>
        </div>
        <button class="close" title="收起" @click="chat.togglePanel()">×</button>
      </div>

      <p class="hint">AI 按当前输入框里的问题预选，可自行增删；勾选后本轮及后续提问只在这些文档里找答案。</p>

      <div class="actions">
        <button class="btn-preselect" :disabled="chat.preselecting || !chat.draft.trim()" @click="chat.runPreselect()">
          {{ chat.preselecting ? '预选中…' : 'AI 预选' }}
        </button>
        <button class="btn-clear" :disabled="!chat.selectedIds.length" @click="chat.clearSelection()">清空</button>
      </div>
      <p v-if="!chat.draft.trim()" class="tip">先在下方输入问题，再点「AI 预选」</p>
      <p v-if="chat.preselectError" class="err">{{ chat.preselectError }}</p>
      <p v-if="chat.catalogError" class="err">{{ chat.catalogError }}</p>

      <div class="doc-list">
        <div v-for="group in chat.groupedCatalog" :key="group.category" class="group">
          <div class="group-name">
            <label class="group-check" :title="allSelected(group) ? '取消本分类' : '全选本分类'">
              <input
                type="checkbox"
                :checked="allSelected(group)"
                :indeterminate="someSelected(group) && !allSelected(group)"
                @change="chat.toggleGroup(groupIds(group))"
              />
              {{ group.category }}
            </label>
            <span class="group-count" :class="{ active: selectedCount(group) }">{{ selectedCount(group) }}/{{ group.items.length }}</span>
          </div>
          <label v-for="item in group.items" :key="item.id" class="doc-item" :class="{ checked: chat.selectedIds.includes(item.id) }">
            <input type="checkbox" :checked="chat.selectedIds.includes(item.id)" @change="chat.toggleSelect(item.id)" />
            <span class="doc-title" :title="item.title">{{ item.title }}</span>
            <span class="doc-kind">{{ KIND_LABELS[item.kind] || item.kind }}</span>
          </label>
        </div>
        <p v-if="!chat.groupedCatalog.length && !chat.catalogError" class="tip">目录为空</p>
      </div>
    </div>
  </aside>
</template>
