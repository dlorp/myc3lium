"""Thread management endpoints"""

import random
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, cast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import Thread

router = APIRouter(prefix="/api/threads", tags=["threads"])

# Mock data store (in-memory for development)
_mock_threads: list[Thread] = []


class ThreadPatch(BaseModel):
    """Partial thread update payload"""

    quality: Optional[float] = Field(None, ge=0.0, le=1.0)
    latency: Optional[int] = None
    rssi: Optional[int] = None


def _generate_mock_data():
    """Generate mock thread data for development"""
    if _mock_threads:
        return  # Already initialized

    # Create threads between mock nodes (assuming node_001 through node_008)
    thread_configs = [
        ("node_001", "node_002", "LoRa"),
        ("node_001", "node_003", "HaLow"),
        ("node_002", "node_004", "LoRa"),
        ("node_003", "node_005", "WiFi"),
        ("node_004", "node_006", "HaLow"),
        ("node_005", "node_007", "LoRa"),
        ("node_006", "node_008", "WiFi"),
        ("node_007", "node_008", "HaLow"),
        ("node_001", "node_004", "LoRa"),
        ("node_002", "node_005", "WiFi"),
        ("node_003", "node_006", "HaLow"),
    ]

    for i, (source_id, target_id, radio_type) in enumerate(thread_configs):
        thread = Thread(
            id=f"thread_{i + 1:03d}",
            source_id=source_id,
            target_id=target_id,
            radio_type=cast(Literal["LoRa", "HaLow", "WiFi"], radio_type),
            rssi=random.randint(-95, -30) if random.random() > 0.1 else None,
            quality=round(random.uniform(0.3, 0.99), 2),
            latency=random.randint(5, 150) if random.random() > 0.2 else None,
            established=datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 86400)),
        )
        _mock_threads.append(thread)


@router.get("", response_model=list[Thread])
async def get_threads(
    node_id: Optional[str] = Query(None, description="Filter by node ID (source or target)"),
    radio_type: Optional[Literal["LoRa", "HaLow", "WiFi"]] = Query(
        None, description="Filter by radio technology type"
    ),
    min_quality: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Filter by minimum quality threshold"
    ),
):
    """
    Get all mesh network threads with optional filters

    Returns a list of all threads (radio links) in the mycelial network with their
    quality metrics, latency, and signal strength.

    Args:
        node_id: Filter threads connected to a specific node (as source or target)
        radio_type: Filter threads by radio technology (LoRa/HaLow/WiFi)
        min_quality: Filter threads with quality >= threshold

    Returns:
        List of threads matching the filter criteria
    """
    _generate_mock_data()

    filtered_threads = _mock_threads

    if node_id:
        filtered_threads = [
            t for t in filtered_threads if t.source_id == node_id or t.target_id == node_id
        ]

    if radio_type:
        filtered_threads = [t for t in filtered_threads if t.radio_type == radio_type]

    if min_quality is not None:
        filtered_threads = [t for t in filtered_threads if t.quality >= min_quality]

    return filtered_threads


@router.get("/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """
    Get a specific thread by ID

    Args:
        thread_id: Unique thread identifier

    Returns:
        Thread details

    Raises:
        HTTPException: 404 if thread not found
    """
    _generate_mock_data()

    for thread in _mock_threads:
        if thread.id == thread_id:
            return thread

    raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")


@router.patch("/{thread_id}", response_model=Thread)
async def update_thread(thread_id: str, patch: ThreadPatch):
    """
    Update thread properties

    Partial update of a thread. Only provided fields will be updated.

    Args:
        thread_id: Thread to update
        patch: Fields to update (quality, latency, rssi)

    Returns:
        Updated thread

    Raises:
        HTTPException: 404 if thread not found
    """
    _generate_mock_data()

    for thread in _mock_threads:
        if thread.id == thread_id:
            # Apply partial updates
            update_data = patch.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(thread, field, value)

            # Update timestamp
            thread.established = datetime.now(timezone.utc)
            return thread

    raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(thread_id: str):
    """
    Delete a thread from the network

    Args:
        thread_id: Thread to delete

    Raises:
        HTTPException: 404 if thread not found
    """
    _generate_mock_data()

    for i, thread in enumerate(_mock_threads):
        if thread.id == thread_id:
            _mock_threads.pop(i)
            return

    raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
