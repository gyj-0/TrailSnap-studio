# TrailSnap 部署指南

## 目录

1. [环境要求](#环境要求)
2. [Docker Compose 部署](#docker-compose-部署)
3. [Kubernetes 部署](#kubernetes-部署)
4. [裸机部署](#裸机部署)
5. [SSL 配置](#ssl-配置)
6. [监控配置](#监控配置)

## 环境要求

### 基础环境

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Docker | 20.10 | 24.0+ |
| Docker Compose | 2.0 | 2.20+ |
| Kubernetes | 1.25 | 1.28+ |
| NVIDIA Docker | 2.0 | 2.13+ |

### 硬件要求

#### 开发环境

| 服务 | CPU | 内存 | 存储 |
|------|-----|------|------|
| PostgreSQL | 1核 | 1GB | 10GB |
| Redis | 0.5核 | 512MB | - |
| 后端服务 | 1核 | 1GB | - |
| AI 服务 (CPU) | 2核 | 4GB | 5GB |
| 前端服务 | 0.5核 | 512MB | - |
| **总计** | **5核** | **7GB** | **15GB** |

#### 生产环境

| 服务 | CPU | 内存 | GPU | 存储 |
|------|-----|------|-----|------|
| PostgreSQL | 4核 | 8GB | - | 500GB SSD |
| Redis | 2核 | 4GB | - | - |
| 后端服务 (3副本) | 6核 | 6GB | - | - |
| AI 服务 | 8核 | 32GB | 1x RTX 4090 | 20GB |
| 前端服务 | 2核 | 2GB | - | - |
| Nginx | 2核 | 2GB | - | - |
| **总计** | **24核** | **54GB** | **1x GPU** | **520GB** |

## Docker Compose 部署

### 1. 快速启动（推荐开发测试）

```bash
# 克隆项目
git clone https://github.com/yourusername/trailsnap.git
cd trailsnap

# 复制环境变量
cp .env.example .env
# 编辑 .env 文件，修改必要配置

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. 生产环境配置

创建 `docker-compose.prod.yml`:

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    container_name: trailsnap-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=2GB"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - trailsnap-network

  redis:
    image: redis:7-alpine
    container_name: trailsnap-redis
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - trailsnap-network

  server:
    build:
      context: ./package/server
      dockerfile: Dockerfile
    image: trailsnap/server:latest
    container_name: trailsnap-server
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - AI_SERVICE_URL=http://ai:8001
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - LOG_LEVEL=INFO
      - WORKERS=4
    volumes:
      - uploads_data:/app/uploads
      - ./logs/server:/app/logs
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - trailsnap-network
    command: >
      sh -c "alembic upgrade head &&
             gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000"

  ai:
    build:
      context: ./package/ai
      dockerfile: Dockerfile
    image: trailsnap/ai:latest
    container_name: trailsnap-ai
    environment:
      - MODEL_PATH=/app/models
      - DEVICE=${AI_DEVICE:-cuda}
      - LOG_LEVEL=INFO
    volumes:
      - model_data:/app/models
      - uploads_data:/app/uploads:ro
      - ./logs/ai:/app/logs
    ports:
      - "127.0.0.1:8001:8001"
    restart: unless-stopped
    networks:
      - trailsnap-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: >
      gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001

  nginx:
    image: nginx:alpine
    container_name: trailsnap-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - uploads_data:/var/www/uploads:ro
    depends_on:
      - server
      - website
    restart: unless-stopped
    networks:
      - trailsnap-network

  # 前端使用构建后的静态文件
  website:
    build:
      context: ./package/website
      dockerfile: Dockerfile.prod
    image: trailsnap/website:latest
    container_name: trailsnap-website
    environment:
      - VITE_API_BASE_URL=/api
    restart: unless-stopped
    networks:
      - trailsnap-network

volumes:
  postgres_data:
  redis_data:
  uploads_data:
  model_data:

networks:
  trailsnap-network:
    driver: bridge
```

### 3. 环境变量配置

创建 `.env` 文件:

```bash
# 数据库
POSTGRES_USER=trailsnap
POSTGRES_PASSWORD=your-strong-password-here
POSTGRES_DB=trailsnap

# 安全
SECRET_KEY=$(openssl rand -hex 32)

# AI 配置
AI_DEVICE=cuda
```

### 4. Nginx 配置

创建 `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # 上游服务
    upstream backend {
        server server:8000;
    }

    upstream ai_service {
        server ai:8001;
    }

    # HTTP 重定向到 HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL 证书
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api/ {
            proxy_pass http://backend/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 300s;
        }

        # AI 服务代理（可选，建议内网访问）
        location /ai/ {
            proxy_pass http://ai_service/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 300s;
            client_max_body_size 50M;
        }

        # 文件服务
        location /uploads/ {
            alias /var/www/uploads/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## Kubernetes 部署

### 1. Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: trailsnap
```

### 2. ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trailsnap-config
  namespace: trailsnap
data:
  DATABASE_URL: "postgresql+asyncpg://trailsnap:password@postgres:5432/trailsnap"
  REDIS_URL: "redis://redis:6379/0"
  AI_SERVICE_URL: "http://ai:8001"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
```

### 3. Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: trailsnap-secret
  namespace: trailsnap
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  POSTGRES_PASSWORD: "your-db-password"
```

### 4. PostgreSQL

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: trailsnap
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          env:
            - name: POSTGRES_USER
              value: "trailsnap"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: trailsnap-secret
                  key: POSTGRES_PASSWORD
            - name: POSTGRES_DB
              value: "trailsnap"
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: trailsnap
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
```

### 5. 后端服务

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: server
  namespace: trailsnap
spec:
  replicas: 3
  selector:
    matchLabels:
      app: server
  template:
    metadata:
      labels:
        app: server
    spec:
      initContainers:
        - name: migrate
          image: trailsnap/server:latest
          command: ["alembic", "upgrade", "head"]
          envFrom:
            - configMapRef:
                name: trailsnap-config
            - secretRef:
                name: trailsnap-secret
      containers:
        - name: server
          image: trailsnap/server:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: trailsnap-config
            - secretRef:
                name: trailsnap-secret
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 2000m
              memory: 2Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: server
  namespace: trailsnap
spec:
  selector:
    app: server
  ports:
    - port: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: server-hpa
  namespace: trailsnap
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: server
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### 6. AI 服务（GPU）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai
  namespace: trailsnap
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai
  template:
    metadata:
      labels:
        app: ai
    spec:
      nodeSelector:
        accelerator: nvidia-gpu
      containers:
        - name: ai
          image: trailsnap/ai:latest
          ports:
            - containerPort: 8001
          env:
            - name: DEVICE
              value: "cuda"
          resources:
            limits:
              nvidia.com/gpu: 1
              cpu: 8
              memory: 32Gi
            requests:
              nvidia.com/gpu: 1
              cpu: 4
              memory: 16Gi
          volumeMounts:
            - name: model-data
              mountPath: /app/models
      volumes:
        - name: model-data
          persistentVolumeClaim:
            claimName: model-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: ai
  namespace: trailsnap
spec:
  selector:
    app: ai
  ports:
    - port: 8001
  type: ClusterIP
```

### 7. Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: trailsnap-ingress
  namespace: trailsnap
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: 50m
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  tls:
    - hosts:
        - your-domain.com
      secretName: trailsnap-tls
  rules:
    - host: your-domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: website
                port:
                  number: 80
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: server
                port:
                  number: 8000
```

## 裸机部署

### 1. 安装依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql-16 redis-server nodejs npm

# 安装 CUDA（GPU 支持）
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-1
```

### 2. 数据库配置

```bash
# 创建数据库
sudo -u postgres psql -c "CREATE DATABASE trailsnap;"
sudo -u postgres psql -c "CREATE USER trailsnap WITH PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE trailsnap TO trailsnap;"
```

### 3. 后端部署

```bash
cd package/server
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 使用 Gunicorn 启动
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 4. 前端构建

```bash
cd package/website
npm install
npm run build

# 使用 Nginx 或 Caddy 托管 dist 目录
```

### 5. AI 服务部署

```bash
cd package/ai
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动服务
gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

### 6. Systemd 服务

创建 `/etc/systemd/system/trailsnap-server.service`:

```ini
[Unit]
Description=TrailSnap Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=trailsnap
WorkingDirectory=/opt/trailsnap/package/server
Environment=PATH=/opt/trailsnap/package/server/venv/bin
EnvironmentFile=/opt/trailsnap/.env
ExecStart=/opt/trailsnap/package/server/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable trailsnap-server
sudo systemctl start trailsnap-server
```

## SSL 配置

### 使用 Let's Encrypt (Certbot)

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

### 使用 Cloudflare Origin CA

```bash
# 生成私钥
openssl genrsa -out private.key 2048

# 生成 CSR
openssl req -new -sha256 -key private.key -out csr.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# 在 Cloudflare 控制台生成证书，然后保存为 cert.pem
```

## 监控配置

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: "3.9"

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3001:3000"

  node-exporter:
    image: prom/node-exporter:latest
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro

volumes:
  prometheus_data:
  grafana_data:
```

### 关键监控指标

| 指标 | 告警阈值 |
|------|----------|
| API 响应时间 | P99 > 1s |
| 错误率 | > 1% |
| CPU 使用率 | > 80% |
| 内存使用率 | > 85% |
| 磁盘使用率 | > 85% |
| GPU 显存 | > 90% |

## 备份策略

### 数据库备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/postgres
mkdir -p $BACKUP_DIR

# PostgreSQL 备份
docker exec trailsnap-postgres pg_dump -U trailsnap trailsnap | gzip > $BACKUP_DIR/trailsnap_$DATE.sql.gz

# 保留最近 7 天
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### 文件备份

```bash
# 使用 rclone 同步到云存储
rclone sync /opt/trailsnap/uploads remote:trailsnap-backups/uploads
```

## 故障排查

### 常见问题

1. **AI 服务启动失败**
   - 检查 GPU 驱动: `nvidia-smi`
   - 检查 CUDA 版本兼容性
   - 查看模型文件是否存在

2. **数据库连接失败**
   - 检查 PostgreSQL 是否运行: `systemctl status postgresql`
   - 验证连接字符串
   - 检查防火墙规则

3. **文件上传失败**
   - 检查磁盘空间: `df -h`
   - 检查目录权限
   - 查看 Nginx 的 `client_max_body_size`

### 日志位置

```
Docker: docker logs <container>
Systemd: journalctl -u trailsnap-server -f
文件: /opt/trailsnap/logs/
```
