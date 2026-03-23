"""
Mesh status and topology endpoints — live data from batctl + Reticulum.

Provides real-time mesh network health monitoring including:
- Overall mesh status (BATMAN-adv + Reticulum)
- Per-radio interface statistics
- Full network topology (nodes + edges)
- BATMAN-adv statistics
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import batctl_service
from app.services.live_data_source import LiveDataSource
from app.services.reticulum_service import ReticulumBridge

router = APIRouter(prefix="/api/mesh", tags=["mesh"])

# Global service instances - will be set by main.py
_data_source: Optional[LiveDataSource] = None
_reticulum: Optional[ReticulumBridge] = None


class MeshStatus(BaseModel):
    """Overall mesh health status"""

    batman: dict  # BATMAN-adv status (originators, neighbors)
    reticulum: dict  # Reticulum status (available, identity, inbox)


class RadioStatus(BaseModel):
    """Per-radio interface status"""

    name: str
    type: str  # HaLow, LoRa, WiFi
    status: str  # up, down
    throughput: Optional[int] = None
    neighbors: int


def set_services(data_source: LiveDataSource, reticulum: ReticulumBridge):
    """
    Inject service dependencies (called by main.py)

    Args:
        data_source: Live or mock data source
        reticulum: Reticulum bridge instance
    """
    global _data_source, _reticulum
    _data_source = data_source
    _reticulum = reticulum


@router.get("/status", response_model=MeshStatus)
async def mesh_status():
    """
    Overall mesh health: BATMAN + Reticulum combined.

    Returns:
        Combined status of BATMAN-adv mesh layer and Reticulum routing layer
    """
    bat_available = batctl_service.is_available()
    originators = batctl_service.get_originators() if bat_available else None
    neighbors = batctl_service.get_neighbors() if bat_available else None

    rns_status = _reticulum.get_status() if _reticulum else None

    return MeshStatus(
        batman={
            "available": bat_available,
            "originator_count": len(originators) if originators else 0,
            "neighbor_count": len(neighbors) if neighbors else 0,
            "interfaces": ["halow0", "lora0"] if bat_available else [],
        },
        reticulum={
            "available": rns_status.available if rns_status else False,
            "identity": rns_status.identity_hash if rns_status else None,
            "address": rns_status.address_hash if rns_status else None,
            "inbox_count": rns_status.inbox_count if rns_status else 0,
        },
    )


@router.get("/radios")
async def radio_status():
    """
    Per-radio interface health.

    Returns:
        Dictionary mapping interface names to RadioStatus objects
    """
    radios = {}

    # Check each radio interface
    for iface, radio_type in [("halow0", "HaLow"), ("lora0", "LoRa")]:
        stats = batctl_service.get_interface_stats(iface)
        # Fix: get_neighbors() takes no arguments, filter by interface instead (H-3)
        all_neighbors = batctl_service.get_neighbors() if stats else None
        neighbors = [n for n in (all_neighbors or []) if n.interface == iface] if all_neighbors else None

        radios[iface] = {
            "name": iface,
            "type": radio_type,
            "status": "up" if stats else "down",
            "throughput": stats.tx_bytes + stats.rx_bytes if stats else None,
            "neighbors": len(neighbors) if neighbors else 0,
            "stats": (
                {
                    "tx_bytes": stats.tx_bytes,
                    "rx_bytes": stats.rx_bytes,
                    "tx_packets": stats.tx_packets,
                    "rx_packets": stats.rx_packets,
                }
                if stats
                else None
            ),
        }

    return radios


@router.get("/topology")
async def mesh_topology():
    """
    Full topology graph for visualization.

    Returns nodes and edges (threads) for rendering the mesh network graph.

    Returns:
        Dictionary with 'nodes' and 'edges' arrays
    """
    if not _data_source:
        raise HTTPException(status_code=503, detail="Data source not initialized")

    nodes = _data_source.get_nodes()
    threads = _data_source.get_threads()

    return {
        "nodes": [n.model_dump() for n in nodes],
        "edges": [t.model_dump() for t in threads],
    }


@router.get("/statistics")
async def mesh_statistics():
    """
    BATMAN-adv network statistics.

    Returns detailed statistics from batctl including packet counts,
    routing table size, and mesh health metrics.

    Returns:
        Dictionary with 'available' flag and optional statistics data
    """
    stats = batctl_service.get_statistics()
    return {"available": stats is not None, "data": stats or {}}
