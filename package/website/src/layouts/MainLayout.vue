<template>
  <el-container class="main-layout">
    <!-- Sidebar -->
    <AppSidebar />
    
    <el-container class="main-container">
      <!-- Header -->
      <AppHeader />
      
      <!-- Main Content -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
      
      <!-- Footer -->
      <AppFooter />
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import AppFooter from '@/components/common/AppFooter.vue'
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.main-container {
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  background-color: var(--bg-page);
}
</style>
