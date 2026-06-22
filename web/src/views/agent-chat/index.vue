<template>
  <a-config-provider :theme="antdTheme">
    <div class="agent-chat-page">
      <AppNav />

      <div class="agent-app">
        <div v-if="sidebarOpen" class="agent-app__backdrop" @click="sidebarOpen = false" />

        <aside class="agent-sidebar" :class="{ 'agent-sidebar--open': sidebarOpen }">
          <div class="agent-sidebar__brand">
            <div class="agent-sidebar__logo">A</div>
            <div class="agent-sidebar__brand-text">
              <p class="agent-sidebar__name">{{ AGENT_PAGE_NAME }}</p>
              <p class="agent-sidebar__tagline">自动调用工具 · 知识库可选</p>
            </div>
          </div>

          <button
            class="agent-sidebar__new"
            type="button"
            :disabled="isStreaming"
            @click="handleNewSession"
          >
            <span class="agent-sidebar__new-icon">+</span>
            新对话
          </button>

          <div class="agent-sidebar__section">
            <p class="agent-sidebar__section-title">知识库</p>
            <a-spin :spinning="kbLoading" size="small">
              <a-select
                v-model:value="selectedKbId"
                class="agent-sidebar__kb-dropdown"
                placeholder="不绑定知识库"
                :options="kbOptions"
                :disabled="isStreaming"
                @change="onKbChange"
              />
            </a-spin>
          </div>

          <div class="agent-sidebar__section agent-sidebar__section--grow">
            <p class="agent-sidebar__section-title">对话记录</p>
            <ul v-if="scopeSessions.length" class="agent-sidebar__session-list">
              <li
                v-for="session in scopeSessions"
                :key="session.id"
                class="agent-sidebar__session-item"
                :class="{ 'agent-sidebar__session-item--active': session.id === activeSessionId }"
              >
                <button
                  type="button"
                  class="agent-sidebar__session-select"
                  :title="session.title"
                  :disabled="isStreaming"
                  @click="handleSwitchSession(session.id)"
                >
                  <span class="agent-sidebar__session-title">{{ session.title }}</span>
                  <span class="agent-sidebar__session-time">{{ formatTime(session.updatedAt) }}</span>
                </button>
                <a-popconfirm
                  title="确定删除此对话？"
                  description="删除后无法恢复。"
                  ok-text="删除"
                  cancel-text="取消"
                  ok-type="danger"
                  :disabled="isStreaming"
                  @confirm="deleteSession(session.id)"
                >
                  <button
                    type="button"
                    class="agent-sidebar__session-delete"
                    title="删除"
                    :disabled="isStreaming"
                    @click.stop
                  >
                    ×
                  </button>
                </a-popconfirm>
              </li>
            </ul>
            <div v-else class="agent-sidebar__empty">
              <p>暂无对话记录</p>
            </div>
          </div>

          <RouterLink class="agent-sidebar__manage" to="/knowledge">
            管理知识库
          </RouterLink>
        </aside>

        <section class="agent-main">
          <header class="agent-toolbar">
            <div class="agent-toolbar__left">
              <button
                class="agent-toolbar__menu"
                type="button"
                title="打开侧边栏"
                aria-label="打开侧边栏"
                @click="sidebarOpen = true"
              >
                <IconMenu :size="18" />
              </button>
              <div class="agent-toolbar__titles">
                <h1 class="agent-toolbar__title">{{ toolbarTitle }}</h1>
                <p class="agent-toolbar__subtitle">{{ toolbarSubtitle }}</p>
              </div>
            </div>
          </header>

          <div v-if="kbLoadError" class="agent-alert agent-content" role="alert">
            <span>{{ kbLoadError }}</span>
          </div>
          <div v-if="error" class="agent-alert agent-content" role="alert">
            <span>{{ error }}</span>
            <button
              v-if="lastFailedUserText"
              class="agent-alert__retry"
              type="button"
              :disabled="isStreaming"
              @click="retryLastMessage"
            >
              重试
            </button>
          </div>
          <div v-if="retryNotice" class="agent-retry-notice agent-content" role="status">
            {{ retryNotice }}
          </div>

          <div class="agent-body">
            <div class="agent-messages">
              <div class="agent-content">
                <div v-if="!messages.length && !isStreaming" class="agent-welcome">
                  <div class="agent-welcome__icon">🤖</div>
                  <h2 class="agent-welcome__title">{{ AGENT_PAGE_NAME }}</h2>
                  <p class="agent-welcome__desc">
                    与普通聊天不同：我会根据你的问题<strong>自动选择工具</strong>，再组合给出答案。
                  </p>

                  <div class="agent-welcome__capabilities">
                    <article
                      v-for="cap in visibleCapabilities"
                      :key="cap.title"
                      class="agent-capability"
                      :class="{ 'agent-capability--disabled': cap.requiresKb && !selectedKbId }"
                    >
                      <span class="agent-capability__icon">{{ cap.icon }}</span>
                      <div class="agent-capability__body">
                        <h3 class="agent-capability__title">{{ cap.title }}</h3>
                        <p class="agent-capability__desc">{{ cap.desc }}</p>
                      </div>
                    </article>
                  </div>

                  <p class="agent-welcome__kb-status">
                    <template v-if="selectedKbId">
                      当前知识库：<strong>{{ selectedBase?.name }}</strong>
                    </template>
                    <template v-else>
                      当前未绑定知识库，可使用<strong>计算器</strong>与<strong>文本格式化</strong>。
                      <button
                        v-if="bases.length"
                        type="button"
                        class="agent-welcome__kb-link"
                        @click="pickFirstKb"
                      >
                        绑定知识库
                      </button>
                    </template>
                  </p>

                  <p class="agent-welcome__diff">{{ AGENT_RAG_DIFF_HINT }}</p>

                  <div class="agent-welcome__chips">
                    <button
                      v-for="example in exampleQuestions"
                      :key="example"
                      class="agent-welcome__chip"
                      type="button"
                      :disabled="isStreaming"
                      @click="applyExample(example)"
                    >
                      {{ example }}
                    </button>
                  </div>
                </div>

                <TransitionGroup name="agent-message" tag="div" class="agent-message-list">
                  <article
                    v-for="message in messages"
                    :key="message.id"
                    class="agent-message"
                    :class="`agent-message--${message.role}`"
                  >
                    <div class="agent-message__body">
                      <div class="agent-message__bubble">
                        <div
                          v-if="isMessageStreaming(message) && !getMessageContent(message) && !getMessageToolSteps(message).length"
                          class="agent-message__thinking"
                        >
                          <span /><span /><span />
                          {{ streamingStatus || 'Agent 思考中' }}
                        </div>
                        <template v-else>
                          <AgentToolSteps
                            v-if="message.role === 'assistant'"
                            :steps="getMessageToolSteps(message)"
                            :expanded="isMessageStreaming(message)"
                          />
                          <ChatMessageContent
                            :role="message.role"
                            :content="getMessageContent(message)"
                            :streaming="isMessageStreaming(message)"
                          />
                          <RagCitations
                            v-if="message.role === 'assistant'"
                            :sources="getMessageSources(message)"
                          />
                        </template>
                      </div>
                      <div
                        v-if="message.role === 'assistant' && !isMessageStreaming(message)"
                        class="agent-message__actions"
                      >
                        <button
                          class="agent-message__action"
                          type="button"
                          title="重新生成"
                          :disabled="isStreaming"
                          @click="regenerateMessage(message.id)"
                        >
                          重新生成
                        </button>
                      </div>
                      <p
                        v-if="message.role === 'assistant' && message.usage && !isMessageStreaming(message)"
                        class="agent-message__usage"
                      >
                        本次约 {{ message.usage.total_tokens }} tokens
                        （输入 {{ message.usage.prompt_tokens }} · 输出 {{ message.usage.completion_tokens }}）
                      </p>
                    </div>
                  </article>
                </TransitionGroup>
              </div>
            </div>

            <footer class="agent-composer">
              <div class="agent-composer__box agent-content">
                <textarea
                  v-model="input"
                  class="agent-composer__input"
                  rows="1"
                  :placeholder="composerPlaceholder"
                  :disabled="isStreaming"
                  @keydown="onKeydown"
                />
                <div class="agent-composer__footer">
                  <span class="agent-composer__hint">
                    {{ isStreaming ? (streamingStatus || 'Agent 运行中…') : 'Enter 发送 · Shift+Enter 换行' }}
                  </span>
                  <div class="agent-composer__buttons">
                    <button
                      v-if="isStreaming"
                      class="agent-composer__stop"
                      type="button"
                      @click="stopStreaming"
                    >
                      停止
                    </button>
                    <button
                      class="agent-composer__send"
                      type="button"
                      title="发送"
                      :disabled="!input.trim() || isStreaming"
                      @click="sendMessage"
                    >
                      <IconSend :size="18" />
                    </button>
                  </div>
                </div>
              </div>
            </footer>
          </div>
        </section>
      </div>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { theme as antTheme } from 'ant-design-vue'
