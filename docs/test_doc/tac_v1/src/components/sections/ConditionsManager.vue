<template>
    <el-card class="section-card">
      <template #header><span>{{ $t('conditions.title') }}</span></template>
      <div v-for="(conditionMeta, condName) in formDataStore.conditionsMeta" :key="condName" class="dynamic-list-item">
         <el-form-item :label="$t('conditions.conditionName')">
          <el-input
            v-model="conditionMeta.newName"
            @blur="formDataStore.updateConditionName(condName, conditionMeta.newName, conditionMeta.definition_str)"
            :placeholder="$t('conditions.conditionNamePlaceholder')"
            style="font-weight:bold;"
          />
        </el-form-item>
        <el-form-item :label="$t('conditions.conditionDef')">
          <el-input
            type="textarea"
            v-model="conditionMeta.definition_str"
            @blur="formDataStore.updateConditionName(condName, conditionMeta.newName, conditionMeta.definition_str)"
            :autosize="{ minRows: 3, maxRows: 10 }"
            :placeholder="$t('conditions.conditionDefPlaceholder')"
          />
        </el-form-item>
        <el-button type="danger" @click="formDataStore.removeCondition(condName)">
          {{ $t('remove') }} {{ conditionMeta.newName || condName }}
        </el-button>
      </div>
      <el-button @click="formDataStore.addCondition()" type="primary" plain>{{ $t('conditions.addCondition') }}</el-button>
      <JsonOutputPane :module-data="formDataStore.formData.conditions" :title="$t('conditions.jsonTitle')" />
      <WikiPanel module-key="conditions" :module-title="$t('conditions.title')" />
    </el-card>
  </template>
  
  <script setup>
  import { useFormDataStore } from '@/store/formData';
  import { useI18n } from 'vue-i18n';
  import JsonOutputPane from '../ui/JsonOutputPane.vue';
  import WikiPanel from '../ui/WikiPanel.vue';
  
  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  // Note: Iterating over conditionsMeta allows managing newName and definition_str together.
  // The actual data is in formData.conditions, updated by updateConditionName.
  </script>