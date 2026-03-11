# TrailSnap 开发规范

## 目录

1. [Git 工作流](#git-工作流)
2. [代码规范](#代码规范)
3. [API 设计规范](#api-设计规范)
4. [数据库规范](#数据库规范)
5. [测试规范](#测试规范)
6. [文档规范](#文档规范)

## Git 工作流

### 分支策略

采用 Git Flow 工作流：

```
main          生产分支，只接受来自 release 的合并
  ↑
develop       开发分支，日常开发基于此
  ↑
feature/*     功能分支，从 develop 创建
  ↑
release/*     发布分支，从 develop 创建
  ↑
hotfix/*      热修复分支，从 main 创建
```

### 分支命名

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| 功能 | `feature/功能描述` | `feature/user-authentication` |
| 修复 | `fix/问题描述` | `fix/login-error` |
| 发布 | `release/版本号` | `release/v1.2.0` |
| 热修 | `hotfix/问题描述` | `hotfix/security-patch` |

### Commit 规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖更新 |

#### 示例

```bash
# 新功能
feat(auth): add JWT token refresh mechanism

# Bug 修复
fix(api): resolve photo upload timeout issue

# 文档
docs(readme): update installation instructions

# 性能优化
perf(ocr): optimize image preprocessing pipeline
```

### 提交检查清单

- [ ] 代码自测通过
- [ ] 单元测试通过
- [ ] 无控制台日志/debug 代码
- [ ] 提交信息符合规范
- [ ] 相关文档已更新

## 代码规范

### Python 规范（后端/AI）

#### 代码风格

- 遵循 PEP 8
- 使用 Black 格式化（行宽 100）
- 使用 isort 排序导入
- 类型注解必须完整

#### 项目配置

```ini
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
```

#### 代码示例

```python
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class UserCreate(BaseModel):
    """用户创建模型"""
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    created_at: str


async def create_user(user_data: UserCreate) -> UserResponse:
    """创建新用户
    
    Args:
        user_data: 用户创建数据
        
    Returns:
        创建的用户信息
        
    Raises:
        HTTPException: 当用户名已存在时
    """
    # 检查用户名是否已存在
    if await User.exists(username=user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # 创建用户
    user = await User.create(**user_data.dict())
    
    return UserResponse.from_orm(user)
```

#### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写 + 下划线 | `user_service.py` |
| 类 | 大驼峰 | `UserService` |
| 函数 | 小写 + 下划线 | `create_user` |
| 常量 | 大写 + 下划线 | `MAX_UPLOAD_SIZE` |
| 变量 | 小写 + 下划线 | `user_name` |
| 私有 | 下划线前缀 | `_internal_method` |

### TypeScript/Vue 规范（前端）

#### 代码风格

- 使用 ESLint + Prettier
- 单引号
- 无分号
- 缩进 2 空格

#### 项目配置

```javascript
// .eslintrc.cjs
module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended',
    '@vue/typescript/recommended',
    'plugin:prettier/recommended',
  ],
  parserOptions: {
    ecmaVersion: 2022,
  },
  rules: {
    'vue/multi-word-component-names': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
  },
}
```

#### Vue 组件规范

```vue
<template>
  <div class="user-card">
    <img :src="user.avatar" :alt="user.name" class="avatar" />
    <div class="info">
      <h3 class="name">{{ user.name }}</h3>
      <p class="email">{{ user.email }}</p>
    </div>
    <slot name="actions" :user="user" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { User } from '@/types'

interface Props {
  user: User
  showEmail?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showEmail: true,
})

const emit = defineEmits<{
  (e: 'select', user: User): void
}>()

const displayName = computed(() => {
  return props.user.name || props.user.email.split('@')[0]
})
</script>

<style scoped>
.user-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}
</style>
```

#### 组合式函数规范

```typescript
// composables/useUser.ts
import { ref, computed } from 'vue'
import { getUser, updateUser } from '@/api/user'
import type { User } from '@/types'

export function useUser(userId: string) {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const isLoaded = computed(() => user.value !== null)

  async function fetchUser() {
    loading.value = true
    error.value = null
    try {
      user.value = await getUser(userId)
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  async function saveUser(data: Partial<User>) {
    if (!user.value) return
    await updateUser(userId, data)
    await fetchUser()
  }

  return {
    user,
    loading,
    error,
    isLoaded,
    fetchUser,
    saveUser,
  }
}
```

## API 设计规范

### RESTful 设计原则

1. **资源命名**：使用名词复数
   - ✅ `/users`, `/photos`
   - ❌ `/getUsers`, `/photo/list`

2. **HTTP 方法**：
   - `GET` - 获取资源
   - `POST` - 创建资源
   - `PUT` - 全量更新
   - `PATCH` - 部分更新
   - `DELETE` - 删除资源

3. **状态码**：
   - `200 OK` - 成功
   - `201 Created` - 创建成功
   - `204 No Content` - 删除成功
   - `400 Bad Request` - 请求参数错误
   - `401 Unauthorized` - 未认证
   - `403 Forbidden` - 无权限
   - `404 Not Found` - 资源不存在
   - `422 Unprocessable Entity` - 验证错误
   - `429 Too Many Requests` - 请求过于频繁
   - `500 Internal Server Error` - 服务器错误

### 响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

### 错误响应

```json
{
  "code": 400,
  "message": "Validation failed",
  "detail": {
    "field": "email",
    "error": "Invalid email format"
  }
}
```

### 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

## 数据库规范

### 命名规范

- 表名：小写 + 下划线，复数形式
  - `users`, `photo_albums`
- 字段名：小写 + 下划线
  - `created_at`, `user_id`
- 索引名：`idx_表名_字段名`
  - `idx_users_email`
- 外键名：`fk_表名_关联表名`
  - `fk_photos_album_id`

### 字段规范

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 软删除标记 |
| created_by | BIGINT | 创建者 ID |
| updated_by | BIGINT | 更新者 ID |

### 索引规范

- 主键、外键自动创建索引
- 查询频繁的字段添加索引
- 单表索引不超过 5 个
- 复合索引字段数不超过 3 个

### 模型定义示例

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Photo(Base):
    """照片模型"""
    __tablename__ = "photos"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    album_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("albums.id"), nullable=True, index=True
    )
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    width: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # EXIF 信息
    taken_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # AI 识别结果
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    face_count: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # 状态
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="photos")
    album: Mapped[Optional["Album"]] = relationship("Album", back_populates="photos")
```

## 测试规范

### 测试结构

```
tests/
├── unit/              # 单元测试
│   ├── test_models.py
│   └── test_services.py
├── integration/       # 集成测试
│   └── test_api.py
├── e2e/              # 端到端测试
│   └── test_upload.py
├── fixtures/         # 测试数据
│   └── photos/
└── conftest.py       # pytest 配置
```

### 单元测试示例（Python）

```python
import pytest
from unittest.mock import AsyncMock, patch

from app.crud.user import create_user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_create_user_success(db_session):
    """测试成功创建用户"""
    # 准备
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    # 执行
    user = await create_user(db_session, user_data)
    
    # 断言
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.id is not None


@pytest.mark.asyncio
async def test_create_user_duplicate_username(db_session):
    """测试重复用户名"""
    # 准备
    user_data = UserCreate(
        username="existing",
        email="test@example.com",
        password="SecurePass123!"
    )
    await create_user(db_session, user_data)
    
    # 执行 & 断言
    with pytest.raises(DuplicateError):
        await create_user(db_session, user_data)
```

### 组件测试示例（Vue）

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UserCard from '@/components/UserCard.vue'

describe('UserCard', () => {
  const mockUser = {
    id: 1,
    name: 'Test User',
    email: 'test@example.com',
    avatar: 'https://example.com/avatar.jpg',
  }

  it('renders user name correctly', () => {
    const wrapper = mount(UserCard, {
      props: { user: mockUser },
    })
    expect(wrapper.text()).toContain('Test User')
  })

  it('emits select event when clicked', async () => {
    const wrapper = mount(UserCard, {
      props: { user: mockUser },
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')[0]).toEqual([mockUser])
  })
})
```

### 测试覆盖率要求

| 层级 | 覆盖率 |
|------|--------|
| 单元测试 | ≥ 80% |
| 集成测试 | ≥ 60% |
| 端到端 | 核心流程 |

## 文档规范

### 代码文档

- 所有公共 API 必须有文档字符串
- 复杂逻辑需要注释说明
- 使用类型注解

### API 文档

使用 OpenAPI/Swagger 自动生成，关键接口补充说明：

```python
@router.post(
    "/upload",
    summary="上传照片",
    description="""
    上传单张或多张照片到系统。
    
    支持格式: JPG, PNG, WebP, HEIC
    单文件大小限制: 50MB
    
    上传后会自动进行:
    - EXIF 信息提取
    - 缩略图生成
    - OCR 文字识别
    - 人脸检测
    """,
    response_model=PhotoUploadResponse,
    responses={
        413: {"description": "文件过大"},
        415: {"description": "不支持的文件格式"},
    },
)
async def upload_photo(
    files: List[UploadFile] = File(..., description="照片文件列表"),
    album_id: Optional[int] = Form(None, description="相册 ID"),
):
    ...
```

### 更新日志

使用 Keep a Changelog 格式：

```markdown
## [1.2.0] - 2024-01-15

### Added
- 新增人脸识别功能
- 支持 HEIC 格式图片

### Changed
- 优化 OCR 识别速度（提升 40%）

### Fixed
- 修复上传大文件时的内存问题

### Security
- 升级依赖包修复安全漏洞
```

## 审查检查清单

### 代码审查

- [ ] 代码符合规范（Black/ESLint/Prettier）
- [ ] 类型注解完整
- [ ] 单元测试覆盖
- [ ] 无硬编码敏感信息
- [ ] 错误处理完善
- [ ] 日志记录适当
- [ ] 性能考虑（N+1 查询等）

### 安全审查

- [ ] 输入验证
- [ ] SQL 注入防护
- [ ] XSS 防护
- [ ] CSRF 防护
- [ ] 敏感数据加密
- [ ] 权限检查
- [ ] 依赖漏洞扫描
