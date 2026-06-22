import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/chat/index.vue'),
    meta: { title: 'AI Chat' }
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/knowledge/index.vue'),
    meta: { title: '知识库管理' }
  },
  {
    path: '/rag-chat',
    name: 'RagChat',
    component: () => import('@/views/rag-chat/index.vue'),
    meta: { title: '知识库问答' }
  },
  {
    path: '/agent-chat',
    name: 'AgentChat',
    component: () => import('@/views/agent-chat/index.vue'),
    meta: { title: '工具 Agent' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.afterEach(to => {
  const title = (to.meta.title as string | undefined) ?? import.meta.env.VITE_APP_TITLE
  document.title = title
})

export default router
