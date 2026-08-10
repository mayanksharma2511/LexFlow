"""Asynchronous background task runner module for heavy document processing.

Provides task queuing, state tracking, progress monitoring, and event callbacks
with strict Python 3.13 type safety standards.
"""

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Enumeration of asynchronous task lifecycle states."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class TaskProgress(BaseModel):
    """Data model representing the progress state of an async task."""

    task_id: str
    client_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress_percentage: int = Field(default=0, ge=0, le=100)
    current_step: str = "Task initialized"
    details: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


ProgressCallback = Callable[[TaskProgress], Awaitable[None]]


class AsyncTaskRunner:
    """Enterprise asynchronous background task manager.

    Manages non-blocking task execution queues, tracks real-time progress,
    and invokes registered progress callbacks.
    """

    def __init__(self) -> None:
        """Initialize the task runner with storage and callback registries."""
        self._tasks: dict[str, TaskProgress] = {}
        self._callbacks: list[ProgressCallback] = []
        self._lock = asyncio.Lock()

    def register_callback(self, callback: ProgressCallback) -> None:
        """Register an async callback invoked on task progress updates.

        Args:
            callback: Async function receiving updated TaskProgress instance.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: ProgressCallback) -> None:
        """Unregister a previously registered progress callback.

        Args:
            callback: Async function to remove.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def get_progress(self, task_id: str) -> TaskProgress | None:
        """Retrieve the progress state for a specified task ID.

        Args:
            task_id: Unique task identifier.

        Returns:
            TaskProgress instance if task exists, else None.
        """
        async with self._lock:
            return self._tasks.get(task_id)

    async def update_progress(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        progress_percentage: int | None = None,
        current_step: str | None = None,
        details: str | None = None,
        error: str | None = None,
    ) -> TaskProgress | None:
        """Update progress for an existing task and broadcast update.

        Args:
            task_id: Unique task identifier.
            status: Optional updated TaskStatus.
            progress_percentage: Optional updated percentage (0-100).
            current_step: Optional updated human-readable step description.
            details: Optional details string.
            error: Optional error message if status is FAILED.

        Returns:
            Updated TaskProgress instance, or None if task_id not found.
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None

            if status is not None:
                task.status = status
            if progress_percentage is not None:
                task.progress_percentage = min(max(progress_percentage, 0), 100)
            if current_step is not None:
                task.current_step = current_step
            if details is not None:
                task.details = details
            if error is not None:
                task.error = error

            task.updated_at = datetime.now(timezone.utc)
            updated_task = task.model_copy()

        # Broadcast callbacks outside lock
        await self._notify_callbacks(updated_task)
        return updated_task

    async def submit_task(
        self,
        client_id: str,
        coro_func: Callable[..., Awaitable[Any]],
        *args: Any,
        task_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Submit an async task for background execution.

        Args:
            client_id: Unique client identifier requesting task.
            coro_func: Async callable function to execute.
            *args: Positional arguments passed to coro_func.
            task_id: Optional custom task ID. If None, UUID is generated.
            **kwargs: Keyword arguments passed to coro_func.

        Returns:
            Allocated task_id string.
        """
        final_task_id = task_id or str(uuid.uuid4())
        initial_progress = TaskProgress(
            task_id=final_task_id,
            client_id=client_id,
            status=TaskStatus.PENDING,
            progress_percentage=0,
            current_step="Queued for processing",
        )

        async with self._lock:
            self._tasks[final_task_id] = initial_progress

        await self._notify_callbacks(initial_progress)

        # Launch worker task in background
        asyncio.create_task(
            self._execute_wrapper(final_task_id, coro_func, *args, **kwargs)
        )
        return final_task_id

    async def _execute_wrapper(
        self,
        task_id: str,
        coro_func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Wrap execution of task function to capture status transitions and exceptions.

        Args:
            task_id: Task ID being executed.
            coro_func: Async target function.
            *args: Target arguments.
            **kwargs: Target keyword arguments.
        """
        await self.update_progress(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            progress_percentage=10,
            current_step="Processing started",
        )

        try:
            result = await coro_func(task_id, *args, **kwargs)
            await self.update_progress(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                progress_percentage=100,
                current_step="Processing complete",
                details=str(result) if result is not None else "Operation finished successfully",
            )
        except Exception as exc:
            logger.exception("Background task '%s' failed", task_id)
            await self.update_progress(
                task_id=task_id,
                status=TaskStatus.FAILED,
                progress_percentage=100,
                current_step="Task failed",
                error=str(exc),
            )

    async def _notify_callbacks(self, progress: TaskProgress) -> None:
        """Invoke all registered callbacks with task progress update.

        Args:
            progress: Current TaskProgress instance.
        """
        for callback in list(self._callbacks):
            try:
                await callback(progress)
            except Exception:
                logger.warning("Error invoking task progress callback", exc_info=True)


# Global singleton instance
async_task_runner = AsyncTaskRunner()
