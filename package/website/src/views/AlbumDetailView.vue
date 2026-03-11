<template>
  <div class="album-detail-view page-container">
    <!-- Album Header -->
    <div class="album-header">
      <div class="header-content">
        <div class="album-cover-large">
          <el-image 
            :src="album?.coverUrl || defaultCover" 
            fit="cover"
            class="cover-image-large"
          >
            <template #error>
              <div class="cover-placeholder-large">
                <el-icon :size="64"><Picture /></el-icon>
              </div>
            </template>
          </el-image>
        </div>
        
        <div class="album-details">
          <div class="album-title-row">
            <h1 class="album-title-large">{{ album?.title }}</h1>
            <el-tag v-if="!album?.isPublic" type="warning">私密</el-tag>
          </div>
          
          <p class="album-desc-large">{{ album?.description || '暂无描述' }}</p>
          
          <div class="album-stats-row">
            <div class="stat-item">
              <el-icon><Picture /></el-icon>
              <span>{{ album?.photoCount || 0 }} 张照片</span>
            </div>
            <div class="stat-item">
              <el-icon><Calendar /></el-icon>
              <span>创建于 {{ formatDate(album?.createdAt) }}</span>
            </div>
            <div class="stat-item">
              <el-icon><View /></el-icon>
              <span>1,234 次浏览</span>
            </div>
          </div>
          
          <div class="album-actions">
            <el-button type="primary" @click="showUpload = true">
              <el-icon><Upload /></el-icon>上传照片
            </el-button>
            <el-button @click="showEditDialog = true">
              <el-icon><Edit /></el-icon>编辑相册
            </el-button>
            <el-button @click="shareAlbum">
              <el-icon><Share /></el-icon>分享
            </el-button>
            <el-dropdown @command="handleMoreAction">
              <el-button>
                <el-icon><More /></el-icon>更多
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="download">
                    <el-icon><Download /></el-icon>下载全部
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete" style="color: #f56c6c;">
                    <el-icon><Delete /></el-icon>删除相册
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- Photo Grid -->
    <div class="photos-section">
      <div class="section-header">
        <h2>照片列表</h2>
        <div class="view-options">
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

      <div v-if="photos.length" :class="['photo-container', `view-${viewMode}`]">
        <div
          v-for="photo in photos"
          :key="photo.id"
          class="photo-item"
          @click="viewPhoto(photo)"
        >
          <div class="photo-wrapper">
            <el-image
              :src="photo.thumbnailUrl || photo.url"
              fit="cover"
              class="photo-image"
              lazy
            >
              <template #error>
                <div class="photo-error">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div class="photo-overlay">
              <span class="photo-title-overlay">{{ photo.title }}</span>
              <div class="photo-actions-overlay">
                <el-button text circle size="small" @click.stop="downloadPhoto(photo)">
                  <el-icon><Download /></el-icon>
                </el-button>
                <el-button text circle size="small" @click.stop="deletePhoto(photo)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
          
          <div v-if="viewMode === 'list'" class="photo-list-info">
            <h4>{{ photo.title }}</h4>
            <p>{{ photo.description || '暂无描述' }}</p>
            <span class="photo-date">{{ formatDate(photo.createdAt) }}</span>
          </div>
        </div>
      </div>

      <el-empty v-else description="暂无照片">
        <el-button type="primary" @click="showUpload = true">
          上传第一张照片
        </el-button>
      </el-empty>
    </div>

    <!-- Upload Dialog -->
    <el-dialog
      v-model="showUpload"
      title="上传照片"
      width="700px"
      destroy-on-close
    >
      <ImageUploader 
        :album-id="albumId"
        @success="onUploadSuccess" 
      />
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑相册"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="80px"
      >
        <el-form-item label="相册名称" prop="title">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="相册描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item label="公开可见">
          <el-switch v-model="editForm.isPublic" />
        </el-form-item>
        <el-form-item label="相册封面">
          <el-upload
            class="cover-uploader"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleCoverChange"
          >
            <img v-if="coverPreview" :src="coverPreview" class="cover-preview" />
            <div v-else class="cover-upload-trigger">
              <el-icon><Plus /></el-icon>
              <span>更换封面</span>
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveAlbum">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Picture, Calendar, View, Upload, Edit, Share, More,
  Download, Delete, Grid, List, Plus
} from '@element-plus/icons-vue'
import { useAlbumStore } from '@/stores/album'
import ImageUploader from '@/components/ImageUploader.vue'
import type { Album, Photo, AlbumForm } from '@/types'

const route = useRoute()
const router = useRouter()
const albumStore = useAlbumStore()

const albumId = computed(() => parseInt(route.params.id as string))
const defaultCover = '/default-album-cover.jpg'
const viewMode = ref<'grid' | 'list'>('grid')

const album = ref<Album | null>(null)
const photos = ref<Photo[]>([])

// Dialog states
const showUpload = ref(false)
const showEditDialog = ref(false)
const saving = ref(false)
const coverPreview = ref('')

const editFormRef = ref<FormInstance>()
const editForm = reactive<AlbumForm>({
  title: '',
  description: '',
  isPublic: true
})

const editRules: FormRules = {
  title: [{ required: true, message: '请输入相册名称', trigger: 'blur' }]
}

