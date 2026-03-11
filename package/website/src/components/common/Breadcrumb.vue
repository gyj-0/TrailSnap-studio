<template>
  <el-breadcrumb separator="/">
    <el-breadcrumb-item :to="{ path: '/' }">
      <el-icon><House /></el-icon>
    </el-breadcrumb-item>
    <el-breadcrumb-item 
      v-for="item in breadcrumbs" 
      :key="item.path"
      :to="item.redirect ? undefined : { path: item.path }"
    >
      {{ item.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { House } from '@element-plus/icons-vue'

interface BreadcrumbItem {
  title: string
  path: string
  redirect?: boolean
}

const route = useRoute()
const breadcrumbs = ref<BreadcrumbItem[]>([])

const getBreadcrumbs = (): BreadcrumbItem[] => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    title: item.meta.title as string,
    path: item.path,
    redirect: item.redirect ? true : false
  }))
}

watch(
  () => route.path,
  () => {
    breadcrumbs.value = getBreadcrumbs()
  },
  { immediate: true }
)
</script>

<style scoped>
.el-breadcrumb {
  font-size: 14px;
}

:deep(.el-breadcrumb__item) {
  display: flex;
  align-items: center;
}

:deep(.el-breadcrumb__inner) {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
