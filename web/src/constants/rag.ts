export const RAG_STORAGE_KEY = 'omnichat-rag-sessions'
export const RAG_MODEL_READY_KEY = 'omnichat-rag-model-ready'
export const RAG_DEFAULT_TITLE = '新问答'
export const RAG_DEFAULT_TOP_K = 5
export const RAG_ALLOWED_EXTENSIONS = [
  '.txt',
  '.md',
  '.markdown',
  '.pdf',
  '.doc',
  '.docx',
  '.xlsx',
  '.xls',
  '.pptx',
  '.ppt',
  '.png',
  '.jpg',
  '.jpeg',
  '.webp'
]

/** 上传提示用，与 RAG_ALLOWED_EXTENSIONS 保持一致 */
export const RAG_ALLOWED_EXTENSIONS_LABEL =
  '.txt / .md / .markdown / .pdf / .doc / .docx / .xlsx / .xls / .pptx / .ppt / .png / .jpg / .jpeg / .webp'

export const DOCUMENT_STATUS_LABEL: Record<string, string> = {
  pending: '索引中',
  indexed: '已完成',
  failed: '失败'
}
