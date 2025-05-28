<template>
    <el-card class="section-card">
      <!-- <template #header><span>{{ $t('battleInfo.title') }}</span></template> -->
      <template #header>
        <div class="card-header-wrapper">
          <span>{{ $t('battleInfo.title') }}</span>
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
            <el-button type="danger" plain @click="formDataStore.removeBattlePhase(index)" style="margin-top: 8px; float: right;" :icon="Close">{{ $t('remove') }}</el-button>
          </el-col>
        </el-row>
      </div>
      <el-button @click="formDataStore.addBattlePhase()" type="primary" style="width: 100%;" plain :icon="Plus">{{ $t('battleInfo.addPhase') }}</el-button>
      <JsonOutputPane v-if="showJson" :module-data="formDataStore.formData.battleInfo" :title="$t('battleInfo.jsonTitle')" />
      <WikiPanel module-key="battleInfo" :module-title="$t('battleInfo.title')" />
    </el-card>
  </template>
  
  <script setup>
  import { View, Hide, Close, Plus } from '@element-plus/icons-vue'; // Import icons
  import { ref } from 'vue'; // Add ref
  import { useFormDataStore } from '@/store/formData';
  import { useI18n } from 'vue-i18n';
  import JsonOutputPane from '../ui/JsonOutputPane.vue';
  import WikiPanel from '../ui/WikiPanel.vue';
  const showJson = ref(false); // Local state for this module's JSON pane
  
  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  </script>