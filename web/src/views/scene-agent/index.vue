<template>
  <a-config-provider :theme="antdTheme">
    <div class="scene-page">
      <AppNav />

      <div class="scene-app">
        <div v-if="sidebarOpen" class="scene-app__backdrop" @click="sidebarOpen = false" />

        <aside class="agent-sidebar scene-sidebar" :class="{ 'agent-sidebar--open': sidebarOpen }">
          <div class="agent-sidebar__brand">
            <div class="agent-sidebar__logo">3D</div>
            <div class="agent-sidebar__brand-text">
              <p class="agent-sidebar__name">{{ SCENE_PAGE_NAME }}</p>
              <p class="agent-sidebar__tagline">Three.js · AI 场景控制</p>
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
            <p class="agent-sidebar__section-title">上传模型</p>
            <label class="scene-upload">
              <input
                type="file"
                accept=".glb,.gltf"
                multiple
                :disabled="sceneLoading || isStreaming"
                @change="onFileChange"
              />
              <span class="scene-upload__label">
                {{ sceneLoading ? '加载中…' : '选择 GLB / GLTF' }}
              </span>
            </label>
            <p v-if="sceneLoadError" class="scene-upload__error">{{ sceneLoadError }}</p>
          </div>

          <div class="agent-sidebar__section">
            <p class="agent-sidebar__section-title">场景模型</p>
            <ul v-if="sceneObjects.length" class="agent-sidebar__session-list scene-model-list">
              <li
                v-for="item in sceneObjects"
                :key="item.id"
                class="agent-sidebar__session-item"
                :class="{ 'agent-sidebar__session-item--active': item.id === selectedObjectId }"
              >
                <button
                  type="button"
                  class="agent-sidebar__session-select"
                  :disabled="isStreaming"
                  @click="selectModel(item.id)"
                >
                  <span class="agent-sidebar__session-title">{{ item.name }}</span>
                  <span class="agent-sidebar__session-time">{{ item.fileName }}</span>
                </button>
                <button
                  type="button"
                  class="agent-sidebar__session-delete"
                  title="移除"
                  :disabled="isStreaming"
                  @click="removeModel(item.id)"
                >
                  ×
                </button>
              </li>
            </ul>
            <div v-else class="agent-sidebar__empty">
              <p>上传 GLB 后将显示在这里</p>
            </div>
          </div>

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

        <section class="scene-main">
          <header class="scene-toolbar">
            <div class="scene-toolbar__left">
              <button
                class="scene-toolbar__menu"
                type="button"
                title="打开侧边栏"
                @click="sidebarOpen = true"
              >
                <IconMenu :size="18" />
              </button>
              <div class="scene-toolbar__titles">
                <h1 class="scene-toolbar__title">{{ toolbarTitle }}</h1>
                <p class="scene-toolbar__subtitle">{{ toolbarSubtitle }}</p>
              </div>
            </div>
            <div class="scene-toolbar__actions">
              <button
                v-if="selectedObject"
                class="scene-toolbar__action"
                type="button"
                :disabled="isStreaming"
                @click="explainSelected"
              >
                解释选中模型
              </button>
            </div>
          </header>

          <div class="scene-workspace">
            <div ref="canvasHostRef" class="scene-viewport">
              <div v-if="!sceneObjects.length" class="scene-viewport__empty">
                <p>拖拽或从左侧上传 GLB 模型</p>
                <p class="scene-viewport__hint">点击模型选中 · 顶栏「解释选中模型」可提问</p>
              </div>
            </div>

            <div class="scene-chat">
              <div v-if="kbLoadError" class="scene-alert" role="alert">{{ kbLoadError }}</div>
              <div v-if="error" class="scene-alert" role="alert">
                <span>{{ error }}</span>
                <button
                  v-if="lastFailedUserText"
                  class="scene-alert__retry"
                  type="button"
                  :disabled="isStreaming"
                  @click="retryLastMessage"
                >
                  重试
                </button>
              </div>
              <div v-if="retryNotice" class="scene-retry-notice" role="status">{{ retryNotice }}</div>

              <div class="scene-chat__messages">
                <div v-if="!messages.length && !isStreaming" class="scene-welcome">
                  <div class="scene-welcome__icon">🧊</div>
                  <h2 class="scene-welcome__title">{{ SCENE_PAGE_NAME }}</h2>
                  <p class="scene-welcome__desc">
                    上传 GLB 后，可点击模型选中，再用顶栏按钮或文字/语音控制场景。
                  </p>
                  <div class="scene-welcome__capabilities">
                    <article
                      v-for="cap in SCENE_CAPABILITIES"
                      :key="cap.title"
                      class="scene-capability"
                      :class="{ 'scene-capability--disabled': cap.requiresKb && !selectedKbId }"
                    >
                      <span class="scene-capability__icon">{{ cap.icon }}</span>
                      <div>
                        <h3 class="scene-capability__title">{{ cap.title }}</h3>
                        <p class="scene-capability__desc">{{ cap.desc }}</p>
                      </div>
                    </article>
                  </div>
                  <p class="scene-welcome__hint">{{ SCENE_HINT }}</p>
                  <div class="scene-welcome__chips">
                    <button
                      v-for="example in exampleQuestions"
                      :key="example"
                      class="scene-welcome__chip"
                      type="button"
                      :disabled="isStreaming"
                      @click="applyExample(example)"
                    >
                      {{ example }}
                    </button>
                  </div>
                </div>

                <TransitionGroup name="scene-message" tag="div" class="scene-message-list">
                  <article
                    v-for="message in messages"
                    :key="message.id"
                    class="scene-message"
                    :class="`scene-message--${message.role}`"
                  >
                    <div class="scene-message__body">
                      <div class="scene-message__bubble">
                        <div
                          v-if="isMessageStreaming(message) && !getMessageContent(message) && !getMessageToolSteps(message).length"
                          class="scene-message__thinking"
                        >
                          <span /><span /><span />
                          {{ streamingStatus || 'Scene Agent 思考中' }}
                        </div>
                        <template v-else>
                          <AgentToolSteps
                            v-if="message.role === 'assistant'"
                            :steps="getMessageToolSteps(message)"
                            :expanded="isMessageStreaming(message)"
                            :tool-labels="SCENE_TOOL_LABELS"
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
                        class="scene-message__actions"
                      >
                        <button
                          class="scene-message__action"
                          type="button"
                          :disabled="isStreaming"
                          @click="regenerateMessage(message.id)"
                        >
                          重新生成
                        </button>
                      </div>
                    </div>
                  </article>
                </TransitionGroup>
              </div>

              <footer class="scene-composer">
                <textarea
                  v-model="input"
                  class="scene-composer__input"
                  rows="2"
                  :placeholder="composerPlaceholder"
                  :disabled="isStreaming"
                  @keydown="onKeydown"
                />
                <div v-if="speechError" class="scene-speech-error" role="alert">{{ speechError }}</div>
                <div class="scene-composer__footer">
                  <span class="scene-composer__hint" :class="{ 'scene-composer__hint--live': isSpeechListening }">
                    {{ composerHint }}
                  </span>
                  <div class="scene-composer__buttons">
                    <button
                      v-if="isStreaming"
                      class="scene-composer__stop"
                      type="button"
                      @click="stopStreaming"
                    >
                      停止
                    </button>
                    <button
                      class="scene-composer__mic"
                      :class="{
                        'scene-composer__mic--active': isSpeechListening || isSpeechPending
                      }"
                      type="button"
                      :title="
                        isSpeechListening
                          ? '停止语音输入'
                          : isSpeechPending
                            ? '正在启动…'
                            : speechSupported
                              ? '语音输入'
                              : speechUnsupportedReason || '语音输入不可用'
                      "
                      :disabled="
                        isStreaming || isSpeechBootstrapping || speechLocalModelStatus === 'downloading'
                      "
                      @click="handleMicClick"
                    >
                      <IconMic :size="18" />
                    </button>
                    <button
                      class="scene-composer__send"
                      type="button"
                      :disabled="!input.trim() || isStreaming"
                      @click="sendMessage()"
                    >
                      <IconSend :size="18" />
                    </button>
                  </div>
                </div>
              </footer>
            </div>
          </div>
        </section>
      </div>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { message, theme as antTheme } from 'ant-design-vue'
