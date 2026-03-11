import { createRouter, createWebHistory } from 'vue-router'
import { setupRouterGuards } from './guards'
import { useAppStore } from '@/stores/app'

// Layouts
import MainLayout from '@/layouts/MainLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

// Views
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import DashboardView from '@/views/DashboardView.vue'
import AlbumListView from '@/views/AlbumListView.vue'
import AlbumDetailView from '@/views/AlbumDetailView.vue'
import PhotoDetailView from '@/views/PhotoDetailView.vue'
import SettingsView from '@/views/SettingsView.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: DashboardView,
        meta: { title: '首页', requiresAuth: true }
      },
      {
        path: 'albums',
        name: 'AlbumList',
        component: AlbumListView,
        meta: { title: '相册列表', requiresAuth: true }
      },
      {
        path: 'albums/:id',
        name: 'AlbumDetail',
        component: AlbumDetailView,
        meta: { title: '相册详情', requiresAuth: true }
      },
      {
        path: 'photos/:id',
        name: 'PhotoDetail',
        component: PhotoDetailView,
        meta: { title: '照片详情', requiresAuth: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: SettingsView,
        meta: { title: '设置', requiresAuth: true }
      }
    ]
  },
  {
    path: '/auth',
    component: AuthLayout,
    redirect: '/auth/login',
    meta: { guestOnly: true },
    children: [
      {
        path: 'login',
        name: 'Login',
        component: LoginView,
        meta: { title: '登录' }
      },
      {
        path: 'register',
        name: 'Register',
        component: RegisterView,
        meta: { title: '注册' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Update page title
router.beforeEach((to) => {
  const appStore = useAppStore()
  const title = to.meta.title as string
  if (title) {
    appStore.setPageTitle(title)
  }
})

// Setup guards
setupRouterGuards(router)

export default router
