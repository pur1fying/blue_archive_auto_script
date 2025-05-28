<template>
    <el-card class="section-card">
      <template #header>
        <span>{{ $t('generatedJson') || 'Generated JSON' }}</span>
      </template>
      <div class="action-buttons">
        <el-button type="success" @click="copyJson">{{ $t('generateAndCopy') }}</el-button>
      </div>
      <el-input
        type="textarea"
        :value="formDataStore.generatedJsonString"
        :autosize="{ minRows: 20 }"
        readonly
        class="json-output"
      />
    </el-card>
  </template>
  
  <script setup>
  import { useFormDataStore } from '@/store/formData';
  import { ElMessage } from 'element-plus';
  import { useI18n } from 'vue-i18n';
  
  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  
  const copyJson = () => {
    navigator.clipboard.writeText(formDataStore.generatedJsonString).then(() => {
      ElMessage.success(t('jsonCopiedSuccess') || 'JSON copied to clipboard!');
    }).catch(err => {
      ElMessage.error(t('jsonCopiedError') || 'Failed to copy JSON.');
      console.error('Could not copy text: ', err);
    });
  };
  </script>
  
  <style scoped>
  .json-output {
    width: 100%;
    font-family: monospace;
  }
  </style>