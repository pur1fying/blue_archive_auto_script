<template>
    <el-card class="section-card">
      <template #header><span>{{ $t('bossHealthOcr.title') }}</span></template>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('bossHealthOcr.currentRegion')">
            <el-input v-model="formDataStore.bosshealth_current_ocr_region_str" :placeholder="$t('bossHealthOcr.regionPlaceholder')"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('bossHealthOcr.maxRegion')">
            <el-input v-model="formDataStore.bosshealth_max_ocr_region_str" :placeholder="$t('bossHealthOcr.regionPlaceholder')"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('bossHealthOcr.combinedRegion')">
            <el-input v-model="formDataStore.bosshealth_ocr_region_str" :placeholder="$t('bossHealthOcr.regionPlaceholder')"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('bossHealthOcr.modelName')">
            <el-input v-model="formDataStore.formData.BossHealth.ocr_model_name" :placeholder="$t('bossHealthOcr.modelNamePlaceholder')"></el-input>
          </el-form-item>
        </el-col>
      </el-row>
      <JsonOutputPane :module-data="formDataStore.formData.BossHealth" :title="$t('bossHealthOcr.jsonTitle')" />
      <WikiPanel module-key="bossHealthOcr" :module-title="$t('bossHealthOcr.title')" />
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