// src/components/ui/RightNavigationPanel.vue
<template>
  <div class="right-nav-panel" v-if="sections && sections.length">
    <el-affix > <!-- Adjust offset as needed -->
      <el-card shadow="never" :body-style="{ padding: '10px' }">
        <div class="nav-title">{{ $t('navigation.title') || 'On This Page' }}</div>
        <el-anchor @click="handleAnchorClick" :offset="60"> <!-- Offset for fixed headers -->
          <el-anchor-link
            v-for="section in sections"
            :key="section.id"
            :href="`#${section.id}`"
            :title="$t(section.titleKey) || section.titleKey"
          >
            <!-- You can optionally add icons here if you pass them in `sections` -->
            <!-- <template #icon><el-icon><component :is="section.icon" /></el-icon></template> -->
          </el-anchor-link>
        </el-anchor>
      </el-card>
    </el-affix>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import { useI18n } from 'vue-i18n';
// If you use icons from Element Plus, import them or rely on auto-import
// import { InfoFilled, UserFilled, Histogram, /* ...other icons... */ } from '@element-plus/icons-vue';

const props = defineProps({
  sections: {
    type: Array,
    required: true,
    default: () => [] // [{ id: 'string', titleKey: 'string', icon?: 'string' (component name) }]
  }
});

const emit = defineEmits(['navigate']);
const { t } = useI18n();

const handleAnchorClick = (e, link) => {
  e.preventDefault(); // Prevent default hash change if you want full control
  if (link) {
    const sectionId = link.substring(1); // Remove '#'
    emit('navigate', sectionId);
  }
};
</script>

<style scoped>
.right-nav-panel {
  width: 100%;
  max-height: calc(100vh - 100px); /* Adjust based on header/footer */
  overflow-y: auto;
}
.nav-title {
  font-weight: bold;
  margin-bottom: 10px;
  padding-left: 10px; /* Align with anchor links */
  font-size: 0.9em;
  color: var(--el-text-color-secondary);
}
/* Custom styling for el-anchor if needed */
:deep(.el-anchor-link__title) {
  font-size: 0.9em;
}
</style>