import { fetchKnowledgeBases } from '@/api/knowledge'
import AgentToolSteps from '@/components/agent-tool-steps.vue'
import AppNav from '@/components/app-nav.vue'
import ChatMessageContent from '@/components/chat-message-content.vue'
import IconMenu from '@/components/icons/icon-menu.vue'
import IconMic from '@/components/icons/icon-mic.vue'
import IconSend from '@/components/icons/icon-send.vue'
import RagCitations from '@/components/rag-citations.vue'
import {
  SCENE_CAPABILITIES,
  SCENE_DEFAULT_TITLE,
  SCENE_EXAMPLES_WITH_KB,
  SCENE_EXAMPLES_WITHOUT_KB,
  SCENE_HINT,
  SCENE_KB_NONE,
  SCENE_PAGE_NAME,
  SCENE_TOOL_LABELS
} from '@/constants/scene'
import { useSceneAgent } from '@/hooks/use-scene-agent'
import { useSceneThree } from '@/hooks/use-scene-three'
import { useSpeechRecognition } from '@/hooks/use-speech-recognition'
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
const selectedKbId = ref(SCENE_KB_NONE)
const canvasHostRef = ref<HTMLElement | null>(null)

const {
  objects: sceneObjects,
  selectedObjectId,
  selectedObject,
  objectSnapshots,
  loading: sceneLoading,
  loadError: sceneLoadError,
  initScene,
  loadGlbFile,
  removeObject,
  focusObject,
  applyHighlight,
  executeSceneAction
} = useSceneThree()

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
  explainSelectedObject,
  retryLastMessage,
  regenerateMessage,
  stopStreaming,
  onKeydown,
  getMessageContent,
  getMessageToolSteps,
  getMessageSources,
  isMessageStreaming
} = useSceneAgent({
  initialKnowledgeBaseId: selectedKbId,
  getSceneObjects: () => objectSnapshots.value,
  getSelectedObjectId: () => selectedObjectId.value,
  onSceneAction: action => executeSceneAction(action)
})

