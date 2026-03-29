"""
Bridge between MeshtasticService and MeshStore.

Converts Meshtastic radio nodes into the unified Node/Thread models
so they appear in the P200 lattice map via /api/nodes and /api/threads.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Literal

from app.models import Node, Thread

if TYPE_CHECKING:
    from app.services.mesh_store import MeshStore
    from app.services.meshtastic_service import MeshtasticNode

logger = logging.getLogger(__name__)

# Prefix for Meshtastic node IDs in MeshStore to avoid collisions with BATMAN nodes
MESH_ID_PREFIX = "mesh_"

# Status thresholds (seconds since last_heard)
_ONLINE_THRESHOLD = 300  # 5 minutes
_DEGRADED_THRESHOLD = 3600  # 1 hour


def _last_heard_to_status(
    last_heard: float,
) -> Literal["online", "offline", "degraded"]:
    """Convert last_heard timestamp to node status."""
    age = time.time() - last_heard
    if age < _ONLINE_THRESHOLD:
        return "online"
    if age < _DEGRADED_THRESHOLD:
        return "degraded"
    return "offline"


def snr_to_quality(snr: float | None) -> float:
    """
    Map SNR (dB) to 0-1 quality score.

    SNR ranges for LoRa:
      > 10 dB  = excellent (1.0)
      0 dB     = decent (0.5)
      < -10 dB = poor (0.1)
    """
    if snr is None:
        return 0.5
    clamped = max(-20.0, min(20.0, snr))
    return round(max(0.05, min(1.0, (clamped + 20.0) / 40.0)), 2)


def snr_to_rssi(snr: float | None) -> int | None:
    """Approximate RSSI from SNR (rough LoRa estimation)."""
    if snr is None:
        return None
    return int(-120 + max(0, snr) * 2)


def meshtastic_node_to_mesh_node(mnode: MeshtasticNode) -> Node:
    """
    Convert a MeshtasticNode dataclass into a MeshStore Node model.

    Args:
        mnode: MeshtasticNode from MeshtasticService

    Returns:
        Node model suitable for MeshStore
    """
    raw_callsign = mnode.short_name or mnode.long_name or mnode.node_id
    return Node(
        id=f"{MESH_ID_PREFIX}{mnode.node_id}",
        type="HYPHA",
        callsign=raw_callsign[:32],
        status=_last_heard_to_status(mnode.last_heard),
        rssi=snr_to_rssi(mnode.snr),
        battery=mnode.battery_level,
        last_seen=datetime.fromtimestamp(mnode.last_heard, tz=timezone.utc),
        position=mnode.position or None,
    )


def meshtastic_data_to_mesh_node(data: dict) -> Node:
    """
    Convert a Meshtastic event data dict into a MeshStore Node model.

    Args:
        data: Dict from MeshtasticService callback (meshtastic_node_updated event)

    Returns:
        Node model suitable for MeshStore
    """
    node_id = data.get("node_id", "unknown")
    last_heard = data.get("last_heard", time.time())
    snr = data.get("snr")

    raw_callsign = data.get("short_name") or data.get("long_name") or node_id
    return Node(
        id=f"{MESH_ID_PREFIX}{node_id}",
        type="HYPHA",
        callsign=raw_callsign[:32],
        status=_last_heard_to_status(last_heard),
        rssi=snr_to_rssi(snr),
        battery=data.get("battery_level"),
        last_seen=datetime.fromtimestamp(last_heard, tz=timezone.utc),
        position=data.get("position"),
    )


def create_synthetic_thread(
    node_id: str, local_node_id: str, snr: float | None
) -> Thread:
    """
    Create a synthetic Thread (radio link) between a Meshtastic node and the local node.

    Args:
        node_id: Remote Meshtastic node ID (without prefix)
        local_node_id: Local Meshtastic node ID (without prefix)
        snr: Signal-to-noise ratio from the remote node

    Returns:
        Thread model for MeshStore
    """
    return Thread(
        id=f"thread_{MESH_ID_PREFIX}{node_id}_{MESH_ID_PREFIX}{local_node_id}",
        source_id=f"{MESH_ID_PREFIX}{node_id}",
        target_id=f"{MESH_ID_PREFIX}{local_node_id}",
        radio_type="LoRa",
        rssi=snr_to_rssi(snr),
        quality=snr_to_quality(snr),
        latency=None,
    )


def seed_meshtastic_nodes(
    mesh_store: MeshStore,
    nodes: list[MeshtasticNode],
    local_node_id: str | None,
) -> int:
    """
    Seed MeshStore with initial Meshtastic nodes and synthetic threads.

    Called once at startup after MeshtasticService connects and discovers nodes.

    Args:
        mesh_store: The MeshStore instance
        nodes: List of MeshtasticNode from service.get_nodes()
        local_node_id: The local Meshtastic node ID (for thread creation)

    Returns:
        Number of nodes seeded
    """
    # Pass 1: Seed all nodes first (threads require both endpoints to exist)
    count = 0
    for mnode in nodes:
        try:
            mesh_node = meshtastic_node_to_mesh_node(mnode)
            existing = mesh_store.get_node(mesh_node.id)
            if existing:
                updates = mesh_node.model_dump(exclude={"id"})
                mesh_store.update_node(mesh_node.id, **updates)
            else:
                mesh_store.add_node(mesh_node)
            count += 1
        except Exception as e:
            logger.warning("Failed to seed Meshtastic node %s: %s", mnode.node_id, e)

    # Pass 2: Create synthetic threads (all nodes now exist in store)
    if local_node_id:
        for mnode in nodes:
            if mnode.node_id == local_node_id:
                continue
            try:
                thread = create_synthetic_thread(
                    mnode.node_id, local_node_id, mnode.snr
                )
                existing_thread = mesh_store.get_thread(thread.id)
                if existing_thread:
                    updates = thread.model_dump(exclude={"id"})
                    mesh_store.update_thread(thread.id, **updates)
                else:
                    mesh_store.add_thread(thread)
            except Exception as e:
                logger.warning("Failed to create thread for %s: %s", mnode.node_id, e)

    logger.info("Seeded %d Meshtastic nodes into MeshStore", count)
    return count


def create_store_sync_callback(
    mesh_store: MeshStore, local_node_id: str | None
) -> Callable[[str, dict], None]:
    """
    Create a callback function that syncs Meshtastic events to MeshStore.

    This is registered as a ws_callback on MeshtasticService so that
    real-time node updates flow into MeshStore (and thus to /api/nodes).

    Args:
        mesh_store: The MeshStore instance
        local_node_id: The local Meshtastic node ID

    Returns:
        Callback function with signature (event_type: str, data: dict) -> None
    """

    def _sync_callback(event_type: str, data: dict) -> None:
        try:
            if event_type == "meshtastic_node_updated":
                mesh_node = meshtastic_data_to_mesh_node(data)
                existing = mesh_store.get_node(mesh_node.id)
                if existing:
                    updates = mesh_node.model_dump(exclude={"id"})
                    mesh_store.update_node(mesh_node.id, **updates)
                else:
                    mesh_store.add_node(mesh_node)

                # Update synthetic thread (only if both endpoints exist)
                node_id = data.get("node_id")
                if local_node_id and node_id and node_id != local_node_id:
                    local_mesh_id = f"{MESH_ID_PREFIX}{local_node_id}"
                    if mesh_store.get_node(local_mesh_id):
                        thread = create_synthetic_thread(
                            node_id, local_node_id, data.get("snr")
                        )
                        existing_thread = mesh_store.get_thread(thread.id)
                        if existing_thread:
                            updates = thread.model_dump(exclude={"id"})
                            mesh_store.update_thread(thread.id, **updates)
                        else:
                            mesh_store.add_thread(thread)

        except Exception as e:
            logger.error("Error syncing Meshtastic to MeshStore: %s", e)

    return _sync_callback
