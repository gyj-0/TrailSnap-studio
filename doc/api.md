# TrailSnap API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证方式

所有需要认证的接口需在请求头中携带 JWT Token：

```http
Authorization: Bearer <access_token>
```

## 通用响应格式

### 成功响应

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
  "message": "错误描述",
  "detail": { }
}
```

### 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

## 认证模块

### 1. 用户注册

**POST** `/auth/register`

#### 请求参数

```json
{
  "username": "string",     // 用户名，3-32字符，必填
  "email": "string",        // 邮箱，必填
  "password": "string",     // 密码，8-128字符，必填
  "full_name": "string"     // 真实姓名，可选
}
```

#### 响应示例

```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

### 2. 用户登录

**POST** `/auth/login`

#### 请求参数

```json
{
  "username": "string",     // 用户名或邮箱
  "password": "string"
}
```

#### 响应示例

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com"
    }
  }
}
```

### 3. 刷新 Token

**POST** `/auth/refresh`

#### 请求头

```http
Authorization: Bearer <refresh_token>
```

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

### 4. 登出

**POST** `/auth/logout`

需要认证。

#### 响应示例

```json
{
  "code": 200,
  "message": "登出成功"
}
```

## 用户模块

### 1. 获取当前用户信息

**GET** `/users/me`

需要认证。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "avatar": "https://...",
    "storage_used": 1073741824,
    "storage_quota": 10737418240,
    "created_at": "2024-01-15T08:30:00Z",
    "last_login": "2024-01-20T10:15:00Z"
  }
}
```

### 2. 更新用户信息

**PUT** `/users/me`

需要认证。

#### 请求参数

```json
{
  "full_name": "string",
  "avatar": "string"
}
```

### 3. 修改密码

**PUT** `/users/me/password`

需要认证。

#### 请求参数

```json
{
  "old_password": "string",
  "new_password": "string"
}
```

## 相册模块

### 1. 获取相册列表

**GET** `/albums`

需要认证。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| page_size | int | 每页数量，默认 20 |
| sort | string | 排序字段: `created_at`, `updated_at`, `name` |
| order | string | 排序方向: `asc`, `desc` |
| keyword | string | 搜索关键词 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "2024 春节旅行",
        "description": "云南之旅",
        "cover_photo": "https://...",
        "photo_count": 128,
        "created_at": "2024-02-10T08:00:00Z",
        "updated_at": "2024-02-15T18:30:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

### 2. 创建相册

**POST** `/albums`

需要认证。

#### 请求参数

```json
{
  "name": "string",         // 相册名称，必填，1-100字符
  "description": "string",  // 描述，可选
  "is_public": false        // 是否公开，默认 false
}
```

#### 响应示例

```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "id": 1,
    "name": "2024 春节旅行",
    "description": "云南之旅",
    "is_public": false,
    "photo_count": 0,
    "created_at": "2024-02-10T08:00:00Z"
  }
}
```

### 3. 获取相册详情

**GET** `/albums/{album_id}`

需要认证。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "2024 春节旅行",
    "description": "云南之旅",
    "cover_photo": "https://...",
    "photo_count": 128,
    "is_public": false,
    "created_at": "2024-02-10T08:00:00Z",
    "updated_at": "2024-02-15T18:30:00Z"
  }
}
```

### 4. 更新相册

**PUT** `/albums/{album_id}`

需要认证，仅相册所有者可操作。

#### 请求参数

```json
{
  "name": "string",
  "description": "string",
  "is_public": false
}
```

### 5. 删除相册

**DELETE** `/albums/{album_id}`

需要认证，仅相册所有者可操作。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| delete_photos | bool | 是否同时删除照片，默认 false |

## 照片模块

### 1. 获取照片列表

**GET** `/photos`

需要认证。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| album_id | int | 相册 ID |
| page | int | 页码，默认 1 |
| page_size | int | 每页数量，默认 20 |
| sort | string | 排序: `created_at`, `taken_at`, `file_size` |
| order | string | 排序方向: `asc`, `desc` |
| keyword | string | 搜索关键词（搜索 OCR 文本、文件名） |
| start_date | string | 开始日期 (YYYY-MM-DD) |
| end_date | string | 结束日期 (YYYY-MM-DD) |
| has_location | bool | 是否有 GPS 信息 |
| has_faces | bool | 是否有人脸 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "album_id": 1,
        "filename": "IMG_001.jpg",
        "original_url": "https://...",
        "thumbnail_url": "https://...",
        "width": 4032,
        "height": 3024,
        "file_size": 5242880,
        "taken_at": "2024-02-10T09:30:00Z",
        "location": {
          "latitude": 24.88,
          "longitude": 102.83,
          "address": "云南省昆明市"
        },
        "exif": {
          "camera": "iPhone 15 Pro",
          "lens": "iPhone 15 Pro back triple camera 6.86mm f/1.78",
          "iso": 100,
          "aperture": "f/1.78",
          "shutter_speed": "1/120s"
        },
        "ocr_text": "昆明站...",
        "face_count": 2,
        "created_at": "2024-02-10T10:00:00Z"
      }
    ],
    "total": 128,
    "page": 1,
    "page_size": 20,
    "pages": 7
  }
}
```

