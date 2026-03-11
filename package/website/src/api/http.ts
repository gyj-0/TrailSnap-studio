import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse, type AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api'
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000')

// Create axios instance
const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
http.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor
http.interceptors.response.use(
  (response: AxiosResponse) => {
    const { code, message, data } = response.data
    
    // If the API returns a specific code format
    if (code !== undefined && code !== 200) {
      ElMessage.error(message || '请求失败')
      return Promise.reject(new Error(message))
    }
    
    return data ?? response.data
  },
  (error: AxiosError) => {
    const { response } = error
    
    if (response) {
      const { status, data } = response as AxiosResponse
      
      switch (status) {
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          useAuthStore().logout()
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data?.message || `请求失败 (${status})`)
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络')
    }
    
    return Promise.reject(error)
  }
)

export default http

// Helper methods
export const get = <T>(url: string, config?: AxiosRequestConfig): Promise<T> => 
  http.get(url, config)

export const post = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => 
  http.post(url, data, config)

export const put = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => 
  http.put(url, data, config)

export const del = <T>(url: string, config?: AxiosRequestConfig): Promise<T> => 
  http.delete(url, config)

export const patch = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => 
  http.patch(url, data, config)