import { fetchKnowledgeBases } from '@/api/knowledge'
import AgentToolSteps from '@/components/agent-tool-steps.vue'
import AppNav from '@/components/app-nav.vue'
import ChatMessageContent from '@/components/chat-message-content.vue'
import IconMenu from '@/components/icons/icon-menu.vue'
import IconSend from '@/components/icons/icon-send.vue'
import RagCitations from '@/components/rag-citations.vue'
import {
  AGENT_CAPABILITIES,
  AGENT_DEFAULT_TITLE,
  AGENT_EXAMPLES_WITH_KB,
  AGENT_EXAMPLES_WITHOUT_KB,
  AGENT_KB_NONE,
  AGENT_PAGE_NAME,
  AGENT_RAG_DIFF_HINT
} from '@/constants/agent'
import { useAgentChat } from '@/hooks/use-agent-chat'
import { useAppStore } from '@/store/modules/app'
import type { KnowledgeBase } from '@/types/knowledge'

const appStore = useAppStore()
const { theme } = storeToRefs(appStore)

const antdTheme = computed(() => ({
  algorithm: theme.value === 'dark' ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm
}))

const sidebarOpen = ref(false)
const kbLoading = ref(false)
const kbLoadError = ref('')
const bases = ref<KnowledgeBase[]>([])
const selectedKbId = ref(AGENT_KB_NONE)

