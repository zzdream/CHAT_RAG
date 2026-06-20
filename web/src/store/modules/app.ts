import { defineStore } from 'pinia'

export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'study-llm-theme'

function getInitialTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'light'

  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') return saved

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme: ThemeMode) {
  document.documentElement.setAttribute('data-theme', theme)
}

export const useAppStore = defineStore('app', () => {
  const appTitle = ref(import.meta.env.VITE_APP_TITLE)
  const theme = ref<ThemeMode>(getInitialTheme())

  applyTheme(theme.value)

  function setAppTitle(title: string) {
    appTitle.value = title
  }

  function setTheme(mode: ThemeMode) {
    theme.value = mode
    localStorage.setItem(STORAGE_KEY, mode)
    applyTheme(mode)
  }

  function toggleTheme() {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  return {
    appTitle,
    theme,
    setAppTitle,
    setTheme,
    toggleTheme
  }
})
