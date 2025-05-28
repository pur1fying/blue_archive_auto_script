<template>
  <!-- The v-if is now handled by the PARENT component -->
  <div class="module-json-pane">
    <el-divider content-position="left">{{ title || 'Module JSON' }}</el-divider>
    <el-input
      type="textarea"
      :value="jsonDataString"
      :autosize="{ minRows: 3, maxRows: 10 }"
      readonly
    />
  </div>
</template>
  
<script setup>
  import { computed } from 'vue';
  // import { useAppSettingsStore } from '@/store/appSettings';
  
  const props = defineProps({
    moduleData: {
      type: Object,
      required: true,
    },
    title: String,
  });
  
  // const appSettings = useAppSettingsStore();
  
  const jsonDataString = computed(() => {
    try {
      return JSON.stringify(props.moduleData, null, 2);
    } catch (e) {
      console.error("Error stringifying module data for JSON pane:", e);
      return "{ \"error\": \"Could not display JSON\" }";
    }
  });
  </script>
  
  <style scoped>
  .module-json-pane {
    margin-top: 15px;
    margin-bottom: 15px;
    border: 1px dashed var(--el-border-color);
    padding: 10px;
    background-color: var(--el-color-info-light-9);
  }
  .dark .module-json-pane {
    background-color: var(--el-color-black);
    border-color: var(--el-border-color-darker);
  }
  </style>