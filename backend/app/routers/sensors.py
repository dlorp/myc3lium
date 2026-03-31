"""Sensor telemetry endpoints — environmental + device metrics from mesh nodes."""

import logging

from fastapi import APIRouter, HTTPException, Path, Query

from app.models import SensorData
from app.services.mock_data import MeshDataSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["sensors"])

# Global data source instance — set by main.py
_data_source: MeshDataSource | None = None

NODE_ID_PATTERN = r"^[a-zA-Z0-9_!-]{1,64}$"


def set_data_source(data_source: MeshDataSource):
    """
    Inject data source dependency (called by main.py)

    Args:
        data_source: Live or mock data source
    """
    global _data_source
    _data_source = data_source


@router.get("", response_model=list[SensorData])
async def get_all_sensor_data(
    limit: int = Query(
        default=500, ge=1, le=2000, description="Max readings to return"
    ),
):
    """
    Bulk fetch sensor data for all nodes.

    Returns a flat list of SensorData objects across all nodes.
    P400 groups them client-side by node_id.

    Args:
        limit: Maximum number of sensor readings to return (default 500, max 2000)

    Returns:
        List of sensor readings (temperature history, humidity, pressure per node)
    """
    if not _data_source:
        raise HTTPException(status_code=503, detail="Data source not initialized")

    nodes = _data_source.get_nodes()
    result: list[SensorData] = []
    for node in nodes:
        result.extend(_data_source.get_sensor_data(node.id))
        if len(result) >= limit:
            break
    return result[:limit]


@router.get("/{node_id}", response_model=list[SensorData])
async def get_node_sensor_data(
    node_id: str = Path(..., pattern=NODE_ID_PATTERN),
):
    """
    Sensor data for a single node.

    Returns an empty list if the node exists but has no sensor readings yet.

    Args:
        node_id: Node identifier

    Returns:
        List of sensor readings for the specified node

    Raises:
        HTTPException: 404 if node does not exist, 503 if data source uninitialized
    """
    if not _data_source:
        raise HTTPException(status_code=503, detail="Data source not initialized")

    # Check node existence independently of sensor data
    node_ids = {n.id for n in _data_source.get_nodes()}
    if node_id not in node_ids:
        raise HTTPException(status_code=404, detail="Node not found")

    return _data_source.get_sensor_data(node_id)
