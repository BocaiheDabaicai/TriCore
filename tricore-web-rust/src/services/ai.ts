import api from './http'

export const aiAPI = {
  getConfig: () => api.get('/ai/config'),
  updateConfig: (data: Record<string, unknown>) => api.put('/ai/config', data),
  chat: (messages: { role: string; content: string }[]) =>
    api.post('/ai/chat', { messages, stream: false }),
  chatStream: (messages: { role: string; content: string }[], onEvent: (e: SseEvent) => void, onError: (msg: string) => void, onDone: () => void) => {
    const token = localStorage.getItem('token')
    return fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ messages, stream: true }),
    }).then(async (resp) => {
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ message: `HTTP ${resp.status}` }))
        throw new Error(err.message || `HTTP ${resp.status}`)
      }
      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data: ')) continue
          try {
            const json = JSON.parse(line.slice(6))
            if (json.type === 'done') { onDone(); return }
            if (json.type === 'error') { onError(json.message || '未知错误'); return }
            onEvent(json as SseEvent)
          } catch { /* skip malformed */ }
        }
      }
    }).catch((err) => {
      if (err instanceof TypeError && err.message.includes('fetch')) {
        onError('网络连接失败，请检查后端服务是否启动')
      } else {
        onError(err.message || '请求失败')
      }
    })
  },
}

export const mcpAPI = {
  listServers: () => api.get('/mcp/servers'),
  createServer: (data: Record<string, unknown>) => api.post('/mcp/servers', data),
  updateServer: (id: string, data: Record<string, unknown>) => api.put(`/mcp/servers/${id}`, data),
  deleteServer: (id: string) => api.delete(`/mcp/servers/${id}`),
  listTools: () => api.get('/mcp/tools'),
  refresh: () => api.post('/mcp/refresh'),
}

export interface SseEvent {
  type: 'thinking' | 'message' | 'error' | 'done'
  tool?: string
  args?: Record<string, unknown>
  result?: string
  content?: string
  message?: string
}

