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
    global _service, _event_processor_task
    _service = service

    # Start event processor if not already running
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
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


# WebSocket connections pool
_ws_connections: list[WebSocket] = []


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Meshtastic updates.

    Streams:
        - New messages
        - Node updates
        - Status changes
    """
    await websocket.accept()
    _ws_connections.append(websocket)
    logger.info("WebSocket client connected to Meshtastic stream")

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

        # Keep connection alive and listen for close
        while True:
            # Wait for client messages (ping/pong)
            data = await websocket.receive_text()
            # Echo back for keepalive
            await websocket.send_json({"type": "pong", "data": data})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from Meshtastic stream")
        _ws_connections.remove(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)


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
    """
    Internal broadcast function (async, called from event processor).
    """
    if not _ws_connections:
        return

    message = {"type": event_type, "data": data}

    # Send to all connected clients
    disconnected = []
    for ws in _ws_connections:
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.warning("Failed to send to WebSocket client: %s", e)
            disconnected.append(ws)

    # Clean up disconnected clients
    for ws in disconnected:
        _ws_connections.remove(ws)


def broadcast_to_websockets(event_type: str, data: dict):
    """
    Queue an event for broadcast to WebSocket clients.
    Thread-safe: can be called from sync Meshtastic callbacks.

    Args:
        event_type: Type of event (e.g., "meshtastic_message")
        data: Event data dict
    """
    try:
        _event_queue.put_nowait((event_type, data))
    except Exception as e:
        logger.error("Failed to queue WebSocket event: %s", e)
