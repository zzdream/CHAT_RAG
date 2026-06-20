import { streamChat } from '@/api/chat'
import {
  DEFAULT_CHAT_MODEL,
  DEFAULT_TEMPERATURE
} from '@/constants/chat'
import {
  DEFAULT_TITLE,
  STORAGE_KEY,
  buildSessionTitle,
  parseChatSessionsStorage,
  toHistoryPayload
} from '@/utils/chat-session'
import type {
  ChatHistoryMessage,
  ChatMessage,
  ChatSession,
  ChatSessionsStorage,
  TokenUsage
} from '@/types/chat'

const MAX_SESSIONS = 50

function createId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createMessage(role: ChatMessage['role'], content: string): ChatMessage {
  return {
    id: createId(role),
    role,
    content
  }
}

function createSession(): ChatSession {
  const now = Date.now()
  return {
    id: createId('session'),
    title: DEFAULT_TITLE,
    system: '',
    model: DEFAULT_CHAT_MODEL,
    temperature: DEFAULT_TEMPERATURE,
    messages: [],
    createdAt: now,
    updatedAt: now
  }
}

function createDefaultStorage(): ChatSessionsStorage {
  const session = createSession()
  return {
    activeSessionId: session.id,
    sessions: [session]
  }
}

function loadStorage(): ChatSessionsStorage {
  const parsed = parseChatSessionsStorage(localStorage.getItem(STORAGE_KEY))
  return parsed ?? createDefaultStorage()
}

function touchSession(session: ChatSession) {
  session.updatedAt = Date.now()
}

/**
 * 聊天流式对话 hook（多会话 + 多轮上下文 + localStorage 持久化）
 */
