import type { AgentChatRequestPayload, AgentChatStreamEvent } from '@/types/agent'

function getAgentStreamUrl(): string {
  return '/api/chat/agent/stream'
}

function parseSseLine(line: string): AgentChatStreamEvent | null {
  if (!line.startsWith('data: ')) return null
  try {
    return JSON.parse(line.slice(6)) as AgentChatStreamEvent
  } catch {
    return null
  }
}

function parseApiErrorMessage(body: unknown, status: number): string {
  if (!body || typeof body !== 'object') return `请求失败 (${status})`
  const record = body as Record<string, unknown>
  if (typeof record.detail === 'string') return record.detail
  if (typeof record.error === 'string') return record.error
  return `请求失败 (${status})`
}

export async function* streamAgentChat(
  payload: AgentChatRequestPayload,
  signal?: AbortSignal
): AsyncGenerator<AgentChatStreamEvent> {
  const response = await fetch(getAgentStreamUrl(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    throw new Error(parseApiErrorMessage(errorBody, response.status))
  }

  if (!response.body) throw new Error('响应体为空')

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
