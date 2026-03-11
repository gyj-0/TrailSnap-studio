export interface User {
  id: number
  username: string
  email: string
  nickname: string | null
  avatar: string | null
  createdAt: string
  updatedAt: string
}

export interface LoginForm {
  username: string
  password: string
  remember?: boolean
}

export interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}
