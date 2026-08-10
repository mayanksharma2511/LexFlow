"""WebSocket management endpoint and broadcaster for real-time task progress tracking.

Enables active client WebSocket connections and broadcasts async processing events
with Python 3.13 strict type annotations and FastAPI standard exception handling.
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.task_runner import TaskProgress, async_task_runner

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"],
)


class WebSocketManager:
    """Manager for maintaining active WebSocket connections and broadcasting messages."""

    def __init__(self) -> None:
        """Initialize connection registry and subscribe to task runner updates."""
        self._active_connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """Accept WebSocket connection and store in client active set.

        Args:
            client_id: Unique client identifier.
            websocket: Connecting FastAPI WebSocket instance.
        """
        await websocket.accept()
        async with self._lock:
            if client_id not in self._active_connections:
                self._active_connections[client_id] = set()
            self._active_connections[client_id].add(websocket)

    async def disconnect(self, client_id: str, websocket: WebSocket) -> None:
        """Remove WebSocket connection from active set upon disconnection.

        Args:
            client_id: Unique client identifier.
            websocket: Disconnecting FastAPI WebSocket instance.
        """
        async with self._lock:
            if client_id in self._active_connections:
                self._active_connections[client_id].discard(websocket)
                if not self._active_connections[client_id]:
                    del self._active_connections[client_id]

    async def broadcast_to_client(self, client_id: str, message: str) -> None:
        """Send JSON string message to all active WebSockets for specified client_id.

        Args:
            client_id: Destination client identifier.
            message: JSON-encoded string payload.
        """
        async with self._lock:
            connections = list(self._active_connections.get(client_id, set()))

        stale: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:  # noqa: BLE001
                stale.append(connection)

        if stale:
            async with self._lock:
                for conn in stale:
                    if client_id in self._active_connections:
                        self._active_connections[client_id].discard(conn)


websocket_manager = WebSocketManager()


async def _task_runner_progress_listener(progress: TaskProgress) -> None:
    """Callback function registered with async_task_runner to broadcast progress updates.

    Args:
        progress: Updated TaskProgress instance.
    """
    payload = progress.model_dump_json()
    await websocket_manager.broadcast_to_client(progress.client_id, payload)


# Register task progress callback on startup
async_task_runner.register_callback(_task_runner_progress_listener)


@router.websocket("/tasks/{client_id}")
async def websocket_task_progress_endpoint(
    websocket: WebSocket,
    client_id: str,
) -> None:
    """WebSocket endpoint broadcasting real-time progress for a specific client.

    Args:
        websocket: FastAPI WebSocket context.
        client_id: Client identifier subscribing to updates.
    """
    await websocket_manager.connect(client_id, websocket)
    try:
        # Keep connection open and handle incoming ping or cancellation messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await websocket_manager.disconnect(client_id, websocket)
    except Exception:
        logger.exception("Unexpected error in WebSocket endpoint for '%s'", client_id)
        await websocket_manager.disconnect(client_id, websocket)
