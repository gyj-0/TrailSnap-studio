"""AI Service Configuration"""
import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class AISettings(BaseSettings):
    """AI 服务配置类"""
    
    # 服务配置
    APP_NAME: str = Field(default="TrailSnap AI Service", description="服务名称")
    APP_VERSION: str = Field(default="1.0.0", description="服务版本")
    HOST: str = Field(default="0.0.0.0", description="监听地址")
    PORT: int = Field(default=8001, description="监听端口")
    
    # 环境配置
    ENV: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 设备配置
    DEVICE: str = Field(default="auto", description="计算设备 (auto/gpu/cpu)")
    GPU_ID: int = Field(default=0, description="GPU 设备 ID")
    
    # 模型路径配置
    MODELS_DIR: Path = Field(default=Path("./models"), description="模型存放目录")
    
    # OCR 配置
    OCR_LANG: str = Field(default="ch", description="OCR 识别语言")
    OCR_USE_ANGLE_CLS: bool = Field(default=True, description="使用方向分类器")
    OCR_USE_GPU: bool = Field(default=True, description="OCR 使用 GPU")
    
    # 人脸识别配置
    FACE_DET_THRESHOLD: float = Field(default=0.5, description="人脸检测阈值")
    FACE_RECOGNITION_THRESHOLD: float = Field(default=0.6, description="人脸识别阈值")
    FACE_MODEL_NAME: str = Field(default="buffalo_l", description="InsightFace 模型名称")
    
    # 目标检测配置
    DETECTION_MODEL: str = Field(default="yolov8n", description="检测模型名称")
    DETECTION_CONF: float = Field(default=0.25, description="检测置信度阈值")
    DETECTION_IOU: float = Field(default=0.45, description="检测 IOU 阈值")
    
    # 票据识别配置
    TICKET_MIN_CONFIDENCE: float = Field(default=0.7, description="票据识别最低置信度")
    
    # 资源管理配置
    MODEL_CACHE_SIZE: int = Field(default=3, description="模型缓存数量")
    MODEL_IDLE_TIMEOUT: int = Field(default=300, description="模型空闲超时时间(秒)")
    MAX_IMAGE_SIZE: int = Field(default=10 * 1024 * 1024, description="最大图片大小(字节)")
    MAX_IMAGE_DIMENSION: int = Field(default=4096, description="最大图片尺寸")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_DIR: Path = Field(default=Path("./logs"), description="日志目录")
    LOG_MAX_BYTES: int = Field(default=100 * 1024 * 1024, description="单个日志文件最大字节数")
    LOG_BACKUP_COUNT: int = Field(default=7, description="日志备份数量")
    
    class Config:
        env_file = ".env"
        env_prefix = "AI_"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_gpu_available(self) -> bool:
        """检查 GPU 是否可用"""
        if self.DEVICE == "cpu":
            return False
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    @property
    def actual_device(self) -> str:
        """获取实际使用的设备"""
        if self.DEVICE == "auto":
            return "cuda" if self.is_gpu_available else "cpu"
        return self.DEVICE
    
    def get_model_path(self, model_name: str) -> Path:
        """获取模型路径"""
        return self.MODELS_DIR / model_name


@lru_cache()
def get_settings() -> AISettings:
    """获取配置单例"""
    return AISettings()


settings = get_settings()
