import type { TokenUsage } from '@/types/chat'
import type { RagSource } from '@/types/rag'

export interface AgentToolStep {
  id: string
  type: 'tool_call' | 'tool_result'
  name: string
  arguments?: string
  result?: string
}

export interface AgentHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AgentChatRequestPayload {
  message: string
  system?: string
  history?: AgentHistoryMessage[]
  temperature?: number
  model?: string
  knowledge_base_id?: string
  top_k?: number
}

export interface AgentChatStreamEvent {
  content?: string
  tool_call?: {
    id: string
    name: string
    arguments: string
  }
  tool_result?: {
    id: string
    name: string
    result: string
  }
  sources?: RagSource[]
  usage?: TokenUsage
  retry?: {
    attempt: number
    max_attempts: number
    message: string
  }
  done?: boolean
  error?: string
}

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  toolSteps?: AgentToolStep[]
  sources?: RagSource[]
  usage?: TokenUsage
}

export interface AgentSession {
  id: string
  title: string
  knowledgeBaseId: string
  messages: AgentMessage[]
  createdAt: number
  updatedAt: number
}

export interface AgentSessionsStorage {
  activeSessionId: string
  sessions: AgentSession[]
}
