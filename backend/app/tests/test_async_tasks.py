"""Async task runner unit tests for background task execution and callback notifications."""

import asyncio
from typing import Any

import pytest

from app.services.task_runner import AsyncTaskRunner, TaskProgress, TaskStatus


@pytest.mark.asyncio
async def test_async_task_runner_success_flow() -> None:
    """Test successful asynchronous task execution and state transitions."""
    runner = AsyncTaskRunner()
    received_updates: list[TaskProgress] = []

    async def sample_callback(progress: TaskProgress) -> None:
        received_updates.append(progress)

    runner.register_callback(sample_callback)

    async def dummy_coro(task_id: str, value: int) -> str:
        await runner.update_progress(
            task_id=task_id,
            progress_percentage=50,
            current_step="Processing halfway",
        )
        return f"Completed with value {value}"

    task_id = await runner.submit_task("client_123", dummy_coro, 42)
    assert task_id is not None

    # Wait briefly for worker task to complete
    await asyncio.sleep(0.1)

    progress = await runner.get_progress(task_id)
    assert progress is not None
    assert progress.status == TaskStatus.SUCCESS
    assert progress.progress_percentage == 100
    assert "42" in (progress.details or "")
    assert len(received_updates) >= 3


@pytest.mark.asyncio
async def test_async_task_runner_failure_flow() -> None:
    """Test task failure handling and error capture."""
    runner = AsyncTaskRunner()

    async def failing_coro(task_id: str, *args: Any, **kwargs: Any) -> None:
        raise ValueError("Simulated processing error")

    task_id = await runner.submit_task("client_456", failing_coro)
    await asyncio.sleep(0.1)

    progress = await runner.get_progress(task_id)
    assert progress is not None
    assert progress.status == TaskStatus.FAILED
    assert progress.error == "Simulated processing error"
