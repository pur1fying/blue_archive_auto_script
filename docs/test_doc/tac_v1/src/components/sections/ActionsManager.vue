<template>
    <el-card class="section-card">
      <!-- <template #header><span>{{ $t('actions.title') }}</span></template> -->

      <template #header>
        <div class="card-header-wrapper">
          <span>{{ $t('actions.title') }}</span>
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

      <div v-for="(actionSteps, actionName) in formDataStore.formData.actions" :key="actionName" class="dynamic-list-item">
        <el-form-item :label="$t('actions.actionName')">
          <el-input
            v-model="formDataStore.actionsMeta[actionName].newName"
            @blur="formDataStore.updateActionName(actionName, formDataStore.actionsMeta[actionName].newName)"
            :placeholder="$t('actions.actionNamePlaceholder')"
            style="font-weight:bold;"
          />
        </el-form-item>
  
        <div>
          <h4 style="display: inline;">{{ $t('actions.actionSteps') }}</h4>
          <el-button type="danger" @click="formDataStore.removeAction(actionName)" style=" float: right; margin-top: -8px;" plain :icon="Close">
          {{ $t('remove') }} {{ formDataStore.actionsMeta[actionName]?.newName || actionName }}
        </el-button>
        </div>
        <div v-for="(step, stepIndex) in actionSteps" :key="stepIndex" class="nested-list-item">
          <el-row :gutter="10" align="top">
            <el-col :span="6">
              <el-form-item :label="$t('actions.stepType')">
                <el-select v-model="step.t" :placeholder="$t('actions.selectStepType')">
                  <el-option :label="$t('actions.typeAcc')" value="acc"></el-option>
                  <el-option :label="$t('actions.typeAuto')" value="auto"></el-option>
                  <el-option :label="$t('actions.typeSkill')" value="skill"></el-option>
                  <!-- Add other action types from WIKI -->
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="14">
              <el-form-item :label="$t('actions.stepDesc')">
                <el-input v-model="step.desc" :placeholder="$t('actions.stepDescPlaceholder')"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="4" style="padding-top: 30px;"> <!-- Adjust padding for alignment -->
              <el-button type="danger" @click="formDataStore.removeActionStep(actionName, stepIndex)" plain style="float: right;" :icon="Close">{{ $t('actions.removeStep') }}</el-button>
            </el-col>
          </el-row>
          <!-- Parameters specific to action type -->
          <div v-if="step.t === 'acc'">
            <el-form-item :label="$t('actions.accValue')">
              <el-input-number v-model="step.acc" :min="1" :max="3" :placeholder="$t('actions.accValuePlaceholder')"></el-input-number>
            </el-form-item>
          </div>
          <div v-if="step.t === 'auto'">
            <el-form-item :label="$t('actions.autoState')">
              <el-switch v-model="step.auto_state" :active-text="$t('on')" :inactive-text="$t('off')"></el-switch>
            </el-form-item>
          </div>
          <div v-if="step.t === 'skill'">
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item :label="$t('actions.skillName')">
                  <el-input v-model="step.skill_name" :placeholder="$t('actions.skillNamePlaceholder')"></el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="$t('actions.skillTarget')">
                  <el-input v-model="step.target" :placeholder="$t('actions.skillTargetPlaceholder')"></el-input>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </div>
        <el-button @click="formDataStore.addActionStep(actionName)" type="success" plain :icon="Plus" style="width: 100%;">{{ $t('actions.addStep') }}</el-button>

      </div>
      <el-button @click="formDataStore.addAction()" type="primary" plain style="width: 100%;">{{ $t('actions.addAction') }}</el-button>
      <JsonOutputPane v-if="showJson" :module-data="formDataStore.formData.actions" :title="$t('actions.jsonTitle')" />
      <WikiPanel module-key="actions" :module-title="$t('actions.title')" />
    </el-card>
  </template>
  
  <script setup>
  import { View, Hide, Plus, Close } from '@element-plus/icons-vue'; // Import icons
  import { ref } from 'vue'; // Add ref
  import { useFormDataStore } from '@/store/formData';
  import { useI18n } from 'vue-i18n';
  import JsonOutputPane from '../ui/JsonOutputPane.vue';
  import WikiPanel from '../ui/WikiPanel.vue';
  const showJson = ref(false); // Local state for this module's JSON pane

  const { t } = useI18n();
  const formDataStore = useFormDataStore();
  </script>