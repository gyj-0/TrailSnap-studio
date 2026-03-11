"""JSON formatted logging with queue and daily capacity-based rotation."""

import json
import logging
import logging.handlers
import os
import queue
import sys
import threading
import time
from datetime import datetime, timedelta
from logging import LogRecord
from pathlib import Path
from typing import Any

from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter with structured output."""

    def __init__(self, include_extra: bool = True) -> None:
        super().__init__()
        self.include_extra = include_extra
        self.hostname = os.uname().nodename if hasattr(os, "uname") else "unknown"

    def format(self, record: LogRecord) -> str:
        """Format log record as JSON."""
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "source": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
                "module": record.module,
            },
            "host": self.hostname,
            "thread": record.thread,
            "process": record.process,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if self.include_extra:
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if k
                not in {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "process",
                    "processName",
                    "msg",
                    "message",
                }
            }
            if extra_fields:
                log_obj["extra"] = extra_fields

        return json.dumps(log_obj, ensure_ascii=False, default=str)


class DailyCapacityRotatingFileHandler(logging.Handler):
    """
    Custom log handler that rotates files daily with capacity limit.
    
    Features:
    - Rotates at midnight or when daily capacity is reached
    - Maintains backup files for specified number of days
    - Thread-safe with queue-based logging
    """

    def __init__(
        self,
        log_dir: Path,
        max_bytes_per_day: int = 100 * 1024 * 1024,  # 100MB
        backup_days: int = 30,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self.log_dir = Path(log_dir)
        self.max_bytes_per_day = max_bytes_per_day
        self.backup_days = backup_days
        self.encoding = encoding
        self.current_date = datetime.now().date()
        self.current_bytes = 0
        self._lock = threading.Lock()
        self._file: Any = None
        self._ensure_log_dir()
        self._open_current_file()

    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self, date: datetime.date) -> Path:
        """Get log file path for specific date."""
        return self.log_dir / f"app-{date.isoformat()}.log"

    def _open_current_file(self) -> None:
        """Open the current log file."""
        if self._file:
            self._file.close()

        log_path = self._get_log_file_path(self.current_date)
        self._file = open(log_path, "a", encoding=self.encoding)
        
        # Calculate current size
        if log_path.exists():
            self.current_bytes = log_path.stat().st_size
        else:
            self.current_bytes = 0

    def _rotate_if_needed(self) -> None:
        """Check and perform rotation if needed."""
        now = datetime.now()
        current_date = now.date()

        # Check for date change
        if current_date != self.current_date:
            self.current_date = current_date
            self._open_current_file()
            self._cleanup_old_logs()
            return

        # Check for capacity limit
        if self.current_bytes >= self.max_bytes_per_day:
            # Create new file with sequence number
            seq = 1
            while True:
                new_path = self.log_dir / f"app-{current_date.isoformat()}-{seq}.log"
                if not new_path.exists():
                    break
                seq += 1
            
            if self._file:
                self._file.close()
            
            self._file = open(new_path, "a", encoding=self.encoding)
            self.current_bytes = 0

    def _cleanup_old_logs(self) -> None:
        """Remove log files older than backup_days."""
        cutoff_date = datetime.now().date() - timedelta(days=self.backup_days)
        
        try:
            for log_file in self.log_dir.glob("app-*.log"):
                try:
                    # Extract date from filename
                    name_parts = log_file.stem.split("-")
                    if len(name_parts) >= 3:
                        file_date = datetime.strptime(
                            "-".join(name_parts[1:4]), "%Y-%m-%d"
                        ).date()
                        if file_date < cutoff_date:
                            log_file.unlink()
                except (ValueError, OSError):
                    continue
        except OSError:
            pass

    def emit(self, record: LogRecord) -> None:
        """Emit a log record."""
        try:
            with self._lock:
                self._rotate_if_needed()
                msg = self.format(record)
                self._file.write(msg + "\n")
                self._file.flush()
                self.current_bytes += len(msg.encode(self.encoding))
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Close the handler."""
        with self._lock:
            if self._file:
                self._file.close()
                self._file = None
        super().close()


class QueueHandler(logging.Handler):
    """Asynchronous queue-based log handler for non-blocking logging."""

    def __init__(self, handler: logging.Handler, max_queue_size: int = 10000) -> None:
        super().__init__()
        self.handler = handler
        self.queue: queue.Queue[LogRecord | None] = queue.Queue(maxsize=max_queue_size)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._start_worker()

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self._thread = threading.Thread(target=self._process_queue, daemon=True)
        self._thread.start()

    def _process_queue(self) -> None:
        """Process log records from queue."""
        while not self._stop_event.is_set():
            try:
                record = self.queue.get(timeout=0.1)
                if record is None:
                    break
                self.handler.emit(record)
            except queue.Empty:
                continue
            except Exception:
                pass

    def emit(self, record: LogRecord) -> None:
        """Add record to queue."""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # Drop oldest record if queue is full
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(record)
            except queue.Empty:
                pass

    def close(self) -> None:
        """Close the handler gracefully."""
        self._stop_event.set()
        self.queue.put(None)
        if self._thread:
            self._thread.join(timeout=5)
        self.handler.close()
        super().close()


class LoggerManager:
    """Centralized logger manager with JSON formatting and daily rotation."""

    _instance: "LoggerManager | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "LoggerManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._loggers: dict[str, logging.Logger] = {}
        self._handlers: list[logging.Handler] = []
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup log handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        console_handler.setFormatter(JSONFormatter())
        self._handlers.append(console_handler)

        # File handler with daily rotation
        file_handler = DailyCapacityRotatingFileHandler(
            log_dir=settings.LOG_DIR,
            max_bytes_per_day=settings.LOG_MAX_BYTES_PER_DAY,
            backup_days=settings.LOG_BACKUP_DAYS,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())

        # Queue handler for async logging
        queue_handler = QueueHandler(file_handler)
        queue_handler.setLevel(logging.DEBUG)
        self._handlers.append(queue_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the specified name."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            
            # Remove existing handlers
            logger.handlers = []
            
            # Add our handlers
            for handler in self._handlers:
                logger.addHandler(handler)
            
            # Prevent propagation to root logger
            logger.propagate = False
            self._loggers[name] = logger

        return self._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    manager = LoggerManager()
    return manager.get_logger(name)
