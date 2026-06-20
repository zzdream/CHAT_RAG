<template>
  <a-config-provider :theme="antdTheme">
    <div class="chat-app">
    <div
      v-if="sidebarOpen"
      class="chat-app__backdrop"
      @click="sidebarOpen = false"
    />

    <aside class="chat-sidebar" :class="{ 'chat-sidebar--open': sidebarOpen }">
      <div class="chat-sidebar__brand">
        <div class="chat-sidebar__logo">S</div>
        <div>
          <p class="chat-sidebar__name">{{ appTitle }}</p>
          <p class="chat-sidebar__tagline">DeepSeek · 流式对话</p>
        </div>
      </div>

      <button
        class="chat-sidebar__new"
        type="button"
        :disabled="isStreaming"
        @click="handleNewSession"
      >
        <span class="chat-sidebar__new-icon">+</span>
        新对话
      </button>

      <ul class="chat-sidebar__list">
        <li
          v-for="session in sessions"
          :key="session.id"
          class="chat-sidebar__item"
          :class="{ 'chat-sidebar__item--active': session.id === activeSessionId }"
        >
          <button
            class="chat-sidebar__select"
            type="button"
            :title="session.title"
            :disabled="isStreaming"
            @click="handleSwitchSession(session.id)"
          >
            <span class="chat-sidebar__title">{{ session.title }}</span>
            <span class="chat-sidebar__time">{{ formatTime(session.updatedAt) }}</span>
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
              class="chat-sidebar__delete"
              type="button"
              title="删除此对话"
              :disabled="isStreaming"
              @click.stop
            >
              ×
            </button>
          </a-popconfirm>
        </li>
      </ul>
    </aside>

    <section class="chat-main">
      <header class="chat-toolbar">
        <div class="chat-toolbar__left">
          <button
            class="chat-toolbar__icon-btn chat-toolbar__menu"
            type="button"
            title="会话列表"
            aria-label="打开会话列表"
            @click="sidebarOpen = true"
          >
            <IconMenu :size="18" />
          </button>
          <h1 class="chat-toolbar__title">{{ activeSessionTitle }}</h1>
        </div>
        <div class="chat-toolbar__right chat-toolbar__right--desktop">
          <button
            class="chat-toolbar__icon-btn"
            type="button"
            :title="theme === 'dark' ? '浅色模式' : '深色模式'"
            @click="toggleTheme"
          >
            <IconSun v-if="theme === 'dark'" :size="18" />
            <IconMoon v-else :size="18" />
          </button>
          <button
            class="chat-toolbar__pill"
            type="button"
            :class="{ 'chat-toolbar__pill--active': settingsDrawerOpen && settingsTab === 'model' }"
            :disabled="isStreaming"
            @click="openSettingsDrawer('model')"
          >
            模型设置
          </button>
          <a-dropdown :disabled="!activeSession || isStreaming" :trigger="['click']">
            <button
              class="chat-toolbar__pill"
              type="button"
              :disabled="!activeSession || isStreaming"
            >
              导出
            </button>
            <template #overlay>
              <a-menu @click="handleExport">
                <a-menu-item key="markdown">导出 Markdown</a-menu-item>
                <a-menu-item key="json">导出 JSON</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
          <button
            class="chat-toolbar__pill"
            type="button"
            :class="{ 'chat-toolbar__pill--active': settingsDrawerOpen && settingsTab === 'system' }"
            :disabled="isStreaming"
            @click="openSettingsDrawer('system')"
          >
            角色设定
          </button>
        </div>
        <div class="chat-toolbar__right chat-toolbar__right--mobile">
          <a-dropdown :trigger="['click']">
            <button
              class="chat-toolbar__icon-btn"
              type="button"
              title="更多"
              aria-label="更多操作"
            >
              ⋯
            </button>
            <template #overlay>
              <a-menu @click="handleMobileToolbarMenu">
                <a-menu-item key="model" :disabled="isStreaming">模型设置</a-menu-item>
                <a-menu-item key="export-markdown" :disabled="!activeSession || isStreaming">导出 Markdown</a-menu-item>
                <a-menu-item key="export-json" :disabled="!activeSession || isStreaming">导出 JSON</a-menu-item>
                <a-menu-item key="system" :disabled="isStreaming">角色设定</a-menu-item>
                <a-menu-divider />
                <a-menu-item key="theme">{{ theme === 'dark' ? '浅色模式' : '深色模式' }}</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </header>

      <a-drawer
        v-model:open="settingsDrawerOpen"
        class="chat-settings-drawer"
        title="对话设置"
        placement="right"
        :width="settingsDrawerWidth"
        :destroy-on-close="false"
      >
        <a-tabs v-model:activeKey="settingsTab" class="chat-settings-tabs">
          <a-tab-pane key="model" tab="模型">
            <div class="chat-drawer-section">
              <p class="chat-drawer-section__desc">模型与采样温度（仅当前对话）</p>
              <label class="chat-drawer-field">
                <span>模型</span>
                <select
                  v-model="sessionModel"
                  class="chat-drawer-field__select"
                  :disabled="isStreaming"
                >
                  <option
                    v-for="item in chatModels"
                    :key="item.value"
                    :value="item.value"
                  >
                    {{ item.label }}
                  </option>
                </select>
              </label>
              <label class="chat-drawer-field">
                <span>温度 {{ sessionTemperature.toFixed(1) }}</span>
                <input
                  v-model.number="sessionTemperature"
                  class="chat-drawer-field__range"
                  type="range"
                  :min="MIN_TEMPERATURE"
                  :max="MAX_TEMPERATURE"
                  :step="TEMPERATURE_STEP"
                  :disabled="isStreaming"
                />
                <span class="chat-drawer-field__hint">低更稳定 · 高更有创意</span>
              </label>
            </div>
          </a-tab-pane>
          <a-tab-pane key="system" tab="角色">
            <div class="chat-drawer-section">
              <p class="chat-drawer-section__desc">系统提示词（仅当前对话）</p>
              <div class="chat-drawer-presets">
                <button
                  v-for="preset in systemPresets"
                  :key="preset.label"
                  class="chat-drawer-presets__item"
                  type="button"
                  :disabled="isStreaming"
                  @click="applySystemPreset(preset.value)"
                >
                  {{ preset.label }}
                </button>
              </div>
              <textarea
                v-model="systemPrompt"
                class="chat-drawer-field__textarea"
                rows="6"
                placeholder="例如：你是一位耐心的编程助教，用简洁中文回答。"
                :disabled="isStreaming"
              />
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-drawer>

      <div v-if="error" class="chat-alert chat-content" role="alert">
        <span>{{ error }}</span>
        <button class="chat-alert__close" type="button" aria-label="关闭" @click="clearError">×</button>
      </div>

      <div ref="messageListRef" class="chat-body">
        <div class="chat-messages">
        <div class="chat-content">
        <div v-if="messages.length === 0" class="chat-welcome">
          <div class="chat-welcome__icon">✦</div>
          <h2 class="chat-welcome__title">有什么可以帮你？</h2>
          <p class="chat-welcome__desc">基于 DeepSeek 的流式 AI 助手，支持多轮对话与 Markdown 代码高亮。</p>
          <div class="chat-welcome__chips">
            <button
              v-for="example in exampleQuestions"
              :key="example"
              class="chat-welcome__chip"
              type="button"
              :disabled="isStreaming"
              @click="applyExample(example)"
            >
              {{ example }}
            </button>
          </div>
        </div>

        <TransitionGroup name="chat-message" tag="div" class="chat-message-list">
        <article
          v-for="message in messages"
          :key="message.id"
          class="chat-message"
          :class="`chat-message--${message.role}`"
        >
          <div class="chat-message__body">
            <div class="chat-message__bubble">
              <div
                v-if="isMessageStreaming(message) && !getMessageContent(message)"
                class="chat-message__thinking"
              >
                <span /><span /><span />
                思考中
              </div>
              <ChatMessageContent
                v-else
                :role="message.role"
                :content="getMessageContent(message)"
                :streaming="isMessageStreaming(message)"
              />
            </div>
            <div
              v-if="getMessageContent(message).trim() && !isMessageStreaming(message)"
              class="chat-message__actions"
            >
              <button
                class="chat-message__action"
                :class="{ 'chat-message__action--done': copiedMessageId === message.id }"
                type="button"
                title="复制"
                aria-label="复制"
                @click="copyMessage(message)"
              >
                <IconCheck v-if="copiedMessageId === message.id" :size="15" />
                <IconCopy v-else :size="15" />
              </button>
              <button
                v-if="canRegenerate(message)"
                class="chat-message__action"
                type="button"
                title="重新生成"
                aria-label="重新生成"
                @click="regenerateMessage(message.id)"
              >
                <IconRegenerate :size="15" />
              </button>
            </div>
            <p
              v-if="message.role === 'assistant' && getMessageUsage(message)"
              class="chat-message__usage"
            >
              本次约 {{ getMessageUsage(message)!.total_tokens }} tokens
              （输入 {{ getMessageUsage(message)!.prompt_tokens }} · 输出 {{ getMessageUsage(message)!.completion_tokens }}）
            </p>
          </div>
        </article>
        </TransitionGroup>
        </div>
        </div>

      <footer class="chat-composer">
        <div class="chat-composer__box chat-content">
          <textarea
            ref="inputRef"
            v-model="input"
            class="chat-composer__input"
            rows="1"
            placeholder="发消息，Enter 发送，Shift + Enter 换行"
            :disabled="isStreaming"
            @keydown="onKeydown"
            @input="resizeInput"
          />
          <div class="chat-composer__footer">
            <span class="chat-composer__hint">{{ isStreaming ? '生成中…' : 'Enter 发送' }}</span>
            <div class="chat-composer__buttons">
              <button
                v-if="isStreaming"
                class="chat-composer__stop"
                type="button"
                @click="stopStreaming"
              >
                停止
              </button>
              <button
                class="chat-composer__send"
                type="button"
                title="发送"
                :disabled="isStreaming || !input.trim()"
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
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { theme as antdThemeApi } from 'ant-design-vue'
import { storeToRefs } from 'pinia'
import ChatMessageContent from '@/components/chat-message-content.vue'
import IconCheck from '@/components/icons/icon-check.vue'
import IconCopy from '@/components/icons/icon-copy.vue'
import IconMenu from '@/components/icons/icon-menu.vue'
import IconMoon from '@/components/icons/icon-moon.vue'
import IconRegenerate from '@/components/icons/icon-regenerate.vue'
import IconSend from '@/components/icons/icon-send.vue'
import IconSun from '@/components/icons/icon-sun.vue'
import {
  CHAT_MODELS,
  MAX_TEMPERATURE,
  MIN_TEMPERATURE,
  TEMPERATURE_STEP
} from '@/constants/chat'
import { useChatStream } from '@/hooks/use-chat-stream'
import { useAppStore } from '@/store'
import { exportSessionAsJson, exportSessionAsMarkdown } from '@/utils/export-chat'

