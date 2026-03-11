import type { PaginationParams } from './index'

export interface Album {
  id: number
  title: string
  description: string | null
  coverUrl: string | null
  isPublic: boolean
  photoCount: number
  ownerId: number
  createdAt: string
  updatedAt: string
}

export interface AlbumForm {
  title: string
  description?: string
  isPublic: boolean
}

export interface AlbumQuery extends PaginationParams {
  keyword?: string
  isPublic?: boolean
}

export interface AlbumState {
  albums: Album[]
  currentAlbum: Album | null
  loading: boolean
  total: number
}
