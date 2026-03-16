"""WebSocket endpoint for real-time updates"""

import asyncio
import random
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models import NodeUpdate
from app.websocket import manager

router = APIRouter(tags=["websocket"])

MAX_MESSAGE_SIZE = 4096


async def simulate_node_updates():
    """Background task that simulates node status updates"""
    node_ids = [f"node_{i + 1:03d}" for i in range(8)]
    statuses = ["online", "offline", "degraded"]

    while True:
        await asyncio.sleep(random.uniform(3, 8))  # Random interval between updates

        # Simulate a node update
        node_id = random.choice(node_ids)
        update = NodeUpdate(
            event=random.choice(["node_update", "connection_update"]),
            data={
                "id": node_id,
                "status": random.choice(statuses),
                "battery": random.randint(10, 100),
                "rssi": random.randint(-90, -30),
            },
            timestamp=datetime.now(UTC),
        )

        # Broadcast to all connected clients
        await manager.broadcast(update.model_dump(mode="json"))


# Track if background task is running
_background_task = None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time mesh network updates

    Clients connect to receive live updates about node status changes,
    new connections, and network events.

    Message format:
    ```json
    {
        "event": "node_update|node_added|node_removed|connection_update",
        "data": { ... },
        "timestamp": "2026-03-16T12:00:00Z"
    }
    ```
    """
    global _background_task

    # Accept connection and get client ID
    client_id = await manager.connect(websocket)

    # Start background update simulation if not already running
    if _background_task is None or _background_task.done():
        _background_task = asyncio.create_task(simulate_node_updates())

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "event": "connected",
                "data": {
                    "client_id": client_id,
                    "message": "Connected to MYC3LIUM network",
                    "connections": manager.get_connection_count(),
                },
                "timestamp": datetime.now(UTC).isoformat(),
            },
            client_id,
        )

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()

            if len(data) > MAX_MESSAGE_SIZE:
                await websocket.close(
                    code=1009, reason=f"Message too large (max {MAX_MESSAGE_SIZE} bytes)"
                )
                break

            # Echo back (clients can send keepalive pings)
            await manager.send_personal_message(
                {
                    "event": "echo",
                    "data": {"received": data},
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                client_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        # Broadcast disconnection to other clients
        await manager.broadcast(
            {
                "event": "client_disconnected",
                "data": {"client_id": client_id, "connections": manager.get_connection_count()},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
