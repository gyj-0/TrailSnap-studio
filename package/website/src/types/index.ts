// Common types
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface PaginationParams {
  page: number
  size: number
}

export interface PaginationData<T> {
  list: T[]
  total: number
  page: number
  size: number
  totalPages: number
}

export interface FileInfo {
  name: string
  url: string
  size: number
  type: string
}