const chatModels = CHAT_MODELS

const exampleQuestions = [
  '用 Python 写一个快速排序',
  '解释什么是 SSE 流式输出',
  'React 和 Vue 有什么区别？'
]

const systemPresets = [
  { label: '编程助教', value: '你是一位耐心的编程助教，用简洁中文回答，必要时附带可运行代码示例。' },
  { label: '翻译官', value: '你是专业翻译，将用户内容翻译成自然流畅的中文；若已是中文则翻译成英文。' },
  { label: '简洁模式', value: '用简短、分点的中文回答，每次不超过 150 字。' }
]

const appStore = useAppStore()
const { appTitle, theme } = storeToRefs(appStore)
const { toggleTheme } = appStore

const {
  sessions,
  activeSessionId,
  activeSession,
  messages,
  input,
  systemPrompt,
  sessionModel,
  sessionTemperature,
  isStreaming,
  error,
  streamingContent,
  copiedMessageId,
  createNewSession,
  switchSession,
  deleteSession,
  sendMessage,
  regenerateMessage,
  copyMessage,
  stopStreaming,
  onKeydown,
  getMessageContent,
  getMessageUsage,
  isMessageStreaming,
  canRegenerate
} = useChatStream()

const sidebarOpen = ref(false)
const messageListRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const settingsDrawerOpen = ref(false)
const settingsTab = ref<'model' | 'system'>('model')
const settingsDrawerWidth = ref(380)

