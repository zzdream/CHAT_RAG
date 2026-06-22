<template>
  <nav class="app-nav">
    <RouterLink class="app-nav__brand" to="/">LLM</RouterLink>
    <div class="app-nav__links">
      <RouterLink class="app-nav__link" to="/chat">自由对话</RouterLink>
      <RouterLink class="app-nav__link" to="/knowledge">知识库</RouterLink>
      <RouterLink class="app-nav__link" to="/rag-chat">知识库问答</RouterLink>
      <RouterLink class="app-nav__link" to="/agent-chat">工具 Agent</RouterLink>
    </div>
    <button
      class="app-nav__theme"
      type="button"
      :title="theme === 'dark' ? '浅色模式' : '深色模式'"
      @click="toggleTheme"
    >
      <IconSun v-if="theme === 'dark'" :size="16" />
      <IconMoon v-else :size="16" />
    </button>
  </nav>
</template>

<script setup lang="ts">
import IconMoon from '@/components/icons/icon-moon.vue'
import IconSun from '@/components/icons/icon-sun.vue'
import { useAppStore } from '@/store/modules/app'

const appStore = useAppStore()
const { theme } = storeToRefs(appStore)
const { toggleTheme } = appStore
</script>

<style scoped>
.app-nav {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
}

.app-nav__brand {
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
}

.app-nav__links {
  display: flex;
  gap: 8px;
  flex: 1;
}

.app-nav__link {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
}

.app-nav__link.router-link-active {
  background: var(--accent-soft);
  color: var(--accent);
}

.app-nav__theme {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-secondary);
}
</style>
