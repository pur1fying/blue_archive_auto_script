<template>
    <el-collapse v-model="activeNames" class="wiki-panel-collapse">
      <el-collapse-item :title="$t('wikiPanelTitle') + (moduleTitle ? `: ${moduleTitle}` : '')" name="1">
        <!-- <div v-if="!isEditing"> -->
          <div>
          <div v-html="renderedWikiText" class="wiki-content"></div>
          <!-- <el-button type="primary" link @click="isEditing = true" size="small" style="margin-top:10px;">Edit Wiki</el-button> -->
        </div>
        <!-- <div v-else>
          <el-input
            type="textarea"
            v-model="editableWikiText"
            :autosize="{ minRows: 5, maxRows: 15 }"
            placeholder="Enter wiki content here (supports basic HTML or Markdown if you add a renderer)"
          />
          <div style="margin-top:10px;">
            <el-button type="success" @click="saveWikiChanges" size="small">Save</el-button>
            <el-button @click="cancelEdit" size="small">Cancel</el-button>
          </div>
        </div> -->
      </el-collapse-item>
    </el-collapse>
  </template>
  
  <script setup>
  import { ref, computed, watch } from 'vue';
  import { useWikiDataStore } from '@/store/wikiData';
  import { marked } from 'marked'; // Optional: for Markdown rendering
  
  const props = defineProps({
    moduleKey: { // e.g., 'formation', 'states'
      type: String,
      required: true,
    },
    moduleTitle: String, // Optional title for the panel
  });
  
  const wikiStore = useWikiDataStore();
  const activeNames = ref([]); // Controls collapse state
  
  const isEditing = ref(false);
  const editableWikiText = ref('');
  
  const currentWikiText = computed(() => wikiStore.getWikiText(props.moduleKey));
  
  // For rendering, you can choose plain HTML or Markdown
  const renderedWikiText = computed(() => {
    // return currentWikiText.value; // For plain HTML
    return marked(currentWikiText.value || ''); // For Markdown
  });
  
  watch(currentWikiText, (newVal) => {
    if (!isEditing.value) {
      editableWikiText.value = newVal;
    }
  }, { immediate: true });
  
  const saveWikiChanges = () => {
    wikiStore.updateWikiText(props.moduleKey, editableWikiText.value);
    isEditing.value = false;
  };
  
  const cancelEdit = () => {
    editableWikiText.value = currentWikiText.value; // Revert
    isEditing.value = false;
  };
  </script>
  
  <style scoped>
  .wiki-panel-collapse {
    margin-top: 20px;
  }
  .wiki-content {
    padding: 10px;
    border-radius: 4px;
    background-color: var(--el-fill-color-extra-light);
    min-height: 50px;
    word-wrap: break-word;
  }
  .dark .wiki-content {
      background-color: var(--el-fill-color-darker);
  }
  /* Basic styling for rendered HTML/Markdown */
  .wiki-content :deep(h1), .wiki-content :deep(h2), .wiki-content :deep(h3) { margin-top: 0.5em; margin-bottom: 0.25em; }
  .wiki-content :deep(p) { margin-bottom: 0.5em; line-height: 1.6; }
  .wiki-content :deep(ul), .wiki-content :deep(ol) { margin-left: 20px; }
  .wiki-content :deep(code) {
    background-color: var(--el-color-primary-light-9);
    padding: 2px 4px;
    border-radius: 4px;
    font-family: monospace;
  }
  .dark .wiki-content :deep(code) {
    background-color: var(--el-color-primary-dark-2);
    color: var(--el-color-white);
  }
  </style>