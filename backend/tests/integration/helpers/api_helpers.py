"""Helper functions for integration test API interactions"""

from datetime import datetime
from typing import Optional

from fastapi.testclient import TestClient


def create_thread(
    client: TestClient,
    source_id: str,
    target_id: str,
    radio_type: str = "LoRa",
    quality: float = 0.85,
) -> dict:
    """
    Create a thread via API

    Args:
        client: FastAPI test client
        source_id: Source node ID
        target_id: Target node ID
        radio_type: Radio type (LoRa, HaLow, WiFi)
        quality: Connection quality (0-1)

    Returns:
        Created thread data
    """
    # Note: Thread creation is not yet implemented in the API
    # This helper is prepared for future API endpoint
    raise NotImplementedError("Thread creation API not yet implemented")


def get_thread(client: TestClient, thread_id: str) -> dict:
    """
    Get a thread by ID

    Args:
        client: FastAPI test client
        thread_id: Thread identifier

    Returns:
        Thread data or None if not found
    """
    response = client.get(f"/api/threads/{thread_id}")
    if response.status_code == 200:
        return response.json()
    return None


def create_message(
    client: TestClient,
    sender_id: str,
    content: str,
    recipient_id: Optional[str] = None,
    hops: int = 0,
) -> dict:
    """
    Create a message via API

    Args:
        client: FastAPI test client
        sender_id: Sending node ID
        content: Message content
        recipient_id: Target node ID (None for broadcast)
        hops: Number of hops

    Returns:
        Created message data
    """
    payload = {
        "sender_id": sender_id,
        "content": content,
        "hops": hops,
    }
    if recipient_id:
        payload["recipient_id"] = recipient_id

    response = client.post("/api/messages", json=payload)
    assert response.status_code == 201, f"Failed to create message: {response.text}"
    return response.json()


def get_message(client: TestClient, message_id: str) -> Optional[dict]:
    """
    Get a message by ID

    Args:
        client: FastAPI test client
        message_id: Message identifier

    Returns:
        Message data or None if not found
    """
    response = client.get(f"/api/messages/{message_id}")
    if response.status_code == 200:
        return response.json()
    return None


def get_messages(
    client: TestClient,
    sender_id: Optional[str] = None,
    recipient_id: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """
    Get messages with optional filters

    Args:
        client: FastAPI test client
        sender_id: Filter by sender
        recipient_id: Filter by recipient
        limit: Max number of messages

    Returns:
        List of messages
    """
    params = {"limit": limit}
    if sender_id:
        params["sender_id"] = sender_id
    if recipient_id:
        params["recipient_id"] = recipient_id

    response = client.get("/api/messages", params=params)
    assert response.status_code == 200, f"Failed to get messages: {response.text}"
    return response.json()


def verify_message_structure(message: dict):
    """
    Verify that a message has the correct structure

    Args:
        message: Message data to verify

    Raises:
        AssertionError: If structure is invalid
    """
    required_fields = ["id", "sender_id", "content", "timestamp", "hops"]
    for field in required_fields:
        assert field in message, f"Message missing required field: {field}"

    # recipient_id is optional (can be None for broadcast)
    assert "recipient_id" in message

    # Verify timestamp is valid ISO format
    assert isinstance(message["timestamp"], str)
    datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))


def verify_thread_structure(thread: dict):
    """
    Verify that a thread has the correct structure

    Args:
        thread: Thread data to verify

    Raises:
        AssertionError: If structure is invalid
    """
    required_fields = [
        "id",
        "source_id",
        "target_id",
        "radio_type",
        "quality",
        "established",
    ]
    for field in required_fields:
        assert field in thread, f"Thread missing required field: {field}"

    # Verify quality is in valid range
    assert 0 <= thread["quality"] <= 1, f"Invalid quality: {thread['quality']}"

    # Verify radio_type is valid
    assert thread["radio_type"] in ["LoRa", "HaLow", "WiFi"]

    # Verify timestamp is valid ISO format
    assert isinstance(thread["established"], str)
    datetime.fromisoformat(thread["established"].replace("Z", "+00:00"))
