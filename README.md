<div align="center">

# 🚂 TrailSnap Studio

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.122.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.4+-4FC08D.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-3178C6.svg)](https://www.typescriptlang.org/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-3.3.2-FF6F00.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**智能照片管理与票据识别系统**

[English](./README_EN.md) | 简体中文

</div>

---

## 📸 项目介绍

TrailSnap Studio 是一个基于前后端分离架构的智能照片管理与票据识别系统。专为铁路摄影爱好者、旅行者和票据收藏者设计，提供照片智能分类、OCR 票据识别、人脸聚类、地图轨迹展示等功能。

### ✨ 核心特性

| 功能 | 描述 |
|------|------|
| 📷 **智能照片管理** | 支持 EXIF 信息提取、GPS 定位、自动分类和标签 |
| 🎫 **票据识别** | 火车票、发票、收据的智能 OCR 识别与结构化提取 |
| 👤 **人脸识别** | 基于 InsightFace 的人脸检测、特征提取与智能聚类 |
| 🗺️ **地图轨迹** | 基于 GPS 数据的照片地图展示和轨迹回放 |
| 🚄 **铁路集成** | 铁路行程管理与照片关联 |
| 🔍 **全文检索** | 基于 OCR 文本的照片内容搜索 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        TrailSnap Studio                         │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Vue 3) │  Backend (FastAPI)  │  AI Service (Python)  │
│  ───────────────  │  ─────────────────  │  ───────────────────  │
│  • Vue 3.4        │  • FastAPI 0.122    │  • PaddleOCR 3.3.2    │
│  • TypeScript 5.3 │  • SQLAlchemy 2.0   │  • InsightFace        │
│  • Pinia 2.1      │  • PostgreSQL       │  • PyTorch 2.0        │
│  • Element Plus   │  • JWT Auth         │  • YOLO Detection     │
│  • Vite 5.0       │  • APScheduler      │  • GPU Acceleration   │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

#### 前端 (package/website)
- **框架**: Vue 3.4 + Composition API
- **语言**: TypeScript 5.3
- **构建**: Vite 5.0
- **状态管理**: Pinia 2.1
- **路由**: Vue Router 4.2
- **UI 组件**: Element Plus
- **HTTP 客户端**: Axios

#### 后端 (package/server)
- **语言**: Python 3.12+
- **Web 框架**: FastAPI 0.122.0
- **ASGI 服务器**: Uvicorn 0.38.0
- **ORM**: SQLAlchemy 2.0.44
- **数据库**: PostgreSQL 16
- **迁移工具**: Alembic 1.17.2
- **任务调度**: APScheduler
- **缓存**: Redis 7

#### AI 微服务 (package/ai)
- **OCR 引擎**: PaddleOCR 3.3.2
- **深度学习**: PaddlePaddle-GPU 3.2.0
- **人脸识别**: InsightFace
- **目标检测**: YOLO + PyTorch 2.0
- **图像处理**: OpenCV 4.9+, Pillow

---

## 🚀 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (GPU 支持，可选)

### 方式一：Docker Compose 一键启动（推荐）

