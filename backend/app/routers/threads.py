"""Thread management endpoints"""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import Thread
from app.services.mesh_store import MeshStore

router = APIRouter(prefix="/api/threads", tags=["threads"])

# Global mesh store instance - will be set by main.py
mesh_store: Optional[MeshStore] = None


class ThreadPatch(BaseModel):
    """Partial thread update payload"""

    quality: Optional[float] = Field(None, ge=0.0, le=1.0)
    latency: Optional[int] = None
    rssi: Optional[int] = None


@router.get("", response_model=list[Thread])
async def get_threads(
    node_id: Optional[str] = Query(
        None, description="Filter by node ID (source or target)"
    ),
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
    if not mesh_store:
        return []

    filtered_threads = mesh_store.get_all_threads()

    if node_id:
        filtered_threads = [
            t
            for t in filtered_threads
            if t.source_id == node_id or t.target_id == node_id
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
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    thread = mesh_store.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    return thread


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
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    # Apply partial updates
    update_data = patch.model_dump(exclude_unset=True)
    update_data["established"] = datetime.now(timezone.utc)

    updated_thread = mesh_store.update_thread(thread_id, **update_data)
    if not updated_thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    return updated_thread


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(thread_id: str):
    """
    Delete a thread from the network

    Args:
        thread_id: Thread to delete

    Raises:
        HTTPException: 404 if thread not found
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    removed = mesh_store.remove_thread(thread_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
