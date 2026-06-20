import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  deleteDocument,
  fetchDocuments,
  fetchKnowledgeBases,
  uploadDocument
} from '@/api/knowledge'
import { RAG_MODEL_READY_KEY } from '@/constants/rag'
import type { KnowledgeBase, KnowledgeDocument } from '@/types/knowledge'

function readModelReadyFlag(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem(RAG_MODEL_READY_KEY) === '1'
}

function markModelReady() {
  if (typeof window === 'undefined') return
  localStorage.setItem(RAG_MODEL_READY_KEY, '1')
}

export function useKnowledge() {
  const bases = ref<KnowledgeBase[]>([])
  const documents = ref<KnowledgeDocument[]>([])
  const activeBaseId = ref<string>('')
  const loading = ref(false)
  const uploading = ref(false)
  const error = ref('')

  let pollTimer: ReturnType<typeof setInterval> | null = null

  const activeBase = computed(() =>
    bases.value.find(item => item.id === activeBaseId.value) ?? null
  )

  const modelReady = ref(readModelReadyFlag())

  function syncModelReadyFromDocuments(items: KnowledgeDocument[]) {
    if (modelReady.value) return
    if (items.some(item => item.status === 'indexed')) {
      modelReady.value = true
      markModelReady()
    }
  }

  function syncBaseDocumentCount(kbId: string) {
    const baseIndex = bases.value.findIndex(item => item.id === kbId)
    if (baseIndex < 0) return

    bases.value[baseIndex] = {
      ...bases.value[baseIndex],
      document_count: documents.value.length
    }
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function startPolling(kbId: string) {
    stopPolling()

    pollTimer = setInterval(async () => {
      try {
        documents.value = await fetchDocuments(kbId)
        syncModelReadyFromDocuments(documents.value)
        if (!documents.value.some(item => item.status === 'pending')) {
          stopPolling()
          await loadBases()
        }
      } catch {
        // 轮询失败时静默重试
      }
    }, 2500)
  }

  async function loadBases() {
    loading.value = true
    error.value = ''
    try {
      bases.value = await fetchKnowledgeBases()
      if (!activeBaseId.value && bases.value.length > 0) {
        activeBaseId.value = bases.value[0].id
      }
      if (activeBaseId.value && !bases.value.some(item => item.id === activeBaseId.value)) {
        activeBaseId.value = bases.value[0]?.id ?? ''
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function loadDocuments(kbId?: string) {
    const targetId = kbId ?? activeBaseId.value
    if (!targetId) {
      documents.value = []
      return
    }

    loading.value = true
    error.value = ''
    try {
      documents.value = await fetchDocuments(targetId)
      syncModelReadyFromDocuments(documents.value)
      syncBaseDocumentCount(targetId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载文档失败'
    } finally {
      loading.value = false
    }
  }

  async function createBase(name: string, description = '') {
    error.value = ''
    const created = await createKnowledgeBase({ name, description })
    bases.value = [created, ...bases.value]
    activeBaseId.value = created.id
    documents.value = []
    return created
  }

  async function removeBase(id: string) {
    error.value = ''
    await deleteKnowledgeBase(id)
    bases.value = bases.value.filter(item => item.id !== id)
    if (activeBaseId.value === id) {
      activeBaseId.value = bases.value[0]?.id ?? ''
    }
    if (activeBaseId.value) {
      await loadDocuments(activeBaseId.value)
    } else {
      documents.value = []
    }
  }

  async function uploadDoc(file: File) {
    if (!activeBaseId.value) throw new Error('请先选择知识库')
    uploading.value = true
    error.value = ''
    try {
      const doc = await uploadDocument(activeBaseId.value, file)
      documents.value = [doc, ...documents.value.filter(item => item.id !== doc.id)]
      syncBaseDocumentCount(activeBaseId.value)
      if (doc.status === 'pending') {
        startPolling(activeBaseId.value)
      }
      return doc
    } finally {
      uploading.value = false
    }
  }

  async function removeDoc(docId: string) {
    error.value = ''
    await deleteDocument(docId)
    documents.value = documents.value.filter(item => item.id !== docId)
    if (activeBaseId.value) {
      syncBaseDocumentCount(activeBaseId.value)
    }
  }

  watch(activeBaseId, kbId => {
    stopPolling()
    if (kbId) {
      loadDocuments(kbId).then(() => {
        if (documents.value.some(item => item.status === 'pending')) {
          startPolling(kbId)
        }
      })
    } else {
      documents.value = []
    }
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    bases,
    documents,
    activeBaseId,
    activeBase,
    loading,
    uploading,
    error,
    loadBases,
    loadDocuments,
    createBase,
    removeBase,
    uploadDoc,
    removeDoc
  }
}
