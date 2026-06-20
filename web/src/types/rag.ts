import type { TokenUsage } from '@/types/chat'

export interface RagSource {
  document_id: string
  filename: string
  chunk_index: number
  content: string
  score: number
}

export interface RagHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface RagChatRequestPayload {
  message: string
  knowledge_base_id: string
  history?: RagHistoryMessage[]
  top_k?: number
  temperature?: number
  model?: string
}

export interface RagChatStreamEvent {
  content?: string
  sources?: RagSource[]
  usage?: TokenUsage
  done?: boolean
  error?: string
}

export interface RagMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: RagSource[]
  usage?: TokenUsage
}

export interface RagSession {
  id: string
  title: string
  knowledgeBaseId: string
  messages: RagMessage[]
  createdAt: number
  updatedAt: number
}

export interface RagSessionsStorage {
  activeSessionId: string
  sessions: RagSession[]
}
