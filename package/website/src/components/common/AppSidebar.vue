<template>
  <el-aside 
    class="app-sidebar" 
    :width="appStore.sidebarCollapsed ? '64px' : '240px'"
  >
    <div class="sidebar-logo">
      <el-icon :size="32"><Train /></el-icon>
      <span v-show="!appStore.sidebarCollapsed" class="logo-text">TrailSnap</span>
    </div>
    
    <el-menu
      :default-active="activeMenu"
      :collapse="appStore.sidebarCollapsed"
      :collapse-transition="false"
      router
      background-color="var(--sidebar-bg)"
      text-color="var(--sidebar-text)"
      active-text-color="var(--sidebar-active-text)"
    >
      <el-menu-item index="/dashboard">
        <el-icon><HomeFilled /></el-icon>
        <template #title>首页</template>
      </el-menu-item>
      
      <el-menu-item index="/albums">
        <el-icon><PictureFilled /></el-icon>
        <template #title>相册管理</template>
      </el-menu-item>
      
      <el-sub-menu index="/upload">
        <template #title>
          <el-icon><UploadFilled /></el-icon>
          <span>上传管理</span>
        </template>
        <el-menu-item index="/upload/photo">上传照片</el-menu-item>
        <el-menu-item index="/upload/batch">批量上传</el-menu-item>
      </el-sub-menu>
      
      <el-menu-item index="/statistics">
        <el-icon><TrendCharts /></el-icon>
        <template #title>数据统计</template>
      </el-menu-item>
      
      <el-divider />
      
      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <template #title>系统设置</template>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Train, HomeFilled, PictureFilled, UploadFilled, 
  TrendCharts, Setting
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)
</script>

<style scoped>
.app-sidebar {
  background-color: var(--sidebar-bg);
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 16px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}

.el-menu {
  flex: 1;
  border-right: none;
}

:deep(.el-menu-item), :deep(.el-sub-menu__title) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-divider) {
  margin: 12px 16px;
  background-color: rgba(255, 255, 255, 0.1);
}

/* Custom scrollbar for sidebar */
:deep(.el-menu::-webkit-scrollbar) {
  width: 4px;
}

:deep(.el-menu::-webkit-scrollbar-thumb) {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}
</style>
