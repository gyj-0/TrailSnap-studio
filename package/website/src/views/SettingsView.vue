<template>
  <div class="settings-view page-container">
    <h1 class="page-title">系统设置</h1>
    
    <el-tabs tab-position="left" class="settings-tabs">
      <!-- Profile Settings -->
      <el-tab-pane label="个人资料" name="profile">
        <div class="settings-section">
          <h2>个人资料</h2>
          <el-form :model="profileForm" label-width="100px" class="settings-form">
            <el-form-item label="头像">
              <div class="avatar-section">
                <el-avatar :size="100" :src="profileForm.avatar" :icon="UserFilled" />
                <el-upload
                  action="#"
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="handleAvatarChange"
                >
                  <el-button text type="primary">更换头像</el-button>
                </el-upload>
              </div>
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="个人简介">
              <el-input
                v-model="profileForm.bio"
                type="textarea"
                rows="4"
                placeholder="介绍一下你自己..."
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingProfile" @click="saveProfile">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
      
      <!-- Security Settings -->
      <el-tab-pane label="账号安全" name="security">
        <div class="settings-section">
          <h2>修改密码</h2>
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
            class="settings-form"
          >
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="changingPassword" @click="changePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <h2>登录设备管理</h2>
          <div class="device-list">
            <div class="device-item active">
              <div class="device-info">
                <el-icon :size="24"><Computer /></el-icon>
                <div>
                  <div class="device-name">当前设备 - Chrome on Windows</div>
                  <div class="device-meta">北京 · 2024-03-10 14:30</div>
                </div>
              </div>
              <el-tag type="success">当前在线</el-tag>
            </div>
          </div>
        </div>
      </el-tab-pane>
      
      <!-- Preference Settings -->
      <el-tab-pane label="偏好设置" name="preferences">
        <div class="settings-section">
          <h2>界面设置</h2>
          <el-form label-width="200px" class="settings-form">
            <el-form-item label="主题模式">
              <el-radio-group v-model="preferences.theme">
                <el-radio-button label="light">
                  <el-icon><Sunny /></el-icon> 浅色
                </el-radio-button>
                <el-radio-button label="dark">
                  <el-icon><Moon /></el-icon> 深色
                </el-radio-button>
                <el-radio-button label="auto">
                  <el-icon><SemiSelect /></el-icon> 跟随系统
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="语言">
              <el-select v-model="preferences.language" style="width: 200px">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item label="每页显示数量">
              <el-select v-model="preferences.pageSize" style="width: 200px">
                <el-option label="12 条" :value="12" />
                <el-option label="24 条" :value="24" />
                <el-option label="48 条" :value="48" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <h2>通知设置</h2>
          <el-form label-width="200px" class="settings-form">
            <el-form-item label="邮件通知">
              <el-switch v-model="preferences.emailNotification" />
            </el-form-item>
            <el-form-item label="新评论通知">
              <el-switch v-model="preferences.commentNotification" />
            </el-form-item>
            <el-form-item label="系统更新通知">
              <el-switch v-model="preferences.updateNotification" />
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
      
      <!-- About -->
      <el-tab-pane label="关于" name="about">
        <div class="settings-section">
          <div class="about-section">
            <div class="logo-large">
              <el-icon :size="80" color="var(--primary-color)"><Train /></el-icon>
            </div>
            <h1 class="app-name">TrailSnap</h1>
            <p class="app-version">版本 {{ appVersion }}</p>
            <p class="app-description">
              TrailSnap 是一款专为铁路摄影爱好者打造的相册管理系统，
              帮助您轻松整理、管理和分享您的铁路摄影作品。
            </p>
            
            <el-divider />
            
            <div class="about-links">
              <el-link type="primary" :underline="false">
                <el-icon><Document /></el-icon> 使用文档
              </el-link>
              <el-link type="primary" :underline="false">
                <el-icon><Service /></el-icon> 联系支持
              </el-link>
              <el-link type="primary" :underline="false">
                <el-icon><Share /></el-icon> 推荐给朋友
              </el-link>
            </div>
            
            <p class="copyright">&copy; 2024 TrailSnap. All rights reserved.</p>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import {
  UserFilled, Computer, Sunny, Moon, SemiSelect, Train,
  Document, Service, Share
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const authStore = useAuthStore()
const appStore = useAppStore()
const appVersion = import.meta.env.VITE_APP_VERSION || '1.0.0'

// Profile form
const profileForm = reactive({
  nickname: authStore.user?.nickname || '',
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
  avatar: authStore.user?.avatar || '',
  bio: ''
})
const savingProfile = ref(false)

// Password form
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}
const changingPassword = ref(false)

// Preferences
const preferences = reactive({
  theme: 'light',
  language: 'zh-CN',
  pageSize: 24,
  emailNotification: true,
  commentNotification: true,
  updateNotification: false
})

const handleAvatarChange = (file: { raw: File }) => {
  profileForm.avatar = URL.createObjectURL(file.raw)
}

const saveProfile = async () => {
  savingProfile.value = true
  // Simulate API call
  await new Promise(resolve => setTimeout(resolve, 1000))
  savingProfile.value = false
  ElMessage.success('个人资料已更新')
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPassword.value = true
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      changingPassword.value = false
      ElMessage.success('密码修改成功')
      passwordFormRef.value?.resetFields()
    }
  })
}
</script>

<style scoped>
.settings-tabs {
  background: var(--bg-base);
  border-radius: 12px;
  padding: 24px;
  min-height: calc(100vh - 180px);
}

.settings-tabs :deep(.el-tabs__content) {
  padding-left: 24px;
}

.settings-section {
  max-width: 600px;
}

.settings-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.settings-form {
  margin-top: 20px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.device-list {
  margin-top: 16px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--border-lighter);
  border-radius: 8px;
  margin-bottom: 12px;
}

.device-item.active {
  background: var(--primary-light);
  border-color: var(--primary-color);
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-name {
  font-weight: 500;
  color: var(--text-primary);
}

.device-meta {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.about-section {
  text-align: center;
  padding: 40px 20px;
}

.logo-large {
  margin-bottom: 16px;
}

.app-name {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.app-version {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.app-description {
  font-size: 14px;
  color: var(--text-regular);
  line-height: 1.6;
  max-width: 400px;
  margin: 0 auto;
}

.about-links {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin: 24px 0;
}

.about-links .el-link {
  display: flex;
  align-items: center;
  gap: 4px;
}

.copyright {
  font-size: 12px;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .settings-tabs :deep(.el-tabs__nav-wrap) {
    margin-bottom: 20px;
  }
  
  .settings-tabs :deep(.el-tabs__content) {
    padding-left: 0;
  }
  
  .about-links {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
