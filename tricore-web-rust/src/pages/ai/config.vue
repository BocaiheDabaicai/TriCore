<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Button, Input, Select, message, Spin } from 'ant-design-vue'
import { SaveOutlined, EyeInvisibleOutlined, EyeOutlined } from '@ant-design/icons-vue'
import { aiAPI } from '@/services/api'

const loading = ref(true)
const saving = ref(false)
const showKey = ref(false)
const form = ref({ api_key: '', model: 'claude-sonnet-4-6', base_url: 'https://api.anthropic.com', system_prompt: '' })

const modelOptions = [
  { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6 (推荐)' },
  { value: 'claude-opus-4-7', label: 'Claude Opus 4.7' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
  { value: 'deepseek-chat', label: 'DeepSeek V3 (deepseek-chat)' },
  { value: 'deepseek-v4-pro', label: 'DeepSeek V4 Pro (1m)' },
  { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' },
  { value: 'deepseek-reasoner', label: 'DeepSeek R1 (Reasoner)' },
  { value: 'gpt-4o', label: 'GPT-4o' },
]

onMounted(async () => {
  try {
    const res: any = await aiAPI.getConfig()
    const data = res?.data
    if (data) {
      form.value.api_key = data.api_key || ''
      form.value.model = data.model || 'claude-sonnet-4-6'
      form.value.base_url = data.base_url || 'https://api.anthropic.com'
      form.value.system_prompt = data.system_prompt || ''
    }
  } catch { /* use defaults */ }
  finally { loading.value = false }
})

const handleSave = async () => {
  if (!form.value.api_key.trim()) { message.warning('请输入 API Key'); return }
  saving.value = true
  try {
    await aiAPI.updateConfig({ ...form.value })
    message.success('配置已保存')
  } catch (err: any) { message.error(err?.response?.data?.message || '保存失败') }
  finally { saving.value = false }
}
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="gradient-text">AI 配置</h2>
      <p>设置 AI 助手的连接参数和模型选项</p>
    </div>
    <Spin :spinning="loading">
      <div class="glass-card p-6 max-w-xl mx-auto">
        <div class="space-y-4">
          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">
              API Key <span :style="{ color: 'var(--danger)' }">*</span>
            </label>
            <div class="flex gap-2">
              <Input
                v-model:value="form.api_key"
                :type="showKey ? 'text' : 'password'"
                placeholder="sk-ant-..."
                class="flex-1"
              />
              <Button @click="showKey = !showKey">
                <EyeOutlined v-if="!showKey" />
                <EyeInvisibleOutlined v-else />
              </Button>
            </div>
            <p class="text-xs mt-1" :style="{ color: 'var(--text-muted)' }">获取地址: console.anthropic.com → API Keys</p>
          </div>

          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">模型</label>
            <Select v-model:value="form.model" class="w-full" :options="modelOptions" placeholder="选择模型" showSearch />
          </div>

          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">API 地址</label>
            <Input v-model:value="form.base_url" placeholder="https://api.anthropic.com" />
            <p class="text-xs mt-1" :style="{ color: 'var(--text-muted)' }">支持兼容 Anthropic API 格式的服务（如 DeepSeek、OpenAI 兼容代理等）</p>
          </div>

          <div>
            <label class="text-xs mb-1.5 block font-medium" :style="{ color: 'var(--text-secondary)' }">
              系统提示词
              <span class="text-xs" :style="{ color: 'var(--text-muted)' }">（可选，自定义 AI 助手行为）</span>
            </label>
            <Input.TextArea v-model:value="form.system_prompt" :rows="4" placeholder="自定义系统提示词..." />
          </div>

          <Button type="primary" block size="large" @click="handleSave" :loading="saving">
            <SaveOutlined /> 保存配置
          </Button>
        </div>
      </div>
    </Spin>
  </div>
</template>
