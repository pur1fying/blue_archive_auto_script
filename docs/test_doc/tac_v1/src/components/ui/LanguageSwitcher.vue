<template>
  <el-dropdown @command="handleLanguageChange">
    <el-button>
      {{ currentLanguageName }} 
      <el-icon class="el-icon--right"><arrow-down /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="en">English</el-dropdown-item>
        <el-dropdown-item command="zh">中文</el-dropdown-item>
        <el-dropdown-item command="ja">日本語</el-dropdown-item>
        <el-dropdown-item command="ko">한국어</el-dropdown-item>
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
  switch (appSettings.language) {
    case 'zh':
      return '中文';
    case 'ja':
      return '日本語';
    case 'ko':
      return '한국어';
    case 'en':
    default:
      return 'English';
  }
});

const handleLanguageChange = (lang) => {
  appSettings.setLanguage(lang);
  // i18n.locale is updated elsewhere (e.g., via a watcher)
};
</script>
