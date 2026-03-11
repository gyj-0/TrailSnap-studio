import type { PaginationParams } from './index'

export interface Photo {
  id: number
  albumId: number
  title: string
  description: string | null
  url: string
  thumbnailUrl: string
  fileSize: number
  width: number
  height: number
  takenAt: string | null
  location: string | null
  trainNumber: string | null
  createdAt: string
}

export interface PhotoForm {
  title: string
  description?: string
  albumId: number
  takenAt?: string
  location?: string
  trainNumber?: string
}

export interface PhotoQuery extends PaginationParams {
  albumId?: number
  keyword?: string
  trainNumber?: string
}

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface PhotoState {
  photos: Photo[]
  currentPhoto: Photo | null
  loading: boolean
  total: number
  uploadProgress: Record<string, UploadProgress>
}
