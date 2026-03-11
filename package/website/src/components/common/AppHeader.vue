<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-button
        text
        class="menu-toggle"
        @click="appStore.toggleSidebar"
      >
        <el-icon :size="20">
          <Fold v-if="!appStore.sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </el-button>
      
      <breadcrumb class="breadcrumb" />
    </div>
    
    <div class="header-right">
      <!-- Search -->
      <el-tooltip content="搜索">
        <el-button text circle>
          <el-icon><Search /></el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- Theme Toggle -->
      <el-tooltip :content="appStore.isDark ? '切换亮色' : '切换暗色'">
        <el-button text circle @click="appStore.toggleTheme">
          <el-icon>
            <Sunny v-if="appStore.isDark" />
            <Moon v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- Fullscreen -->
      <el-tooltip content="全屏">
        <el-button text circle @click="toggleFullscreen">
          <el-icon>
            <FullScreen v-if="!isFullscreen" />
            <Aim v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- Notification -->
      <el-badge :value="3" class="notification-badge">
        <el-tooltip content="通知">
          <el-button text circle>
            <el-icon><Bell /></el-icon>
          </el-button>
        </el-tooltip>
      </el-badge>
      
      <!-- User Menu -->
      <el-dropdown class="user-dropdown" @command="handleCommand">
        <span class="user-info">
          <el-avatar 
            :size="32" 
            :src="authStore.user?.avatar || ''"
            :icon="UserFilled"
          />
          <span class="username">{{ authStore.user?.nickname || authStore.user?.username }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>个人中心
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>账号设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Fold, Expand, Search, Sunny, Moon, FullScreen, Aim, Bell,
  ArrowDown, UserFilled, User, Setting, SwitchButton
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import Breadcrumb from './Breadcrumb.vue'

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

const isFullscreen = ref(false)

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/settings')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      authStore.logout()
      router.push('/auth/login')
      break
  }
}
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  background: var(--bg-base);
  border-bottom: 1px solid var(--border-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-toggle {
  font-size: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-badge {
  margin-right: 8px;
}

.user-dropdown {
  margin-left: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: var(--border-extra-light);
}

.username {
  font-size: 14px;
  color: var(--text-regular);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .username {
    display: none;
  }
  
  .breadcrumb {
    display: none;
  }
}
</style>
