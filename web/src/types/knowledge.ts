export interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  created_at: string
  updated_at: string
}

export interface KnowledgeDocument {
  id: string
  knowledge_base_id: string
  filename: string
  file_size: number
  status: 'pending' | 'indexed' | 'failed'
  chunk_count: number
  error_message: string
  created_at: string
  updated_at: string
}

export interface CreateKnowledgeBasePayload {
  name: string
  description?: string
}
