import { streamRagChat } from '@/api/chat-rag'
import { DEFAULT_CHAT_MODEL, DEFAULT_TEMPERATURE } from '@/constants/chat'
import { RAG_DEFAULT_TITLE, RAG_DEFAULT_TOP_K, RAG_STORAGE_KEY } from '@/constants/rag'
import type { TokenUsage } from '@/types/chat'
import type {
  RagHistoryMessage,
  RagMessage,
  RagSession,
  RagSessionsStorage,
  RagSource
} from '@/types/rag'

function formatRagError(message: string): string {
  if (/401|authentication|api key|invalid.*key/i.test(message)) {
    return 'DeepSeek API Key 无效或未配置，请在 server/.env 中设置 DEEPSEEK_API_KEY 后重启后端'
  }
  return message
}

function createId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createMessage(role: RagMessage['role'], content: string, sources?: RagSource[]): RagMessage {
  return { id: createId(role), role, content, sources }
}

function createSession(knowledgeBaseId: string): RagSession {
  const now = Date.now()
  return {
    id: createId('rag-session'),
    title: RAG_DEFAULT_TITLE,
    knowledgeBaseId,
    messages: [],
    createdAt: now,
    updatedAt: now
  }
}

function createDefaultStorage(knowledgeBaseId: string): RagSessionsStorage {
  const session = createSession(knowledgeBaseId)
  return { activeSessionId: session.id, sessions: [session] }
}

function parseStorage(raw: string | null, fallbackKbId: string): RagSessionsStorage {
  if (!raw) return createDefaultStorage(fallbackKbId)
  try {
    const parsed = JSON.parse(raw) as RagSessionsStorage
    if (!parsed.sessions?.length) return createDefaultStorage(fallbackKbId)
    return parsed
  } catch {
    return createDefaultStorage(fallbackKbId)
  }
}

