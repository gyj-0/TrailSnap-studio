import { computed } from 'vue'
import { useAlbumStore } from '@/stores/album'
import type { AlbumQuery, AlbumForm } from '@/types'

export function useAlbum() {
  const albumStore = useAlbumStore()

  return {
    // State
    albums: computed(() => albumStore.albums),
    currentAlbum: computed(() => albumStore.currentAlbum),
    loading: computed(() => albumStore.loading),
    total: computed(() => albumStore.total),

    // Actions
    fetchAlbums: (params?: AlbumQuery) => albumStore.fetchAlbums(params),
    fetchAlbum: (id: number) => albumStore.fetchAlbum(id),
    createAlbum: (form: AlbumForm) => albumStore.createAlbum(form),
    updateAlbum: (id: number, form: Partial<AlbumForm>) => albumStore.updateAlbum(id, form),
    deleteAlbum: (id: number) => albumStore.deleteAlbum(id),
    updateCover: (id: number, file: File) => albumStore.updateCover(id, file)
  }
}