```bash
# 克隆项目
git clone https://github.com/gyj-0/TrailSnap-studio.git
cd TrailSnap-studio

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库密码等

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | 用户界面 |
| 后端 API | http://localhost:8000 | REST API |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| AI 服务 | http://localhost:8001 | AI 推理接口 |

### 方式二：开发模式启动

#### 1. 启动基础设施

```bash
docker-compose up -d postgres redis
```

#### 2. 后端服务

```bash
cd package/server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn main:app --reload --port 8000
```

#### 3. AI 微服务

```bash
cd package/ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8001
```

#### 4. 前端服务

```bash
cd package/website
npm install
npm run dev
```

---

## 📁 项目结构

```
TrailSnap-studio/
├── 📦 package/
│   ├── 🖥️ server/              # FastAPI 后端服务
│   │   ├── app/
│   │   │   ├── api/v1/         # API 路由 (REST endpoints)
│   │   │   ├── core/           # 核心配置 (Config, Logger, Security)
│   │   │   ├── crud/           # 数据库 CRUD 操作
│   │   │   ├── db/             # 数据库模型与会话
│   │   │   ├── schemas/        # Pydantic 数据模型
│   │   │   ├── service/        # 业务逻辑服务
│   │   │   └── utils/          # 工具函数
│   │   ├── railway/            # 铁路相关功能模块
│   │   ├── yolo_ocr/           # OCR 与票据识别
│   │   └── main.py             # 应用入口 (端口 8000)
│   │
│   ├── 💻 website/             # Vue 3 前端应用
│   │   ├── src/
│   │   │   ├── api/            # 后端接口封装
│   │   │   ├── components/     # Vue 组件
│   │   │   ├── composables/    # 组合式函数 (Hooks)
│   │   │   ├── layouts/        # 页面布局
│   │   │   ├── router/         # 路由配置
│   │   │   ├── stores/         # Pinia 状态管理
│   │   │   ├── types/          # TypeScript 类型定义
│   │   │   └── views/          # 页面视图
│   │   └── package.json
│   │
│   └── 🤖 ai/                  # AI 微服务
│       ├── app/
│       │   ├── core/           # 配置与日志
│       │   ├── routers/        # API 路由
│       │   ├── services/       # AI 模型服务
│       │   │   ├── ocr_service.py      # OCR 服务
│       │   │   ├── face_service.py     # 人脸识别
│       │   │   ├── detection_service.py # 目标检测
│       │   │   └── model_manager.py    # 模型管理
│       │   └── utils/          # 工具函数
│       ├── models/             # 预训练模型存储
│       └── main.py             # 服务入口 (端口 8001)
│
├── 📚 doc/                     # 项目文档
│   ├── architecture.md         # 架构设计
│   ├── api.md                  # 后端 API 文档
│   ├── ai-api.md               # AI 服务接口
│   ├── deployment.md           # 部署指南
│   └── development.md          # 开发规范
│
├── 🐳 docker-compose.yml       # Docker 编排配置
├── 📄 README.md                # 项目说明
└── ⚙️ .env.example             # 环境变量模板
```

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [架构设计](./doc/architecture.md) | 系统架构、数据流、数据库设计 |
| [API 文档](./doc/api.md) | 后端 RESTful API 完整文档 |
| [AI 接口文档](./doc/ai-api.md) | OCR、人脸识别、目标检测接口 |
| [部署指南](./doc/deployment.md) | Docker/Kubernetes/裸机部署 |
| [开发规范](./doc/development.md) | Git 工作流、代码规范、测试规范 |

---

## 🔧 功能模块

### 照片管理
- [x] 照片上传（支持批量）
- [x] EXIF 信息提取与展示
- [x] GPS 定位与地图展示
- [x] 智能相册分类
- [x] 照片搜索（文件名、OCR 内容）
- [x] 缩略图生成

### AI 能力
- [x] 多语言 OCR 识别（中文、英文、日文等）
- [x] 火车票识别与结构化
- [x] 增值税发票识别
- [x] 通用票据识别
- [x] 人脸检测与识别
- [x] 人脸聚类
- [x] 目标检测

### 用户系统
- [x] 用户注册/登录
- [x] JWT 认证
- [x] 个人设置
- [x] 存储配额管理

---

## 🛣️ 路线图

- [ ] 移动端 App (React Native / Flutter)
- [ ] 视频内容分析
- [ ] 智能相册封面推荐
- [ ] 社交分享功能
- [ ] 多语言界面支持
- [ ] 云端同步备份

---

## 🤝 贡献指南

我们欢迎社区贡献！请参考以下步骤：

1. **Fork** 本仓库
2. 创建功能分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'feat: add some amazing feature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 创建 **Pull Request**

请参考 [开发规范](./doc/development.md) 了解代码规范。

---

## 📄 许可证

本项目采用 [MIT](./LICENSE) 许可证。

---

## 👨‍💻 作者

- **gyj-0** - [GitHub](https://github.com/gyj-0)

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR 引擎
- [InsightFace](https://github.com/deepinsight/insightface) - 人脸识别
- [Vue.js](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI 组件库

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**

[报告问题](https://github.com/gyj-0/TrailSnap-studio/issues) · [提交功能请求](https://github.com/gyj-0/TrailSnap-studio/issues) · [查看文档](./doc)

</div>
