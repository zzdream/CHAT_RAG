import {
  DEFAULT_CHAT_MODEL,
  DEFAULT_TEMPERATURE
} from '@/constants/chat'
import type {
  ChatHistoryMessage,
  ChatMessage,
  ChatSession,
  ChatSessionsStorage
} from '@/types/chat'

export const STORAGE_KEY = 'study-llm-chat-sessions'
export const DEFAULT_TITLE = '新对话'
export const SESSION_TITLE_MAX = 24
export const MAX_HISTORY_MESSAGES = 20

export function buildSessionTitle(text: string): string {
  const trimmed = text.trim()
  if (!trimmed) return DEFAULT_TITLE
  return trimmed.length > SESSION_TITLE_MAX
    ? `${trimmed.slice(0, SESSION_TITLE_MAX)}…`
    : trimmed
}

export function toHistoryPayload(messages: ChatMessage[]): ChatHistoryMessage[] {
  return messages
    .filter(item => item.content.trim())
    .slice(-MAX_HISTORY_MESSAGES)
    .map(item => ({ role: item.role, content: item.content }))
}

function isChatMessage(item: unknown): item is ChatMessage {
  return !!item
    && typeof item === 'object'
    && typeof (item as ChatMessage).id === 'string'
    && ((item as ChatMessage).role === 'user' || (item as ChatMessage).role === 'assistant')
    && typeof (item as ChatMessage).content === 'string'
}

function isChatSession(item: unknown): item is ChatSession {
  if (!item || typeof item !== 'object') return false

  const session = item as ChatSession
  const systemOk = session.system === undefined || typeof session.system === 'string'
  const modelOk = session.model === undefined || typeof session.model === 'string'
  const temperatureOk =
    session.temperature === undefined || typeof session.temperature === 'number'

  return typeof session.id === 'string'
    && typeof session.title === 'string'
    && systemOk
    && modelOk
    && temperatureOk
    && Array.isArray(session.messages)
    && typeof session.createdAt === 'number'
    && typeof session.updatedAt === 'number'
    && session.messages.every(isChatMessage)
}

export function normalizeSession(session: ChatSession): ChatSession {
  return {
    ...session,
    system: session.system ?? '',
    model: session.model ?? DEFAULT_CHAT_MODEL,
    temperature: session.temperature ?? DEFAULT_TEMPERATURE
  }
}

/** 从 localStorage 原始字符串解析会话；解析失败返回 null */
export function parseChatSessionsStorage(raw: string | null): ChatSessionsStorage | null {
  if (!raw) return null

  try {
    const parsed: unknown = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return null

    const record = parsed as Partial<ChatSessionsStorage>
    if (!Array.isArray(record.sessions) || typeof record.activeSessionId !== 'string') {
      return null
    }

    const sessions = record.sessions.filter(isChatSession).map(normalizeSession)
    if (sessions.length === 0) return null

    const activeSessionId = sessions.some(s => s.id === record.activeSessionId)
      ? record.activeSessionId!
      : sessions[0].id

    return { activeSessionId, sessions }
  } catch {
    return null
  }
}
