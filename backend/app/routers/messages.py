"""Message management endpoints"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import Message
from app.services.mesh_store import MeshStore
from app.services.reticulum_service import ReticulumBridge

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Global mesh store instance - will be set by main.py
mesh_store: Optional[MeshStore] = None

# Global reticulum bridge - will be set by main.py
reticulum: Optional[ReticulumBridge] = None

# Export for testing and internal use
__all__ = ["router"]


class MessageCreate(BaseModel):
    """Message creation payload"""

    sender_id: str = Field(..., max_length=64, description="Sending node ID")
    recipient_id: Optional[str] = Field(
        None, max_length=64, description="Target node ID (null for broadcast)"
    )
    content: str = Field(..., max_length=1024, description="Message content")
    hops: int = Field(0, ge=0, description="Number of hops to destination")


class MessageSend(BaseModel):
    """Reticulum message send payload"""

    destination_hash: str = Field(
        ..., max_length=32, description="Destination identity hash (hex)"
    )
    content: str = Field(..., max_length=1024, description="Message content")


def _get_node_ids() -> set[str]:
    """Get all valid node IDs from the mesh store"""
    if not mesh_store:
        return set()

    return {node.id for node in mesh_store.get_all_nodes()}


@router.get("", response_model=list[Message])
async def get_messages(
    sender_id: Optional[str] = Query(None, description="Filter by sender node ID"),
    recipient_id: Optional[str] = Query(
        None, description="Filter by recipient node ID"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of messages to return"
    ),
    cursor: Optional[str] = Query(
        None, description="Pagination cursor (message ID to start after)"
    ),
):
    """
    Get messages with optional filters and pagination

    Returns a list of messages from the mesh network with optional filtering
    by sender, recipient, and cursor-based pagination.

    Args:
        sender_id: Filter messages by sender node ID
        recipient_id: Filter messages by recipient node ID
        limit: Maximum number of messages to return (1-1000)
        cursor: Message ID to start after (for pagination)

    Returns:
        List of messages matching the filter criteria (sorted newest first)
    """
    if not mesh_store:
        return []

    # Get all messages sorted by timestamp (newest first)
    sorted_messages = mesh_store.get_all_messages()

    # Apply sender filter
    if sender_id:
        sorted_messages = [m for m in sorted_messages if m.sender_id == sender_id]

    # Apply recipient filter
    if recipient_id:
        sorted_messages = [m for m in sorted_messages if m.recipient_id == recipient_id]

    # Apply cursor pagination
    if cursor:
        # Find the position of the cursor message
        cursor_found = False
        filtered_messages = []
        for msg in sorted_messages:
            if cursor_found:
                filtered_messages.append(msg)
            elif msg.id == cursor:
                cursor_found = True
        sorted_messages = filtered_messages

    # Apply limit
    sorted_messages = sorted_messages[:limit]

    return sorted_messages


@router.get("/{message_id}", response_model=Message)
async def get_message(message_id: str):
    """
    Get a specific message by ID

    Args:
        message_id: Unique message identifier

    Returns:
        Message details

    Raises:
        HTTPException: 404 if message not found
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    message = mesh_store.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")

    return message


@router.post("", response_model=Message, status_code=201)
async def create_message(payload: MessageCreate):
    """
    Send a new message in the mesh network

    Args:
        payload: Message creation data

    Returns:
        Created message with generated ID and timestamp

    Raises:
        HTTPException: 400 if sender or recipient doesn't exist
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    # Generate message ID
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    # Create message
    message = Message(
        id=message_id,
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        content=payload.content,
        timestamp=datetime.now(timezone.utc),
        hops=payload.hops,
    )

    try:
        created_message = mesh_store.add_message(message)
        return created_message
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{message_id}", status_code=204)
async def delete_message(message_id: str):
    """
    Delete a message from the store

    Args:
        message_id: Message to delete

    Raises:
        HTTPException: 404 if message not found
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    removed = mesh_store.remove_message(message_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")


@router.post("/send", status_code=202)
async def send_message(payload: MessageSend):
    """
    Send a message via Reticulum LXMF.

    This endpoint queues a message for delivery over the mesh network using
    Reticulum's LXMF protocol. Messages are delivered asynchronously.

    Args:
        payload: Message send data (destination hash, content)

    Returns:
        Acknowledgment with message ID

    Raises:
        HTTPException: 503 if Reticulum unavailable, 400 if send fails
    """
    if not reticulum or not reticulum.available:
        raise HTTPException(
            status_code=503,
            detail="Reticulum not available. Message sending requires RNS/LXMF.",
        )

    try:
        # Send via Reticulum
        success = reticulum.send_message(
            dest_hash=payload.destination_hash, content=payload.content
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to send message via Reticulum"
            )

        # Generate message ID for tracking
        message_id = f"lxmf_{uuid.uuid4().hex[:12]}"

        logger.info(
            f"Message {message_id} queued for delivery to {payload.destination_hash}"
        )

        return {
            "status": "accepted",
            "message_id": message_id,
            "destination": payload.destination_hash,
            "note": "Message queued for delivery via LXMF",
        }

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
