<template>
    <el-card class="section-card">
      <template #header><span>{{ $t('yolo.title') }}</span></template>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('yolo.model')">
            <el-select v-model="formDataStore.formData.yolo_setting.model" :placeholder="$t('yolo.selectModel')" class="full-width-select">
              <el-option :label="$t('yolo.modelFp32')" value="best.onnx"></el-option>
              <el-option :label="$t('yolo.modelFp16')" value="best_fp16.onnx"></el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('yolo.updateInterval')">
            <el-input-number v-model="formDataStore.formData.yolo_setting.update_interval" :min="0"></el-input-number>
          </el-form-item>
        </el-col>
      </el-row>
      <JsonOutputPane :module-data="formDataStore.formData.yolo_setting" :title="$t('yolo.jsonTitle')" />
      <WikiPanel module-key="yolo" :module-title="$t('yolo.title')" />
    </el-card>
  </template>
  
  <script setup>
  import { useFormDataStore } from '@/store/formData';
  import { useI18n } from 'vue-i18n';
  import JsonOutputPane from '../ui/JsonOutputPane.vue';
  import WikiPanel from '../ui/WikiPanel.vue';
  
  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  </script>