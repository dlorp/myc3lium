"""Sensor telemetry endpoints — environmental + device metrics from mesh nodes."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path, Query

from app.models import SensorData
from app.services.mesh_store import MeshStore
from app.services.meshtastic_service import MeshtasticService
from app.services.mock_data import MeshDataSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["sensors"])

# Global service instances — set by main.py
_data_source: MeshDataSource | None = None
_mesh_store: MeshStore | None = None
_meshtastic_service: MeshtasticService | None = None

NODE_ID_PATTERN = r"^[a-zA-Z0-9_!-]{1,64}$"


def set_data_source(data_source: MeshDataSource):
    """Inject data source dependency (called by main.py)"""
    global _data_source
    _data_source = data_source


def set_mesh_store(mesh_store: MeshStore):
    """Inject mesh store for node lookup (called by main.py)"""
    global _mesh_store
    _mesh_store = mesh_store


def set_meshtastic_service(service: MeshtasticService):
    """Inject Meshtastic service for device metrics (called by main.py)"""
    global _meshtastic_service
    _meshtastic_service = service


def _meshtastic_sensor_data() -> list[SensorData]:
    """
    Synthesize SensorData from Meshtastic device metrics.

    Converts voltage, battery_level, channel_utilization, and air_util_tx
    from each Meshtastic node into SensorData objects that P400 can display.
    """
    if not _meshtastic_service or not _meshtastic_service.available:
        return []

    result: list[SensorData] = []

    for mnode in _meshtastic_service.get_nodes():
        node_id = f"mesh_{mnode.node_id}"
        ts = datetime.fromtimestamp(mnode.last_heard, tz=timezone.utc)

        if mnode.voltage is not None:
            result.append(
                SensorData(
                    node_id=node_id,
                    sensor_type="voltage",
                    value=mnode.voltage,
                    unit="V",
                    timestamp=ts,
                )
            )

        if mnode.battery_level is not None:
            result.append(
                SensorData(
                    node_id=node_id,
                    sensor_type="battery",
                    value=float(mnode.battery_level),
                    unit="percent",
                    timestamp=ts,
                )
            )

        if mnode.channel_utilization is not None:
            result.append(
                SensorData(
                    node_id=node_id,
                    sensor_type="channel_utilization",
                    value=mnode.channel_utilization,
                    unit="percent",
                    timestamp=ts,
                )
            )

        if mnode.air_util_tx is not None:
            result.append(
                SensorData(
                    node_id=node_id,
                    sensor_type="air_util_tx",
                    value=mnode.air_util_tx,
                    unit="percent",
                    timestamp=ts,
                )
            )

    return result


@router.get("", response_model=list[SensorData])
async def get_all_sensor_data(
    limit: int = Query(
        default=500, ge=1, le=2000, description="Max readings to return"
    ),
):
    """
    Bulk fetch sensor data for all nodes.

    Aggregates environmental sensor data from the data source (BATMAN/mock nodes)
    and device metrics from Meshtastic nodes (voltage, battery, channel utilization).

    Args:
        limit: Maximum number of sensor readings to return (default 500, max 2000)

    Returns:
        List of sensor readings across all node types
    """
    if not _data_source:
        raise HTTPException(status_code=503, detail="Data source not initialized")

    result: list[SensorData] = []

    # Environmental sensors from data source (BATMAN/mock nodes)
    for node in _data_source.get_nodes():
        result.extend(_data_source.get_sensor_data(node.id))
        if len(result) >= limit:
            return result[:limit]

    # Device metrics from Meshtastic nodes
    result.extend(_meshtastic_sensor_data())

    return result[:limit]


@router.get("/{node_id}", response_model=list[SensorData])
async def get_node_sensor_data(
    node_id: str = Path(..., pattern=NODE_ID_PATTERN),
):
    """
    Sensor data for a single node.

    For BATMAN/mock nodes: returns environmental data (temperature, humidity, pressure).
    For Meshtastic nodes (mesh_ prefix): returns device metrics (voltage, battery, etc).

    Args:
        node_id: Node identifier

    Returns:
        List of sensor readings for the specified node
    """
    if not _data_source:
        raise HTTPException(status_code=503, detail="Data source not initialized")

    # Check if it's a Meshtastic-bridged node
    if node_id.startswith("mesh_") and _meshtastic_service:
        # Verify node exists in mesh store
        if _mesh_store and not _mesh_store.get_node(node_id):
            raise HTTPException(status_code=404, detail="Node not found")

        return [sd for sd in _meshtastic_sensor_data() if sd.node_id == node_id]

    # BATMAN/mock node — check data source
    data_source_ids = {n.id for n in _data_source.get_nodes()}
    if node_id not in data_source_ids:
        # Also check mesh store for any node type
        if _mesh_store and _mesh_store.get_node(node_id):
            return []  # Node exists but no sensor data yet
        raise HTTPException(status_code=404, detail="Node not found")

    return _data_source.get_sensor_data(node_id)
