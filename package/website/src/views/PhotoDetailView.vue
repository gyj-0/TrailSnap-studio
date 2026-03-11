<template>
  <div class="photo-detail-view page-container">
    <div class="photo-container">
      <!-- Image Section -->
      <div class="image-section">
        <el-image
          :src="photo?.url"
          :preview-src-list="[photo?.url || '']"
          fit="contain"
          class="main-image"
        >
          <template #error>
            <div class="image-error">
              <el-icon :size="64"><Picture /></el-icon>
              <p>图片加载失败</p>
            </div>
          </template>
        </el-image>
        
        <div class="image-nav">
          <el-button circle @click="prevPhoto">
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          <span class="photo-counter">{{ currentIndex + 1 }} / {{ totalPhotos }}</span>
          <el-button circle @click="nextPhoto">
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- Info Section -->
      <div class="info-section">
        <div class="info-header">
          <h1 class="photo-title">{{ photo?.title }}</h1>
          <div class="photo-actions">
            <el-button text circle @click="toggleFavorite">
              <el-icon :size="20" :color="isFavorite ? '#f56c6c' : ''">
                <Star v-if="isFavorite" />
                <StarFilled v-else />
              </el-icon>
            </el-button>
            <el-button text circle @click="downloadPhoto">
              <el-icon :size="20"><Download /></el-icon>
            </el-button>
            <el-button text circle @click="sharePhoto">
              <el-icon :size="20"><Share /></el-icon>
            </el-button>
            <el-dropdown @command="handleMoreAction">
              <el-button text circle>
                <el-icon :size="20"><More /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">
                    <el-icon><Edit /></el-icon>编辑信息
                  </el-dropdown-item>
                  <el-dropdown-item command="move">
                    <el-icon><FolderOpened /></el-icon>移动到相册
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete" style="color: #f56c6c;">
                    <el-icon><Delete /></el-icon>删除照片
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <p class="photo-description">{{ photo?.description || '暂无描述' }}</p>
        
        <!-- EXIF Info -->
        <div class="info-group">
          <h3>拍摄信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <el-icon><Camera /></el-icon>
              <div class="info-content">
                <span class="info-label">拍摄设备</span>
                <span class="info-value">{{ photo?.exif?.camera || '未知' }}</span>
              </div>
            </div>
            <div class="info-item">
              <el-icon><Timer /></el-icon>
              <div class="info-content">
                <span class="info-label">快门速度</span>
                <span class="info-value">{{ photo?.exif?.shutter || '未知' }}</span>
              </div>
            </div>
            <div class="info-item">
              <el-icon><Aperture /></el-icon>
              <div class="info-content">
                <span class="info-label">光圈</span>
                <span class="info-value">{{ photo?.exif?.aperture || '未知' }}</span>
              </div>
            </div>
            <div class="info-item">
              <el-icon><Sunny /></el-icon>
              <div class="info-content">
                <span class="info-label">ISO</span>
                <span class="info-value">{{ photo?.exif?.iso || '未知' }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Railway Info -->
        <div class="info-group">
          <h3>铁路信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="车次">
              <TrainTicket :train-number="photo?.trainNumber" />
            </el-descriptions-item>
            <el-descriptions-item label="拍摄地点">
              {{ photo?.location || '未知' }}
            </el-descriptions-item>
            <el-descriptions-item label="拍摄时间">
              {{ formatDateTime(photo?.takenAt) }}
            </el-descriptions-item>
            <el-descriptions-item label="图片尺寸">
              {{ photo?.width }} × {{ photo?.height }}
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ formatFileSize(photo?.fileSize) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <!-- Tags -->
        <div class="info-group">
          <h3>标签</h3>
          <div class="tags-list">
            <el-tag
              v-for="tag in photoTags"
              :key="tag"
              class="photo-tag"
              closable
              @close="removeTag(tag)"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="inputTagVisible"
              ref="tagInputRef"
              v-model="inputTagValue"
              size="small"
              style="width: 100px"
              @keyup.enter="addTag"
              @blur="addTag"
            />
            <el-button v-else size="small" @click="showTagInput">
              <el-icon><Plus /></el-icon>添加标签
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Picture, ArrowLeft, ArrowRight, Star, StarFilled, Download,
  Share, More, Edit, FolderOpened, Delete, Camera, Timer,
  Aperture, Sunny, Plus
} from '@element-plus/icons-vue'
import TrainTicket from '@/components/TrainTicket.vue'
import type { Photo } from '@/types'