export function useRagChat(initialKnowledgeBaseId: Ref<string>) {
  const storage = parseStorage(localStorage.getItem(RAG_STORAGE_KEY), initialKnowledgeBaseId.value)
  const sessions = ref<RagSession[]>(storage.sessions)
  const activeSessionId = ref(storage.activeSessionId)
  const input = ref('')
  const isStreaming = ref(false)
  const error = ref('')
  const streamingContent = ref('')
  const streamingSources = ref<RagSource[]>([])
  const streamingMessageId = ref<string | null>(null)
  const lastUsage = ref<TokenUsage | null>(null)

  let abortController: AbortController | null = null

  const activeSession = computed(
    () => sessions.value.find(item => item.id === activeSessionId.value) ?? null
  )

  const messages = computed(() => activeSession.value?.messages ?? [])

  function persist() {
    localStorage.setItem(
      RAG_STORAGE_KEY,
      JSON.stringify({
        activeSessionId: activeSessionId.value,
        sessions: sessions.value
      } satisfies RagSessionsStorage)
    )
  }

  watch([sessions, activeSessionId], persist, { deep: true })

  watch(initialKnowledgeBaseId, kbId => {
    if (!kbId) return
    const session = activeSession.value
    if (!session || session.knowledgeBaseId !== kbId) {
      ensureSessionForKb(kbId)
    }
  })

  function getWritableSession(): RagSession | null {
    return sessions.value.find(item => item.id === activeSessionId.value) ?? null
  }

  function buildTitle(text: string): string {
    const trimmed = text.trim()
    return trimmed.length > 24 ? `${trimmed.slice(0, 24)}…` : trimmed || RAG_DEFAULT_TITLE
  }

  function toHistoryPayload(messagesList: RagMessage[]): RagHistoryMessage[] {
    return messagesList.map(item => ({ role: item.role, content: item.content }))
  }

  function createNewSession(knowledgeBaseId?: string) {
    if (isStreaming.value) return
    const kbId = knowledgeBaseId ?? initialKnowledgeBaseId.value
    if (!kbId) return

    const session = createSession(kbId)
    sessions.value = [session, ...sessions.value].slice(0, 30)
    activeSessionId.value = session.id
    input.value = ''
    error.value = ''
  }

  /** 确保当前知识库至少有一个会话，但不重复创建空会话 */
  function ensureSessionForKb(kbId: string) {
    const forKb = sessions.value.filter(item => item.knowledgeBaseId === kbId)
    if (!forKb.length) {
      createNewSession(kbId)
      return
    }

    const active = activeSession.value
    if (active?.knowledgeBaseId === kbId && forKb.some(item => item.id === active.id)) {
      return
    }

    const latest = [...forKb].sort((a, b) => b.updatedAt - a.updatedAt)[0]
    activeSessionId.value = latest.id
    input.value = ''
    error.value = ''
  }

  /**
   * 与后端知识库列表对齐：
   * 1. 删除已不存在知识库的会话（如删库后 localStorage 残留）
   * 2. 同一知识库下多个空会话只保留最新一条
   */
  function syncSessionsWithKnowledgeBases(validKbIds: string[]) {
    const validSet = new Set(validKbIds)
    const kept = sessions.value.filter(item => validSet.has(item.knowledgeBaseId))

    const byKb = new Map<string, RagSession[]>()
    for (const session of kept) {
      const list = byKb.get(session.knowledgeBaseId) ?? []
      list.push(session)
      byKb.set(session.knowledgeBaseId, list)
    }

    const next: RagSession[] = []
    for (const list of byKb.values()) {
      const withMessages = list.filter(item => item.messages.length > 0)
      const empty = list.filter(item => item.messages.length === 0)

      if (empty.length <= 1) {
        next.push(...list)
        continue
      }

      const newestEmpty = empty.sort((a, b) => b.updatedAt - a.updatedAt)[0]
      next.push(...withMessages, newestEmpty)
    }

    sessions.value = next.sort((a, b) => b.updatedAt - a.updatedAt)

    if (sessions.value.some(item => item.id === activeSessionId.value)) return

    const kbId = initialKnowledgeBaseId.value
    if (kbId && validSet.has(kbId)) {
      ensureSessionForKb(kbId)
    } else if (sessions.value.length) {
      activeSessionId.value = sessions.value[0].id
    }
  }

  function switchSession(sessionId: string) {
    if (isStreaming.value) return
    const session = sessions.value.find(item => item.id === sessionId)
    if (!session) return
    activeSessionId.value = sessionId
    input.value = ''
    error.value = ''
  }

  function deleteSession(sessionId: string) {
    if (isStreaming.value) return
    const target = sessions.value.find(item => item.id === sessionId)
    if (!target) return

    sessions.value = sessions.value.filter(item => item.id !== sessionId)

    if (activeSessionId.value !== sessionId) return

    const kbId = target.knowledgeBaseId
    const remaining = sessions.value.filter(item => item.knowledgeBaseId === kbId)
    if (remaining.length) {
      activeSessionId.value = remaining[0].id
    } else {
      createNewSession(kbId)
    }
  }

  function commitStreamingContent(fallback = '（无回复内容）') {
    if (!streamingMessageId.value) return

    const session = getWritableSession()
    const target = session?.messages.find(item => item.id === streamingMessageId.value)
    if (target) {
      target.content = streamingContent.value || fallback
      target.sources = streamingSources.value.length ? [...streamingSources.value] : undefined
      if (session) session.updatedAt = Date.now()
    }

    streamingContent.value = ''
    streamingSources.value = []
    streamingMessageId.value = null
  }

  async function sendMessage() {
    const text = input.value.trim()
    const session = getWritableSession()
    const kbId = initialKnowledgeBaseId.value

    if (!text || !session || !kbId || isStreaming.value) return

    error.value = ''
    const history = toHistoryPayload(session.messages)
    const isFirst = session.messages.length === 0

    session.messages.push(createMessage('user', text))
    if (isFirst) session.title = buildTitle(text)
    session.updatedAt = Date.now()
    input.value = ''

    const assistant = createMessage('assistant', '')
    session.messages.push(assistant)
    streamingMessageId.value = assistant.id
    streamingContent.value = ''
    streamingSources.value = []
    isStreaming.value = true
    lastUsage.value = null
    abortController = new AbortController()

    try {
      for await (const event of streamRagChat(
        {
          message: text,
          knowledge_base_id: kbId,
          history,
          top_k: RAG_DEFAULT_TOP_K,
          model: DEFAULT_CHAT_MODEL,
          temperature: DEFAULT_TEMPERATURE
        },
        abortController.signal
      )) {
        if (event.error) throw new Error(event.error)
        if (event.sources) streamingSources.value = event.sources
        if (event.content) streamingContent.value += event.content
        if (event.usage && streamingMessageId.value) {
          const target = session.messages.find(item => item.id === streamingMessageId.value)
          if (target) target.usage = event.usage
          lastUsage.value = event.usage
        }
        if (event.done) break
      }
      commitStreamingContent()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        streamingContent.value = streamingContent.value || '（已停止生成）'
        commitStreamingContent('（已停止生成）')
        return
      }
      const message = formatRagError(err instanceof Error ? err.message : '发送失败')
      error.value = message
      session.messages = session.messages.filter(item => item.id !== assistant.id)
      streamingMessageId.value = null
      streamingContent.value = ''
      streamingSources.value = []
    } finally {
      isStreaming.value = false
      abortController = null
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

  function getMessageContent(message: RagMessage) {
    if (message.id === streamingMessageId.value) return streamingContent.value
    return message.content
  }

  function getMessageSources(message: RagMessage) {
    if (message.id === streamingMessageId.value) return streamingSources.value
    return message.sources ?? []
  }

  function isMessageStreaming(message: RagMessage) {
    return isStreaming.value && message.id === streamingMessageId.value
  }

  return {
    sessions,
    activeSessionId,
    activeSession,
    messages,
    input,
    isStreaming,
    error,
    lastUsage,
    createNewSession,
    ensureSessionForKb,
    syncSessionsWithKnowledgeBases,
    switchSession,
    deleteSession,
    sendMessage,
    stopStreaming,
    onKeydown,
    getMessageContent,
    getMessageSources,
    isMessageStreaming
  }
}
