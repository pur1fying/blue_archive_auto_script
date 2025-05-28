<template>
    <el-card class="section-card">
      <!-- <template #header><span>{{ $t('conditions.title') }}</span></template> -->
      <template #header>
        <div class="card-header-wrapper">
          <span>{{ $t('conditions.title') }}</span>
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
        <el-button type="danger" @click="formDataStore.removeCondition(condName)" plain style="width: 100%;" :icon="Close">
          {{ $t('remove') }} "{{ conditionMeta.newName || condName }}"
        </el-button>
      </div>
      <el-button @click="formDataStore.addCondition()" type="primary" plain style="width: 100%;" :icon="Plus">{{ $t('conditions.addCondition') }}</el-button>
      <JsonOutputPane v-if="showJson" :module-data="formDataStore.formData.conditions" :title="$t('conditions.jsonTitle')" />
      <WikiPanel module-key="conditions" :module-title="$t('conditions.title')" />
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
  // Note: Iterating over conditionsMeta allows managing newName and definition_str together.
  // The actual data is in formData.conditions, updated by updateConditionName.
  </script>