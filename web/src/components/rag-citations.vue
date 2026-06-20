<template>
  <details v-if="sources.length" class="rag-citations">
    <summary class="rag-citations__summary">
      引用来源（{{ sources.length }}）
    </summary>
    <ul class="rag-citations__list">
      <li v-for="(source, index) in sources" :key="`${source.document_id}-${source.chunk_index}-${index}`">
        <div class="rag-citations__meta">
          <span>{{ source.filename || '未知文件' }}</span>
          <span>相似度 {{ (source.score * 100).toFixed(0) }}%</span>
        </div>
        <p class="rag-citations__content">{{ source.content }}</p>
      </li>
    </ul>
  </details>
</template>

<script setup lang="ts">
import type { RagSource } from '@/types/rag'

defineProps<{
  sources: RagSource[]
}>()
</script>

<style scoped>
.rag-citations {
  margin-top: 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-muted);
  overflow: hidden;
}

.rag-citations__summary {
  cursor: pointer;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  user-select: none;
}

.rag-citations__list {
  list-style: none;
  margin: 0;
  padding: 0 12px 12px;
  display: grid;
  gap: 10px;
}

.rag-citations__meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.rag-citations__content {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