const {
  isSupported: speechSupported,
  unsupportedReason: speechUnsupportedReason,
  isListening: isSpeechListening,
  isPending: isSpeechPending,
  isBootstrapping: isSpeechBootstrapping,
  recognitionMode: speechRecognitionMode,
  localModelStatus: speechLocalModelStatus,
  error: speechError,
  toggle: toggleSpeech
} = useSpeechRecognition({
  onInterim: text => {
    input.value = text
  },
  onFinal: text => {
    input.value = text
  },
  onPending: () => {
    message.loading({ content: '启动语音识别…', key: 'scene-speech', duration: 0 })
  },
  onListening: () => {
    message.destroy('scene-speech')
    message.info('正在聆听，再次点击麦克风结束', 2)
  },
  onError: text => {
    message.destroy('scene-speech')
    if (text) message.error(text, 5)
  },
  onSettled: () => {
    message.destroy('scene-speech')
  }
})

function handleMicClick() {
  if (isStreaming.value) return
  speechError.value = ''
  if (!speechSupported.value) {
    speechError.value = speechUnsupportedReason.value || '当前环境不支持语音输入'
    message.warning(speechError.value, 5)
    return
  }
  toggleSpeech(input.value)
}

const composerHint = computed(() => {
  if (isStreaming.value) return streamingStatus.value || '运行中…'
  if (isSpeechBootstrapping.value) return '正在检测语音识别能力…'
  if (isSpeechPending.value) return '正在启动麦克风…'
  if (isSpeechListening.value) return '正在聆听… 再次点击麦克风结束 · Enter 手动发送'
  if (speechLocalModelStatus.value === 'downloading') return '本地语音模型下载中，完成后可离线识别'
  if (speechRecognitionMode.value === 'local') {
    return 'Enter 发送 · 麦克风语音输入（本地识别，无需 Google）'
  }
  if (speechRecognitionMode.value === 'cloud') {
    return 'Enter 发送 · 麦克风语音输入（云端识别，国内网络可能不可用）'
  }
  if (speechSupported.value) return 'Enter 发送 · 麦克风语音输入'
  if (speechUnsupportedReason.value) return speechUnsupportedReason.value
  return 'Enter 发送'
})

