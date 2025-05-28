import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css' // Import dark theme CSS vars
import App from './App.vue'
import pinia from './store'
import i18n from './i18n'
import { useAppSettingsStore } from './store/appSettings' // For setting initial i18n locale

import './assets/main.css' // Your global styles

const app = createApp(App)

app.use(pinia) // Use Pinia first so stores are available

// Set i18n locale from store after Pinia is initialized
const appSettingsStore = useAppSettingsStore()
if (i18n.global.locale.value !== appSettingsStore.language) {
  i18n.global.locale.value = appSettingsStore.language
}


app.use(ElementPlus)
app.use(i18n)

app.mount('#app')