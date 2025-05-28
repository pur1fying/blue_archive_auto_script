import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useAppSettingsStore = defineStore('appSettings', () => {
  const theme = ref(localStorage.getItem('theme') || 'light') // 'light' or 'dark'
  const language = ref(localStorage.getItem('language') || 'en') // 'en', 'zh', etc.
  // const showModuleJsonPanes = ref(false)

  watch(theme, (newTheme) => {
    localStorage.setItem('theme', newTheme)
    document.documentElement.className = newTheme // For Element Plus dark mode
  })

  watch(language, (newLang) => {
    localStorage.setItem('language', newLang)
    // i18n instance will be updated separately
  })

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  function setLanguage(lang) {
    language.value = lang
  }

  // function toggleModuleJsonPanes() {
  //   showModuleJsonPanes.value = !showModuleJsonPanes.value
  // }

  // Initialize theme class on load
  document.documentElement.className = theme.value

  return {
    theme,
    language,
    // showModuleJsonPanes,
    toggleTheme,
    setLanguage,
    // toggleModuleJsonPanes,
  }
})