export function useChatStream() {
  const storage = loadStorage()
  const sessions = ref<ChatSession[]>(storage.sessions)
  const activeSessionId = ref(storage.activeSessionId)
  const input = ref('')
  const isStreaming = ref(false)
  const error = ref('')
  const streamingContent = ref('')
  const streamingMessageId = ref<string | null>(null)
  const copiedMessageId = ref<string | null>(null)
  const lastUsage = ref<TokenUsage | null>(null)

  let abortController: AbortController | null = null
  let copyTimer: ReturnType<typeof setTimeout> | null = null

  const activeSession = computed(() =>
    sessions.value.find(item => item.id === activeSessionId.value) ?? null
  )

  const messages = computed(() => activeSession.value?.messages ?? [])

  const systemPrompt = computed({
    get: () => activeSession.value?.system ?? '',
    set: (value: string) => {
      const session = getWritableSession()
      if (!session) return
      session.system = value
      touchSession(session)
    }
  })

  const sessionModel = computed({
    get: () => activeSession.value?.model ?? DEFAULT_CHAT_MODEL,
    set: (value: string) => {
      const session = getWritableSession()
      if (!session) return
      session.model = value
      touchSession(session)
    }
  })

  const sessionTemperature = computed({
    get: () => activeSession.value?.temperature ?? DEFAULT_TEMPERATURE,
    set: (value: number) => {
      const session = getWritableSession()
      if (!session) return
      session.temperature = value
      touchSession(session)
    }
  })

  const sortedSessions = computed(() =>
    [...sessions.value].sort((a, b) => b.updatedAt - a.updatedAt)
  )

  function persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        activeSessionId: activeSessionId.value,
        sessions: sessions.value
      } satisfies ChatSessionsStorage)
    )
  }

  watch([sessions, activeSessionId], persist, { deep: true })

  function getWritableSession(): ChatSession | null {
    return sessions.value.find(item => item.id === activeSessionId.value) ?? null
  }

  function commitStreamingContent(fallback = '（无回复内容）') {
    if (!streamingMessageId.value) return

    const session = getWritableSession()
    const target = session?.messages.find(item => item.id === streamingMessageId.value)
    if (target) {
      target.content = streamingContent.value || fallback
      if (session) touchSession(session)
    }

    streamingContent.value = ''
    streamingMessageId.value = null
  }

  function applyUsageToMessage(messageId: string, usage: TokenUsage) {
    const session = getWritableSession()
    const target = session?.messages.find(item => item.id === messageId)
    if (target) {
      target.usage = usage
      if (session) touchSession(session)
    }
    lastUsage.value = usage
  }

  async function streamAssistantReply(
    session: ChatSession,
    userText: string,
    history: ChatHistoryMessage[]
  ) {
    const system = session.system?.trim() || undefined
    const model = session.model?.trim() || undefined
    const temperature = session.temperature ?? DEFAULT_TEMPERATURE
    const assistantMessage = createMessage('assistant', '')
    session.messages.push(assistantMessage)
    streamingMessageId.value = assistantMessage.id
    streamingContent.value = ''
    isStreaming.value = true
    lastUsage.value = null
    abortController = new AbortController()

    try {
      for await (const event of streamChat(
        { message: userText, history, system, model, temperature },
        abortController.signal
      )) {
        if (event.error) {
          throw new Error(event.error)
        }

        if (event.content) {
          streamingContent.value += event.content
        }

        if (event.usage && streamingMessageId.value) {
          applyUsageToMessage(streamingMessageId.value, event.usage)
        }

        if (event.done) break
      }

      commitStreamingContent()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        if (streamingContent.value) {
          streamingContent.value += '\n\n（已停止生成）'
        } else {
          streamingContent.value = '（已停止生成）'
        }
        commitStreamingContent('（已停止生成）')
        return
      }

      const message = err instanceof Error ? err.message : '发送失败，请稍后重试'
      error.value = message
      commitStreamingContent(`出错了：${message}`)
    } finally {
      isStreaming.value = false
      abortController = null
    }
  }

  function createNewSession() {
    if (isStreaming.value) return

    const session = createSession()
    sessions.value = [session, ...sessions.value].slice(0, MAX_SESSIONS)
    activeSessionId.value = session.id
    input.value = ''
    error.value = ''
    lastUsage.value = null
  }

  function switchSession(sessionId: string) {
    if (isStreaming.value || activeSessionId.value === sessionId) return
    if (!sessions.value.some(item => item.id === sessionId)) return

    activeSessionId.value = sessionId
    input.value = ''
    error.value = ''
    lastUsage.value = null
  }

  function deleteSession(sessionId: string) {
    if (isStreaming.value) return

    const index = sessions.value.findIndex(item => item.id === sessionId)
    if (index === -1) return

    const nextSessions = sessions.value.filter(item => item.id !== sessionId)

    if (nextSessions.length === 0) {
      const session = createSession()
      sessions.value = [session]
      activeSessionId.value = session.id
    } else {
      sessions.value = nextSessions
      if (activeSessionId.value === sessionId) {
        activeSessionId.value = nextSessions[0].id
      }
    }

    input.value = ''
    error.value = ''
    lastUsage.value = null
  }

  async function sendMessage() {
    const text = input.value.trim()
    const session = getWritableSession()
    if (!text || isStreaming.value || !session) return

    error.value = ''
    const history = toHistoryPayload(session.messages)
    const isFirstMessage = session.messages.length === 0

    session.messages.push(createMessage('user', text))
    if (isFirstMessage) {
      session.title = buildSessionTitle(text)
    }
    touchSession(session)
    input.value = ''

    await streamAssistantReply(session, text, history)
  }

  async function regenerateMessage(assistantMessageId: string) {
    const session = getWritableSession()
    if (!session || isStreaming.value) return

    const assistantIndex = session.messages.findIndex(item => item.id === assistantMessageId)
    if (assistantIndex === -1 || session.messages[assistantIndex].role !== 'assistant') return

    const userIndex = assistantIndex - 1
    if (userIndex < 0 || session.messages[userIndex].role !== 'user') return

    const userText = session.messages[userIndex].content
    if (!userText.trim()) return

    error.value = ''
    const history = toHistoryPayload(session.messages.slice(0, userIndex))
    session.messages.splice(assistantIndex)
    touchSession(session)

    await streamAssistantReply(session, userText, history)
  }

  async function copyMessage(message: ChatMessage) {
    const text = getMessageContent(message)
    if (!text.trim()) return

    try {
      await navigator.clipboard.writeText(text)
      copiedMessageId.value = message.id
      if (copyTimer) clearTimeout(copyTimer)
      copyTimer = setTimeout(() => {
        copiedMessageId.value = null
        copyTimer = null
      }, 2000)
    } catch {
      error.value = '复制失败，请检查浏览器权限'
    }
  }

  function stopStreaming() {
    abortController?.abort()
  }

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  function getMessageContent(message: ChatMessage) {
    if (message.id === streamingMessageId.value) {
      return streamingContent.value
    }
    return message.content
  }

  function isMessageStreaming(message: ChatMessage) {
    return isStreaming.value && message.id === streamingMessageId.value
  }

  function canRegenerate(message: ChatMessage) {
    if (message.role !== 'assistant' || isStreaming.value) return false
    const session = activeSession.value
    if (!session) return false

    const index = session.messages.findIndex(item => item.id === message.id)
    if (index <= 0 || session.messages[index - 1].role !== 'user') return false

    // 仅最后一条消息显示重新生成
    return index === session.messages.length - 1
  }

  function getMessageUsage(message: ChatMessage) {
    if (message.id === streamingMessageId.value && lastUsage.value) {
      return lastUsage.value
    }
    return message.usage
  }

  return {
    sessions: sortedSessions,
    activeSessionId,
    activeSession,
    messages,
    input,
    systemPrompt,
    sessionModel,
    sessionTemperature,
    lastUsage,
    isStreaming,
    error,
    streamingContent,
    copiedMessageId,
    createNewSession,
    switchSession,
    deleteSession,
    sendMessage,
    regenerateMessage,
    copyMessage,
    stopStreaming,
    onKeydown,
    getMessageContent,
    getMessageUsage,
    isMessageStreaming,
    canRegenerate
  }
}
