import type {
  CreateKnowledgeBasePayload,
  KnowledgeBase,
  KnowledgeDocument
} from '@/types/knowledge'

const BASE = '/api/knowledge'

async function parseError(response: Response): Promise<string> {
  const body = await response.json().catch(() => null)
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return `请求失败 (${response.status})`
}

export async function fetchKnowledgeBases(): Promise<KnowledgeBase[]> {
  const response = await fetch(`${BASE}/bases`)
  if (!response.ok) throw new Error(await parseError(response))
  return response.json()
}

export async function createKnowledgeBase(
  payload: CreateKnowledgeBasePayload
): Promise<KnowledgeBase> {
  const response = await fetch(`${BASE}/bases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!response.ok) throw new Error(await parseError(response))
  return response.json()
}

export async function deleteKnowledgeBase(id: string): Promise<void> {
  const response = await fetch(`${BASE}/bases/${id}`, { method: 'DELETE' })
  if (!response.ok) throw new Error(await parseError(response))
}

export async function fetchDocuments(kbId: string): Promise<KnowledgeDocument[]> {
  const response = await fetch(`${BASE}/bases/${kbId}/documents`)
  if (!response.ok) throw new Error(await parseError(response))
  return response.json()
}

export async function uploadDocument(kbId: string, file: File): Promise<KnowledgeDocument> {
  const form = new FormData()
  form.append('file', file)

  const response = await fetch(`${BASE}/bases/${kbId}/documents`, {
    method: 'POST',
    body: form
  })
  if (!response.ok) throw new Error(await parseError(response))
  return response.json()
}

export async function deleteDocument(docId: string): Promise<void> {
  const response = await fetch(`${BASE}/documents/${docId}`, { method: 'DELETE' })
  if (!response.ok) throw new Error(await parseError(response))
}
