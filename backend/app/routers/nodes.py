"""Node management endpoints"""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import Node
from app.services.mesh_store import MeshStore

router = APIRouter(prefix="/api/nodes", tags=["nodes"])

# Global mesh store instance - will be set by main.py
mesh_store: Optional[MeshStore] = None

# Export for testing and internal use
__all__ = ["router", "_mock_nodes"]


class NodePatch(BaseModel):
    """Partial node update payload"""

    type: Optional[Literal["SPORE", "HYPHA", "FROND", "RHIZOME"]] = None
    callsign: Optional[str] = None
    status: Optional[Literal["online", "offline", "degraded"]] = None
    rssi: Optional[int] = None
    battery: Optional[int] = Field(None, ge=0, le=100)
    position: Optional[dict[str, float]] = None


@router.get("", response_model=list[Node])
async def get_nodes(
    status: Optional[Literal["online", "offline", "degraded"]] = Query(
        None, description="Filter by node status"
    ),
    type: Optional[Literal["SPORE", "HYPHA", "FROND", "RHIZOME"]] = Query(
        None, description="Filter by node type"
    ),
):
    """
    Get all mesh network nodes with optional filters

    Returns a list of all nodes in the mycelial network with their current status,
    signal strength, battery levels, and last seen timestamps.

    Args:
        status: Filter nodes by status (online/offline/degraded)
        type: Filter nodes by type (SPORE/HYPHA/FROND/RHIZOME)

    Returns:
        List of nodes matching the filter criteria
    """
    if not mesh_store:
        return []

    nodes = mesh_store.get_all_nodes()

    if status:
        nodes = [n for n in nodes if n.status == status]

    if type:
        nodes = [n for n in nodes if n.type == type]

    return nodes


@router.get("/{node_id}", response_model=Node)
async def get_node(node_id: str):
    """
    Get a specific node by ID

    Args:
        node_id: Unique node identifier

    Returns:
        Node details

    Raises:
        HTTPException: 404 if node not found
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    node = mesh_store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    return node


@router.post("", response_model=Node, status_code=201)
async def create_node(node: Node):
    """
    Create a new node in the mesh network

    Args:
        node: Node to create

    Returns:
        Created node

    Raises:
        HTTPException: 400 if node with same ID already exists
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    try:
        created_node = mesh_store.add_node(node)
        return created_node
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{node_id}", response_model=Node)
async def update_node(node_id: str, patch: NodePatch):
    """
    Update node properties

    Partial update of a node. Only provided fields will be updated.

    Args:
        node_id: Node to update
        patch: Fields to update

    Returns:
        Updated node

    Raises:
        HTTPException: 404 if node not found
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    # Apply partial updates
    update_data = patch.model_dump(exclude_unset=True)
    update_data["last_seen"] = datetime.now(timezone.utc)

    updated_node = mesh_store.update_node(node_id, **update_data)
    if not updated_node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    return updated_node


@router.delete("/{node_id}", status_code=204)
async def delete_node(node_id: str):
    """
    Delete a node from the network

    Args:
        node_id: Node to delete

    Raises:
        HTTPException: 404 if node not found
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    removed = mesh_store.remove_node(node_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")


@router.post("/{node_id}/status", response_model=Node)
async def update_node_status(node_id: str, status: str):
    """
    Update node status

    Args:
        node_id: Node to update
        status: New status (online/offline/degraded)

    Returns:
        Updated node

    Raises:
        HTTPException: 404 if node not found, 400 if invalid status
    """
    if not mesh_store:
        raise HTTPException(status_code=503, detail="Mesh store not initialized")

    valid_statuses = ["online", "offline", "degraded"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    updated_node = mesh_store.update_node(
        node_id, status=status, last_seen=datetime.now(timezone.utc)
    )
    if not updated_node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    return updated_node
