"""Task manager for background job processing."""

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar
from uuid import UUID, uuid4

from app.core.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task definition."""

    id: UUID
    name: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None
    progress: int = 0  # 0-100


class TaskManager:
    """Manager for background tasks."""

    _instance: "TaskManager | None" = None

    def __new__(cls) -> "TaskManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks: dict[UUID, Task] = {}
        self._running_tasks: dict[UUID, asyncio.Task] = {}

    async def submit(
        self,
        name: str,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> UUID:
        """
        Submit a new background task.
        
        Args:
            name: Task name
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Task ID
        """
        task_id = uuid4()
        task = Task(id=task_id, name=name)
        self._tasks[task_id] = task

        # Create and store the asyncio task
        asyncio_task = asyncio.create_task(
            self._execute_task(task_id, func, *args, **kwargs),
            name=f"task-{task_id}",
        )
        self._running_tasks[task_id] = asyncio_task

        logger.info(f"Task submitted: {name} ({task_id})")
        return task_id

    async def _execute_task(
        self,
        task_id: UUID,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Execute a task and handle status updates."""
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            result = await func(*args, **kwargs)
            task.status = TaskStatus.COMPLETED
            task.result = result
            logger.info(f"Task completed: {task.name} ({task_id})")
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            logger.warning(f"Task cancelled: {task.name} ({task_id})")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task failed: {task.name} ({task_id}): {e}")
        finally:
            task.completed_at = datetime.now()
            self._running_tasks.pop(task_id, None)

    def get_task(self, task_id: UUID) -> Task | None:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def get_tasks(
        self,
        status: TaskStatus | None = None,
        limit: int = 100,
    ) -> list[Task]:
        """Get tasks with optional filtering."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

    async def cancel_task(self, task_id: UUID) -> bool:
        """Cancel a running task."""
        asyncio_task = self._running_tasks.get(task_id)
        if asyncio_task and not asyncio_task.done():
            asyncio_task.cancel()
            try:
                await asyncio_task
            except asyncio.CancelledError:
                pass
            return True
        return False

    async def wait_for_task(
        self,
        task_id: UUID,
        timeout: float | None = None,
    ) -> Task:
        """Wait for a task to complete."""
        asyncio_task = self._running_tasks.get(task_id)
        if asyncio_task:
            try:
                await asyncio.wait_for(asyncio_task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Task wait timeout: {task_id}")
        return self._tasks.get(task_id)

    def update_progress(self, task_id: UUID, progress: int) -> None:
        """Update task progress (0-100)."""
        task = self._tasks.get(task_id)
        if task:
            task.progress = max(0, min(100, progress))


# Global task manager instance
task_manager = TaskManager()


# Convenience functions for common task types
async def submit_photo_processing(
    photo_id: int,
    process_func: Callable[..., Coroutine[Any, Any, Any]],
) -> UUID:
    """Submit a photo processing task."""
    return await task_manager.submit(
        f"photo_processing_{photo_id}",
        process_func,
        photo_id,
    )


async def submit_batch_import(
    album_id: int,
    file_paths: list[str],
    import_func: Callable[..., Coroutine[Any, Any, Any]],
) -> UUID:
    """Submit a batch import task."""
    return await task_manager.submit(
        f"batch_import_{album_id}",
        import_func,
        album_id,
        file_paths,
    )
