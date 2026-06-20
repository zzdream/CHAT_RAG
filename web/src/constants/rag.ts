export const RAG_STORAGE_KEY = 'study-llm-rag-sessions'
export const RAG_MODEL_READY_KEY = 'study-llm-rag-model-ready'
export const RAG_DEFAULT_TITLE = '新问答'
export const RAG_DEFAULT_TOP_K = 5
export const RAG_ALLOWED_EXTENSIONS = ['.txt', '.md', '.markdown']

export const DOCUMENT_STATUS_LABEL: Record<string, string> = {
  pending: '索引中',
  indexed: '已完成',
  failed: '失败'
}
