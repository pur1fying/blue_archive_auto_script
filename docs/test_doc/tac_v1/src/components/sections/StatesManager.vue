<template>
    <el-card class="section-card">
      <template #header><span>{{ $t('states.title') }}</span></template>
      <div v-for="(state, stateName) in formDataStore.formData.states" :key="stateName" class="dynamic-list-item">
        <el-form-item :label="$t('states.stateName')">
          <el-input
            v-model="formDataStore.statesMeta[stateName].newName"
            @blur="formDataStore.updateStateName(stateName, formDataStore.statesMeta[stateName].newName)"
            :placeholder="$t('states.stateNamePlaceholder')"
            style="font-weight:bold;"
          />
        </el-form-item>
  
        <el-form-item :label="$t('states.action')">
          <el-select v-model="state.action" :placeholder="$t('states.selectAction')" filterable clearable class="full-width-select">
            <el-option v-for="actionName in formDataStore.actionNames" :key="actionName" :label="actionName" :value="actionName"></el-option>
          </el-select>
        </el-form-item>
  
        <h4>{{ $t('states.transitions') }}</h4>
        <div v-for="(transition, transIndex) in state.transitions" :key="transIndex" class="nested-list-item">
          <el-row :gutter="10" align="middle">
            <el-col :span="10">
              <el-form-item :label="$t('states.condition')">
                <el-select v-model="transition.condition" :placeholder="$t('states.selectCondition')" filterable class="full-width-select">
                  <el-option v-for="condName in formDataStore.conditionNames" :key="condName" :label="condName" :value="condName"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item :label="$t('states.nextState')">
                <el-select v-model="transition.next" :placeholder="$t('states.selectNextState')" filterable class="full-width-select">
                  <el-option v-for="sName in formDataStore.stateNames" :key="sName" :label="sName" :value="sName"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-button type="danger" @click="formDataStore.removeTransition(stateName, transIndex)" plain size="small">{{ $t('remove') }}</el-button>
            </el-col>
          </el-row>
        </div>
        <el-button @click="formDataStore.addTransition(stateName)" type="success" plain size="small">{{ $t('states.addTransition') }}</el-button>
  
        <el-form-item :label="$t('states.defaultTransition')" style="margin-top:15px;">
          <el-select v-model="state.default_transition" :placeholder="$t('states.selectDefaultState')" filterable clearable class="full-width-select">
            <el-option v-for="sName in formDataStore.stateNames" :key="sName" :label="sName" :value="sName"></el-option>
          </el-select>
        </el-form-item>
        <el-button type="danger" @click="formDataStore.removeState(stateName)" style="margin-top:10px;">{{ $t('remove') }} {{ formDataStore.statesMeta[stateName]?.newName || stateName }}</el-button>
      </div>
      <el-button @click="formDataStore.addState()" type="primary" plain>{{ $t('states.addState') }}</el-button>
      <JsonOutputPane :module-data="formDataStore.formData.states" :title="$t('states.jsonTitle')" />
      <WikiPanel module-key="states" :module-title="$t('states.title')" />
    </el-card>
  </template>
  
  <script setup>
  import { useFormDataStore } from '@/store/formData';
  import { useI18n } from 'vue-i18n';
  import JsonOutputPane from '../ui/JsonOutputPane.vue';
  import WikiPanel from '../ui/WikiPanel.vue';
  
  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  // Note: The key for v-for on states should ideally be stable.
  // If stateName can change and cause issues, consider using an index or a unique ID if you assign one.
  // However, for object iteration, the key is the property name.
  </script>