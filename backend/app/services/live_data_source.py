"""
Hybrid data source with automatic fallback to mock data.

This module provides LiveDataSource, which:
1. Attempts to fetch live BATMAN-adv mesh topology via batctl
2. Attempts to fetch live LXMF messages via Reticulum
3. Falls back gracefully to MockMeshDataSource when live data unavailable
4. Respects USE_LIVE_DATA config flag (defaults to True on Linux, False on Mac)

The fallback is transparent — callers use the same MeshDataSource interface
regardless of whether they're getting live or mock data.
"""

import logging
import os
import platform
from datetime import datetime, timezone
from typing import Optional

from app.models import Message, Node, SensorData, Thread
from app.services import batctl_service, reticulum_service
from app.services.mock_data import MeshDataSource, MockMeshDataSource

logger = logging.getLogger(__name__)

# Configuration: Use live data if environment variable set or running on Linux
_use_live_default = "true" if platform.system() == "Linux" else "false"
USE_LIVE_DATA = os.getenv("MYC3LIUM_USE_LIVE_DATA", _use_live_default).lower() in (
    "true",
    "1",
    "yes",
)


class LiveDataSource(MeshDataSource):
    """
    Mesh data source that pulls from live BATMAN + Reticulum, with mock fallback.

    Usage:
        source = LiveDataSource()
        nodes = source.get_nodes()  # Tries batctl, falls back to mock
        messages = source.get_messages()  # Tries LXMF, falls back to mock
    """

    def __init__(self, use_live: bool = USE_LIVE_DATA):
        """
        Initialize the live data source.

        Args:
            use_live: If True, attempt to use live data sources. If False, use mock only.
        """
        self._use_live = use_live
        self._mock_source = MockMeshDataSource()
        self._reticulum_bridge: Optional[reticulum_service.ReticulumBridge] = None

        # Attempt to start Reticulum bridge if live mode enabled
        if self._use_live:
            try:
                self._reticulum_bridge = reticulum_service.ReticulumBridge()
                if not self._reticulum_bridge.start():
                    logger.warning(
                        "Reticulum bridge failed to start — using mock for messages"
                    )
                    self._reticulum_bridge = None
            except Exception as e:
                logger.warning(
                    "Failed to initialize Reticulum bridge: %s — using mock", e
                )
                self._reticulum_bridge = None

        # Log data source mode
        batctl_available = batctl_service.is_available() if self._use_live else False
        reticulum_available = (
            self._reticulum_bridge.available if self._reticulum_bridge else False
        )

        logger.info(
            "LiveDataSource initialized — USE_LIVE=%s, batctl=%s, reticulum=%s",
            self._use_live,
            batctl_available,
            reticulum_available,
        )

    def get_nodes(self) -> list[Node]:
        """
        Get mesh nodes from live BATMAN data or mock fallback.

        Returns:
            List of Node objects
        """
        if not self._use_live:
            logger.debug("Using mock nodes (live mode disabled)")
            return self._mock_source.get_nodes()

        # Try to get live nodes from batctl
        originators = batctl_service.get_originators()

        if originators is None:
            logger.warning("batctl unavailable — falling back to mock nodes")
            return self._mock_source.get_nodes()

        # Convert batctl originators to Node objects
        nodes = []
        for idx, orig in enumerate(originators):
            # Determine node type based on TQ and interface
            if orig.tq > 240:
                node_type = "HYPHA"  # High-quality relay
            elif orig.tq > 200:
                node_type = "FROND"  # Medium-quality endpoint
            elif orig.tq > 150:
                node_type = "SPORE"  # Low-quality mobile node
            else:
                node_type = "RHIZOME"  # Very weak/intermittent

            # Determine status from last_seen
            if orig.last_seen < 1.0:
                status = "online"
            elif orig.last_seen < 5.0:
                status = "degraded"
            else:
                status = "offline"

            # Convert TQ (0-255) to RSSI estimate (-100 to -40 dBm)
            rssi = int(-100 + (orig.tq / 255.0) * 60)

            node = Node(
                id=orig.mac.replace(":", ""),  # MAC without colons as ID
                type=node_type,
                callsign=f"BATMAN-{orig.mac[-8:].upper()}",  # Last 8 chars of MAC
                status=status,
                rssi=rssi,
                battery=None,  # BATMAN doesn't provide battery info
                last_seen=datetime.now(timezone.utc),
                position=None,  # No GPS data from batctl
            )
            nodes.append(node)

        logger.info("Fetched %d live nodes from batctl", len(nodes))
        return nodes

    def get_threads(self) -> list[Thread]:
        """
        Get mesh threads (connections) from live BATMAN data or mock fallback.

        Returns:
            List of Thread objects
        """
        if not self._use_live:
            logger.debug("Using mock threads (live mode disabled)")
            return self._mock_source.get_threads()

        # Try to get live neighbors from batctl
        neighbors = batctl_service.get_neighbors()

        if neighbors is None:
            logger.warning("batctl neighbors unavailable — falling back to mock threads")
            return self._mock_source.get_threads()

        # Convert batctl neighbors to Thread objects
        threads = []
        for idx, neighbor in enumerate(neighbors):
            # Determine radio type from interface name
            if "wlan" in neighbor.interface.lower():
                radio_type = "WiFi"
            elif "lora" in neighbor.interface.lower():
                radio_type = "LoRa"
            else:
                radio_type = "HaLow"  # Assume HaLow for unknown

            # Convert TQ to quality (0-1 scale)
            quality = neighbor.tq / 255.0

            # Estimate RSSI from TQ
            rssi = int(-100 + (neighbor.tq / 255.0) * 60)

            # Estimate latency based on quality (better quality = lower latency)
            latency = int(10 + (1.0 - quality) * 90)  # 10-100ms range

            # Use MAC as source/target IDs (simplified; real implementation
            # would map to actual node IDs from get_nodes())
            source_id = neighbor.mac.replace(":", "")
            target_id = "local"  # Placeholder for local node

            thread = Thread(
                id=f"thread_{idx:03d}",
                source_id=source_id,
                target_id=target_id,
                radio_type=radio_type,
                rssi=rssi,
                quality=quality,
                latency=latency,
                established=datetime.now(timezone.utc),
            )
            threads.append(thread)

        logger.info("Fetched %d live threads from batctl", len(threads))
        return threads

    def get_messages(self) -> list[Message]:
        """
        Get mesh messages from live LXMF inbox or mock fallback.

        Returns:
            List of Message objects
        """
        if not self._use_live or not self._reticulum_bridge:
            logger.debug("Using mock messages (live mode disabled or Reticulum unavailable)")
            return self._mock_source.get_messages()

        # Fetch LXMF inbox
        try:
            lxmf_messages = self._reticulum_bridge.get_inbox()

            # Convert LXMF messages to Message objects
            messages = []
            for idx, lxmf_msg in enumerate(lxmf_messages):
                msg = Message(
                    id=f"lxmf_{lxmf_msg.source_hash[:8]}_{int(lxmf_msg.timestamp)}",
                    sender_id=lxmf_msg.source_hash,
                    recipient_id=None,  # Broadcast (we're the recipient)
                    content=lxmf_msg.content,
                    timestamp=datetime.fromtimestamp(lxmf_msg.timestamp, tz=timezone.utc),
                    hops=0,  # LXMF doesn't expose hop count in inbox
                )
                messages.append(msg)

            logger.info("Fetched %d live messages from LXMF inbox", len(messages))
            return messages

        except Exception as e:
            logger.error("Failed to fetch LXMF messages: %s — falling back to mock", e)
            return self._mock_source.get_messages()

    def get_sensor_data(self, node_id: str) -> list[SensorData]:
        """
        Get sensor data for a specific node.

        Note: BATMAN and Reticulum don't provide sensor data natively.
        This always falls back to mock data for Phase 1.

        Args:
            node_id: Node identifier

        Returns:
            List of SensorData objects (always from mock for now)
        """
        logger.debug("Sensor data not available from live sources — using mock")
        return self._mock_source.get_sensor_data(node_id)

    def send_message(self, dest_hash: str, content: str) -> bool:
        """
        Send a message via LXMF (if available).

        Args:
            dest_hash: Destination identity hash (hex string)
            content: Message content

        Returns:
            True on success

        Raises:
            RuntimeError: If Reticulum not available or send fails
        """
        if not self._reticulum_bridge or not self._reticulum_bridge.available:
            raise RuntimeError(
                "Cannot send message — Reticulum bridge not available. "
                "Check logs or enable USE_LIVE_DATA."
            )

        return self._reticulum_bridge.send_message(dest_hash, content)

    def get_reticulum_status(self) -> reticulum_service.ReticulumStatus:
        """
        Get Reticulum bridge status.

        Returns:
            ReticulumStatus object (available=False if bridge not initialized)
        """
        if not self._reticulum_bridge:
            return reticulum_service.ReticulumStatus(available=False)

        return self._reticulum_bridge.get_status()

    def set_ws_callback(self, callback):
        """
        Register a WebSocket callback for real-time LXMF message updates.

        Args:
            callback: Function(event_type: str, data: dict)
        """
        if self._reticulum_bridge:
            self._reticulum_bridge.set_ws_callback(callback)
        else:
            logger.warning("Cannot set WS callback — Reticulum bridge not available")
