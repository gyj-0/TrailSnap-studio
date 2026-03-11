"""JSON 队列日志实现 - 按日容量滚动"""
import json
import logging
import logging.handlers
import queue
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class DailyRotatingFileHandler(logging.handlers.BaseRotatingHandler):
    """按日容量滚动的文件处理器
    
    特性：
    1. 按日期分割日志文件
    2. 单日日志超过容量限制时滚动（添加序号）
    3. 自动清理过期日志
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 7,
        encoding: str = "utf-8"
    ):
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.encoding = encoding
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.rollover_count = 0
        
        # 确保日志目录存在
        self.base_path = Path(filename)
        self.base_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成初始文件名
        current_filename = self._get_current_filename()
        super().__init__(current_filename, mode="a", encoding=encoding)
    
    def _get_current_filename(self) -> str:
        """获取当前日志文件名"""
        date_str = self.current_date
        if self.rollover_count > 0:
            return str(self.base_path.parent / f"{self.base_path.stem}-{date_str}-{self.rollover_count}.log")
        return str(self.base_path.parent / f"{self.base_path.stem}-{date_str}.log")
    
    def shouldRollover(self, record: logging.LogRecord) -> bool:
        """检查是否需要滚动"""
        # 检查日期是否变化
        new_date = datetime.now().strftime("%Y-%m-%d")
        if new_date != self.current_date:
            self.current_date = new_date
            self.rollover_count = 0
            return True
        
        # 检查文件大小
        if self.max_bytes > 0:
            if self.stream is None:
                self.stream = self._open()
            if hasattr(self.stream, "seek") and hasattr(self.stream, "tell"):
                self.stream.seek(0, 2)  # 移动到文件末尾
                if self.stream.tell() >= self.max_bytes:
                    self.rollover_count += 1
                    return True
        return False
    
    def doRollover(self):
        """执行日志滚动"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        self.baseFilename = self._get_current_filename()
        self.stream = self._open()
        
        # 清理过期日志
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self):
        """清理过期日志文件"""
        try:
            log_dir = self.base_path.parent
            log_stem = self.base_path.stem
            
            # 获取所有日志文件
            log_files = []
            for f in log_dir.glob(f"{log_stem}-*.log"):
                try:
                    stat = f.stat()
                    log_files.append((f, stat.st_mtime))
                except OSError:
                    continue
            
            # 按修改时间排序
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除过期文件
            for f, _ in log_files[self.backup_count:]:
                try:
                    f.unlink()
                except OSError:
                    pass
        except Exception:
            pass


class AsyncQueueHandler(logging.Handler):
    """异步队列日志处理器"""
    
    def __init__(self, target_handler: logging.Handler, max_queue_size: int = 10000):
        super().__init__()
        self.target_handler = target_handler
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
    
    def emit(self, record: logging.LogRecord):
        """将日志记录放入队列"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # 队列满时直接丢弃，避免阻塞
            pass
    
    def _process_queue(self):
        """后台线程处理日志队列"""
        while not self._stop_event.is_set():
            try:
                record = self.queue.get(timeout=0.1)
                self.target_handler.emit(record)
            except queue.Empty:
                continue
            except Exception:
                pass
    
    def close(self):
        """关闭处理器"""
        self._stop_event.set()
        self._worker_thread.join(timeout=5)
        # 处理队列中剩余的日志
        while not self.queue.empty():
            try:
                record = self.queue.get_nowait()
                self.target_handler.emit(record)
            except Exception:
                break
        self.target_handler.close()
        super().close()


def setup_logging(
    level: Optional[str] = None,
    log_dir: Optional[Path] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None
) -> logging.Logger:
    """配置日志系统
    
    Args:
        level: 日志级别
        log_dir: 日志目录
        max_bytes: 单个日志文件最大字节数
        backup_count: 日志备份数量
    
    Returns:
        配置好的 logger 实例
    """
    level = level or settings.LOG_LEVEL
    log_dir = log_dir or settings.LOG_DIR
    max_bytes = max_bytes or settings.LOG_MAX_BYTES
    backup_count = backup_count or settings.LOG_BACKUP_COUNT
    
    # 创建 logger
    logger = logging.getLogger("ai_service")
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有处理器
    logger.handlers.clear()
    
    # JSON 格式化器
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
        json_indent=None
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（按日滚动）
    log_file = log_dir / "ai_service.log"
    file_handler = DailyRotatingFileHandler(
        filename=str(log_file),
        max_bytes=max_bytes,
        backup_count=backup_count
    )
    file_handler.setFormatter(json_formatter)
    
    # 异步队列处理器
    async_handler = AsyncQueueHandler(file_handler)
    logger.addHandler(async_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取 logger 实例
    
    Args:
        name: logger 名称，默认返回 ai_service
    
    Returns:
        Logger 实例
    """
    if name:
        return logging.getLogger(f"ai_service.{name}")
    return logging.getLogger("ai_service")
