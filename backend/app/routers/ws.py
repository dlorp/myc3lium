"""WebSocket endpoint for real-time mesh network updates"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import batctl_service
from app.services.mock_data import MeshDataSource
from app.services.mesh_store import MeshStore
from app.websocket import manager

router = APIRouter(tags=["websocket"])

# Constants (Fix: Magic numbers H-5)
MAX_MESSAGE_SIZE = 4096
MESH_MONITOR_INTERVAL_SECONDS = 5
BATCTL_TIMEOUT_SECONDS = 10

logger = logging.getLogger(__name__)

# Global mesh store instance - will be initialized in main.py
_mesh_store: Optional[MeshStore] = None

# Global data source for mesh monitoring
_data_source: Optional[MeshDataSource] = None
_monitor_running = False


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
            "event": ws_event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Create a task to broadcast (handlers must be sync, so we schedule the async broadcast)
        # Fix: Use get_running_loop() to ensure we have an active event loop (Bug #2)
        try:
            asyncio.get_running_loop()  # Verify loop exists
            asyncio.create_task(manager.broadcast(message))
        except RuntimeError:
            # No event loop available (e.g., during testing without async context)
            logger.warning("Cannot broadcast: no event loop running")

    mesh_store.on_event(broadcast_mesh_event)


def set_data_source(data_source: MeshDataSource):
    """
    Initialize the data source for mesh monitoring

    Args:
        data_source: MeshDataSource instance to poll for mesh updates
    """
    global _data_source
    _data_source = data_source


async def mesh_monitor_loop():
    """
    Background task: poll batctl every 5s and broadcast changes.

    Only broadcasts mesh_update events when the mesh state has changed,
    reducing WebSocket spam. Handles batctl unavailability gracefully
    (e.g., on Mac development environments).
    """
    global _monitor_running
    _monitor_running = True
    last_state = None

    logger.info("Mesh monitor loop started")

    # Fix: Proper cancellation handling (H-6)
    try:
        while _monitor_running:
            try:
                # Check if batctl is available (gracefully skip on Mac)
                if not batctl_service.is_available():
                    logger.debug("batctl not available, sleeping...")
                    await asyncio.sleep(10)
                    continue

                # Poll batctl for current mesh state
                originators = batctl_service.get_originators()
                neighbors = batctl_service.get_neighbors()

                # Serialize state for comparison
                current_state = {
                    "originators": [
                        {
                            "mac": o.mac,
                            "last_seen": o.last_seen,
                            "tq": o.tq,
                            "next_hop": o.next_hop,
                            "interface": o.interface,
                        }
                        for o in (originators or [])
                    ],
                    "neighbors": [
                        {
                            "mac": n.mac,
                            "last_seen": n.last_seen,
                            "tq": n.tq,
                            "interface": n.interface,
                        }
                        for n in (neighbors or [])
                    ],
                }

                # Only broadcast if state changed (or first run)
                if current_state != last_state:
                    logger.info(
                        "Mesh state changed: %d originators, %d neighbors",
                        len(current_state["originators"]),
                        len(current_state["neighbors"]),
                    )

                    await manager.broadcast(
                        {
                            "event": "mesh_update",
                            "data": {
                                "originators": current_state["originators"],
                                "neighbors": current_state["neighbors"],
                                "timestamp": time.time(),
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                    # Update MeshStore to keep REST API endpoints fresh
                    if _mesh_store and _data_source:
                        nodes = _data_source.get_nodes()
                        threads = _data_source.get_threads()
                        msgs = _data_source.get_messages()
                        _mesh_store.load_from_source(nodes, threads, msgs)

                    last_state = current_state

            except Exception as e:
                logger.error("Mesh monitor error: %s", e, exc_info=True)

            # Poll every 5 seconds (Fix: Use constant instead of magic number H-5)
            await asyncio.sleep(MESH_MONITOR_INTERVAL_SECONDS)

    except asyncio.CancelledError:
        logger.info("Mesh monitor cancelled")
        raise
    finally:
        logger.info("Mesh monitor loop stopped")


def _ws_auth_required() -> bool:
    """Check if auth is required for WebSocket connections."""
    try:
        from app.services.config_service import ConfigService

        return ConfigService().config.system.require_auth
    except Exception:
        return False


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time mesh network updates

    Clients connect to receive live updates about node status changes,
    new connections, network events, and messages.

    Message format:
    ```json
    {
        "event": "node_added | node_updated | node_removed | message_added | ...",
        "data": { ... },
        "timestamp": "2026-03-16T12:00:00Z"
    }
    ```

    Special events:
    - `connected`: Sent when client first connects
    - `echo`: Response to client keepalive messages
    - `client_disconnected`: Broadcast when a client disconnects
    """
    # C3: Validate auth token before accepting WebSocket connection
    if _ws_auth_required():
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        try:
            from app.services.auth_service import AuthError, verify_token

            verify_token(token)
        except (AuthError, Exception):
            await websocket.close(code=1008, reason="Invalid or expired token")
            return

    # Accept connection and get client ID
    client_id = await manager.connect(websocket)

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
                    "event": "stats",
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
                    code=1009,
                    reason=f"Message too large (max {MAX_MESSAGE_SIZE} bytes)",
                )
                break

            # Echo back (clients can send keepalive pings)
            await manager.send_personal_message(
                {
                    "event": "echo",
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
                "event": "client_disconnected",
                "data": {
                    "client_id": client_id,
                    "connections": manager.get_connection_count(),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
