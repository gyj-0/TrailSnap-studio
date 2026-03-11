<template>
  <div class="image-uploader">
    <!-- Upload Area -->
    <el-upload
      ref="uploadRef"
      drag
      action="#"
      :auto-upload="false"
      :show-file-list="false"
      :multiple="true"
      accept="image/*"
      :on-change="handleFileChange"
      :on-exceed="handleExceed"
      class="upload-area"
    >
      <el-icon class="upload-icon"><Upload /></el-icon>
      <div class="upload-text">
        <p>拖拽文件到此处，或 <em>点击上传</em></p>
        <p class="upload-hint">支持 JPG、PNG、WebP 格式，单张最大 10MB</p>
      </div>
    </el-upload>

    <!-- File List -->
    <div v-if="fileList.length" class="file-list">
      <div class="list-header">
        <span>已选择 {{ fileList.length }} 个文件</span>
        <el-button text type="danger" @click="clearAll">清空全部</el-button>
      </div>
      
      <div class="file-items">
        <div
          v-for="(file, index) in fileList"
          :key="file.uid"
          class="file-item"
        >
          <div class="file-preview">
            <el-image
              :src="file.preview"
              fit="cover"
              class="preview-image"
            />
          </div>
          
          <div class="file-info">
            <div class="file-name">{{ file.name }}</div>
            <div class="file-meta">
              <span>{{ formatSize(file.size) }}</span>
              <span>{{ file.width }}×{{ file.height }}</span>
            </div>
            
            <div class="file-form">
              <el-input
                v-model="file.data.title"
                placeholder="照片标题"
                size="small"
              />
              <el-input
                v-model="file.data.description"
                placeholder="描述（可选）"
                size="small"
                type="textarea"
                :rows="2"
              />
            </div>
            
            <div v-if="file.status === 'uploading'" class="progress-bar">
              <el-progress
                :percentage="file.progress"
                :status="file.progress === 100 ? 'success' : undefined"
                :stroke-width="4"
              />
            </div>
          </div>
          
          <div class="file-actions">
            <el-button
              text
              circle
              size="small"
              type="danger"
              :disabled="file.status === 'uploading'"
              @click="removeFile(index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Actions -->
    <div v-if="fileList.length" class="upload-actions">
      <el-checkbox v-model="applyToAll">
        统一设置拍摄信息
      </el-checkbox>
      
      <div v-if="applyToAll" class="common-fields">
        <el-input v-model="commonData.trainNumber" placeholder="车次号" />
        <el-input v-model="commonData.location" placeholder="拍摄地点" />
        <el-date-picker
          v-model="commonData.takenAt"
          type="datetime"
          placeholder="拍摄时间"
          style="width: 100%"
        />
      </div>
      
      <div class="action-buttons">
        <el-button @click="$emit('cancel')">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="!canUpload"
          @click="startUpload"
        >
          {{ uploading ? `上传中 (${completedCount}/${fileList.length})` : '开始上传' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Delete } from '@element-plus/icons-vue'
import { photoApi } from '@/api/photo'

interface UploadFile {
  uid: number
  name: string
  size: number
  raw: File
  preview: string
  width: number
  height: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  data: {
    title: string
    description: string
    trainNumber: string
    location: string
    takenAt: string
  }
}

interface Props {
  albumId?: number
  maxSize?: number // MB
}

const props = withDefaults(defineProps<Props>(), {
  albumId: undefined,
  maxSize: 10
})

const emit = defineEmits<{
  success: []
  cancel: []
}>()

const uploadRef = ref()
const fileList = ref<UploadFile[]>([])
const uploading = ref(false)
const applyToAll = ref(false)

const commonData = reactive({
  trainNumber: '',
  location: '',
  takenAt: ''
})

const canUpload = computed(() => 
  fileList.value.some(f => f.status === 'pending')
)

const completedCount = computed(() =>
  fileList.value.filter(f => f.status === 'success').length
)

const handleFileChange = async (uploadFile: { raw: File }) => {
  const file = uploadFile.raw
  
  // Validate file size
  if (file.size > props.maxSize * 1024 * 1024) {
    ElMessage.error(`文件 ${file.name} 超过 ${props.maxSize}MB 限制`)
    return
  }
  
  // Validate file type
  if (!file.type.startsWith('image/')) {
    ElMessage.error(`文件 ${file.name} 不是有效的图片`)
    return
  }
  
  // Get image dimensions
  const img = new Image()
  img.src = URL.createObjectURL(file)
  await new Promise<void>((resolve) => {
    img.onload = () => {
      resolve()
    }
  })
  
  const uploadFileData: UploadFile = {
    uid: Date.now() + Math.random(),
    name: file.name,
    size: file.size,
    raw: file,
    preview: img.src,
    width: img.naturalWidth,
    height: img.naturalHeight,
    status: 'pending',
    progress: 0,
    data: {
      title: file.name.replace(/\.[^/.]+$/, ''),
      description: '',
      trainNumber: '',
      location: '',
      takenAt: ''
    }
  }
  
  fileList.value.push(uploadFileData)
}

const handleExceed = () => {
  ElMessage.warning('单次最多上传 50 张图片')
}

const removeFile = (index: number) => {
  URL.revokeObjectURL(fileList.value[index].preview)
  fileList.value.splice(index, 1)
}

const clearAll = () => {
  fileList.value.forEach(f => URL.revokeObjectURL(f.preview))
  fileList.value = []
}

const formatSize = (bytes: number) => {
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}

const startUpload = async () => {
  if (!props.albumId) {
    ElMessage.error('请先选择相册')
    return
  }
  
  uploading.value = true
  
  for (const file of fileList.value) {
    if (file.status !== 'pending') continue
    
    file.status = 'uploading'
    
    // Apply common fields if enabled
    if (applyToAll.value) {
      if (commonData.trainNumber) file.data.trainNumber = commonData.trainNumber
      if (commonData.location) file.data.location = commonData.location
      if (commonData.takenAt) file.data.takenAt = commonData.takenAt
    }
    
    try {
      await photoApi.uploadPhoto(
        props.albumId,
        file.raw,
        (progress) => {
          file.progress = progress.percentage
        }
      )
      file.status = 'success'
      file.progress = 100
    } catch (error) {
      file.status = 'error'
      ElMessage.error(`${file.name} 上传失败`)
    }
  }
  
  uploading.value = false
  
  if (completedCount.value === fileList.value.length) {
    ElMessage.success('所有文件上传成功')
    emit('success')
    clearAll()
  }
}
</script>

<style scoped>
.image-uploader {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px 20px;
  background: var(--bg-page);
  border: 2px dashed var(--border-base);
  transition: border-color 0.3s;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
}

.upload-icon {
  font-size: 48px;
  color: var(--text-placeholder);
  margin-bottom: 16px;
}

.upload-text {
  color: var(--text-regular);
}

.upload-text em {
  color: var(--primary-color);
  font-style: normal;
  cursor: pointer;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.file-list {
  margin-top: 20px;
  border: 1px solid var(--border-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-page);
  border-bottom: 1px solid var(--border-lighter);
  font-size: 14px;
  color: var(--text-regular);
}

.file-items {
  max-height: 400px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid var(--border-lighter);
  transition: background-color 0.3s;
}

.file-item:hover {
  background: var(--bg-page);
}

.file-item:last-child {
  border-bottom: none;
}

.file-preview {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.file-meta span {
  margin-right: 12px;
}

.file-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-bar {
  margin-top: 8px;
}

.file-actions {
  display: flex;
  align-items: flex-start;
}

.upload-actions {
  margin-top: 20px;
  padding: 20px;
  background: var(--bg-page);
  border-radius: 8px;
}

.common-fields {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 12px;
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .file-item {
    flex-direction: column;
  }
  
  .file-preview {
    width: 100%;
    height: 150px;
  }
  
  .common-fields {
    grid-template-columns: 1fr;
  }
}
</style>
