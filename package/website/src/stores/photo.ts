import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { photoApi } from '@/api/photo'
import type { Photo, PhotoForm, PhotoQuery, PaginationData, UploadProgress } from '@/types'
import { ElMessage } from 'element-plus'

export const usePhotoStore = defineStore('photo', () => {
  // State
  const photos = ref<Photo[]>([])
  const currentPhoto = ref<Photo | null>(null)
  const loading = ref(false)
  const total = ref(0)
  const uploadProgress = reactive<Record<string, UploadProgress>>({})

  // Actions
  const fetchPhotos = async (params: PhotoQuery = { page: 1, size: 20 }) => {
    loading.value = true
    try {
      const data: PaginationData<Photo> = await photoApi.getPhotos(params)
      photos.value = data.list
      total.value = data.total
      return data
    } finally {
      loading.value = false
    }
  }

  const fetchPhoto = async (id: number) => {
    loading.value = true
    try {
      const data = await photoApi.getPhoto(id)
      currentPhoto.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  const createPhoto = async (form: PhotoForm) => {
    try {
      const data = await photoApi.createPhoto(form)
      photos.value.unshift(data)
      total.value++
      ElMessage.success('照片添加成功')
      return data
    } catch (error) {
      return null
    }
  }

  const deletePhoto = async (id: number) => {
    try {
      await photoApi.deletePhoto(id)
      photos.value = photos.value.filter(p => p.id !== id)
      total.value--
      if (currentPhoto.value?.id === id) {
        currentPhoto.value = null
      }
      ElMessage.success('照片删除成功')
      return true
    } catch (error) {
      return false
    }
  }

  const uploadPhoto = async (albumId: number, file: File) => {
    try {
      const data = await photoApi.uploadPhoto(albumId, file, (progress) => {
        uploadProgress[file.name] = progress
      })
      photos.value.unshift(data)
      total.value++
      delete uploadProgress[file.name]
      return data
    } catch (error) {
      delete uploadProgress[file.name]
      return null
    }
  }

  const batchUpload = async (albumId: number, files: File[]) => {
    const results: Photo[] = []
    for (const file of files) {
      const photo = await uploadPhoto(albumId, file)
      if (photo) {
        results.push(photo)
      }
    }
    if (results.length > 0) {
      ElMessage.success(`成功上传 ${results.length} 张照片`)
    }
    return results
  }

  return {
    photos,
    currentPhoto,
    loading,
    total,
    uploadProgress,
    fetchPhotos,
    fetchPhoto,
    createPhoto,
    deletePhoto,
    uploadPhoto,
    batchUpload
  }
})
