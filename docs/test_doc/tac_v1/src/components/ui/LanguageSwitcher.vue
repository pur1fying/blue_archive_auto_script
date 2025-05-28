<template>
    <el-dropdown @command="handleLanguageChange">
      <el-button>
        {{ currentLanguageName }} <el-icon class="el-icon--right"><arrow-down /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="en">English</el-dropdown-item>
          <el-dropdown-item command="zh">中文</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </template>
  
  <script setup>
  import { computed } from 'vue';
  import { useAppSettingsStore } from '@/store/appSettings';
  import { ArrowDown } from '@element-plus/icons-vue';
  
  
  const appSettings = useAppSettingsStore();
  
  const currentLanguageName = computed(() => {
    return appSettings.language === 'zh' ? '中文' : 'English';
  });
  
  const handleLanguageChange = (lang) => {
    appSettings.setLanguage(lang);
    // The i18n instance locale is updated via a watcher in App.vue or main.js
  };
  </script>