function updateSettingsDrawerWidth() {
  settingsDrawerWidth.value = window.innerWidth <= 768 ? Math.min(window.innerWidth, 360) : 380
}

const activeSessionTitle = computed(() => {
  const session = sessions.value.find(item => item.id === activeSessionId.value)
  return session?.title ?? '新对话'
})

const antdTheme = computed(() => ({
  algorithm: theme.value === 'dark' ? antdThemeApi.darkAlgorithm : antdThemeApi.defaultAlgorithm
}))

watch(
  () => [messages.value.length, activeSessionId.value],
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

watch(streamingContent, async () => {
  await nextTick()
  scrollToBottom()
})

watch(input, async () => {
  await nextTick()
  resizeInput()
})

onMounted(() => {
  resizeInput()
  updateSettingsDrawerWidth()
  window.addEventListener('resize', updateSettingsDrawerWidth)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateSettingsDrawerWidth)
})

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function resizeInput() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

function handleNewSession() {
  createNewSession()
  sidebarOpen.value = false
}

function handleSwitchSession(sessionId: string) {
  switchSession(sessionId)
  sidebarOpen.value = false
}

function applyExample(text: string) {
  input.value = text
  resizeInput()
  inputRef.value?.focus()
}

watch(activeSessionId, () => {
  settingsDrawerOpen.value = false
})

