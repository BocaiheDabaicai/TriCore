<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Button, Input, Select, message, Spin } from 'ant-design-vue'
import { SaveOutlined, EyeInvisibleOutlined, EyeOutlined } from '@ant-design/icons-vue'
import { aiAPI } from '@/services/ai'

const loading = ref(true)
const saving = ref(false)
const showKey = ref(false)
const form = ref({ api_key: '', model: 'claude-sonnet-4-6', base_url: 'https://api.anthropic.com', system_prompt: '' })

const modelOptions = [
  { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6 (推荐)' },
  { value: 'claude-opus-4-7', label: 'Claude Opus 4.7' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
  { value: 'deepseek-chat', label: 'DeepSeek V3' },
  { value: 'deepseek-v4-pro', label: 'DeepSeek V4 Pro (1m)' },
  { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' },
  { value: 'deepseek-reasoner', label: 'DeepSeek R1' },
  { value: 'gpt-4o', label: 'GPT-4o' },
]

onMounted(async () => {
  try {
    const res: any = await aiAPI.getConfig()
    const data = res?.data
    if (data) Object.assign(form.value, { api_key: data.api_key || '', model: data.model || 'claude-sonnet-4-6', base_url: data.base_url || 'https://api.anthropic.com', system_prompt: data.system_prompt || '' })
  } catch { /* defaults */ }
  finally { loading.value = false }
})

const handleSave = async () => {
  if (!form.value.api_key.trim()) { message.warning('请输入 API Key'); return }
  saving.value = true
  try { await aiAPI.updateConfig({ ...form.value }); message.success('配置已保存') }
  catch (err: any) { message.error(err?.response?.data?.message || '保存失败') }
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
      <div class="glass-card" style="padding:24px;max-width:640px;margin:0 auto">
        <div style="display:flex;flex-direction:column;gap:16px">
          <div>
            <label style="font-size:12px;margin-bottom:6px;display:block;font-weight:500;color:var(--text-secondary)">API Key <span style="color:var(--danger)">*</span></label>
            <div style="display:flex;gap:8px">
              <Input v-model:value="form.api_key" :type="showKey ? 'text' : 'password'" placeholder="sk-ant-..." style="flex:1" />
              <Button @click="showKey = !showKey"><EyeOutlined v-if="!showKey" /><EyeInvisibleOutlined v-else /></Button>
            </div>
          </div>
          <div>
            <label style="font-size:12px;margin-bottom:6px;display:block;font-weight:500;color:var(--text-secondary)">模型</label>
            <Select v-model:value="form.model" style="width:100%" :options="modelOptions" showSearch />
          </div>
          <div>
            <label style="font-size:12px;margin-bottom:6px;display:block;font-weight:500;color:var(--text-secondary)">API 地址</label>
            <Input v-model:value="form.base_url" />
          </div>
          <div>
            <label style="font-size:12px;margin-bottom:6px;display:block;font-weight:500;color:var(--text-secondary)">系统提示词 <span style="font-size:12px;color:var(--text-muted)">（可选）</span></label>
            <Input.TextArea v-model:value="form.system_prompt" :rows="4" />
          </div>
          <Button type="primary" block size="large" @click="handleSave" :loading="saving"><SaveOutlined /> 保存配置</Button>
        </div>
      </div>
    </Spin>
  </div>
</template>
