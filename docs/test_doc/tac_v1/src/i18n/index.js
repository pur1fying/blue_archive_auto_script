import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'
import ja from './locales/ja.json'
import ko from './locales/ko.json'
import { useAppSettingsStore } from '@/store/appSettings' // Adjust path if needed

const messages = {
  en,
  zh,
  ja,
  ko
}

// Function to get initial locale, possibly from appSettings store
function getInitialLocale() {
  const settingsStore = useAppSettingsStore(); // Call it outside setup if Pinia is already initialized
  return settingsStore.language || 'en';
}


const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: 'en', // Default, will be updated by appSettings store
  fallbackLocale: 'en',
  messages,
})

export default i18n