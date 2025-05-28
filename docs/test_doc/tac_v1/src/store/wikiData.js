import { defineStore } from 'pinia'
import { reactive } from 'vue'
import wikiContent from '@/i18n/wiki.json' // 这里 @ 代表 src
// Define initial wiki texts here or load them from a static JSON
const initialWikiContent = wikiContent

export const useWikiDataStore = defineStore('wikiData', () => {
  const wikiContent = reactive(initialWikiContent)

  function getWikiText(moduleKey, lang) {
    return wikiContent[lang][moduleKey] || "No wiki content for this module."
  }

  function updateWikiText(moduleKey, newText) {
    if (wikiContent.hasOwnProperty(moduleKey)) {
      wikiContent[moduleKey] = newText
      localStorage.setItem('wikiContent', JSON.stringify(wikiContent)) // Persist changes
    }
  }

  return {
    wikiContent, // mainly for inspection or full reset
    getWikiText,
    updateWikiText,
  }
})