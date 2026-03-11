<template>
  <div class="album-list-view page-container">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">相册管理</h1>
        <span class="album-count">共 {{ albumStore.total }} 个相册</span>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索相册..."
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>新建相册
        </el-button>
      </div>
    </div>

    <!-- Album Grid -->
    <div v-if="!albumStore.loading || albumStore.albums.length" class="album-grid">
      <el-card
        v-for="album in albumStore.albums"
        :key="album.id"
        class="album-card"
        shadow="hover"
        @click="viewAlbum(album.id)"
      >
        <div class="album-cover">
          <el-image 
            :src="album.coverUrl || defaultCover" 
            fit="cover"
            class="cover-image"
          >
            <template #error>
              <div class="cover-placeholder">
                <el-icon :size="48"><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <div class="album-badge">
            <el-icon><Picture /></el-icon>
            {{ album.photoCount }}
          </div>
          <el-tag
            v-if="!album.isPublic"
            size="small"
            type="warning"
            class="privacy-badge"
          >
            私密
          </el-tag>
        </div>
        
        <div class="album-info">
          <h3 class="album-title">{{ album.title }}</h3>
          <p class="album-desc">{{ album.description || '暂无描述' }}</p>
          <div class="album-meta">
            <span>{{ formatDate(album.createdAt) }}</span>
            <el-dropdown @command="handleAction($event, album)" @click.stop>
              <el-button text circle size="small">
                <el-icon><More /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">
                    <el-icon><Edit /></el-icon>编辑
                  </el-dropdown-item>
                  <el-dropdown-item command="upload">
                    <el-icon><Upload /></el-icon>上传照片
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete">
                    <el-icon><Delete /></el-icon>删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Empty State -->
    <el-empty v-else-if="!albumStore.loading" description="暂无相册">
      <el-button type="primary" @click="showCreateDialog = true">
        创建第一个相册
      </el-button>
    </el-empty>

    <!-- Pagination -->
    <div v-if="albumStore.total > pageSize" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="albumStore.total"
        :page-sizes="[12, 24, 36]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- Create Album Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建相册"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-form-item label="相册名称" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入相册名称" />
        </el-form-item>
        <el-form-item label="相册描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入相册描述（可选）"
          />
        </el-form-item>
        <el-form-item label="公开可见">
          <el-switch v-model="createForm.isPublic" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- Edit Album Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑相册"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-form-item label="相册名称" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入相册名称" />
        </el-form-item>
        <el-form-item label="相册描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入相册描述（可选）"
          />
        </el-form-item>
        <el-form-item label="公开可见">
          <el-switch v-model="editForm.isPublic" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="handleUpdate">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Plus, Picture, More, Edit, Upload, Delete } from '@element-plus/icons-vue'
import { useAlbumStore } from '@/stores/album'
import type { Album, AlbumForm } from '@/types'

const router = useRouter()
const albumStore = useAlbumStore()

const defaultCover = '/default-album-cover.jpg'
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(12)

// Dialog states
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const creating = ref(false)
const updating = ref(false)
const currentAlbum = ref<Album | null>(null)

// Form refs
const formRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

// Forms
const createForm = reactive<AlbumForm>({
  title: '',
  description: '',
  isPublic: true
})

const editForm = reactive<AlbumForm>({
  title: '',
  description: '',
  isPublic: true
})

const createRules: FormRules = {
  title: [
    { required: true, message: '请输入相册名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

// Mock data for demo
onMounted(async () => {
  await loadAlbums()
})

const loadAlbums = async () => {
  // In real app: await albumStore.fetchAlbums({ page: currentPage.value, size: pageSize.value })
  // For demo, populate with mock data
  albumStore.albums = [
    { id: 1, title: '高速铁路', description: '中国高速铁路精选照片', coverUrl: '', isPublic: true, photoCount: 56, ownerId: 1, createdAt: '2024-03-01T00:00:00Z', updatedAt: '2024-03-10T00:00:00Z' },
    { id: 2, title: '电力机车', description: '各种电力机车收藏', coverUrl: '', isPublic: true, photoCount: 128, ownerId: 1, createdAt: '2024-02-15T00:00:00Z', updatedAt: '2024-03-08T00:00:00Z' },
    { id: 3, title: '内燃机车', description: '经典内燃机车', coverUrl: '', isPublic: false, photoCount: 45, ownerId: 1, createdAt: '2024-01-20T00:00:00Z', updatedAt: '2024-03-05T00:00:00Z' },
    { id: 4, title: '蒸汽机车', description: '蒸汽时代', coverUrl: '', isPublic: true, photoCount: 32, ownerId: 1, createdAt: '2024-01-10T00:00:00Z', updatedAt: '2024-02-28T00:00:00Z' }
  ]
  albumStore.total = 4
}

const handleSearch = () => {
  currentPage.value = 1
  loadAlbums()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadAlbums()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadAlbums()
}

const viewAlbum = (id: number) => {
  router.push(`/albums/${id}`)
}

const handleCreate = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      creating.value = true
      await albumStore.createAlbum({ ...createForm })
      creating.value = false
      showCreateDialog.value = false
      formRef.value?.resetFields()
    }
  })
}

const handleAction = (command: string, album: Album) => {
  switch (command) {
    case 'edit':
      currentAlbum.value = album
      editForm.title = album.title
      editForm.description = album.description || ''
      editForm.isPublic = album.isPublic
      showEditDialog.value = true
      break
    case 'upload':
      router.push(`/upload?albumId=${album.id}`)
      break
    case 'delete':
      handleDelete(album)
      break
  }
}

const handleUpdate = async () => {
  if (!editFormRef.value || !currentAlbum.value) return
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      await albumStore.updateAlbum(currentAlbum.value!.id, { ...editForm })
      updating.value = false
      showEditDialog.value = false
    }
  })
}

const handleDelete = (album: Album) => {
  ElMessageBox.confirm(
    `确定要删除相册 "${album.title}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    await albumStore.deleteAlbum(album.id)
  }).catch(() => {})
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-lighter);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.album-count {
  color: var(--text-secondary);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.album-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.album-card {
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.album-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

:deep(.album-card .el-card__body) {
  padding: 0;
}

.album-cover {
  position: relative;
  aspect-ratio: 16/10;
  overflow: hidden;
  border-radius: 4px 4px 0 0;
}

.cover-image {
  width: 100%;
  height: 100%;
  transition: transform 0.5s;
}

.album-card:hover .cover-image {
  transform: scale(1.05);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0e0e0 0%, #f0f0f0 100%);
  color: #999;
}

.album-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  border-radius: 12px;
  font-size: 12px;
}

.privacy-badge {
  position: absolute;
  top: 8px;
  right: 8px;
}

.album-info {
  padding: 16px;
}

.album-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-placeholder);
}

.pagination-wrapper {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .header-right {
    width: 100%;
  }
  
  .header-right .el-input {
    flex: 1;
  }
}
</style>
