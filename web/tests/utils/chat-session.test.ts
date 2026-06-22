import { describe, expect, it } from 'vitest'
import {
  buildSessionTitle,
  normalizeSession,
  parseChatSessionsStorage,
  toHistoryPayload
} from '@/utils/chat-session'
import type { ChatMessage, ChatSession } from '@/types/chat'

function createMessage(role: ChatMessage['role'], content: string, id: string): ChatMessage {
  return { id, role, content }
}

describe('buildSessionTitle', () => {
  it('空字符串返回默认标题', () => {
    expect(buildSessionTitle('')).toBe('新对话')
    expect(buildSessionTitle('   ')).toBe('新对话')
  })

  it('短文本原样作为标题', () => {
    expect(buildSessionTitle('你好')).toBe('你好')
  })

  it('超长文本截断并加省略号', () => {
    const longText = '测'.repeat(30)
    expect(buildSessionTitle(longText)).toBe(`${'测'.repeat(24)}…`)
  })
})

describe('toHistoryPayload', () => {
  it('过滤空内容并只保留 role 与 content', () => {
    const messages: ChatMessage[] = [
      createMessage('user', '第一条', 'u1'),
      createMessage('assistant', '   ', 'a1'),
      createMessage('assistant', '回复', 'a2')
    ]

    expect(toHistoryPayload(messages)).toEqual([
      { role: 'user', content: '第一条' },
      { role: 'assistant', content: '回复' }
    ])
  })

  it('超过上限时只保留最近 20 条', () => {
    const messages = Array.from({ length: 25 }, (_, index) =>
      createMessage(index % 2 === 0 ? 'user' : 'assistant', `消息${index}`, `m${index}`)
    )

    const history = toHistoryPayload(messages)
    expect(history).toHaveLength(20)
    expect(history[0].content).toBe('消息5')
    expect(history[19].content).toBe('消息24')
  })
})

describe('parseChatSessionsStorage', () => {
  const validSession: ChatSession = {
    id: 'session-1',
    title: '测试对话',
    system: '你是助手',
    model: 'deepseek-v4-flash',
    temperature: 0.7,
    messages: [createMessage('user', '你好', 'u1')],
    createdAt: 1,
    updatedAt: 2
  }

  it('合法 JSON 能解析并规范化字段', () => {
    const raw = JSON.stringify({
      activeSessionId: 'session-1',
      sessions: [validSession]
    })

    const result = parseChatSessionsStorage(raw)
    expect(result).not.toBeNull()
    expect(result?.activeSessionId).toBe('session-1')
    expect(result?.sessions[0]).toEqual(normalizeSession(validSession))
  })

  it('activeSessionId 不存在时回退到第一个会话', () => {
    const raw = JSON.stringify({
      activeSessionId: 'missing-id',
      sessions: [validSession]
    })

    const result = parseChatSessionsStorage(raw)
    expect(result?.activeSessionId).toBe('session-1')
  })

  it('非法 JSON 或结构错误返回 null', () => {
    expect(parseChatSessionsStorage(null)).toBeNull()
    expect(parseChatSessionsStorage('{bad json')).toBeNull()
    expect(parseChatSessionsStorage(JSON.stringify({ foo: 'bar' }))).toBeNull()
    expect(
      parseChatSessionsStorage(
        JSON.stringify({
          activeSessionId: 'session-1',
          sessions: [{ id: 123, title: '坏数据', messages: [] }]
        })
      )
    ).toBeNull()
  })
})
