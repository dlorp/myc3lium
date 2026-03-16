"""Node management endpoints"""

import random
from datetime import UTC, datetime, timedelta
from typing import List

from fastapi import APIRouter, HTTPException

from app.models import Node

router = APIRouter(prefix="/api/nodes", tags=["nodes"])

# Mock data store (in-memory for development)
_mock_nodes: List[Node] = []


def _generate_mock_data():
    """Generate mock node data for development"""
    if _mock_nodes:
        return  # Already initialized

    node_types = ["SPORE", "HYPHA", "FROND", "RHIZOME"]
    statuses = ["online", "offline", "degraded"]
    callsigns = [
        "relay-alpha", "sensor-beta", "gateway-one", "hub-central",
        "edge-north", "bridge-south", "spore-cluster", "myco-root"
    ]

    for i, callsign in enumerate(callsigns):
        node = Node(
            id=f"node_{i+1:03d}",
            type=random.choice(node_types),
            callsign=callsign,
            status=random.choices(statuses, weights=[0.7, 0.1, 0.2])[0],
            rssi=random.randint(-90, -30) if random.random() > 0.2 else None,
            battery=random.randint(10, 100) if random.random() > 0.3 else None,
            last_seen=datetime.now(UTC) - timedelta(seconds=random.randint(0, 3600)),
            position={
                "lat": 61.2181 + random.uniform(-0.5, 0.5),
                "lon": -149.9003 + random.uniform(-0.5, 0.5)
            } if random.random() > 0.3 else None
        )
        _mock_nodes.append(node)


@router.get("", response_model=List[Node])
async def get_nodes():
    """
    Get all mesh network nodes
    
    Returns a list of all nodes in the mycelial network with their current status,
    signal strength, battery levels, and last seen timestamps.
    """
    _generate_mock_data()
    return _mock_nodes


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
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    for node in _mock_nodes:
        if node.id == node_id:
            node.status = status
            node.last_seen = datetime.now(UTC)
            return node
    
    raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
