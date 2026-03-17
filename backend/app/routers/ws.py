"""WebSocket endpoint for real-time mesh network updates"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.mesh_store import MeshStore
from app.websocket import manager

router = APIRouter(tags=["websocket"])

MAX_MESSAGE_SIZE = 4096

# Global mesh store instance - will be initialized in main.py
_mesh_store: Optional[MeshStore] = None


def set_mesh_store(mesh_store: MeshStore):
    """
    Initialize the mesh store and set up event handlers for WebSocket broadcasting

    Args:
        mesh_store: MeshStore instance to listen for events
    """
    global _mesh_store
    _mesh_store = mesh_store

    # Register event handler to broadcast mesh store events
    def broadcast_mesh_event(event_type: str, data: dict):
        """Broadcast mesh store events to all WebSocket clients"""
        import asyncio

        # Map internal event names to WebSocket event names
        event_map = {
            "node_added": "node_added",
            "node_update": "node_updated",
            "node_removed": "node_removed",
            "message_added": "message_added",
            "thread_added": "thread_added",
            "thread_update": "thread_updated",
            "thread_removed": "thread_removed",
            "message_removed": "message_removed",
            "store_cleared": "store_cleared",
            "store_loaded": "store_loaded",
        }

        ws_event = event_map.get(event_type, event_type)

        message = {
            "type": ws_event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Create a task to broadcast (handlers must be sync, so we schedule the async broadcast)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast(message))
            else:
                # If no loop is running, we can't broadcast (shouldn't happen in production)
                pass
        except RuntimeError:
            # No event loop available (e.g., during testing without async context)
            pass

    mesh_store.on_event(broadcast_mesh_event)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time mesh network updates

    Clients connect to receive live updates about node status changes,
    new connections, network events, and messages.

    Message format:
    ```json
    {
        "type": "node_added | node_updated | node_removed | message_added | ...",
        "data": { ... },
        "timestamp": "2026-03-16T12:00:00Z"
    }
    ```

    Special events:
    - `connected`: Sent when client first connects
    - `echo`: Response to client keepalive messages
    - `client_disconnected`: Broadcast when a client disconnects
    """
    # Accept connection and get client ID
    client_id = await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "data": {
                    "client_id": client_id,
                    "message": "Connected to MYC3LIUM network",
                    "connections": manager.get_connection_count(),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            client_id,
        )

        # If mesh store is available, send current stats
        if _mesh_store:
            stats = _mesh_store.get_stats()
            # Convert datetime to ISO string
            stats["last_update"] = stats["last_update"].isoformat()
            await manager.send_personal_message(
                {
                    "type": "stats",
                    "data": stats,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
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
                    "type": "echo",
                    "data": {"received": data},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                client_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        # Broadcast disconnection to other clients
        await manager.broadcast(
            {
                "type": "client_disconnected",
                "data": {"client_id": client_id, "connections": manager.get_connection_count()},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
