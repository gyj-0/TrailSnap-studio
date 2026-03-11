import { defineStore } from 'pinia'
import { ref } from 'vue'
import { albumApi } from '@/api/album'
import type { Album, AlbumForm, AlbumQuery, PaginationData } from '@/types'
import { ElMessage } from 'element-plus'

export const useAlbumStore = defineStore('album', () => {
  // State
  const albums = ref<Album[]>([])
  const currentAlbum = ref<Album | null>(null)
  const loading = ref(false)
  const total = ref(0)

  // Actions
  const fetchAlbums = async (params: AlbumQuery = { page: 1, size: 10 }) => {
    loading.value = true
    try {
      const data: PaginationData<Album> = await albumApi.getAlbums(params)
      albums.value = data.list
      total.value = data.total
      return data
    } finally {
      loading.value = false
    }
  }

  const fetchAlbum = async (id: number) => {
    loading.value = true
    try {
      const data = await albumApi.getAlbum(id)
      currentAlbum.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  const createAlbum = async (form: AlbumForm) => {
    try {
      const data = await albumApi.createAlbum(form)
      albums.value.unshift(data)
      total.value++
      ElMessage.success('相册创建成功')
      return data
    } catch (error) {
      return null
    }
  }

  const updateAlbum = async (id: number, form: Partial<AlbumForm>) => {
    try {
      const data = await albumApi.updateAlbum(id, form)
      const index = albums.value.findIndex(a => a.id === id)
      if (index !== -1) {
        albums.value[index] = { ...albums.value[index], ...data }
      }
      if (currentAlbum.value?.id === id) {
        currentAlbum.value = { ...currentAlbum.value, ...data }
      }
      ElMessage.success('相册更新成功')
      return data
    } catch (error) {
      return null
    }
  }

  const deleteAlbum = async (id: number) => {
    try {
      await albumApi.deleteAlbum(id)
      albums.value = albums.value.filter(a => a.id !== id)
      total.value--
      if (currentAlbum.value?.id === id) {
        currentAlbum.value = null
      }
      ElMessage.success('相册删除成功')
      return true
    } catch (error) {
      return false
    }
  }

  const updateCover = async (id: number, file: File) => {
    try {
      const { url } = await albumApi.updateCover(id, file)
      const index = albums.value.findIndex(a => a.id === id)
      if (index !== -1) {
        albums.value[index].coverUrl = url
      }
      if (currentAlbum.value?.id === id) {
        currentAlbum.value.coverUrl = url
      }
      ElMessage.success('封面更新成功')
      return url
    } catch (error) {
      return null
    }
  }

  return {
    albums,
    currentAlbum,
    loading,
    total,
    fetchAlbums,
    fetchAlbum,
    createAlbum,
    updateAlbum,
    deleteAlbum,
    updateCover
  }
})
