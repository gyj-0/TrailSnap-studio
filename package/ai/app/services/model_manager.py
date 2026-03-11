"""模型管理器 - 懒加载、单例模式、资源释放"""
import time
import threading
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from functools import wraps
import gc

import psutil

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("model_manager")


@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    instance: Optional[Any] = None
    load_time: float = 0
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    is_loading: bool = False


class ModelManager:
    """模型管理器（单例模式）
    
    特性：
    1. 懒加载 - 首次使用时加载模型
    2. 单例模式 - 全局唯一实例
    3. 资源释放 - 空闲超时自动释放
    4. LRU 缓存 - 限制同时加载的模型数量
    """
    
    _instance: Optional["ModelManager"] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._models: Dict[str, ModelInfo] = {}
        self._loaders: Dict[str, Callable[[], Any]] = {}
        self._model_locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.RLock()
        
        # 启动资源监控线程
        self._stop_monitor = threading.Event()
        self._monitor_thread = threading.Thread(
            target=self._resource_monitor,
            daemon=True,
            name="model-resource-monitor"
        )
        self._monitor_thread.start()
        
        self._initialized = True
        logger.info("ModelManager initialized")
    
    def register_loader(self, name: str, loader: Callable[[], Any]) -> None:
        """注册模型加载器
        
        Args:
            name: 模型名称
            loader: 返回模型实例的可调用对象
        """
        with self._global_lock:
            self._loaders[name] = loader
            self._models[name] = ModelInfo(name=name)
            self._model_locks[name] = threading.Lock()
            logger.info(f"Registered model loader: {name}")
    
    def get_model(self, name: str) -> Any:
        """获取模型实例（懒加载）
        
        Args:
            name: 模型名称
        
        Returns:
            模型实例
        
        Raises:
            KeyError: 模型未注册
            RuntimeError: 模型加载失败
        """
        if name not in self._models:
            raise KeyError(f"Model '{name}' not registered")
        
        model_info = self._models[name]
        model_lock = self._model_locks[name]
        
        # 快速路径：模型已加载
        if model_info.instance is not None:
            with self._global_lock:
                model_info.last_used = time.time()
                model_info.use_count += 1
            return model_info.instance
        
        # 慢速路径：需要加载模型
        with model_lock:
            # 双重检查
            if model_info.instance is not None:
                with self._global_lock:
                    model_info.last_used = time.time()
                    model_info.use_count += 1
                return model_info.instance
            
            # 加载模型
            if model_info.is_loading:
                # 等待其他线程加载完成
                while model_info.is_loading:
                    time.sleep(0.1)
                return model_info.instance
            
            model_info.is_loading = True
            try:
                start_time = time.time()
                logger.info(f"Loading model: {name}")
                
                # 执行加载前检查资源
                self._check_and_release_resources()
                
                # 加载模型
                loader = self._loaders[name]
                model_info.instance = loader()
                model_info.load_time = time.time() - start_time
                model_info.last_used = time.time()
                model_info.use_count = 1
                
                logger.info(f"Model '{name}' loaded in {model_info.load_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to load model '{name}': {e}")
                raise RuntimeError(f"Failed to load model '{name}': {e}")
            finally:
                model_info.is_loading = False
        
        return model_info.instance
    
    def unload_model(self, name: str) -> bool:
        """卸载指定模型
        
        Args:
            name: 模型名称
        
        Returns:
            是否成功卸载
        """
        with self._global_lock:
            if name not in self._models:
                return False
            
            model_info = self._models[name]
            if model_info.instance is None:
                return False
            
            with self._model_locks[name]:
                logger.info(f"Unloading model: {name}")
                
                # 尝试调用模型的清理方法
                if hasattr(model_info.instance, 'release'):
                    try:
                        model_info.instance.release()
                    except Exception as e:
                        logger.warning(f"Error releasing model '{name}': {e}")
                
                # 删除引用
                del model_info.instance
                model_info.instance = None
                model_info.load_time = 0
                model_info.use_count = 0
                
                # 强制垃圾回收
                gc.collect()
                
                logger.info(f"Model '{name}' unloaded")
                return True
    
    def unload_all(self) -> None:
        """卸载所有模型"""
        with self._global_lock:
            for name in list(self._models.keys()):
                self.unload_model(name)
        logger.info("All models unloaded")
    
    def get_model_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息
        
        Args:
            name: 模型名称
        
        Returns:
            模型信息字典
        """
        if name not in self._models:
            return None
        
        model_info = self._models[name]
        return {
            "name": model_info.name,
            "loaded": model_info.instance is not None,
            "load_time": model_info.load_time,
            "last_used": model_info.last_used,
            "idle_time": time.time() - model_info.last_used,
            "use_count": model_info.use_count,
        }
    
    def get_all_model_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型信息"""
        return {
            name: self.get_model_info(name)
            for name in self._models.keys()
        }
    
    def _check_and_release_resources(self) -> None:
        """检查并释放资源"""
        with self._global_lock:
            # 检查当前加载的模型数量
            loaded_models = [
                name for name, info in self._models.items()
                if info.instance is not None
            ]
            
            # 如果超过缓存限制，释放最久未使用的模型
            if len(loaded_models) >= settings.MODEL_CACHE_SIZE:
                # 按最后使用时间排序
                sorted_models = sorted(
                    loaded_models,
                    key=lambda n: self._models[n].last_used
                )
                
                # 释放最久未使用的模型
                for name in sorted_models[:len(sorted_models) - settings.MODEL_CACHE_SIZE + 1]:
                    self.unload_model(name)
    
    def _resource_monitor(self) -> None:
        """资源监控线程"""
        while not self._stop_monitor.is_set():
            try:
                self._cleanup_idle_models()
                self._log_resource_usage()
            except Exception as e:
                logger.error(f"Resource monitor error: {e}")
            
            # 每分钟检查一次
            self._stop_monitor.wait(60)
    
    def _cleanup_idle_models(self) -> None:
        """清理空闲模型"""
        with self._global_lock:
            current_time = time.time()
            timeout = settings.MODEL_IDLE_TIMEOUT
            
            for name, model_info in self._models.items():
                if model_info.instance is None:
                    continue
                
                idle_time = current_time - model_info.last_used
                if idle_time > timeout:
                    logger.info(
                        f"Model '{name}' idle for {idle_time:.0f}s, unloading"
                    )
                    self.unload_model(name)
    
    def _log_resource_usage(self) -> None:
        """记录资源使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            logger.debug(
                f"Resource usage - "
                f"Memory: {memory_info.rss / 1024 / 1024:.1f}MB, "
                f"Models loaded: {sum(1 for info in self._models.values() if info.instance is not None)}"
            )
        except Exception:
            pass
    
    def shutdown(self) -> None:
        """关闭模型管理器，释放所有资源"""
        logger.info("Shutting down ModelManager")
        self._stop_monitor.set()
        self._monitor_thread.join(timeout=5)
        self.unload_all()
        ModelManager._instance = None


def singleton_model_loader(name: str):
    """装饰器：将函数注册为模型加载器"""
    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        @wraps(func)
        def wrapper() -> Any:
            return func()
        
        # 自动注册
        ModelManager().register_loader(name, wrapper)
        return wrapper
    return decorator
