<template>
  <a-config-provider :theme="antdTheme">
    <div class="rag-chat-page">
      <AppNav />

      <div class="rag-app">
        <div v-if="sidebarOpen" class="rag-app__backdrop" @click="sidebarOpen = false" />

        <aside class="rag-sidebar" :class="{ 'rag-sidebar--open': sidebarOpen }">
          <div class="rag-sidebar__brand">
            <div class="rag-sidebar__logo">R</div>
            <div class="rag-sidebar__brand-text">
              <p class="rag-sidebar__name">知识库问答</p>
              <p class="rag-sidebar__tagline">RAG · 检索问答</p>
            </div>
          </div>

          <button
            class="rag-sidebar__new"
            type="button"
            :disabled="!selectedKbId || isStreaming"
            @click="handleNewSession"
          >
            <span class="rag-sidebar__new-icon">+</span>
            新问答
          </button>

          <div class="rag-sidebar__section">
            <p class="rag-sidebar__section-title">知识库</p>
            <a-spin :spinning="kbLoading" size="small">
              <a-select
                v-if="bases.length"
                v-model:value="selectedKbId"
                class="rag-sidebar__kb-dropdown"
                placeholder="请选择知识库"
                :options="kbOptions"
                :disabled="isStreaming"
                @change="onKbChange"
              />
              <div v-else class="rag-sidebar__empty">
                <p>暂无知识库</p>
              </div>
            </a-spin>
          </div>

          <div v-if="selectedKbId" class="rag-sidebar__section rag-sidebar__section--grow">
            <p class="rag-sidebar__section-title">问答记录</p>
            <ul v-if="kbSessions.length" class="rag-sidebar__session-list">
              <li
                v-for="session in kbSessions"
                :key="session.id"
                class="rag-sidebar__session-item"
                :class="{ 'rag-sidebar__session-item--active': session.id === activeSessionId }"
              >
                <button
                  type="button"
                  class="rag-sidebar__session-select"
                  :title="session.title"
                  :disabled="isStreaming"
                  @click="handleSwitchSession(session.id)"
                >
                  <span class="rag-sidebar__session-title">{{ session.title }}</span>
                  <span class="rag-sidebar__session-time">{{ formatTime(session.updatedAt) }}</span>
                </button>
                <a-popconfirm
                  title="确定删除此问答？"
                  description="删除后无法恢复。"
                  ok-text="删除"
                  cancel-text="取消"
                  ok-type="danger"
                  :disabled="isStreaming"
                  @confirm="deleteSession(session.id)"
                >
                  <button
                    type="button"
                    class="rag-sidebar__session-delete"
                    title="删除"
                    :disabled="isStreaming"
                    @click.stop
                  >
                    ×
                  </button>
                </a-popconfirm>
              </li>
            </ul>
            <div v-else class="rag-sidebar__empty">
              <p>暂无问答记录</p>
            </div>
          </div>

          <RouterLink class="rag-sidebar__manage" to="/knowledge">
            管理知识库
          </RouterLink>
        </aside>

        <section class="rag-main">
          <header class="rag-toolbar">
            <div class="rag-toolbar__left">
              <button
                class="rag-toolbar__menu"
                type="button"
                title="打开侧边栏"
                aria-label="打开侧边栏"
                @click="sidebarOpen = true"
              >
                <IconMenu :size="18" />
              </button>
              <h1 class="rag-toolbar__title">{{ toolbarTitle }}</h1>
            </div>
          </header>

          <div v-if="kbLoadError" class="rag-alert rag-content" role="alert">
            <span>{{ kbLoadError }}</span>
          </div>
          <div v-if="error" class="rag-alert rag-content" role="alert">
            <span>{{ error }}</span>
          </div>

          <div class="rag-body">
            <div class="rag-messages">
              <div class="rag-content">
                <div v-if="!kbLoading && !bases.length" class="rag-welcome">
                  <div class="rag-welcome__icon">📚</div>
                  <h2 class="rag-welcome__title">还没有知识库</h2>
                  <p class="rag-welcome__desc">先创建知识库并上传文档，才能在这里进行检索问答。</p>
                  <RouterLink to="/knowledge">
                    <a-button type="primary" size="large">去创建知识库</a-button>
                  </RouterLink>
                </div>

                <div v-else-if="!messages.length && !isStreaming" class="rag-welcome">
                  <div class="rag-welcome__icon">✦</div>
                  <h2 class="rag-welcome__title">基于文档提问</h2>
                  <p class="rag-welcome__desc">
                    从「{{ selectedBase?.name ?? '当前知识库' }}」检索相关内容，回答会附带引用来源。
                  </p>
                  <div class="rag-welcome__features">
                    <span>引用来源可追溯</span>
                    <span>资料外内容会说明</span>
                  </div>
                  <div v-if="selectedKbId" class="rag-welcome__chips">
                    <button
                      v-for="example in exampleQuestions"
                      :key="example"
                      class="rag-welcome__chip"
                      type="button"
                      :disabled="isStreaming"
                      @click="applyExample(example)"
                    >
                      {{ example }}
                    </button>
                  </div>
                </div>

                <TransitionGroup name="rag-message" tag="div" class="rag-message-list">
                  <article
                    v-for="message in messages"
                    :key="message.id"
                    class="rag-message"
                    :class="`rag-message--${message.role}`"
                  >
                    <div class="rag-message__body">
                      <div class="rag-message__bubble">
                        <div
                          v-if="isMessageStreaming(message) && !getMessageContent(message)"
                          class="rag-message__thinking"
                        >
                          <span /><span /><span />
                          检索中
                        </div>
                        <template v-else>
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
                      <p
                        v-if="message.role === 'assistant' && message.usage && !isMessageStreaming(message)"
                        class="rag-message__usage"
                      >
                        本次约 {{ message.usage.total_tokens }} tokens
                        （输入 {{ message.usage.prompt_tokens }} · 输出 {{ message.usage.completion_tokens }}）
                      </p>
                    </div>
                  </article>
                </TransitionGroup>
              </div>
            </div>

            <footer class="rag-composer">
              <div class="rag-composer__box rag-content">
                <textarea
                  v-model="input"
                  class="rag-composer__input"
                  rows="1"
                  :placeholder="composerPlaceholder"
                  :disabled="!selectedKbId || isStreaming"
                  @keydown="onKeydown"
                />
                <div class="rag-composer__footer">
                  <span class="rag-composer__hint">
                    {{ isStreaming ? '生成中…' : 'Enter 发送 · Shift+Enter 换行' }}
                  </span>
                  <div class="rag-composer__buttons">
                    <button
                      v-if="isStreaming"
                      class="rag-composer__stop"
                      type="button"
                      @click="stopStreaming"
                    >
                      停止
                    </button>
                    <button
                      class="rag-composer__send"
                      type="button"
                      title="发送"
                      :disabled="!selectedKbId || !input.trim() || isStreaming"
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
import AppNav from '@/components/app-nav.vue'
import ChatMessageContent from '@/components/chat-message-content.vue'
import IconMenu from '@/components/icons/icon-menu.vue'
import IconSend from '@/components/icons/icon-send.vue'
import RagCitations from '@/components/rag-citations.vue'
import { RAG_DEFAULT_TITLE } from '@/constants/rag'
import { useRagChat } from '@/hooks/use-rag-chat'
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
const selectedKbId = ref('')

