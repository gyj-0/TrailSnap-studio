import { get, post, put, del } from './http'
import type { Album, AlbumForm, AlbumQuery, PaginationData } from '@/types'

export const albumApi = {
  // Get album list
  getAlbums(params: AlbumQuery): Promise<PaginationData<Album>> {
    return get('/albums', { params })
  },

  // Get album detail
  getAlbum(id: number): Promise<Album> {
    return get(`/albums/${id}`)
  },

  // Create album
  createAlbum(data: AlbumForm): Promise<Album> {
    return post('/albums', data)
  },

  // Update album
  updateAlbum(id: number, data: Partial<AlbumForm>): Promise<Album> {
    return put(`/albums/${id}`, data)
  },

  // Delete album
  deleteAlbum(id: number): Promise<void> {
    return del(`/albums/${id}`)
  },

  // Update album cover
  updateCover(id: number, file: File): Promise<{ url: string }> {
    const formData = new FormData()
    formData.append('file', file)
    return post(`/albums/${id}/cover`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}
