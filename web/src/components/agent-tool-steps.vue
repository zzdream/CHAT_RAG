<template>
  <details v-if="steps.length" class="agent-tool-steps" :open="expanded">
    <summary class="agent-tool-steps__summary">
      工具调用（{{ callCount }}）
      <span v-if="expanded" class="agent-tool-steps__live">进行中</span>
    </summary>
    <ol class="agent-tool-steps__list">
      <li
        v-for="(step, index) in steps"
        :key="`${step.id}-${step.type}-${index}`"
        class="agent-tool-steps__item"
        :class="`agent-tool-steps__item--${step.type}`"
      >
        <div class="agent-tool-steps__head">
          <span class="agent-tool-steps__badge">{{ step.type === 'tool_call' ? '调用' : '结果' }}</span>
          <span class="agent-tool-steps__name">{{ toolLabel(step.name) }}</span>
        </div>
        <pre v-if="step.arguments" class="agent-tool-steps__code">{{ formatArgs(step.arguments) }}</pre>
        <pre v-if="step.result" class="agent-tool-steps__code agent-tool-steps__code--result">{{ truncate(step.result) }}</pre>
      </li>
    </ol>
  </details>
</template>

<script setup lang="ts">
import { AGENT_TOOL_LABELS } from '@/constants/agent'
import type { AgentToolStep } from '@/types/agent'

const props = defineProps<{
  steps: AgentToolStep[]
  expanded?: boolean
}>()

const callCount = computed(() => props.steps.filter(item => item.type === 'tool_call').length)

function toolLabel(name: string) {
  return AGENT_TOOL_LABELS[name] ?? name
}

function formatArgs(raw: string) {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
}

function truncate(text: string, max = 600) {
  return text.length > max ? `${text.slice(0, max)}…` : text
}
</script>

<style scoped>
.agent-tool-steps {
  margin-top: 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-muted);
  overflow: hidden;
}

.agent-tool-steps__summary {
  cursor: pointer;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  user-select: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-tool-steps__live {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  background: var(--accent-soft);
  color: var(--accent);
}

.agent-tool-steps__list {
  list-style: none;
  margin: 0;
  padding: 0 12px 12px;
  display: grid;
  gap: 10px;
}

.agent-tool-steps__item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  border: 1px solid var(--border);
}

.agent-tool-steps__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.agent-tool-steps__badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  background: var(--accent-soft);
  color: var(--accent);
}

.agent-tool-steps__item--tool_result .agent-tool-steps__badge {
  background: color-mix(in srgb, #16a34a 15%, transparent);
  color: #16a34a;
}

.agent-tool-steps__name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-tool-steps__code {
  margin: 0;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
}

.agent-tool-steps__code--result {
  max-height: 180px;
  overflow-y: auto;
}
</style>
