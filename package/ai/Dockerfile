# TrailSnap AI 服务 Dockerfile
# 基于 PaddlePaddle GPU 镜像

FROM paddlepaddle/paddle:3.0.0rc1-gpu-cuda12.3-cudnn9.0-trt8.6

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NVIDIA_VISIBLE_DEVICES=all

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（排除 paddlepaddle，基础镜像已包含）
RUN pip install --no-cache-dir \
    fastapi==0.122.0 \
    uvicorn[standard]==0.38.0 \
    python-multipart==0.0.9 \
    aiofiles==23.2.1 \
    Pillow==10.1.0 \
    numpy==1.26.4 \
    opencv-python-headless==4.9.0.80 \
    paddleocr==3.3.2 \
    insightface==0.7.3 \
    onnxruntime-gpu==1.17.0

# 创建模型目录
RUN mkdir -p /app/models /app/logs /app/uploads

# 复制应用代码
COPY . .

# 非 root 用户运行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
