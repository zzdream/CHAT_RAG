<template>
  <a-config-provider :theme="antdTheme">
    <div class="knowledge-page">
      <AppNav />

      <div class="knowledge-page__body">
        <aside class="knowledge-sidebar">
          <div class="knowledge-sidebar__brand">
            <div class="knowledge-sidebar__logo">K</div>
            <div class="knowledge-sidebar__brand-text">
              <p class="knowledge-sidebar__brand-name">知识库</p>
              <p class="knowledge-sidebar__brand-tagline">RAG · 文档检索</p>
            </div>
          </div>

          <button class="knowledge-sidebar__new" type="button" @click="openCreateModal">
            <span class="knowledge-sidebar__new-icon">+</span>
            新建知识库
          </button>

          <a-spin :spinning="loading">
            <ul v-if="bases.length" class="knowledge-sidebar__list">
              <li
                v-for="item in bases"
                :key="item.id"
                class="knowledge-sidebar__item"
                :class="{ 'knowledge-sidebar__item--active': item.id === activeBaseId }"
              >
                <button type="button" class="knowledge-sidebar__select" @click="activeBaseId = item.id">
                  <span class="knowledge-sidebar__name">{{ item.name }}</span>
                  <span class="knowledge-sidebar__meta">{{ item.document_count }} 个文档</span>
                </button>
                <a-popconfirm
                  title="确定删除此知识库？"
                  description="将同时删除所有文档与向量索引。"
                  ok-text="删除"
                  cancel-text="取消"
                  ok-type="danger"
                  @confirm="handleDeleteBase(item.id)"
                >
                  <button type="button" class="knowledge-sidebar__delete" title="删除知识库" @click.stop>
                    ×
                  </button>
                </a-popconfirm>
              </li>
            </ul>
            <div v-else class="knowledge-sidebar__empty">
              <p>创建后将显示在这里</p>
            </div>
          </a-spin>
        </aside>

        <section class="knowledge-main">
          <!-- 无知识库：统一欢迎页 -->
          <div v-if="!bases.length && !loading" class="knowledge-welcome">
            <div class="knowledge-welcome__icon">📚</div>
            <h1 class="knowledge-welcome__title">创建你的第一个知识库</h1>
            <p class="knowledge-welcome__desc">
              上传 TXT / Markdown 文档，系统会自动分块、向量化，供「知识库问答」检索使用。
            </p>
            <ul class="knowledge-welcome__steps">
              <li><span>1</span> 创建知识库</li>
              <li><span>2</span> 上传文档</li>
              <li><span>3</span> 前往知识库问答</li>
            </ul>
            <a-button type="primary" size="large" @click="openCreateModal">创建知识库</a-button>
          </div>

          <template v-else-if="activeBase">
            <header class="knowledge-main__header">
              <div class="knowledge-main__intro">
                <h1>{{ activeBase.name }}</h1>
                <p v-if="activeBase.description">{{ activeBase.description }}</p>
                <p v-else class="knowledge-main__hint">支持 .txt / .md / .markdown，单文件最大 5MB</p>
              </div>
              <a-upload
                :show-upload-list="false"
                :before-upload="handleBeforeUpload"
                :disabled="uploading"
                accept=".txt,.md,.markdown"
              >
                <a-button type="primary" :loading="uploading">上传文档</a-button>
              </a-upload>
            </header>

            <a-alert v-if="error" type="error" :message="error" show-icon class="knowledge-main__alert" />

            <div class="knowledge-main__panel">
              <a-table
                v-if="documents.length || loading"
                :columns="columns"
                :data-source="documents"
                :loading="loading"
                row-key="id"
                :pagination="false"
                size="middle"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'status'">
                    <a-tooltip
                      v-if="record.status === 'failed' && record.error_message"
                      :title="record.error_message"
                    >
                      <a-tag :color="statusColor(record.status)">
                        {{ DOCUMENT_STATUS_LABEL[record.status] ?? record.status }}
                      </a-tag>
                    </a-tooltip>
                    <a-tag v-else :color="statusColor(record.status)">
                      {{ DOCUMENT_STATUS_LABEL[record.status] ?? record.status }}
                    </a-tag>
                  </template>
                  <template v-else-if="column.key === 'size'">
                    {{ formatSize(record.file_size) }}
                  </template>
                  <template v-else-if="column.key === 'actions'">
                    <a-popconfirm
                      title="确定删除此文档？"
                      ok-text="删除"
                      cancel-text="取消"
                      ok-type="danger"
                      @confirm="handleDeleteDoc(record.id)"
                    >
                      <a-button type="link" danger size="small">删除</a-button>
                    </a-popconfirm>
                  </template>
                </template>
              </a-table>

              <div v-else class="knowledge-docs-empty">
                <div class="knowledge-docs-empty__icon">📄</div>
                <p class="knowledge-docs-empty__title">还没有文档</p>
                <p class="knowledge-docs-empty__desc">点击上方「上传文档」，开始构建检索资料</p>
                <a-upload
                  :show-upload-list="false"
                  :before-upload="handleBeforeUpload"
                  :disabled="uploading"
                  accept=".txt,.md,.markdown"
                >
                  <a-button type="primary" ghost :loading="uploading">上传第一个文档</a-button>
                </a-upload>
              </div>
            </div>
          </template>
        </section>
      </div>

      <a-modal
        v-model:open="createModalOpen"
        title="新建知识库"
        ok-text="创建"
        cancel-text="取消"
        :confirm-loading="creating"
        @ok="handleCreateBase"
      >
        <a-form layout="vertical">
          <a-form-item label="名称" required>
            <a-input v-model:value="createForm.name" placeholder="例如：产品文档" />
          </a-form-item>
          <a-form-item label="描述">
            <a-textarea v-model:value="createForm.description" :rows="3" placeholder="可选" />
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import type { UploadProps } from 'ant-design-vue'
import { message, theme as antTheme } from 'ant-design-vue'
import AppNav from '@/components/app-nav.vue'
import { DOCUMENT_STATUS_LABEL, RAG_ALLOWED_EXTENSIONS } from '@/constants/rag'
import { useKnowledge } from '@/hooks/use-knowledge'
import { useAppStore } from '@/store/modules/app'

