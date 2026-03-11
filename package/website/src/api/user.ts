import { get, post } from './http'
import type { ApiResponse, User, LoginForm, RegisterForm } from '@/types'

interface LoginResponse {
  token: string
  user: User
}

export const userApi = {
  // Login
  login(data: LoginForm): Promise<LoginResponse> {
    return post('/auth/login', data)
  },

  // Register
  register(data: RegisterForm): Promise<ApiResponse<User>> {
    return post('/auth/register', data)
  },

  // Get current user info
  getCurrentUser(): Promise<User> {
    return get('/user/me')
  },

  // Update user info
  updateUser(data: Partial<User>): Promise<User> {
    return post('/user/update', data)
  },

  // Upload avatar
  uploadAvatar(file: File): Promise<{ url: string }> {
    const formData = new FormData()
    formData.append('file', file)
    return post('/user/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // Change password
  changePassword(oldPassword: string, newPassword: string): Promise<void> {
    return post('/user/password', { oldPassword, newPassword })
  }
}