const {
  sessions,
  activeSessionId,
  activeSession,
  messages,
  input,
  isStreaming,
  error,
  retryNotice,
  streamingStatus,
  lastFailedUserText,
  createNewSession,
  ensureSessionForScope,
  syncSessionsWithKnowledgeBases,
  switchSession,
  deleteSession,
  sendMessage,
  retryLastMessage,
  regenerateMessage,
  stopStreaming,
  onKeydown,
  getMessageContent,
  getMessageToolSteps,
  getMessageSources,
  isMessageStreaming
} = useAgentChat(selectedKbId)

const selectedBase = computed(() => bases.value.find(item => item.id === selectedKbId.value) ?? null)

const scopeSessions = computed(() =>
  sessions.value
    .filter(item => item.knowledgeBaseId === selectedKbId.value)
    .sort((a, b) => b.updatedAt - a.updatedAt)
)

const visibleCapabilities = computed(() => AGENT_CAPABILITIES)

const exampleQuestions = computed(() =>
  selectedKbId.value ? AGENT_EXAMPLES_WITH_KB : AGENT_EXAMPLES_WITHOUT_KB
)

const toolbarTitle = computed(() => activeSession.value?.title ?? AGENT_DEFAULT_TITLE)

const toolbarSubtitle = computed(() => {
  if (selectedKbId.value && selectedBase.value) {
    return `${AGENT_PAGE_NAME} · 知识库：${selectedBase.value.name}`
  }
  return `${AGENT_PAGE_NAME} · 未绑定知识库（计算器 / 格式化）`
})

const composerPlaceholder = computed(() =>
  selectedKbId.value
    ? '可检索文档、计算或格式化文本…'
    : '可提问计算或文本格式化；绑定知识库后可查文档'
)

const kbOptions = computed(() => {
  const options = [
    {
      label: '不绑定（仅计算器 / 格式化）',
      value: AGENT_KB_NONE
    }
  ]
  for (const item of bases.value) {
    options.push({
      label: `${item.name}（${item.document_count}）`,
      value: item.id
    })
  }
  return options
})

function pickFirstKb() {
  if (!bases.value.length) return
  selectedKbId.value = bases.value[0].id
  ensureSessionForScope(selectedKbId.value)
}

function applyExample(text: string) {
  input.value = text
}

function onKbChange() {
  ensureSessionForScope(selectedKbId.value)
  sidebarOpen.value = false
}

function handleNewSession() {
  createNewSession()
  sidebarOpen.value = false
}

function handleSwitchSession(sessionId: string) {
  switchSession(sessionId)
  sidebarOpen.value = false
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  if (isToday) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

onMounted(async () => {
  kbLoading.value = true
  try {
    bases.value = await fetchKnowledgeBases()
    syncSessionsWithKnowledgeBases(bases.value.map(item => item.id))

    const storedKbId = activeSession.value?.knowledgeBaseId
    if (storedKbId === AGENT_KB_NONE) {
      selectedKbId.value = AGENT_KB_NONE
    } else if (storedKbId && bases.value.some(item => item.id === storedKbId)) {
      selectedKbId.value = storedKbId
    } else {
      selectedKbId.value = bases.value[0]?.id ?? AGENT_KB_NONE
    }

    ensureSessionForScope(selectedKbId.value)
  } catch (err) {
    kbLoadError.value = err instanceof Error ? err.message : '加载知识库失败'
    ensureSessionForScope(AGENT_KB_NONE)
  } finally {
    kbLoading.value = false
  }
})
</script>

<style scoped>
.agent-chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.agent-app {
  flex: 1;
  min-height: 0;
  display: flex;
  position: relative;
}

.agent-app__backdrop {
  display: none;
}

.agent-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.agent-content {
  width: 100%;
  max-width: var(--chat-content-max-width);
  margin-inline: auto;
  padding-inline: 20px;
  box-sizing: border-box;
}

.agent-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-surface);
}

