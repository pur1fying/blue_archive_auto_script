<template>
    <el-card class="section-card">
      <template #header><span>{{ $t('generalInfo.title') }}</span></template>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('generalInfo.axisName')">
            <el-input v-model="formDataStore.formData.name" :placeholder="$t('generalInfo.axisNamePlaceholder')"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('generalInfo.startState')">
            <el-select v-model="formDataStore.formData.start_state" :placeholder="$t('generalInfo.selectStartState')" filterable clearable class="full-width-select">
              <el-option v-for="stateName in formDataStore.stateNames" :key="stateName" :label="stateName" :value="stateName"></el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <JsonOutputPane :module-data="{ name: formDataStore.formData.name, start_state: formDataStore.formData.start_state }" :title="$t('generalInfo.jsonTitle')" />
      <WikiPanel module-key="general" :module-title="$t('generalInfo.title')" />
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