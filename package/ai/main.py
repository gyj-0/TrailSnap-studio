"""AI 服务入口"""
import os
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logger import setup_logging, get_logger
from app.routers import create_api_router
from app.services.model_manager import ModelManager

# 设置日志
logger = get_logger("main")


def setup_signal_handlers():
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        # 清理资源
        model_manager = ModelManager()
        model_manager.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 50)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Device: {settings.actual_device}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info("=" * 50)
    
    # 设置信号处理器
    setup_signal_handlers()
    
    yield
    
    # 关闭时
    logger.info("Shutting down AI Service...")
    model_manager = ModelManager()
    model_manager.shutdown()
    logger.info("AI Service stopped")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="TrailSnap AI 微服务 - 提供 OCR、人脸识别、目标检测等 AI 能力",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc) if settings.DEBUG else None,
            }
        )
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        """健康检查接口"""
        model_manager = ModelManager()
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "device": settings.actual_device,
            "models_loaded": sum(
                1 for info in model_manager.get_all_model_info().values()
                if info and info.get("loaded")
            ),
        }
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径 - 返回服务信息"""
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else None,
            "health": "/health",
        }
    
    # 模型状态
    @app.get("/models")
    async def model_status():
        """获取模型状态"""
        model_manager = ModelManager()
        return {
            "models": model_manager.get_all_model_info(),
            "device": settings.actual_device,
            "gpu_available": settings.is_gpu_available,
        }
    
    # 注册 API 路由
    api_router = create_api_router()
    app.include_router(api_router)
    
    return app


# 创建应用实例
app = create_app()


def main():
    """主入口"""
    # 设置日志
    setup_logging(
        level=settings.LOG_LEVEL,
        log_dir=settings.LOG_DIR,
    )
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else None,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
