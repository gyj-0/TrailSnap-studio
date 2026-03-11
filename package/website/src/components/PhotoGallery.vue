<template>
  <div class="photo-gallery">
    <!-- Filter Bar -->
    <div class="gallery-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索照片..."
          clearable
          style="width: 240px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="sortBy" placeholder="排序方式" style="width: 140px">
          <el-option label="最新上传" value="newest" />
          <el-option label="最早上传" value="oldest" />
          <el-option label="拍摄时间" value="taken" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button label="grid">
            <el-icon><Grid /></el-icon>
          </el-radio-button>
          <el-radio-button label="list">
            <el-icon><List /></el-icon>
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- Photo Grid -->
    <div v-if="displayPhotos.length" :class="['photo-grid', `view-${viewMode}`]">
      <div
        v-for="photo in displayPhotos"
        :key="photo.id"
        class="photo-item"
        @click="selectPhoto(photo)"
      >
        <div class="photo-wrapper">
          <el-image
            :src="photo.thumbnailUrl || photo.url"
            fit="cover"
            class="photo-image"
            lazy
          >
            <template #placeholder>
              <div class="image-placeholder">
                <el-icon class="is-loading"><Loading /></el-icon>
              </div>
            </template>
            <template #error>
              <div class="image-error">
                <el-icon><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          
          <!-- Hover Actions -->
          <div class="photo-actions">
            <el-checkbox
              v-if="selectable"
              v-model="selectedIds"
              :label="photo.id"
              @click.stop
            />
            <div v-else class="action-buttons">
              <el-button text circle size="small" @click.stop="previewPhoto(photo)">
                <el-icon><ZoomIn /></el-icon>
              </el-button>
              <el-button text circle size="small" @click.stop="$emit('favorite', photo)">
                <el-icon><Star /></el-icon>
              </el-button>
            </div>
          </div>
          
          <!-- Photo Info Overlay -->
          <div class="photo-overlay">
            <span class="photo-title">{{ photo.title }}</span>
          </div>
        </div>

        <!-- List View Info -->
        <div v-if="viewMode === 'list'" class="photo-list-info">
          <h4>{{ photo.title }}</h4>
          <p class="photo-desc">{{ photo.description || '暂无描述' }}</p>
          <div class="photo-meta">
            <el-tag v-if="photo.trainNumber" size="small" effect="plain">
              {{ photo.trainNumber }}
            </el-tag>
            <span class="photo-date">{{ formatDate(photo.createdAt) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <el-empty v-else description="暂无照片">
      <template #image>
        <el-icon :size="64" color="#dcdfe6"><Picture /></el-icon>
      </template>
      <el-button v-if="showUploadButton" type="primary" @click="$emit('upload')">
        上传照片
      </el-button>
    </el-empty>

    <!-- Pagination -->
    <div v-if="showPagination && total > pageSize" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[12, 24, 48, 96]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- Image Preview -->
    <el-image-viewer
      v-if="previewVisible"
      :url-list="previewList"
      :initial-index="previewIndex"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Search, Grid, List, Loading, Picture, ZoomIn, Star
} from '@element-plus/icons-vue'
import type { Photo } from '@/types'

interface Props {
  photos: Photo[]
  total?: number
  loading?: boolean
  selectable?: boolean
  showPagination?: boolean
  showUploadButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  total: 0,
  loading: false,
  selectable: false,
  showPagination: true,
  showUploadButton: true
})

const emit = defineEmits<{
  select: [photo: Photo]
  favorite: [photo: Photo]
  upload: []
  pageChange: [page: number]
  sizeChange: [size: number]
}>()

const searchQuery = ref('')
const sortBy = ref('newest')
const viewMode = ref<'grid' | 'list'>('grid')
const currentPage = ref(1)
const pageSize = ref(24)
const selectedIds = ref<number[]>([])
const previewVisible = ref(false)
const previewIndex = ref(0)

const displayPhotos = computed(() => {
  let result = [...props.photos]
  
  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p => 
      p.title.toLowerCase().includes(query) ||
      p.description?.toLowerCase().includes(query) ||
      p.trainNumber?.toLowerCase().includes(query) ||
      p.location?.toLowerCase().includes(query)
    )
  }
  
  // Sort
  result.sort((a, b) => {
    switch (sortBy.value) {
      case 'newest':
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      case 'oldest':
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
      case 'taken':
        return new Date(b.takenAt || b.createdAt).getTime() - 
               new Date(a.takenAt || a.createdAt).getTime()
      default:
        return 0
    }
  })
  
  return result
})

const previewList = computed(() => 
  props.photos.map(p => p.url).filter(Boolean)
)

const selectPhoto = (photo: Photo) => {
  emit('select', photo)
}

const previewPhoto = (photo: Photo) => {
  previewIndex.value = props.photos.findIndex(p => p.id === photo.id)
  previewVisible.value = true
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  emit('pageChange', page)
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  emit('sizeChange', size)
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// Reset page when search changes
watch(searchQuery, () => {
  currentPage.value = 1
})
</script>

<style scoped>
.photo-gallery {
  width: 100%;
}

.gallery-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--bg-base);
  border-radius: 8px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.photo-grid {
  display: grid;
  gap: 16px;
}

.photo-grid.view-grid {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}

.photo-grid.view-list {
  grid-template-columns: 1fr;
}

.view-list .photo-item {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: var(--bg-base);
  border-radius: 8px;
  transition: background-color 0.3s;
}

.view-list .photo-item:hover {
  background: var(--border-extra-light);
}

.view-list .photo-wrapper {
  width: 160px;
  height: 100px;
  flex-shrink: 0;
}

.photo-item {
  cursor: pointer;
}

.photo-wrapper {
  position: relative;
  aspect-ratio: 3/2;
  border-radius: 8px;
  overflow: hidden;
  background: var(--border-lighter);
}

.photo-image {
  width: 100%;
  height: 100%;
  transition: transform 0.3s ease;
}

.photo-item:hover .photo-image {
  transform: scale(1.05);
}

.image-placeholder,
.image-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder);
}

.photo-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.photo-item:hover .photo-actions {
  opacity: 1;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.action-buttons .el-button {
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  border: none;
}

.action-buttons .el-button:hover {
  background: rgba(0, 0, 0, 0.7);
}

.photo-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px 12px 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.6));
  transform: translateY(100%);
  transition: transform 0.3s;
}

.photo-item:hover .photo-overlay {
  transform: translateY(0);
}

.photo-title {
  color: #fff;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-list-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.photo-list-info h4 {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.photo-date {
  font-size: 12px;
  color: var(--text-placeholder);
}

.pagination-wrapper {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .gallery-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .toolbar-left {
    flex-direction: column;
  }
  
  .toolbar-left .el-input,
  .toolbar-left .el-select {
    width: 100% !important;
  }
  
  .photo-grid.view-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .view-list .photo-wrapper {
    width: 100px;
    height: 70px;
  }
}
</style>