const scopeSessions = computed(() =>
  sessions.value
    .filter(item => item.knowledgeBaseId === selectedKbId.value)
    .sort((a, b) => b.updatedAt - a.updatedAt)
)

const selectedBase = computed(
  () => bases.value.find(item => item.id === selectedKbId.value) ?? null
)

const toolbarTitle = computed(() => activeSession.value?.title ?? SCENE_DEFAULT_TITLE)

const toolbarSubtitle = computed(() => {
  const count = sceneObjects.value.length
  const selected = selectedObject.value?.name
  const kb = selectedBase.value?.name
  const parts = [`${count} 个模型`]
  if (selected) parts.push(`选中：${selected}`)
  if (kb) parts.push(`知识库：${kb}`)
  else parts.push('未绑定知识库')
  return parts.join(' · ')
})

const composerPlaceholder = computed(() =>
  sceneObjects.value.length
    ? '例如：把选中的模型向右移 1 米 / 绕 Y 轴转 45 度'
    : '请先上传 GLB 模型，再向 Scene Agent 提问'
)

const exampleQuestions = computed(() =>
  selectedKbId.value ? SCENE_EXAMPLES_WITH_KB : SCENE_EXAMPLES_WITHOUT_KB
)

const kbOptions = computed(() => {
  const options = [{ label: '不绑定知识库', value: SCENE_KB_NONE }]
  for (const item of bases.value) {
    options.push({
      label: `${item.name}（${item.document_count}）`,
      value: item.id
    })
  }
  return options
})

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function handleNewSession() {
  createNewSession()
  sidebarOpen.value = false
}

function handleSwitchSession(sessionId: string) {
  switchSession(sessionId)
  sidebarOpen.value = false
}

function onKbChange() {
  ensureSessionForScope(selectedKbId.value)
}

async function onFileChange(event: Event) {
  const inputEl = event.target as HTMLInputElement
  const files = inputEl.files
  if (!files?.length) return
  for (const file of Array.from(files)) {
    await loadGlbFile(file)
  }
  inputEl.value = ''
}

function selectModel(id: string) {
  applyHighlight(id)
  focusObject(id)
}

function removeModel(id: string) {
  removeObject(id)
}

function explainSelected() {
  if (!selectedObject.value) return
  explainSelectedObject(selectedObject.value.name)
}

function applyExample(text: string) {
  input.value = text
}

onMounted(async () => {
  if (canvasHostRef.value) initScene(canvasHostRef.value)

  kbLoading.value = true
  try {
    bases.value = await fetchKnowledgeBases()
    syncSessionsWithKnowledgeBases(bases.value.map(item => item.id))
    ensureSessionForScope(selectedKbId.value)
  } catch (err) {
    kbLoadError.value = err instanceof Error ? err.message : '加载知识库失败'
    ensureSessionForScope(SCENE_KB_NONE)
  } finally {
    kbLoading.value = false
  }
})
</script>

<style scoped>
.scene-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.scene-app {
  flex: 1;
  min-height: 0;
  display: flex;
  position: relative;
}

.scene-app__backdrop {
  display: none;
}

.scene-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.scene-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-surface);
}

.scene-toolbar__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.scene-toolbar__titles {
  min-width: 0;
}

.scene-toolbar__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.scene-toolbar__subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scene-toolbar__menu {
  display: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-secondary);
}

.scene-toolbar__action {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 13px;
}

.scene-toolbar__action:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.scene-workspace {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
}

.scene-viewport {
  position: relative;
  min-width: 0;
  min-height: 0;
  background: #0f1117;
  border-right: 1px solid var(--border);
}

.scene-viewport :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

.scene-viewport__empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #94a3b8;
  pointer-events: none;
  text-align: center;
  padding: 20px;
}

