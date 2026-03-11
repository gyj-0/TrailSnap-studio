<template>
  <div class="dashboard-view page-container">
    <!-- Welcome Section -->
    <div class="welcome-section">
      <div class="welcome-info">
        <h1 class="welcome-title">
          欢迎回来，{{ authStore.user?.nickname || authStore.user?.username }}！
        </h1>
        <p class="welcome-desc">今天是 {{ today }}，祝您拍摄愉快 📷</p>
      </div>
      <div class="quick-actions">
        <el-button type="primary" size="large" @click="router.push('/albums')">
          <el-icon><Picture /></el-icon>
          浏览相册
        </el-button>
        <el-button size="large" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传照片
        </el-button>
      </div>
    </div>

    <!-- Statistics Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #ecf5ff; color: #409eff;">
            <el-icon :size="32"><Picture /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalAlbums }}</div>
            <div class="stat-label">相册总数</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f0f9eb; color: #67c23a;">
            <el-icon :size="32"><Camera /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalPhotos }}</div>
            <div class="stat-label">照片总数</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c;">
            <el-icon :size="32"><View /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalViews }}</div>
            <div class="stat-label">总浏览量</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fef0f0; color: #f56c6c;">
            <el-icon :size="32"><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.thisMonth }}</div>
            <div class="stat-label">本月新增</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activity & Quick Upload -->
    <el-row :gutter="20" class="content-row">
      <el-col :xs="24" :lg="16">
        <el-card class="recent-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>最近上传</span>
              <el-button text type="primary" @click="router.push('/albums')">
                查看全部
              </el-button>
            </div>
          </template>
          
          <div v-if="recentPhotos.length" class="photo-grid">
            <div 
              v-for="photo in recentPhotos" 
              :key="photo.id"
              class="photo-item"
              @click="viewPhoto(photo)"
            >
              <el-image 
                :src="photo.thumbnailUrl || photo.url" 
                fit="cover"
                class="photo-thumb"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div class="photo-overlay">
                <span class="photo-title">{{ photo.title }}</span>
                <span class="photo-date">{{ formatDate(photo.createdAt) }}</span>
              </div>
            </div>
          </div>
          
          <el-empty v-else description="暂无照片，快去上传第一张吧！" />
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="activity-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>最近动态</span>
            </div>
          </template>
          
          <el-timeline>
            <el-timeline-item
              v-for="activity in activities"
              :key="activity.id"
              :type="activity.type"
              :timestamp="activity.time"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <!-- Upload Dialog -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传照片"
      width="600px"
      destroy-on-close
    >
      <ImageUploader @success="onUploadSuccess" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Picture, Upload, Camera, View, Calendar } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import ImageUploader from '@/components/ImageUploader.vue'
import type { Photo } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const showUploadDialog = ref(false)

const today = computed(() => {
  const date = new Date()
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 星期${weekdays[date.getDay()]}`
})

// Mock stats data
const stats = ref({
  totalAlbums: 12,
  totalPhotos: 368,
  totalViews: 12580,
  thisMonth: 45
})

// Mock recent photos
const recentPhotos = ref<Photo[]>([
  { id: 1, albumId: 1, title: 'CRH380A  passing by', url: '', thumbnailUrl: '', fileSize: 0, width: 1920, height: 1080, takenAt: null, location: null, trainNumber: null, createdAt: '2024-03-10T10:30:00Z', description: null },
  { id: 2, albumId: 1, title: 'HXD3D at sunset', url: '', thumbnailUrl: '', fileSize: 0, width: 1920, height: 1080, takenAt: null, location: null, trainNumber: null, createdAt: '2024-03-09T15:20:00Z', description: null },
  { id: 3, albumId: 2, title: 'SS9G departure', url: '', thumbnailUrl: '', fileSize: 0, width: 1920, height: 1080, takenAt: null, location: null, trainNumber: null, createdAt: '2024-03-08T09:15:00Z', description: null },
  { id: 4, albumId: 2, title: 'CR400AF  in mist', url: '', thumbnailUrl: '', fileSize: 0, width: 1920, height: 1080, takenAt: null, location: null, trainNumber: null, createdAt: '2024-03-07T16:45:00Z', description: null },
  { id: 5, albumId: 3, title: 'DF4B freight train', url: '', thumbnailUrl: '', fileSize: 0, width: 1920, height: 1080, takenAt: null, location: null, trainNumber: null, createdAt: '2024-03-06T11:00:00Z', description: null },
  { id: 6, albumId: 3, title: 'CRH2A at station', url: '', thumbnailUrl: '', fileSize: 0, width: 1920, height: 1080, takenAt: null, location: null, trainNumber: null, createdAt: '2024-03-05T14:30:00Z', description: null }
])

// Mock activities
const activities = ref([
  { id: 1, content: '上传了新照片 "CRH380A passing by"', time: '2小时前', type: 'primary' },
  { id: 2, content: '创建了相册 "京沪高铁精选"', time: '昨天', type: 'success' },
  { id: 3, content: '更新了个人资料', time: '3天前', type: 'info' },
  { id: 4, content: '上传了 5 张照片到 "电力机车"', time: '1周前', type: 'warning' }
])

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const viewPhoto = (photo: Photo) => {
  router.push(`/photos/${photo.id}`)
}

const onUploadSuccess = () => {
  showUploadDialog.value = false
  // Refresh data
}
</script>

<style scoped>
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 14px;
  opacity: 0.9;
}

.quick-actions {
  display: flex;
  gap: 12px;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  margin-bottom: 20px;
}

:deep(.stat-card .el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.content-row {
  margin-top: 8px;
}

.recent-card,
.activity-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.photo-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.photo-thumb {
  width: 100%;
  height: 100%;
  transition: transform 0.3s;
}

.photo-item:hover .photo-thumb {
  transform: scale(1.05);
}

.photo-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px 8px 8px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: #fff;
}

.photo-title {
  display: block;
  font-size: 12px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-date {
  font-size: 11px;
  opacity: 0.8;
}

.image-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--border-lighter);
  color: var(--text-placeholder);
}

@media (max-width: 768px) {
  .welcome-section {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .photo-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