.agent-toolbar__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.agent-toolbar__titles {
  min-width: 0;
}

.agent-toolbar__subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  font-weight: 400;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-toolbar__menu {
  display: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-secondary);
}

.agent-toolbar__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-alert {
  margin-top: 12px;
  padding: 10px 14px;
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--radius-md);
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.agent-alert__retry {
  flex-shrink: 0;
  padding: 6px 12px;
  border: 1px solid rgba(220, 38, 38, 0.35);
  border-radius: 999px;
  background: var(--bg-surface);
  color: var(--danger);
  font-size: 12px;
}

.agent-retry-notice {
  margin-top: 12px;
  padding: 10px 14px;
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  border-radius: var(--radius-md);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 13px;
}

.agent-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.agent-messages {
  flex: 1;
  padding-block: 20px 72px;
}

.agent-welcome {
  margin: 48px auto 0;
  text-align: center;
  animation: welcome-in 0.45s ease;
}

.agent-welcome__icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 24px;
}

.agent-welcome__title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.agent-welcome__desc {
  margin: 0 0 20px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.agent-welcome__desc strong {
  color: var(--text-primary);
  font-weight: 600;
}

.agent-welcome__capabilities {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin: 0 auto 20px;
  max-width: 640px;
  text-align: left;
}

.agent-capability {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s, transform 0.15s;
}

.agent-capability:hover {
  border-color: var(--border-strong);
  transform: translateY(-1px);
}

.agent-capability--disabled {
  opacity: 0.55;
}

.agent-capability__icon {
  flex-shrink: 0;
  font-size: 22px;
  line-height: 1;
}

.agent-capability__title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-capability__desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-muted);
}

.agent-welcome__kb-status {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.agent-welcome__kb-link {
  margin-left: 6px;
  padding: 0;
  border: none;
  background: none;
  color: var(--accent);
  font-size: 13px;
  cursor: pointer;
  text-decoration: underline;
}

.agent-welcome__diff {
  margin: 0 0 24px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: var(--bg-muted);
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-muted);
}

.agent-welcome__features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
}

.agent-welcome__features span {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-muted);
  font-size: 12px;
  color: var(--text-muted);
}

.agent-welcome__chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.agent-welcome__chip {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s;
  box-shadow: var(--shadow-sm);
}

.agent-welcome__chip:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

.agent-message {
  margin-bottom: 20px;
}

.agent-message-enter-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}

.agent-message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.agent-message--user {
  display: flex;
  justify-content: flex-end;
}

.agent-message--user .agent-message__body {
  max-width: min(100%, 520px);
}

.agent-message--user .agent-message__bubble {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--accent), #6366f1);
  color: var(--text-inverse);
}

.agent-message--assistant .agent-message__bubble {
  padding: 8px 0;
}

.agent-message__thinking {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 14px;
}

.agent-message__thinking span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: agent-bounce 1.2s infinite ease-in-out;
}

.agent-message__thinking span:nth-child(2) {
  animation-delay: 0.15s;
}

.agent-message__thinking span:nth-child(3) {
  animation-delay: 0.3s;
}

.agent-message__usage {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}

.agent-message__actions {
  margin-top: 8px;
}

.agent-message__action {
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-muted);
  color: var(--text-secondary);
  font-size: 12px;
}

.agent-message__action:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.agent-composer {
  position: sticky;
  bottom: 0;
  z-index: 5;
  margin-top: -64px;
  padding: 64px 0 20px;
}

.agent-composer__box {
  padding: 12px;
  border: 1px solid var(--composer-border);
  border-radius: var(--radius-xl);
  background: var(--composer-surface);
  box-shadow: var(--shadow-md);
}

.agent-composer__input {
  width: 100%;
  min-height: 24px;
  max-height: 160px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  resize: none;
  line-height: 1.6;
  font-family: inherit;
  font-size: 14px;
}

.agent-composer__input:focus {
  outline: none;
}

.agent-composer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.agent-composer__hint {
  font-size: 12px;
  color: var(--text-muted);
}

.agent-composer__buttons {
  display: flex;
  gap: 8px;
}

.agent-composer__stop {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-muted);
  font-size: 12px;
}

.agent-composer__send {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
}

.agent-composer__send:disabled {
  opacity: 0.45;
}

@keyframes agent-bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }

  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

@keyframes welcome-in {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 768px) {
  .agent-app__backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    z-index: 15;
  }

  .agent-toolbar__menu {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