.scene-viewport__hint {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.scene-chat {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.scene-upload {
  display: block;
  cursor: pointer;
}

.scene-upload input {
  display: none;
}

.scene-upload__label {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 14px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 13px;
  transition: border-color 0.15s, background 0.15s;
}

.scene-upload:hover .scene-upload__label {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.scene-upload__error {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--danger);
}

.scene-model-list {
  max-height: 160px;
}

.scene-alert {
  margin: 10px 12px 0;
  padding: 10px 12px;
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--radius-md);
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.scene-alert__retry {
  padding: 4px 10px;
  border: 1px solid rgba(220, 38, 38, 0.35);
  border-radius: 999px;
  background: var(--bg-surface);
  font-size: 12px;
}

.scene-retry-notice {
  margin: 10px 12px 0;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  border-radius: var(--radius-md);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
}

.scene-chat__messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 14px 12px;
}

.scene-welcome {
  text-align: center;
  padding: 12px 0 20px;
}

.scene-welcome__icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.scene-welcome__title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.scene-welcome__desc {
  margin: 0 0 14px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.scene-welcome__capabilities {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
  text-align: left;
}

.scene-capability {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
}

.scene-capability--disabled {
  opacity: 0.55;
}

.scene-capability__icon {
  font-size: 18px;
}

.scene-capability__title {
  margin: 0 0 2px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.scene-capability__desc {
  margin: 0;
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
}

.scene-welcome__hint {
  margin: 0 0 12px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-muted);
}

.scene-welcome__chips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scene-welcome__chip {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 12px;
  text-align: left;
}

.scene-message {
  margin-bottom: 14px;
}

.scene-message--user {
  display: flex;
  justify-content: flex-end;
}

.scene-message--user .scene-message__bubble {
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--accent), #6366f1);
  color: var(--text-inverse);
}

.scene-message__thinking {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.scene-message__thinking span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: scene-bounce 1.2s infinite ease-in-out;
}

.scene-message__thinking span:nth-child(2) {
  animation-delay: 0.15s;
}

.scene-message__thinking span:nth-child(3) {
  animation-delay: 0.3s;
}

.scene-message__actions {
  margin-top: 6px;
}

.scene-message__action {
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
}

.scene-composer {
  flex-shrink: 0;
  padding: 12px 14px 14px;
  border-top: 1px solid var(--border);
  background: var(--bg-surface);
}

.scene-composer__input {
  width: 100%;
  min-height: 56px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-input);
  color: var(--text-primary);
  resize: vertical;
  font: inherit;
  box-sizing: border-box;
}

.scene-composer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.scene-composer__hint {
  font-size: 11px;
  color: var(--text-muted);
}

.scene-composer__buttons {
  display: flex;
  gap: 8px;
}

.scene-composer__hint--live {
  color: var(--danger);
}

.scene-speech-error {
  margin-top: 6px;
  font-size: 12px;
  color: var(--danger);
}

.scene-composer__mic {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.scene-composer__mic:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.scene-composer__mic--active {
  border-color: var(--danger);
  background: var(--danger-soft);
  color: var(--danger);
  animation: scene-mic-pulse 1.2s ease-in-out infinite;
}

.scene-composer__mic:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@keyframes scene-mic-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.25);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(220, 38, 38, 0.08);
  }
}

.scene-composer__stop,
.scene-composer__send {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.scene-composer__stop {
  padding: 8px 12px;
  background: var(--bg-muted);
  color: var(--text-secondary);
  font-size: 12px;
}

.scene-composer__send {
  width: 36px;
  height: 36px;
  background: var(--accent);
  color: #fff;
}

.scene-composer__send:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@keyframes scene-bounce {
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

@media (max-width: 960px) {
  .scene-workspace {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(240px, 42vh) 1fr;
  }

  .scene-viewport {
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }
}

@media (max-width: 768px) {
  .scene-app__backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    z-index: 15;
  }

  .scene-sidebar.agent-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    box-shadow: var(--shadow-sidebar);
  }

  .scene-sidebar.agent-sidebar--open {
    transform: translateX(0);
  }

  .scene-toolbar__menu {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