const appStore = useAppStore()
const { theme } = storeToRefs(appStore)

const antdTheme = computed(() => ({
  algorithm: theme.value === 'dark' ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm
}))

const {
  bases,
  documents,
  activeBaseId,
  activeBase,
  loading,
  uploading,
  error,
  loadBases,
  createBase,
  removeBase,
  uploadDoc,
  removeDoc
} = useKnowledge()

const createModalOpen = ref(false)
const creating = ref(false)
const createForm = reactive({ name: '', description: '' })

const columns = [
  { title: '文件名', dataIndex: 'filename', key: 'filename' },
  { title: '状态', key: 'status', width: 100 },
  { title: '分块数', dataIndex: 'chunk_count', key: 'chunk_count', width: 90 },
  { title: '大小', key: 'size', width: 100 },
  { title: '操作', key: 'actions', width: 90 }
]

onMounted(() => {
  loadBases()
})

function openCreateModal() {
  createForm.name = ''
  createForm.description = ''
  createModalOpen.value = true
}

async function handleCreateBase() {
  const name = createForm.name.trim()
  if (!name) {
    message.error('请输入知识库名称')
    return
  }

  creating.value = true
  try {
    await createBase(name, createForm.description.trim())
    createModalOpen.value = false
    message.success('创建成功')
  } catch (err) {
    message.error(err instanceof Error ? err.message : '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleDeleteBase(id: string) {
  try {
    await removeBase(id)
    message.success('已删除')
  } catch (err) {
    message.error(err instanceof Error ? err.message : '删除失败')
  }
}

async function handleDeleteDoc(id: string) {
  try {
    await removeDoc(id)
    message.success('已删除')
  } catch (err) {
    message.error(err instanceof Error ? err.message : '删除失败')
  }
}

const handleBeforeUpload: UploadProps['beforeUpload'] = async file => {
  const ext = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`
  if (!RAG_ALLOWED_EXTENSIONS.includes(ext)) {
    message.error('仅支持 .txt / .md / .markdown')
    return false
  }

  try {
    const doc = await uploadDoc(file as File)
    if (doc.status === 'indexed') {
      message.success('上传完成')
    } else if (doc.status === 'failed') {
      message.error(doc.error_message || '索引失败')
    }
  } catch (err) {
    message.error(err instanceof Error ? err.message : '上传失败')
  }

  return false
}

function statusColor(status: string) {
  if (status === 'indexed') return 'success'
  if (status === 'failed') return 'error'
  return 'processing'
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
.knowledge-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
}

.knowledge-page__body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
}

/* ── 侧边栏 ── */
.knowledge-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-right: 1px solid var(--border);
  background: var(--bg-sidebar);
  padding: 0 16px 16px;
  overflow: auto;
  box-shadow: var(--shadow-sidebar);
}

.knowledge-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0 12px;
}

.knowledge-sidebar__logo {
  flex-shrink: 0;
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

.knowledge-sidebar__brand-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.knowledge-sidebar__brand-name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-primary);
}

.knowledge-sidebar__brand-tagline {
  margin: 2px 0 0;
  font-size: 12px;
  line-height: 1.3;
  color: var(--text-muted);
}

.knowledge-sidebar__new {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  margin-bottom: 12px;
  padding: 10px 14px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-primary);
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.knowledge-sidebar__new:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
  box-shadow: var(--shadow-sm);
}

.knowledge-sidebar__new-icon {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 16px;
  line-height: 1;
}

.knowledge-sidebar__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.knowledge-sidebar__item {
  display: flex;
  align-items: stretch;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-surface);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.knowledge-sidebar__item--active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent-ring);
}

.knowledge-sidebar__select {
  flex: 1;
  border: 0;
  background: transparent;
  text-align: left;
  padding: 10px 12px;
  cursor: pointer;
}

.knowledge-sidebar__select:hover {
  background: var(--bg-muted);
}

.knowledge-sidebar__name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.knowledge-sidebar__meta {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.knowledge-sidebar__delete {
  width: 36px;
  border: 0;
  border-left: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  transition: color 0.2s ease, background 0.2s ease;
}

.knowledge-sidebar__delete:hover {
  color: var(--danger);
  background: var(--danger-soft);
}

.knowledge-sidebar__empty {
  margin-top: 8px;
  padding: 20px 12px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-md);
  text-align: center;
}

.knowledge-sidebar__empty p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}

/* ── 主区域 ── */
.knowledge-main {
  padding: 24px 28px;
  overflow: auto;
}

.knowledge-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100% - 48px);
  max-width: 480px;
  margin: 0 auto;
  text-align: center;
}

.knowledge-welcome__icon {
  font-size: 48px;
  line-height: 1;
  margin-bottom: 16px;
}

.knowledge-welcome__title {
  margin: 0 0 10px;
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
}

.knowledge-welcome__desc {
  margin: 0 0 24px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.knowledge-welcome__steps {
  list-style: none;
  margin: 0 0 28px;
  padding: 0;
  display: grid;
  gap: 10px;
  width: 100%;
  text-align: left;
}

.knowledge-welcome__steps li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  font-size: 14px;
  color: var(--text-secondary);
}

.knowledge-welcome__steps span {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.knowledge-main__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.knowledge-main__intro h1 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 700;
}

.knowledge-main__intro p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.knowledge-main__hint {
  font-size: 13px;
  color: var(--text-muted) !important;
}

.knowledge-main__alert {
  margin-bottom: 16px;
}

.knowledge-main__panel {
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.knowledge-main__panel :deep(.ant-table) {
  background: transparent;
}

.knowledge-main__panel :deep(.ant-table-thead > tr > th) {
  background: var(--bg-muted);
  font-weight: 600;
}

.knowledge-docs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 56px 24px;
  text-align: center;
}

.knowledge-docs-empty__icon {
  font-size: 40px;
  margin-bottom: 12px;
  opacity: 0.9;
}

.knowledge-docs-empty__title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.knowledge-docs-empty__desc {
  margin: 0 0 20px;
  font-size: 13px;
  color: var(--text-muted);
}

@media (max-width: 900px) {
  .knowledge-page__body {
    grid-template-columns: 1fr;
  }

  .knowledge-sidebar {
    border-right: 0;
    border-bottom: 1px solid var(--border);
    max-height: 280px;
  }

  .knowledge-welcome {
    min-height: auto;
    padding: 32px 0;
  }
}
</style>
