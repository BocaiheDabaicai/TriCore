import request from './request'

// 第2层：聊天模块的接口 —— 组件和 pinia 只认这里的函数，不关心底层是 axios 还是 fetch

// 状态检查（普通请求 → axios）
export function getStatus() {
  // baseURL 是 /api，这里路径只写后半段；响应拦截器已剥掉包装，直接返回 data
  return request.get('/status')
}

// 流式问答（SSE → fetch）—— axios 在浏览器读不了流式响应体，
// 只能 fetch + ReadableStream 逐块读；封装成 async 生成器，
// 调用方用 for await...of 逐个拿事件，屏蔽底层差异
export async function* streamChat(question, sessionId, history) {
  const resp = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId, history }),
  })

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // SSE 消息之间用空行分隔，按 "\n\n" 切块；最后一块可能不完整，留到下一轮拼
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop()

    for (const block of blocks) {
      yield parseSseBlock(block)
    }
  }
  // 流结束：buffer 里若还有完整消息（服务端最后没以空行结尾时），补解析一次
  if (buffer.trim()) {
    yield parseSseBlock(buffer)
  }
}

// 解析一条 SSE 消息块："event: xxx\ndata: {...}" → { event, data }
function parseSseBlock(block) {
  let event = 'message'
  const dataLines = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
  }
  try {
    return { event, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    return { event, data: {} }
  }
}
