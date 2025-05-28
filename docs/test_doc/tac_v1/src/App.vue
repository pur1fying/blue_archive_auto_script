<template>
  <el-config-provider :locale="currentElementLocale">
    <div class="app-layout">
      <!-- Main Header (Stays at the top or within the main content area) -->
      <el-page-header :content="$t('appName')" class="app-header">
        <template #breadcrumb >
          <!-- 不提供内容，覆盖默认返回图标 -->
        </template>
         <template #extra>
            <div class="header-actions">
              <LanguageSwitcher />
              <ThemeSwitcher />
            </div>
          </template>
      </el-page-header>

      <el-row :gutter="20" class="main-content-wrapper">
        <!-- Main Content Area (Form Sections) -->
        <el-col :xs="24" :sm="24" :md="18" :lg="19" :xl="19" class="main-content-col">
          <div class="scrollable-content">
            <el-card class="section-card global-actions-card">
              <div class="action-buttons">
                <span style="font-size: 27px; line-height: 27px; font-weight: bold; margin-right: 20px; margin-top: 4px;">{{ $t('operation') }}</span>
                <el-button @click="triggerFileInput">{{ $t('importFile') }}</el-button>
                <el-button @click="formDataStore.loadExampleData()">{{ $t('loadWikiExample') }}</el-button>
                <el-button @click="formDataStore.resetForm()">{{ $t('resetForm') }}</el-button>
                <input type="file" ref="fileInput" @change="handleFileUpload" accept=".json" style="display: none;" />
                <!-- <el-button @click="appSettingsStore.toggleModuleJsonPanes()">
                  {{ appSettingsStore.showModuleJsonPanes ? 'Hide' : 'Show' }} {{ $t('toggleModuleJson') }}
                </el-button> -->
              </div>
            </el-card>

            <el-form label-position="top" ref="mainFormRef">
              <GeneralInfoForm id="general-info-section" />
              <FormationForm id="formation-section" />
              <BattleInfoForm id="battle-info-section" />
              <BossHealthOcrForm id="boss-health-ocr-section" />
              <YoloSettingForm id="yolo-setting-section" />
              <StatesManager id="states-section" />
              <ActionsManager id="actions-section" />
              <ConditionsManager id="conditions-section" />
            </el-form>

            <OutputDisplay id="output-section" />
          </div>
        </el-col>

        <!-- Right Navigation Sidebar -->
        <el-col :xs="0" :sm="0" :md="6" :lg="5" :xl="5" class="right-nav-col">
          <RightNavigationPanel :sections="navSections" @navigate="scrollToSection" />
        </el-col>
      </el-row>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElConfigProvider } from 'element-plus';
import enEp from 'element-plus/dist/locale/en.mjs' // Element Plus locales
import zhCnEp from 'element-plus/dist/locale/zh-cn.mjs'

import { useAppSettingsStore } from './store/appSettings';
import { useFormDataStore } from './store/formData';

// Import section components
import GeneralInfoForm from './components/sections/GeneralInfoForm.vue';
import FormationForm from './components/sections/FormationForm.vue';
import BattleInfoForm from './components/sections/BattleInfoForm.vue';
import BossHealthOcrForm from './components/sections/BossHealthOcrForm.vue';
import YoloSettingForm from './components/sections/YoloSettingForm.vue';
import StatesManager from './components/sections/StatesManager.vue';
import ActionsManager from './components/sections/ActionsManager.vue';
import ConditionsManager from './components/sections/ConditionsManager.vue';

// Import UI components
import ThemeSwitcher from './components/ui/ThemeSwitcher.vue';
import LanguageSwitcher from './components/ui/LanguageSwitcher.vue';
import OutputDisplay from './components/ui/OutputDisplay.vue';

// Import navigation components
import RightNavigationPanel from './components/ui/RightNavigationPanel.vue'; // New component

// Define sections for navigation
const navSections = ref([
  { id: 'general-info-section', titleKey: 'generalInfo.title', icon: 'InfoFilled' }, // Using Element Plus icon names
  { id: 'formation-section', titleKey: 'formation.title', icon: 'UserFilled' },
  { id: 'battle-info-section', titleKey: 'battleInfo.title', icon: 'Histogram' },
  { id: 'boss-health-ocr-section', titleKey: 'bossHealthOcr.title', icon: 'View' },
  { id: 'yolo-setting-section', titleKey: 'yolo.title', icon: 'Aim' },
  { id: 'states-section', titleKey: 'states.title', icon: 'Switch' },
  { id: 'actions-section', titleKey: 'actions.title', icon: 'Promotion' },
  { id: 'conditions-section', titleKey: 'conditions.title', icon: 'Condition' }, // Custom or find suitable
  { id: 'output-section', titleKey: 'generatedJson', icon: 'Document' },
]);



const { t, locale } = useI18n();
const appSettingsStore = useAppSettingsStore();
const formDataStore = useFormDataStore();

const fileInput = ref(null);

const currentElementLocale = computed(() => {
  return appSettingsStore.language === 'zh' ? zhCnEp : enEp;
});

// Watch for store language changes to update i18n instance
watch(() => appSettingsStore.language, (newLang) => {
  locale.value = newLang;
});

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileUpload = (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  if (file.type !== 'application/json') {
    ElMessage.error('Invalid file type. Please upload a JSON file.');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const content = JSON.parse(e.target.result);
      formDataStore.loadDataFromFile(content);
    } catch (error) {
      ElMessage.error('Failed to parse JSON file: ' + error.message);
      console.error("File parsing error:", error);
    }
  };
  reader.onerror = (error) => {
      ElMessage.error('Failed to read file.');
      console.error("File reading error:", error);
  };
  reader.readAsText(file);
  event.target.value = ''; // Reset file input
};

const scrollToSection = (sectionId) => {
  const element = document.getElementById(sectionId);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};
</script>

<style scoped>
/* App.vue specific styles if any */

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Make app take full viewport height */
}

.app-header {
  padding: 10px 20px;
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0; /* Prevent header from shrinking */
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
}

.main-content-wrapper {
  flex-grow: 1; /* Allow this row to take remaining space */
  overflow: hidden; /* Prevent page scrollbars, scrolling is in .scrollable-content */
  padding: 0 20px 20px 20px; /* Add some padding around */
  margin: 0 !important;
}

.main-content-col {
  height: 100%; /* Make column take full height of its row */
}

.scrollable-content {
  height: 100%;
  overflow-y: auto; /* Enable vertical scrollbar for content */
  padding-right: 15px; /* Space for scrollbar */
  padding-top: 20px;
}

.right-nav-col {
  height: 100%;
  padding-top: 20px; /* Align with top of first card potentially */
}



</style>