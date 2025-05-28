<template>
  <el-card class="section-card output-display-card">
    <template #header>
      <div class="card-header">
        <span>{{ $t('generatedJson') || 'Generated JSON' }}</span>
      </div>
    </template>
    <div class="action-buttons">
      <el-button type="success" @click="copyJson" :icon="CopyDocument">{{ $t('generateAndCopy') }}</el-button>
      <el-button type="primary" @click="exportJsonToFile" :icon="Download">{{ $t('exportToFile') || 'Export to File' }}</el-button>
    </div>
    <el-input
      type="textarea"
      :model-value="formDataStore.generatedJsonString"
      :autosize="{ minRows: 20 }"
      readonly
      class="json-output"
    />
  </el-card>
</template>

<script setup>
import { useFormDataStore } from '@/store/formData';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { CopyDocument, Download } from '@element-plus/icons-vue'; // Import icons

const { t } = useI18n();
const formDataStore = useFormDataStore();

const copyJson = () => {
  if (!formDataStore.generatedJsonString) {
    ElMessage.warning(t('jsonOutputEmpty') || 'JSON output is empty.');
    return;
  }
  navigator.clipboard.writeText(formDataStore.generatedJsonString).then(() => {
    ElMessage.success(t('jsonCopiedSuccess') || 'JSON copied to clipboard!');
  }).catch(err => {
    ElMessage.error(t('jsonCopiedError') || 'Failed to copy JSON.');
    console.error('Could not copy text: ', err);
  });
};

const exportJsonToFile = () => {
  if (!formDataStore.generatedJsonString) {
    ElMessage.warning(t('jsonOutputEmpty') || 'JSON output is empty. Nothing to export.');
    return;
  }

  // Attempt to use the "name" field from formData for the filename, otherwise use a default
  const axisName = formDataStore.formData.name || 'baas_auto_fight_config';
  // Sanitize the filename (simple sanitization)
  const filename = `${axisName.replace(/[^a-z0-9_.-]/gi, '_').substring(0, 50)}.json`;

  const blob = new Blob([formDataStore.generatedJsonString], { type: 'application/json;charset=utf-8;' });
  const link = document.createElement('a');

  if (link.download !== undefined) { // Check for browser support
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url); // Clean up
    ElMessage.success(`${t('fileExportedSuccess') || 'File exported successfully as'} ${filename}`);
  } else {
    // Fallback for older browsers (though less common now)
    ElMessage.error(t('fileExportErrorBrowser') || 'File export is not supported by your browser.');
    // You could try navigator.msSaveBlob if targeting IE
  }
};
</script>

<style scoped>
.output-display-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.json-output {
  width: 100%;
  font-family: monospace;
}
.action-buttons {
  margin-bottom: 15px; /* Add some space above the textarea */
  display: flex;
  gap: 10px;
}
</style>