### 2. 上传照片

**POST** `/photos/upload`

需要认证，支持单文件或多文件上传。

#### 请求参数

Content-Type: `multipart/form-data`

| 参数 | 类型 | 说明 |
|------|------|------|
| files | File[] | 照片文件，支持 jpg/jpeg/png/gif/webp |
| album_id | int | 相册 ID，可选 |

#### 响应示例

```json
{
  "code": 201,
  "message": "上传成功",
  "data": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "photos": [
      {
        "id": 1,
        "filename": "IMG_001.jpg",
        "thumbnail_url": "https://...",
        "status": "success"
      }
    ]
  }
}
```

### 3. 获取照片详情

**GET** `/photos/{photo_id}`

需要认证。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "album_id": 1,
    "filename": "IMG_001.jpg",
    "original_url": "https://...",
    "thumbnail_url": "https://...",
    "preview_url": "https://...",
    "width": 4032,
    "height": 3024,
    "file_size": 5242880,
    "mime_type": "image/jpeg",
    "taken_at": "2024-02-10T09:30:00Z",
    "location": {
      "latitude": 24.88,
      "longitude": 102.83,
      "address": "云南省昆明市官渡区"
    },
    "exif": { ... },
    "ocr_result": {
      "text": "昆明站...",
      "regions": [
        {
          "text": "昆明站",
          "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
          "confidence": 0.98
        }
      ]
    },
    "faces": [
      {
        "id": 1,
        "bbox": [x, y, w, h],
        "embedding_id": "uuid",
        "person_name": "张三"
      }
    ],
    "created_at": "2024-02-10T10:00:00Z"
  }
}
```

### 4. 更新照片信息

**PUT** `/photos/{photo_id}`

需要认证。

#### 请求参数

```json
{
  "album_id": 1,
  "description": " string"
}
```

### 5. 删除照片

**DELETE** `/photos/{photo_id}`

需要认证。

### 6. 批量删除照片

**DELETE** `/photos/batch`

需要认证。

#### 请求参数

```json
{
  "photo_ids": [1, 2, 3]
}
```

### 7. 获取照片时间线

**GET** `/photos/timeline`

按时间聚合的照片统计，用于时间轴展示。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| group_by | string | 分组方式: `day`, `month`, `year`，默认 month |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "timeline": [
      {
        "date": "2024-02",
        "count": 128,
        "photos": [
          {
            "id": 1,
            "thumbnail_url": "https://..."
          }
        ]
      }
    ]
  }
}
```

## 地图模块

### 1. 获取照片地理分布

**GET** `/map/clusters`

需要认证。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| bbox | string | 地图边界框，格式: `minLat,minLng,maxLat,maxLng` |
| zoom | int | 地图缩放级别 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "clusters": [
      {
        "id": "cluster_1",
        "latitude": 24.88,
        "longitude": 102.83,
        "count": 15,
        "thumbnail": "https://..."
      }
    ],
    "points": [
      {
        "id": 1,
        "latitude": 24.88,
        "longitude": 102.83,
        "thumbnail": "https://..."
      }
    ]
  }
}
```

### 2. 获取位置搜索建议

**GET** `/map/geocode`

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词 |

## 票据模块

### 1. 识别票据

**POST** `/tickets/recognize`

需要认证，支持图片上传或 URL。

#### 请求参数

Content-Type: `multipart/form-data`

| 参数 | 类型 | 说明 |
|------|------|------|
| file | File | 票据图片 |
| type | string | 票据类型: `auto`, `train`, `invoice`, `receipt` |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "type": "train_ticket",
    "confidence": 0.95,
    "fields": {
      "ticket_no": "G123456",
      "departure": "北京南",
      "arrival": "上海虹桥",
      "date": "2024-02-10",
      "time": "08:00",
      "seat": "12车 3A号",
      "price": 553.5,
      "passenger": "张三",
      "id_card": "110101********1234"
    },
    "raw_text": "..."
  }
}
```

### 2. 获取票据列表

**GET** `/tickets`

需要认证。

### 3. 关联票据与照片

**POST** `/tickets/{ticket_id}/link`

#### 请求参数

```json
{
  "photo_id": 1
}
```

## 系统模块

### 1. 健康检查

**GET** `/health`

无需认证。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "services": {
      "database": "connected",
      "redis": "connected",
      "ai_service": "connected"
    },
    "timestamp": "2024-01-20T10:30:00Z"
  }
}
```

### 2. 获取系统信息

**GET** `/system/info`

需要认证（管理员）。

### 3. 获取存储统计

**GET** `/system/stats`

需要认证。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_photos": 1024,
    "total_albums": 10,
    "total_storage": 10737418240,
    "used_storage": 5368709120,
    "photo_by_month": [
      {
        "month": "2024-01",
        "count": 256,
        "size": 1342177280
      }
    ]
  }
}
```

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证错误 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 限流策略

- 普通接口: 100 次/分钟
- 上传接口: 20 次/分钟
- 登录接口: 5 次/分钟
