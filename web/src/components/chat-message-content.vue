<template>
  <div
    class="chat-md"
    :class="{
      'chat-md--user': role === 'user',
      'chat-md--assistant': role === 'assistant' && !streaming,
      'chat-md--plain': streaming
    }"
  >
    <div
      v-if="role === 'assistant' && !streaming"
      class="chat-md__html"
      v-html="html"
      @click="onHtmlClick"
    />
    <p v-else class="chat-md__text">
      {{ content }}<span v-if="streaming" class="chat-md__cursor">|</span>
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatRole } from '@/types/chat'
import { renderMarkdown } from '@/utils/markdown'
import { checkIconSvg, copyIconSvg } from '@/utils/chat-icons'

const props = defineProps<{
  role: ChatRole
  content: string
  streaming?: boolean
}>()

const html = computed(() => renderMarkdown(props.content))

function onHtmlClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  const button = target?.closest<HTMLButtonElement>('.code-block__copy')
  if (!button) return

  event.preventDefault()

  const block = button.closest('.code-block')
  const code = block?.querySelector('code')?.textContent ?? ''
  if (!code) return

  navigator.clipboard.writeText(code).then(() => {
    button.classList.add('code-block__copy--done')
    button.innerHTML = checkIconSvg(14)
    window.setTimeout(() => {
      button.classList.remove('code-block__copy--done')
      button.innerHTML = copyIconSvg(14)
    }, 2000)
  }).catch(() => {
    button.setAttribute('title', '复制失败')
    window.setTimeout(() => {
      button.setAttribute('title', '复制代码')
    }, 2000)
  })
}
</script>

<style scoped>
.chat-md__text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-md__cursor {
  animation: blink 1s step-end infinite;
}

.chat-md--assistant {
  width: 100%;
}

.chat-md--assistant :deep(.chat-md__html) {
  width: 100%;
  line-height: 1.7;
  word-break: break-word;
}

.chat-md--assistant :deep(p) {
  margin: 0 0 0.75em;
}

.chat-md--assistant :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-md--assistant :deep(ul),
.chat-md--assistant :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.4em;
}

.chat-md--assistant :deep(li) {
  margin: 0.25em 0;
}

.chat-md--assistant :deep(blockquote) {
  margin: 0.5em 0;
  padding-left: 12px;
  border-left: 3px solid var(--border-strong);
  color: var(--text-secondary);
}

.chat-md--assistant :deep(a) {
  color: var(--accent);
}

.chat-md--assistant :deep(:not(pre) > code) {
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-muted);
  font-size: 0.9em;
}

.chat-md--assistant :deep(.code-block) {
  width: 100%;
  box-sizing: border-box;
  margin: 0.75em 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-code);
}

.chat-md--assistant :deep(.code-block__header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-code-header);
  border-bottom: 1px solid var(--border);
}

.chat-md--assistant :deep(.code-block__lang) {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: lowercase;
}

.chat-md--assistant :deep(.code-block__copy) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
}

.chat-md--assistant :deep(.code-block__copy:hover) {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.chat-md--assistant :deep(.code-block__copy--done) {
  color: var(--success);
  border-color: var(--success);
}

.chat-md--assistant :deep(.code-block pre) {
  margin: 0;
  padding: 14px 16px;
  overflow-x: auto;
  background: var(--bg-code);
}

.chat-md--assistant :deep(.code-block pre code) {
  padding: 0;
  background: transparent;
  font-size: 13px;
  line-height: 1.6;
}

.chat-md--assistant :deep(h1),
.chat-md--assistant :deep(h2),
.chat-md--assistant :deep(h3) {
  margin: 0.8em 0 0.4em;
  font-size: 1em;
  font-weight: 700;
}

.chat-md--assistant :deep(table) {
  display: block;
  width: 100%;
  max-width: 100%;
  margin: 0.75em 0;
  border-collapse: collapse;
  overflow-x: auto;
}

.chat-md--assistant :deep(th),
.chat-md--assistant :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--border);
  text-align: left;
}

.chat-md--assistant :deep(th) {
  background: var(--bg-muted);
  font-weight: 600;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}
</style>
