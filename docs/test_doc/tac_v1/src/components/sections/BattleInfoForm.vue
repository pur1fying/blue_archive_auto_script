<template>
    <el-card class="section-card">
      <template #header><span>{{ $t('battleInfo.title') }}</span></template>
      <div v-for="(phase, index) in formDataStore.formData.battle.boss_max_health_phases" :key="index" class="dynamic-list-item">
        <el-row :gutter="10" align="middle">
          <el-col :span="10">
            <el-form-item :label="`${$t('battleInfo.phase')} ${index + 1} ${$t('battleInfo.name')}`">
              <el-input v-model="phase.name" :placeholder="$t('battleInfo.phaseNamePlaceholder')"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item :label="`${$t('battleInfo.phase')} ${index + 1} ${$t('battleInfo.health')}`">
              <el-input-number v-model="phase.health" :min="0" controls-position="right"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-button type="danger" @click="formDataStore.removeBattlePhase(index)" plain size="small">{{ $t('remove') }}</el-button>
          </el-col>
        </el-row>
      </div>
      <el-button @click="formDataStore.addBattlePhase()" type="primary" plain>{{ $t('battleInfo.addPhase') }}</el-button>
      <JsonOutputPane :module-data="formDataStore.formData.battle" :title="$t('battleInfo.jsonTitle')" />
      <WikiPanel module-key="battleInfo" :module-title="$t('battleInfo.title')" />
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