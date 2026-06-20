import type { ChatRequestPayload, ChatStreamEvent } from '@/types/chat'

function getChatStreamUrl(): string {
  // 走 Vite 同源代理，避免跨域 preflight；由 vite.config.ts 转发到后端
  return '/api/chat/stream'
}

function parseSseLine(line: string): ChatStreamEvent | null {
  if (!line.startsWith('data: ')) return null

  try {
    return JSON.parse(line.slice(6)) as ChatStreamEvent
  } catch {
    return null
  }
}

function parseApiErrorMessage(body: unknown, status: number): string {
  if (!body || typeof body !== 'object') {
    return `请求失败 (${status})`
  }

  const record = body as Record<string, unknown>

  if (typeof record.detail === 'string') {
    return record.detail
  }

  if (typeof record.error === 'string') {
    return record.error
  }

  if (Array.isArray(record.detail) && record.detail.length > 0) {
    const first = record.detail[0]
    if (first && typeof first === 'object' && 'msg' in first) {
      const msg = String((first as { msg: string }).msg)
      return msg.replace(/^Value error,\s*/i, '')
    }
  }

  return `请求失败 (${status})`
}

/**
 * 消费后端 SSE 流式聊天接口
 * @example
 * for await (const event of streamChat({ message: '你好' })) {
 *   if (event.content) console.log(event.content)
 * }
 */
export async function* streamChat(
  payload: ChatRequestPayload,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamEvent> {
  const response = await fetch(getChatStreamUrl(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    throw new Error(parseApiErrorMessage(errorBody, response.status))
  }

  if (!response.body) {
    throw new Error('响应体为空')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue

      const event = parseSseLine(trimmed)
      if (event) yield event
    }
  }

  const tail = buffer.trim()
  if (tail) {
    const event = parseSseLine(tail)
    if (event) yield event
  }
}