const exampleQuestions = [
  '这份资料主要讲了什么？',
  '帮我总结关键要点',
  '有哪些需要注意的细节？'
]

const selectedBase = computed(() => bases.value.find(item => item.id === selectedKbId.value) ?? null)

const {
  sessions,
  activeSessionId,
  activeSession,
  messages,
  input,
  isStreaming,
  error,
  createNewSession,
  ensureSessionForKb,
  syncSessionsWithKnowledgeBases,
  switchSession,
  deleteSession,
  sendMessage,
  stopStreaming,
  onKeydown,
  getMessageContent,
  getMessageSources,
  isMessageStreaming
} = useRagChat(selectedKbId)

const kbSessions = computed(() =>
  sessions.value
    .filter(item => item.knowledgeBaseId === selectedKbId.value)
    .sort((a, b) => b.updatedAt - a.updatedAt)
)

const toolbarTitle = computed(() => activeSession.value?.title ?? RAG_DEFAULT_TITLE)

const composerPlaceholder = computed(() =>
  selectedKbId.value ? '基于知识库提问…' : '请先选择或创建知识库'
)

const kbOptions = computed(() =>
  bases.value.map(item => ({
    label: `${item.name}（${item.document_count}）`,
    value: item.id
  }))
)

function applyExample(text: string) {
  input.value = text
}

function onKbChange() {
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
    const matched = storedKbId && bases.value.some(item => item.id === storedKbId)

    selectedKbId.value = matched ? storedKbId! : (bases.value[0]?.id ?? '')

    if (selectedKbId.value) {
      ensureSessionForKb(selectedKbId.value)
    }
  } catch (err) {
    kbLoadError.value = err instanceof Error ? err.message : '加载知识库失败'
  } finally {
    kbLoading.value = false
  }
})
</script>

<style scoped>
.rag-chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.rag-app {
  flex: 1;
  min-height: 0;
  display: flex;
  position: relative;
}

.rag-app__backdrop {
  display: none;
}

/* ── 主区域 ── */
.rag-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.rag-content {
  width: 100%;
  max-width: var(--chat-content-max-width);
  margin-inline: auto;
  padding-inline: 20px;
  box-sizing: border-box;
}

