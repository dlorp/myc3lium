"""Message management endpoints"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import Message

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Mock data store (in-memory for development)
_mock_messages: list[Message] = []

# Export for testing and internal use
__all__ = ["router", "_mock_messages"]


class MessageCreate(BaseModel):
    """Message creation payload"""

    sender_id: str = Field(..., max_length=64, description="Sending node ID")
    recipient_id: Optional[str] = Field(
        None, max_length=64, description="Target node ID (null for broadcast)"
    )
    content: str = Field(..., max_length=1024, description="Message content")
    hops: int = Field(0, ge=0, description="Number of hops to destination")


def _get_node_ids() -> set[str]:
    """Get all valid node IDs from the nodes router"""
    # Import here to avoid circular dependency
    from app.routers import nodes

    return {node.id for node in nodes._mock_nodes}


@router.get("", response_model=list[Message])
async def get_messages(
    sender_id: Optional[str] = Query(None, description="Filter by sender node ID"),
    recipient_id: Optional[str] = Query(None, description="Filter by recipient node ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of messages to return"),
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
    # Sort messages by timestamp (newest first)
    sorted_messages = sorted(_mock_messages, key=lambda m: m.timestamp, reverse=True)

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
    for message in _mock_messages:
        if message.id == message_id:
            return message

    raise HTTPException(status_code=404, detail=f"Message {message_id} not found")


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
    # Get valid node IDs
    valid_node_ids = _get_node_ids()

    # Validate sender exists
    if payload.sender_id not in valid_node_ids:
        raise HTTPException(
            status_code=400, detail=f"Sender node {payload.sender_id} does not exist"
        )

    # Validate recipient exists (if not broadcast)
    if payload.recipient_id and payload.recipient_id not in valid_node_ids:
        raise HTTPException(
            status_code=400, detail=f"Recipient node {payload.recipient_id} does not exist"
        )

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

    _mock_messages.append(message)
    return message


@router.delete("/{message_id}", status_code=204)
async def delete_message(message_id: str):
    """
    Delete a message from the store

    Args:
        message_id: Message to delete

    Raises:
        HTTPException: 404 if message not found
    """
    for i, message in enumerate(_mock_messages):
        if message.id == message_id:
            _mock_messages.pop(i)
            return

    raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