function openSettingsDrawer(tab: 'model' | 'system') {
  if (settingsDrawerOpen.value && settingsTab.value === tab) {
    settingsDrawerOpen.value = false
    return
  }

  settingsTab.value = tab
  settingsDrawerOpen.value = true
}

function applySystemPreset(text: string) {
  systemPrompt.value = text
  openSettingsDrawer('system')
}

function handleExport({ key }: { key: string }) {
  if (!activeSession.value) return

  if (key === 'markdown') {
    exportSessionAsMarkdown(activeSession.value)
    return
  }

  if (key === 'json') {
    exportSessionAsJson(activeSession.value)
  }
}

function handleMobileToolbarMenu({ key }: { key: string }) {
  if (key === 'model') {
    openSettingsDrawer('model')
    return
  }

  if (key === 'system') {
    openSettingsDrawer('system')
    return
  }

  if (key === 'theme') {
    toggleTheme()
    return
  }

  if (key === 'export-markdown' || key === 'export-json') {
    handleExport({ key: key.replace('export-', '') })
  }
}

function clearError() {
  error.value = ''
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
</script>

<style scoped>
.chat-app {
  display: flex;
  height: 100%;
  min-height: 0;
  position: relative;
}

.chat-app__backdrop {
  display: none;
}

.chat-sidebar {
  flex-shrink: 0;
  width: var(--sidebar-width);
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  z-index: 20;
}

.chat-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px 12px;
}

.chat-sidebar__logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent), #7c3aed);
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  box-shadow: var(--shadow-sm);
}

.chat-sidebar__name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.chat-sidebar__tagline {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}