onMounted(async () => {
  await loadAlbum()
  loadPhotos()
})

const loadAlbum = async () => {
  // Mock album data
  album.value = {
    id: albumId.value,
    title: '高速铁路',
    description: '中国高速铁路精选照片集，记录了中国高铁的发展历程。',
    coverUrl: '',
    isPublic: true,
    photoCount: 56,
    ownerId: 1,
    createdAt: '2024-03-01T00:00:00Z',
    updatedAt: '2024-03-10T00:00:00Z'
  }
  
  editForm.title = album.value.title
  editForm.description = album.value.description || ''
  editForm.isPublic = album.value.isPublic
}

const loadPhotos = () => {
  // Mock photos
  photos.value = Array.from({ length: 12 }, (_, i) => ({
    id: i + 1,
    albumId: albumId.value,
    title: `照片 ${i + 1}`,
    description: `这是第 ${i + 1} 张照片的描述`,
    url: '',
    thumbnailUrl: '',
    fileSize: 1024 * 1024 * (2 + Math.random() * 3),
    width: 1920,
    height: 1080,
    takenAt: new Date(Date.now() - i * 86400000).toISOString(),
    location: i % 3 === 0 ? '北京南站' : i % 3 === 1 ? '上海虹桥' : '广州南站',
    trainNumber: `G${100 + i}`,
    createdAt: new Date(Date.now() - i * 86400000).toISOString()
  }))
}

const viewPhoto = (photo: Photo) => {
  router.push(`/photos/${photo.id}`)
}

const downloadPhoto = (photo: Photo) => {
  ElMessage.success(`开始下载: ${photo.title}`)
}

const deletePhoto = (photo: Photo) => {
  ElMessageBox.confirm(`确定要删除 "${photo.title}" 吗？`, '确认删除', {
    type: 'warning'
  }).then(() => {
    photos.value = photos.value.filter(p => p.id !== photo.id)
    ElMessage.success('已删除')
  }).catch(() => {})
}

const handleCoverChange = (file: { raw: File }) => {
  coverPreview.value = URL.createObjectURL(file.raw)
}

const saveAlbum = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      await albumStore.updateAlbum(albumId.value, { ...editForm })
      saving.value = false
      showEditDialog.value = false
      loadAlbum()
    }
  })
}

const handleMoreAction = (command: string) => {
  switch (command) {
    case 'download':
      ElMessage.success('开始打包下载')
      break
    case 'delete':
      ElMessageBox.confirm('确定要删除此相册吗？相册内的照片也会被删除。', '确认删除', {
        type: 'warning'
      }).then(async () => {
        await albumStore.deleteAlbum(albumId.value)
        router.push('/albums')
      }).catch(() => {})
      break
  }
}

const shareAlbum = () => {
  ElMessage.success('链接已复制到剪贴板')
}

const onUploadSuccess = () => {
  showUpload.value = false
  loadPhotos()
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.album-header {
  background: var(--bg-base);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--box-shadow-base);
}

.header-content {
  display: flex;
  gap: 24px;
}

.album-cover-large {
  width: 200px;
  height: 200px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.cover-image-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder-large {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0e0e0 0%, #f0f0f0 100%);
  color: #999;
}

.album-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.album-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.album-title-large {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.album-desc-large {
  color: var(--text-secondary);
  line-height: 1.6;
}

.album-stats-row {
  display: flex;
  gap: 24px;
  color: var(--text-secondary);
  font-size: 14px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.album-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
  padding-top: 12px;
}

.photos-section {
  background: var(--bg-base);
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--box-shadow-base);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 18px;
  font-weight: 500;
}

.view-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.view-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.view-list .photo-item {
  display: flex;
  gap: 16px;
  padding: 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.view-list .photo-item:hover {
  background: var(--border-extra-light);
}

.view-list .photo-wrapper {
  width: 120px;
  height: 80px;
}

.photo-wrapper {
  position: relative;
  aspect-ratio: 3/2;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.photo-image {
  width: 100%;
  height: 100%;
  transition: transform 0.3s;
}

.photo-wrapper:hover .photo-image {
  transform: scale(1.05);
}

.photo-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px 12px 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  display: flex;
  justify-content: space-between;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.photo-wrapper:hover .photo-overlay {
  opacity: 1;
}

.photo-title-overlay {
  color: #fff;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60%;
}

.photo-actions-overlay {
  display: flex;
  gap: 4px;
}

.photo-actions-overlay .el-button {
  color: #fff;
}

.photo-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--border-lighter);
  color: var(--text-placeholder);
}

.photo-list-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.photo-list-info h4 {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
}

.photo-list-info p {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.photo-list-info .photo-date {
  font-size: 12px;
  color: var(--text-placeholder);
}

.cover-uploader {
  border: 1px dashed var(--border-base);
  border-radius: 6px;
  width: 178px;
  height: 178px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.cover-uploader:hover {
  border-color: var(--primary-color);
}

.cover-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-upload-trigger {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  gap: 8px;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
  }
  
  .album-cover-large {
    width: 100%;
    height: 200px;
  }
  
  .album-actions {
    flex-wrap: wrap;
  }
  
  .view-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