.rag-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-surface);
}

.rag-toolbar__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.rag-toolbar__menu {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-secondary);
}

.rag-toolbar__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rag-alert {
  flex-shrink: 0;
  margin-top: 12px;
  padding: 10px 14px;
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--radius-md);
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 14px;
}

.rag-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-gutter: stable both-edges;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--text-muted) 50%, transparent) transparent;
}

.rag-body::-webkit-scrollbar {
  width: 8px;
}

.rag-body::-webkit-scrollbar-track {
  background: transparent;
}

.rag-body::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--text-muted) 40%, transparent);
  border-radius: 4px;
}

.rag-body::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--text-muted) 60%, transparent);
}

.rag-messages {
  flex: 1;
  padding-block: 20px 72px;
}

.rag-welcome {
  margin: 48px auto 0;
  text-align: center;
  animation: welcome-in 0.45s ease;
}

.rag-welcome__icon {
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

.rag-welcome__title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.rag-welcome__desc {
  margin: 0 0 20px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.rag-welcome__features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
}

.rag-welcome__features span {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-muted);
  font-size: 12px;
  color: var(--text-muted);
}

.rag-welcome__chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.rag-welcome__chip {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s;
  box-shadow: var(--shadow-sm);
}

.rag-welcome__chip:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

.rag-message-list {
  display: block;
}

.rag-message {
  margin-bottom: 20px;
}

.rag-message--user {
  display: flex;
  justify-content: flex-end;
}

.rag-message__body {
  width: 100%;
  min-width: 0;
}

.rag-message--user .rag-message__body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  width: auto;
  max-width: min(100%, 520px);
}

.rag-message__bubble {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  line-height: 1.7;
  word-break: break-word;
}

.rag-message--user .rag-message__bubble {
  background: linear-gradient(135deg, var(--accent), #6366f1);
  color: var(--text-inverse);
  box-shadow: var(--shadow-sm);
}

.rag-message--assistant .rag-message__bubble {
  padding: 8px 0;
  background: transparent;
  color: var(--text-primary);
}

.rag-message__thinking {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 14px;
}

.rag-message__thinking span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: rag-bounce 1.2s infinite ease-in-out;
}

.rag-message__thinking span:nth-child(2) {
  animation-delay: 0.15s;
}

.rag-message__thinking span:nth-child(3) {
  animation-delay: 0.3s;
}

.rag-message__usage {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}

.rag-message-enter-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}

.rag-message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.rag-composer {
  position: sticky;
  bottom: 0;
  z-index: 5;
  flex-shrink: 0;
  margin-top: -64px;
  padding: 64px 0 20px;
  background: transparent;
  isolation: isolate;
}

.rag-composer::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background: linear-gradient(
    to top,
    var(--composer-fade-solid) 0%,
    var(--composer-fade-mid) 42%,
    var(--composer-fade-clear) 100%
  );
  -webkit-backdrop-filter: blur(var(--composer-blur)) saturate(1.15);
  backdrop-filter: blur(var(--composer-blur)) saturate(1.15);
  -webkit-mask-image: linear-gradient(to top, #000 58%, transparent 100%);
  mask-image: linear-gradient(to top, #000 58%, transparent 100%);
}

.rag-composer__box {
  padding-block: 12px;
  border: 1px solid var(--composer-border);
  border-radius: var(--radius-xl);
  background: var(--composer-surface);
  -webkit-backdrop-filter: blur(calc(var(--composer-blur) + 4px)) saturate(1.1);
  backdrop-filter: blur(calc(var(--composer-blur) + 4px)) saturate(1.1);
  box-shadow: var(--shadow-md);
}

.rag-composer__input {
  width: 100%;
  min-height: 24px;
  max-height: 160px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text-primary);
  resize: none;
  line-height: 1.6;
  font-family: inherit;
  font-size: 14px;
}

.rag-composer__input:focus {
  outline: none;
}

.rag-composer__input:disabled {
  opacity: 0.6;
}

.rag-composer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.rag-composer__hint {
  font-size: 12px;
  color: var(--text-muted);
}

.rag-composer__buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rag-composer__stop {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-muted);
  color: var(--text-secondary);
  font-size: 12px;
}

.rag-composer__send {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  transition: background 0.15s, transform 0.15s;
}

.rag-composer__send:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.04);
}

.rag-composer__send:disabled {
  opacity: 0.45;
}

@keyframes rag-bounce {
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
  .rag-app__backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    z-index: 15;
  }

  .rag-toolbar__menu {
    display: inline-flex;
  }

  .rag-toolbar {
    padding: 10px 12px;
  }

  .rag-content {
    padding-inline: 12px;
  }

  .rag-messages {
    padding-block: 12px 64px;
  }

  .rag-composer {
    margin-top: -56px;
    padding: 56px 12px calc(12px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
