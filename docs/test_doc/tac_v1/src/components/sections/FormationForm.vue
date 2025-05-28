<template>
    <el-card class="section-card">
      <template #header><span>{{ $t('formation.title') }}</span></template>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('formation.frontChars')">
            <el-input v-model="formDataStore.formation_front_str" />
            <!-- Assuming formation_front_str is a computed in formDataStore -->
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('formation.backChars')">
            <el-input v-model="formDataStore.formation_back_str" />
          </el-form-item>
        </el-col>
        <!-- ... other formation fields ... -->
        <el-col :span="8">
            <el-form-item :label="$t('formation.slotCount')">
                <el-input-number v-model="formDataStore.formData.formation.slot_count" :min="1" :max="6"></el-input-number>
            </el-form-item>
        </el-col>
        <el-col :span="16">
            <el-form-item :label="$t('formation.allAppearedSkills')">
                <el-input v-model="formDataStore.formation_all_appeared_skills_str"></el-input>
            </el-form-item>
        </el-col>
        <!-- ... etc. -->
      </el-row>
  
      <!-- Per-module JSON Pane -->
      <JsonOutputPane :module-data="formDataStore.formData.formation" :title="$t('formation.jsonTitle')" />
  
      <!-- Wiki Panel -->
      <WikiPanel module-key="formation" :module-title="$t('formation.title')" />
    </el-card>
  </template>
  
  <script setup>
  import { useFormDataStore } from '@/store/formData';
  import { useI18n } from 'vue-i18n';
  import JsonOutputPane from '../ui/JsonOutputPane.vue';
  import WikiPanel from '../ui/WikiPanel.vue';
  
  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  
  // If you need component-specific computed properties or methods, define them here.
  // For example, if formation_front_str was managed locally:
  // const formation_front_str = computed({
  //   get: () => formDataStore.formData.formation.front.join(', '),
  //   set: (val) => { formDataStore.updateFormationArray('front', val); } // You'd need an action in store
  // });
  // But it's generally better to keep such computed props in the store if they directly map to store state.
  </script>