import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type Theme = 'light' | 'dark'

export const useAppStore = defineStore('app', () => {
  // State
  const sidebarCollapsed = ref(false)
  const theme = ref<Theme>('light')
  const loading = ref(false)
  const pageTitle = ref('')

  // Getters
  const isDark = computed(() => theme.value === 'dark')

  // Actions
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed
  }

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    updateDocumentClass()
  }

  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    updateDocumentClass()
  }

  const updateDocumentClass = () => {
    if (theme.value === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const setPageTitle = (title: string) => {
    pageTitle.value = title
    document.title = title ? `${title} - TrailSnap` : 'TrailSnap'
  }

  // Initialize
  const init = () => {
    updateDocumentClass()
  }

  return {
    sidebarCollapsed,
    theme,
    loading,
    pageTitle,
    isDark,
    toggleSidebar,
    setSidebarCollapsed,
    toggleTheme,
    setTheme,
    setLoading,
    setPageTitle,
    init
  }
})
