# TrailSnap

TrailSnap 是一个基于前后端分离架构的智能照片管理与票据识别系统。

## 项目架构

```
TrailSnap/
├── package/
│   ├── server/          # FastAPI 后端服务 (端口 8000)
│   ├── website/         # Vue 3 前端应用
│   └── ai/              # AI 微服务 (端口 8001)
├── doc/                 # 项目文档
├── docker-compose.yml   # 完整服务编排
└── README.md
```

## 技术栈

### 后端 (package/server)
- **Python**: 3.12+
- **Web 框架**: FastAPI 0.122.0
- **ASGI 服务器**: Uvicorn 0.38.0
- **ORM**: SQLAlchemy 2.0.44
- **数据库迁移**: Alembic 1.17.2
- **数据库**: PostgreSQL
- **任务调度**: APScheduler

### 前端 (package/website)
- **框架**: Vue 3.4+
- **语言**: TypeScript 5.3+
- **构建工具**: Vite 5.0+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **UI 组件**: Element Plus

### AI 微服务 (package/ai)
- **OCR**: PaddleOCR 3.3.2
- **深度学习框架**: PaddlePaddle-GPU 3.2.0
- **视觉处理**: OpenCV 4.9+
- **人脸识别**: InsightFace
- **目标检测**: YOLO / PyTorch

## 快速开始

### 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+ (前端开发)
- Python 3.12+ (后端开发)
- NVIDIA Docker (GPU 支持，可选)

### 使用 Docker Compose 启动

```bash
# 克隆项目
cd TrailSnap

# 复制环境变量模板
cp package/server/.env.example package/server/.env
cp package/ai/.env.example package/ai/.env

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

访问地址：
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- AI 服务: http://localhost:8001
- API 文档: http://localhost:8000/docs

### 开发模式启动

#### 1. 启动基础设施
```bash
docker-compose up -d postgres redis
```

#### 2. 后端开发
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

#### 3. AI 微服务开发
```bash
cd package/ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8001
```

#### 4. 前端开发
```bash
cd package/website
npm install
npm run dev
```

## 项目文档

详细文档请查看 `doc/` 目录：

- [架构设计](./doc/architecture.md)
- [API 接口文档](./doc/api.md)
- [AI 服务接口](./doc/ai-api.md)
- [部署指南](./doc/deployment.md)
- [开发规范](./doc/development.md)

## 主要功能

### 核心功能
- 📷 **照片管理**: 上传、浏览、搜索、相册组织
- 🎫 **票据识别**: 火车票、发票、收据智能识别
- 👤 **人脸识别**: 照片人脸检测与识别
- 🗺️ **地图轨迹**: 基于 EXIF GPS 的照片地图展示
- 🚄 **铁路集成**: 铁路行程与照片关联

### AI 能力
- 🔍 **OCR 识别**: 基于 PaddleOCR 的多语言文本识别
- 😊 **人脸识别**: 基于 InsightFace 的人脸检测与识别
- 🎯 **目标检测**: 通用物体检测与分类
- 📊 **票据结构化**: 智能提取票据关键信息

## 目录结构

```
package/server/
├── app/
│   ├── api/            # API 路由
│   ├── core/           # 核心配置与日志
│   ├── crud/           # 数据库操作
│   ├── db/             # 模型与会话
│   ├── schemas/        # Pydantic 模型
│   ├── service/        # 业务服务
│   └── utils/          # 工具函数
├── railway/            # 铁路相关功能
├── yolo_ocr/           # OCR 与票据识别
└── main.py

package/website/
├── src/
│   ├── api/            # 后端接口封装
│   ├── components/     # Vue 组件
│   ├── composables/    # 组合式函数
│   ├── layouts/        # 页面布局
│   ├── router/         # 路由配置
│   ├── stores/         # Pinia 状态管理
│   ├── types/          # TypeScript 类型
│   └── views/          # 页面视图
└── package.json

package/ai/
├── app/
│   ├── core/           # 配置与日志
│   ├── routers/        # API 路由
│   ├── services/       # AI 模型服务
│   └── utils/          # 工具函数
├── models/             # 预训练模型
└── main.py
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

[MIT](./LICENSE)

## 联系方式

- 项目主页: https://github.com/yourusername/trailsnap
- 问题反馈: https://github.com/yourusername/trailsnap/issues