.chat-sidebar__new {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 8px 12px 12px;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-weight: 600;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.chat-sidebar__new:hover:not(:disabled) {
  border-color: var(--accent);
  box-shadow: var(--shadow-sm);
}

.chat-sidebar__new:disabled {
  opacity: 0.5;
}

.chat-sidebar__new-icon {
  font-size: 18px;
  line-height: 1;
  color: var(--accent);
}

.chat-sidebar__list {
  list-style: none;
  margin: 0;
  padding: 0 8px 16px;
  overflow-y: auto;
  flex: 1;
}

.chat-sidebar__item {
  display: flex;
  align-items: stretch;
  gap: 2px;
  margin-bottom: 4px;
  border-radius: var(--radius-md);
  transition: background 0.15s;
}

.chat-sidebar__item:hover {
  background: var(--bg-elevated);
}

.chat-sidebar__item--active {
  background: var(--accent-soft);
}

.chat-sidebar__item--active .chat-sidebar__title {
  color: var(--accent);
  font-weight: 600;
}

.chat-sidebar__select {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  padding: 10px 8px 10px 12px;
  border: none;
  background: transparent;
  text-align: left;
  color: inherit;
}

.chat-sidebar__title {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  color: var(--text-primary);
}

.chat-sidebar__time {
  font-size: 11px;
  color: var(--text-muted);
}

.chat-sidebar__delete {
  flex-shrink: 0;
  width: 32px;
  margin: 6px 4px 6px 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-size: 18px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
}

.chat-sidebar__item:hover .chat-sidebar__delete,
.chat-sidebar__item--active .chat-sidebar__delete {
  opacity: 1;
}

.chat-sidebar__delete:hover:not(:disabled) {
  background: var(--danger-soft);
  color: var(--danger);
}

.chat-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.chat-content {
  width: 100%;
  max-width: var(--chat-content-max-width);
  margin-inline: auto;
  padding-inline: 20px;
  box-sizing: border-box;
}

.chat-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-surface);
}

.chat-toolbar__left,
.chat-toolbar__right {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.chat-toolbar__menu {
  display: none;
}

.chat-toolbar__right--mobile {
  display: none;
}

.chat-toolbar__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-toolbar__icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  transition: border-color 0.15s, color 0.15s;
}

.chat-toolbar__icon-btn:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.chat-toolbar__pill {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s;
}

.chat-toolbar__pill:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.chat-toolbar__pill--active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}

.chat-drawer-section__desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.chat-drawer-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.chat-drawer-field__select,
.chat-drawer-field__textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-primary);
  line-height: 1.5;
}

.chat-drawer-field__select:focus,
.chat-drawer-field__textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-ring);
}

.chat-drawer-field__textarea {
  resize: vertical;
  min-height: 140px;
}

.chat-drawer-field__range {
  width: 100%;
  accent-color: var(--accent);
}

.chat-drawer-field__hint {
  font-size: 12px;
  color: var(--text-muted);
}

.chat-drawer-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.chat-drawer-presets__item {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-muted);
  color: var(--text-secondary);
  font-size: 12px;
  transition: all 0.15s;
}

.chat-drawer-presets__item:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.chat-alert {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 14px;
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--radius-md);
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 14px;
}

.chat-alert__close {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 18px;
  line-height: 1;
  padding: 0 4px;
}

.chat-body {
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

.chat-body::-webkit-scrollbar {
  width: 8px;
}

.chat-body::-webkit-scrollbar-track {
  background: transparent;
}

.chat-body::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--text-muted) 40%, transparent);
  border-radius: 4px;
}

.chat-body::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--text-muted) 60%, transparent);
}

.chat-messages {
  flex: 1;
  padding-block: 20px 72px;
}

.chat-welcome {
  margin: 48px auto 0;
  text-align: center;
  animation: welcome-in 0.45s ease;
}

