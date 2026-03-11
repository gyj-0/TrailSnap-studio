import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '@/api/user'
import type { User, LoginForm, RegisterForm, AuthState } from '@/types'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'trailsnap_token'
const USER_KEY = 'trailsnap_user'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(null)
  const loading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // Initialize user from storage
  const initUser = () => {
    const storedUser = localStorage.getItem(USER_KEY)
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        localStorage.removeItem(USER_KEY)
      }
    }
  }

  // Actions
  const login = async (form: LoginForm) => {
    loading.value = true
    try {
      const response = await userApi.login(form)
      token.value = response.token
      user.value = response.user
      
      localStorage.setItem(TOKEN_KEY, response.token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.user))
      
      ElMessage.success('登录成功')
      return true
    } catch (error) {
      return false
    } finally {
      loading.value = false
    }
  }

  const register = async (form: RegisterForm) => {
    loading.value = true
    try {
      await userApi.register(form)
      ElMessage.success('注册成功')
      return true
    } catch (error) {
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const data = await userApi.getCurrentUser()
      user.value = data
      localStorage.setItem(USER_KEY, JSON.stringify(data))
    } catch (error) {
      logout()
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    ElMessage.success('已退出登录')
  }

  const updateProfile = async (data: Partial<User>) => {
    try {
      const updated = await userApi.updateUser(data)
      user.value = updated
      localStorage.setItem(USER_KEY, JSON.stringify(updated))
      ElMessage.success('更新成功')
      return true
    } catch (error) {
      return false
    }
  }

  // Initialize on store creation
  initUser()

  return {
    token,
    user,
    loading,
    isAuthenticated,
    login,
    register,
    fetchUser,
    logout,
    updateProfile
  }
})
