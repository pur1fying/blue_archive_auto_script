<template>
    <el-card class="section-card">
      <!-- <template #header><span>{{ $t('bossHealthOcr.title') }}</span></template> -->
      <template #header>
        <div class="card-header-wrapper">
          <span>{{ $t('bossHealthOcr.title') }}</span>
          <el-button
            type="primary"
            link
            @click="showJson = !showJson"
            :icon="showJson ? Hide : View"
            style="float: right;"
          >
            {{ showJson ? $t('hideJson') : $t('showJson') }}
          </el-button>
        </div>
      </template>
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
      <JsonOutputPane v-if="showJson" :module-data="formDataStore.formData.BossHealth" :title="$t('bossHealthOcr.jsonTitle')" />
      <WikiPanel module-key="bossHealthOcr" :module-title="$t('bossHealthOcr.title')" />
    </el-card>
  </template>
  
  <script setup>
  import { View, Hide } from '@element-plus/icons-vue'; // Import icons
  import { ref } from 'vue'; // Add ref
  import { useFormDataStore } from '@/store/formData';
  import { useI18n } from 'vue-i18n';
  import JsonOutputPane from '../ui/JsonOutputPane.vue';
  import WikiPanel from '../ui/WikiPanel.vue';
  const showJson = ref(false); // Local state for this module's JSON pane
  
  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  </script>