.chat-welcome__icon {
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

.chat-welcome__title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.chat-welcome__desc {
  margin: 0 0 24px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.chat-welcome__chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.chat-welcome__chip {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s;
  box-shadow: var(--shadow-sm);
}

.chat-welcome__chip:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

.chat-message-list {
  display: block;
}

.chat-message {
  margin-bottom: 20px;
}

.chat-message--user {
  display: flex;
  justify-content: flex-end;
}

.chat-message__body {
  width: 100%;
  min-width: 0;
}

.chat-message--user .chat-message__body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  width: auto;
  max-width: min(100%, 520px);
}

.chat-message__bubble {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  line-height: 1.7;
  word-break: break-word;
}

.chat-message--user .chat-message__bubble {
  background: linear-gradient(135deg, var(--accent), #6366f1);
  color: var(--text-inverse);
  box-shadow: var(--shadow-sm);
}

.chat-message--assistant .chat-message__bubble {
  padding: 8px 0;
  background: transparent;
  color: var(--text-primary);
  border: none;
  box-shadow: none;
}

.chat-message__thinking {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 14px;
}

.chat-message__thinking span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: bounce 1.2s infinite ease-in-out;
}

.chat-message__thinking span:nth-child(2) {
  animation-delay: 0.15s;
}

.chat-message__thinking span:nth-child(3) {
  animation-delay: 0.3s;
}

.chat-message__actions {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}

.chat-message--user .chat-message__actions {
  justify-content: flex-end;
}

.chat-message__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  transition: background 0.15s, color 0.15s;
}

.chat-message__action:hover {
  background: var(--bg-elevated);
  color: var(--text-secondary);
}

.chat-message__action--done {
  color: var(--success);
}

.chat-message__usage {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}

.chat-message-enter-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}

.chat-message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.chat-composer {
  position: sticky;
  bottom: 0;
  z-index: 5;
  flex-shrink: 0;
  margin-top: -64px;
  padding: 64px 0 20px;
  background: transparent;
  isolation: isolate;
}

.chat-composer::before {
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

.chat-composer__box {
  padding-block: 12px;
  border: 1px solid var(--composer-border);
  border-radius: var(--radius-xl);
  background: var(--composer-surface);
  -webkit-backdrop-filter: blur(calc(var(--composer-blur) + 4px)) saturate(1.1);
  backdrop-filter: blur(calc(var(--composer-blur) + 4px)) saturate(1.1);
  box-shadow: var(--shadow-md);
}

.chat-composer__input {
  width: 100%;
  min-height: 24px;
  max-height: 160px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text-primary);
  resize: none;
  line-height: 1.6;
}

.chat-composer__input:focus {
  outline: none;
}

.chat-composer__input:disabled {
  opacity: 0.6;
}

.chat-composer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.chat-composer__hint {
  font-size: 12px;
  color: var(--text-muted);
}

.chat-composer__buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-composer__stop {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-muted);
  color: var(--text-secondary);
  font-size: 12px;
}

.chat-composer__send {
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

.chat-composer__send:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.04);
}

.chat-composer__send:disabled {
  opacity: 0.45;
}

@keyframes bounce {
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
  .chat-app__backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    z-index: 15;
  }

  .chat-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    box-shadow: var(--shadow-sidebar);
  }

  .chat-sidebar--open {
    transform: translateX(0);
  }

  .chat-toolbar__menu {
    display: inline-flex;
  }

  .chat-toolbar__right--desktop {
    display: none;
  }

  .chat-toolbar__right--mobile {
    display: flex;
    flex-shrink: 0;
  }

  .chat-toolbar {
    padding: 10px 12px;
    gap: 8px;
  }

  .chat-toolbar__left {
    flex: 1;
    min-width: 0;
    gap: 6px;
  }

  .chat-toolbar__title {
    font-size: 15px;
  }

  .chat-toolbar__icon-btn {
    width: 34px;
    height: 34px;
  }

  .chat-content {
    padding-inline: 0;
  }

  .chat-messages {
    padding-block: 12px 64px;
  }

  .chat-messages .chat-content {
    padding-inline: 12px;
  }

  .chat-composer {
    margin-top: -56px;
    padding: 56px 12px calc(12px + env(safe-area-inset-bottom, 0px));
  }

  .chat-composer::before {
    -webkit-mask-image: linear-gradient(to top, #000 52%, transparent 100%);
    mask-image: linear-gradient(to top, #000 52%, transparent 100%);
  }

  .chat-composer__box {
    padding-block: 10px;
    padding-inline: 14px;
  }

  .chat-composer__footer {
    margin-top: 8px;
    padding-top: 0;
    border-top: none;
  }

  .chat-composer__hint {
    display: none;
  }
}
</style>
