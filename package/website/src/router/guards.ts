import type { Router, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

// White list for routes that don't need authentication
const whiteList = ['/auth/login', '/auth/register']

export function setupRouterGuards(router: Router) {
  // Global before guard
  router.beforeEach(async (to: RouteLocationNormalized, from, next) => {
    const authStore = useAuthStore()

    // Check if user is authenticated
    const isAuthenticated = authStore.isAuthenticated

    // Route requires authentication
    if (to.meta.requiresAuth) {
      if (!isAuthenticated) {
        ElMessage.warning('请先登录')
        next({
          path: '/auth/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }

    // Route is for guests only (e.g., login page)
    if (to.meta.guestOnly) {
      if (isAuthenticated) {
        next('/dashboard')
        return
      }
    }

    next()
  })

  // Global after hook
  router.afterEach((to) => {
    // Analytics or logging could go here
    console.log(`Navigated to: ${to.fullPath}`)
  })

  // Error handler
  router.onError((error) => {
    console.error('Router error:', error)
    ElMessage.error('页面加载失败')
  })
}
