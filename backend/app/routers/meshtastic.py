"""
Meshtastic API endpoints for mesh radio communication.

Provides:
- Connection status and node info
- List of mesh nodes
- Recent messages with filters
- Send messages to mesh
- WebSocket endpoint for real-time updates
"""

import asyncio
import logging
import os
from asyncio import Queue
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from app.auth import verify_api_key
from app.rate_limit import send_limiter
from app.websocket import ConnectionManager

from app.services.meshtastic_service import (
    MeshtasticService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meshtastic", tags=["meshtastic"])

# Global service instance - will be set by main.py
_service: Optional[MeshtasticService] = None

# Event queue for async/sync bridge
_event_queue: Queue = Queue()
_event_processor_task = None


class MessageResponse(BaseModel):
    """API response model for messages"""

    sender: str
    text: str
    timestamp: float
    channel: int
    snr: Optional[float] = None
    rssi: Optional[int] = None
    hop_limit: Optional[int] = None


class NodeResponse(BaseModel):
    """API response model for nodes"""

    node_id: str
    short_name: str
    long_name: str
    last_heard: float
    snr: Optional[float] = None
    position: Optional[dict] = None
    battery_level: Optional[int] = None
    voltage: Optional[float] = None
    channel_utilization: Optional[float] = None
    air_util_tx: Optional[float] = None


class StatusResponse(BaseModel):
    """API response model for status"""

    connected: bool
    device: Optional[str] = None
    node_id: Optional[str] = None
    short_name: Optional[str] = None
    long_name: Optional[str] = None
    battery_level: Optional[int] = None
    voltage: Optional[float] = None
    channel_utilization: Optional[float] = None
    air_util_tx: Optional[float] = None
    nodes_count: int


class SendMessageRequest(BaseModel):
    """Request model for sending messages"""

    text: str
    channel: int = 0
    destination: Optional[str] = None


def set_service(service: MeshtasticService):
    """
    Inject service dependency (called by main.py)

    Args:
        service: MeshtasticService instance
    """
    global _service
    _service = service
    # Don't start event processor here - no event loop at import time


async def start_event_processor():
    """Start the event processor task. Must be called from within a running event loop."""
    global _event_processor_task, _event_loop
    _event_loop = asyncio.get_running_loop()
    if _event_processor_task is None:
        _event_processor_task = asyncio.create_task(_process_event_queue())
        logger.info("Event processor task started")


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get current Meshtastic connection status and node info.

    Returns:
        Connection status, node info, signal metrics
    """
    if _service is None:
        raise HTTPException(
            status_code=503, detail="Meshtastic service not initialized"
        )

    status = _service.get_status()

    return StatusResponse(
        connected=status.connected,
        device=status.device,
        node_id=status.node_id,
        short_name=status.short_name,
        long_name=status.long_name,
        battery_level=status.battery_level,
        voltage=status.voltage,
        channel_utilization=status.channel_utilization,
        air_util_tx=status.air_util_tx,
        nodes_count=status.nodes_count,
    )


@router.get("/nodes", response_model=list[NodeResponse])
async def get_nodes():
    """
    Get list of all known mesh nodes.

    Returns:
        List of mesh nodes with their info and last-heard times
    """
    if _service is None:
        raise HTTPException(
            status_code=503, detail="Meshtastic service not initialized"
        )

    if not _service.available:
        raise HTTPException(status_code=503, detail="Meshtastic service not connected")

    nodes = _service.get_nodes()

    return [
        NodeResponse(
            node_id=node.node_id,
            short_name=node.short_name,
            long_name=node.long_name,
            last_heard=node.last_heard,
            snr=node.snr,
            position=node.position,
            battery_level=node.battery_level,
            voltage=node.voltage,
            channel_utilization=node.channel_utilization,
            air_util_tx=node.air_util_tx,
        )
        for node in nodes
    ]


@router.get("/messages", response_model=list[MessageResponse])
async def get_messages(
    limit: Optional[int] = 100,
    sender: Optional[str] = None,
    channel: Optional[int] = None,
):
    """
    Get recent messages with optional filters.

    Args:
        limit: Maximum number of messages to return (default: 100)
        sender: Filter by sender node ID
        channel: Filter by channel index

    Returns:
        List of recent messages matching filters
    """
    if _service is None:
        raise HTTPException(
            status_code=503, detail="Meshtastic service not initialized"
        )

    if not _service.available:
        raise HTTPException(status_code=503, detail="Meshtastic service not connected")

    messages = _service.get_messages(limit=limit, sender=sender, channel=channel)

    return [
        MessageResponse(
            sender=msg.sender,
            text=msg.text,
            timestamp=msg.timestamp,
            channel=msg.channel,
            snr=msg.snr,
            rssi=msg.rssi,
            hop_limit=msg.hop_limit,
        )
        for msg in messages
    ]


@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    req: Request,
    api_key: str = Depends(verify_api_key),
    _rate_limit=Depends(send_limiter),
):
    """
    Send a text message to the mesh.

    Args:
        request: Message content, channel, and optional destination

    Returns:
        Success status
    """
    if _service is None:
        raise HTTPException(
            status_code=503, detail="Meshtastic service not initialized"
        )

    if not _service.available:
        raise HTTPException(status_code=503, detail="Meshtastic service not connected")

    try:
        _service.send_message(
            text=request.text,
            channel=request.channel,
            destination=request.destination,
        )
        return {
            "status": "sent",
            "text": request.text,
            "channel": request.channel,
            "destination": request.destination or "broadcast",
        }

    except Exception as e:
        logger.error("Failed to send message: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to send message to mesh radio"
        )


# WebSocket connection manager
_meshtastic_ws_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time Meshtastic updates."""
    # Optional token auth (skip if no API key configured, like REST endpoints)
    api_key = os.getenv("MESHTASTIC_API_KEY")
    if api_key:
        token = websocket.query_params.get("token")
        if token != api_key:
            await websocket.close(code=1008, reason="Unauthorized")
            return

    # Accept connection (ConnectionManager handles capacity check)
    try:
        client_id = await _meshtastic_ws_manager.connect(websocket)
    except ValueError:
        return  # Already closed with 1008 by ConnectionManager

    logger.info("WebSocket client %s connected to Meshtastic stream", client_id)

    try:
        # Send initial status
        if _service:
            status = _service.get_status()
            await websocket.send_json(
                {
                    "type": "status",
                    "data": {
                        "connected": status.connected,
                        "node_id": status.node_id,
                        "short_name": status.short_name,
                        "nodes_count": status.nodes_count,
                    },
                }
            )

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            # Message size validation
            if len(data) > 1024:
                await websocket.send_json(
                    {"type": "error", "data": {"message": "Message too large"}}
                )
                continue
            # Echo back for keepalive
            await websocket.send_json({"type": "pong", "data": data})

    except WebSocketDisconnect:
        logger.info(
            "WebSocket client %s disconnected from Meshtastic stream", client_id
        )
    except Exception as e:
        logger.error("WebSocket error for client %s: %s", client_id, e)
    finally:
        _meshtastic_ws_manager.disconnect(client_id)


async def _process_event_queue():
    """
    Process events from the queue and broadcast to WebSocket clients.
    Runs as background task to bridge sync callbacks to async WebSocket sends.
    """
    logger.info("Event processor started")
    while True:
        try:
            event_type, data = await _event_queue.get()
            await _broadcast_to_websockets_internal(event_type, data)
        except Exception as e:
            logger.error("Event processor error: %s", e)


async def _broadcast_to_websockets_internal(event_type: str, data: dict):
    """Internal broadcast function (async, called from event processor)."""
    message = {"type": event_type, "data": data}
    await _meshtastic_ws_manager.broadcast(message)


# Reference to the running event loop, set during startup
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def broadcast_to_websockets(event_type: str, data: dict):
    """
    Queue an event for broadcast to WebSocket clients.
    Thread-safe: uses call_soon_threadsafe since meshtastic callbacks
    fire from a background serial reader thread, not the asyncio loop.

    Args:
        event_type: Type of event (e.g., "meshtastic_message")
        data: Event data dict
    """
    try:
        if _event_loop is not None and _event_loop.is_running():
            _event_loop.call_soon_threadsafe(
                _event_queue.put_nowait, (event_type, data)
            )
        else:
            logger.warning("No event loop available for WebSocket broadcast")
    except Exception as e:
        logger.error("Failed to queue WebSocket event: %s", e)
