export type ChatRole = 'user' | 'assistant'

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  /** 仅 assistant 消息在流式结束后可能有 */
  usage?: TokenUsage
}

/** 单个聊天会话 */
export interface ChatSession {
  id: string
  title: string
  /** 可选系统提示词，仅当前会话生效 */
  system?: string
  /** 当前会话使用的模型 */
  model?: string
  /** 当前会话采样温度 0～2 */
  temperature?: number
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

/** localStorage 持久化结构 */
export interface ChatSessionsStorage {
  activeSessionId: string
  sessions: ChatSession[]
}

/** 发给后端的历史消息（不含 id） */
export interface ChatHistoryMessage {
  role: ChatRole
  content: string
}

export interface ChatRequestPayload {
  message: string
  system?: string
  /** 当前 message 之前的多轮对话 */
  history?: ChatHistoryMessage[]
  temperature?: number
  model?: string
}

export interface ChatStreamEvent {
  content?: string
  usage?: TokenUsage
  done?: boolean
  error?: string
}

export interface ChatResponsePayload {
  content: string
  model: string
}
