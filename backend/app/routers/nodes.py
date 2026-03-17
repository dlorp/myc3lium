"""Node management endpoints"""

import random
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, cast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import Node

router = APIRouter(prefix="/api/nodes", tags=["nodes"])

# Mock data store (in-memory for development)
_mock_nodes: list[Node] = []


class NodePatch(BaseModel):
    """Partial node update payload"""

    type: Optional[Literal["SPORE", "HYPHA", "FROND", "RHIZOME"]] = None
    callsign: Optional[str] = None
    status: Optional[Literal["online", "offline", "degraded"]] = None
    rssi: Optional[int] = None
    battery: Optional[int] = Field(None, ge=0, le=100)
    position: Optional[dict[str, float]] = None


def _generate_mock_data():
    """Generate mock node data for development"""
    if _mock_nodes:
        return  # Already initialized

    node_types = ["SPORE", "HYPHA", "FROND", "RHIZOME"]
    statuses = ["online", "offline", "degraded"]
    callsigns = [
        "relay-alpha",
        "sensor-beta",
        "gateway-one",
        "hub-central",
        "edge-north",
        "bridge-south",
        "spore-cluster",
        "myco-root",
    ]

    for i, callsign in enumerate(callsigns):
        node = Node(
            id=f"node_{i + 1:03d}",
            type=cast(
                Literal["SPORE", "HYPHA", "FROND", "RHIZOME"],
                random.choice(node_types),
            ),
            callsign=callsign,
            status=cast(
                Literal["online", "offline", "degraded"],
                random.choices(statuses, weights=[0.7, 0.1, 0.2])[0],
            ),
            rssi=random.randint(-90, -30) if random.random() > 0.2 else None,
            battery=random.randint(10, 100) if random.random() > 0.3 else None,
            last_seen=datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 3600)),
            position={
                "lat": 61.2181 + random.uniform(-0.5, 0.5),
                "lon": -149.9003 + random.uniform(-0.5, 0.5),
            }
            if random.random() > 0.3
            else None,
        )
        _mock_nodes.append(node)


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
    _generate_mock_data()

    filtered_nodes = _mock_nodes

    if status:
        filtered_nodes = [n for n in filtered_nodes if n.status == status]

    if type:
        filtered_nodes = [n for n in filtered_nodes if n.type == type]

    return filtered_nodes


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
    _generate_mock_data()

    for node in _mock_nodes:
        if node.id == node_id:
            return node

    raise HTTPException(status_code=404, detail=f"Node {node_id} not found")


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
    _generate_mock_data()

    for node in _mock_nodes:
        if node.id == node_id:
            # Apply partial updates
            update_data = patch.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(node, field, value)

            # Update timestamp
            node.last_seen = datetime.now(timezone.utc)
            return node

    raise HTTPException(status_code=404, detail=f"Node {node_id} not found")


@router.delete("/{node_id}", status_code=204)
async def delete_node(node_id: str):
    """
    Delete a node from the network

    Args:
        node_id: Node to delete

    Raises:
        HTTPException: 404 if node not found
    """
    _generate_mock_data()

    for i, node in enumerate(_mock_nodes):
        if node.id == node_id:
            _mock_nodes.pop(i)
            return

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
    _generate_mock_data()

    valid_statuses = ["online", "offline", "degraded"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    for node in _mock_nodes:
        if node.id == node_id:
            node.status = cast(Literal["online", "offline", "degraded"], status)
            node.last_seen = datetime.now(timezone.utc)
            return node

    raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
