import { defineStore } from 'pinia'
import { reactive } from 'vue'

// Define initial wiki texts here or load them from a static JSON
const initialWikiContent = {
  general: "Wiki for General Info section. Describes 'Axis Name' and 'Start State'.",
  formation: "Wiki for Formation. Explains front, back, slot count, skills.",
  battleInfo: "Wiki for Battle Info. How to configure boss health per phase.",
  bossHealthOcr: "Wiki for Boss Health OCR settings.",
  yolo: "Wiki for YOLO object detection settings.",
  states: "Wiki for States. How to define states, actions, transitions.",
  actions: "Wiki for Actions. Define sequences of operations.",
  conditions: "Wiki for Conditions. Define criteria for state transitions.",
}

export const useWikiDataStore = defineStore('wikiData', () => {
  const wikiContent = reactive(JSON.parse(localStorage.getItem('wikiContent')) || initialWikiContent)

  function getWikiText(moduleKey) {
    return wikiContent[moduleKey] || "No wiki content for this module."
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