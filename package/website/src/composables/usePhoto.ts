import { computed } from 'vue'
import { usePhotoStore } from '@/stores/photo'
import type { PhotoQuery, PhotoForm, UploadProgress } from '@/types'

export function usePhoto() {
  const photoStore = usePhotoStore()

  return {
    // State
    photos: computed(() => photoStore.photos),
    currentPhoto: computed(() => photoStore.currentPhoto),
    loading: computed(() => photoStore.loading),
    total: computed(() => photoStore.total),
    uploadProgress: computed(() => photoStore.uploadProgress),

    // Actions
    fetchPhotos: (params?: PhotoQuery) => photoStore.fetchPhotos(params),
    fetchPhoto: (id: number) => photoStore.fetchPhoto(id),
    createPhoto: (form: PhotoForm) => photoStore.createPhoto(form),
    deletePhoto: (id: number) => photoStore.deletePhoto(id),
    uploadPhoto: (albumId: number, file: File, onProgress?: (progress: UploadProgress) => void) => 
      photoStore.uploadPhoto(albumId, file, onProgress),
    batchUpload: (albumId: number, files: File[]) => photoStore.batchUpload(albumId, files)
  }
}