const route = useRoute()
const router = useRouter()

const photoId = computed(() => parseInt(route.params.id as string))
const photo = ref<Photo | null>(null)
const currentIndex = ref(0)
const totalPhotos = ref(20)
const isFavorite = ref(false)
const photoTags = ref<string[]>(['高铁', 'CRH380A', '上海'])

const inputTagVisible = ref(false)
const inputTagValue = ref('')
const tagInputRef = ref<HTMLInputElement>()

onMounted(() => {
  loadPhoto()
})

const loadPhoto = () => {
  // Mock photo data
  photo.value = {
    id: photoId.value,
    albumId: 1,
    title: 'CRH380A  动车组通过南京南站',
    description: '京沪高铁上的 CRH380A  高速动车组，以 300km/h 的速度飞驰而过。这张照片拍摄于南京南站附近，捕捉到了列车疾驰而过的瞬间。',
    url: '',
    thumbnailUrl: '',
    fileSize: 5242880,
    width: 5472,
    height: 3648,
    takenAt: '2024-03-10T14:30:00Z',
    location: '南京南站',
    trainNumber: 'G1234',
    createdAt: '2024-03-10T16:00:00Z',
    exif: {
      camera: 'Canon EOS R5',
      shutter: '1/1000s',
      aperture: 'f/5.6',
      iso: 'ISO 400'
    }
  } as Photo & { exif?: Record<string, string> }
}

const prevPhoto = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    // router.push(`/photos/${prevId}`)
  }
}

const nextPhoto = () => {
  if (currentIndex.value < totalPhotos.value - 1) {
    currentIndex.value++
    // router.push(`/photos/${nextId}`)
  }
}

const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  ElMessage.success(isFavorite.value ? '已添加到收藏' : '已取消收藏')
}

const downloadPhoto = () => {
  ElMessage.success('开始下载照片')
}

const sharePhoto = () => {
  ElMessage.success('链接已复制到剪贴板')
}

const handleMoreAction = (command: string) => {
  switch (command) {
    case 'edit':
      ElMessage.info('编辑功能开发中')
      break
    case 'move':
      ElMessage.info('移动功能开发中')
      break
    case 'delete':
      ElMessageBox.confirm('确定要删除这张照片吗？', '确认删除', {
        type: 'warning'
      }).then(() => {
        ElMessage.success('已删除')
        router.back()
      }).catch(() => {})
      break
  }
}

const showTagInput = () => {
  inputTagVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const addTag = () => {
  if (inputTagValue.value && !photoTags.value.includes(inputTagValue.value)) {
    photoTags.value.push(inputTagValue.value)
  }
  inputTagVisible.value = false
  inputTagValue.value = ''
}

const removeTag = (tag: string) => {
  photoTags.value = photoTags.value.filter(t => t !== tag)
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '未知'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
}
</script>

<style scoped>
.photo-detail-view {
  padding: 20px;
}

.photo-container {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  background: var(--bg-base);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--box-shadow-base);
  min-height: calc(100vh - 140px);
}

.image-section {
  background: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 40px;
}

.main-image {
  max-width: 100%;
  max-height: calc(100vh - 240px);
  object-fit: contain;
}

.image-error {
  color: #999;
  text-align: center;
}

.image-nav {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(0, 0, 0, 0.6);
  padding: 8px 16px;
  border-radius: 24px;
}

.photo-counter {
  color: #fff;
  font-size: 14px;
  min-width: 60px;
  text-align: center;
}

.info-section {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(100vh - 140px);
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.photo-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  flex: 1;
  padding-right: 16px;
}

.photo-actions {
  display: flex;
  gap: 4px;
}

.photo-description {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 24px;
}

.info-group {
  margin-bottom: 24px;
}

.info-group h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-regular);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-lighter);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-page);
  border-radius: 8px;
}

.info-item .el-icon {
  color: var(--primary-color);
  font-size: 20px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.photo-tag {
  cursor: pointer;
}

@media (max-width: 1024px) {
  .photo-container {
    grid-template-columns: 1fr;
  }
  
  .image-section {
    min-height: 400px;
  }
  
  .info-section {
    max-height: none;
  }
}
</style>
