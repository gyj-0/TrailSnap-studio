import { get, post, del } from './http'
import type { Photo, PhotoForm, PhotoQuery, PaginationData, UploadProgress } from '@/types'
import http from './http'

export const photoApi = {
  // Get photo list
  getPhotos(params: PhotoQuery): Promise<PaginationData<Photo>> {
    return get('/photos', { params })
  },

  // Get photo detail
  getPhoto(id: number): Promise<Photo> {
    return get(`/photos/${id}`)
  },

  // Create photo metadata
  createPhoto(data: PhotoForm): Promise<Photo> {
    return post('/photos', data)
  },

  // Delete photo
  deletePhoto(id: number): Promise<void> {
    return del(`/photos/${id}`)
  },

  // Upload photo file with progress
  uploadPhoto(
    albumId: number, 
    file: File, 
    onProgress?: (progress: UploadProgress) => void
  ): Promise<Photo> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('albumId', albumId.toString())

    return http.post('/photos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage: Math.round((progressEvent.loaded * 100) / progressEvent.total)
          })
        }
      }
    })
  },

  // Batch upload photos
  batchUploadPhotos(
    albumId: number,
    files: File[],
    onProgress?: (fileName: string, progress: UploadProgress) => void
  ): Promise<Photo[]> {
    return Promise.all(
      files.map(file => 
        this.uploadPhoto(albumId, file, (progress) => {
          onProgress?.(file.name, progress)
        })
      )
    )
  }
}
