<template>
    <el-button @click="appSettings.toggleTheme()" :icon="themeIcon" circle id="theme-switcher-button">
      <!-- {{ $t('toggleTheme') }} (Icon is better for header) -->
    </el-button>
  </template>
  
  <script setup>
  import { computed } from 'vue';
  import { useAppSettingsStore } from '@/store/appSettings';
  import { Sunny, Moon } from '@element-plus/icons-vue'; // Import icons
  
  const appSettings = useAppSettingsStore();
  const themeIcon = computed(() => (appSettings.theme === 'light' ? Moon : Sunny));
  </script>

<style>
#theme-switcher-button .el-icon {
  margin-left: 5px;
}
</style>