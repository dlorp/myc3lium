"""
Meshtastic bridge for mesh radio communication via Heltec V3.

This service provides:
- Singleton MeshtasticService for managing SerialInterface lifecycle
- Message send/receive via Meshtastic mesh
- Node tracking and status queries
- WebSocket callback hooks for real-time updates
"""

import logging
import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

try:
    from pubsub import pub
except ImportError:
    pub = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Input validation constants for mesh radio packets (untrusted external input)
_MAX_TEXT_LENGTH = 237  # Meshtastic max LoRa payload for TEXT_MESSAGE_APP
_MAX_NODE_ID_LENGTH = 20
_MAX_CHANNELS = 8
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")

# Lazy imports — meshtastic may not be installed on dev machines
_meshtastic = None
_serial = None
_IMPORT_ATTEMPTED = False


def _ensure_imports() -> bool:
    """
    Try to import meshtastic modules.

    Returns:
        True if modules successfully imported, False otherwise
    """
    global _meshtastic, _serial, _IMPORT_ATTEMPTED

    if _IMPORT_ATTEMPTED:
        return _meshtastic is not None

    _IMPORT_ATTEMPTED = True

    try:
        import meshtastic.serial_interface

        _meshtastic = meshtastic
        _serial = meshtastic.serial_interface
        logger.info("Meshtastic modules loaded successfully")
        return True
    except ImportError as e:
        logger.info("Meshtastic not installed — Meshtastic features disabled: %s", e)
        return False


@dataclass
class MeshtasticMessage:
    """Incoming Meshtastic message"""

    sender: str  # node ID or name
    text: str
    timestamp: float
    channel: int = 0
    snr: Optional[float] = None
    rssi: Optional[int] = None
    hop_limit: Optional[int] = None


@dataclass
class MeshtasticNode:
    """Meshtastic mesh node info"""

    node_id: str  # !12345678 format
    short_name: str
    long_name: str
    last_heard: float
    snr: Optional[float] = None
    position: Optional[dict] = None  # {"lat": float, "lon": float, "alt": int}
    battery_level: Optional[int] = None
    voltage: Optional[float] = None
    channel_utilization: Optional[float] = None
    air_util_tx: Optional[float] = None


@dataclass
class MeshtasticStatus:
    """Current Meshtastic service status"""

    connected: bool = False
    device: Optional[str] = None
    node_id: Optional[str] = None
    short_name: Optional[str] = None
    long_name: Optional[str] = None
    battery_level: Optional[int] = None
    voltage: Optional[float] = None
    channel_utilization: Optional[float] = None
    air_util_tx: Optional[float] = None
    nodes_count: int = 0


class MeshtasticService:
    """
    Singleton bridge between Meshtastic radio and FastAPI backend.

    Usage:
        service = MeshtasticService()
        if service.start():
            status = service.get_status()
            service.send_message("Hello mesh!")
            messages = service.get_messages()
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, device_path: str = "/dev/ttyUSB1", max_messages: int = 100):
        """
        Initialize the service (only runs once due to singleton).

        Args:
            device_path: Serial device path for Heltec V3
            max_messages: Maximum messages to store in ring buffer
        """
        # Avoid re-initialization if already started
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._available = False
        self._interface = None
        self._device_path = device_path
        self._messages: deque[MeshtasticMessage] = deque(maxlen=max_messages)
        self._nodes: dict[str, MeshtasticNode] = {}
        self._ws_callback: Optional[Callable] = None
        self._messages_lock = threading.Lock()
        self._nodes_lock = threading.Lock()
        self._my_node_id: Optional[str] = None
        self._subscribed = False

    def start(self) -> bool:
        """
        Initialize Meshtastic SerialInterface.

        Returns:
            True if started successfully, False if meshtastic unavailable
        """
        if self._available:
            logger.info("MeshtasticService already started")
            return True

        if not _ensure_imports():
            logger.warning("Cannot start Meshtastic — library not installed")
            return False

        # Type guard
        if _serial is None:
            logger.error("Cannot start — meshtastic imports failed")
            return False

        try:
            # Register callbacks BEFORE connecting — SerialInterface constructor
            # downloads the full nodedb, firing node.updated events during init.
            if pub:
                pub.subscribe(self._on_receive, "meshtastic.receive")
                pub.subscribe(self._on_connection, "meshtastic.connection.established")
                pub.subscribe(self._on_node_info_updated, "meshtastic.node.updated")
                self._subscribed = True
                logger.info("Registered PyPubSub callbacks for Meshtastic events")
            else:
                logger.warning("PyPubSub not available - callbacks won't work")

            # Connect to Heltec V3 via serial
            logger.info("Connecting to Meshtastic device at %s", self._device_path)
            interface = _serial.SerialInterface(devPath=self._device_path)

            self._interface = interface
            self._available = True

            # Give it a moment to fetch initial node info
            time.sleep(2)

            # Store local node ID from interface.nodes (myInfo is protobuf, not dict)
            if interface.myInfo and interface.nodes:
                my_node_num = str(interface.myInfo.my_node_num)
                for nid, ndata in interface.nodes.items():
                    if str(ndata.get("num")) == my_node_num:
                        self._my_node_id = ndata.get("user", {}).get("id")
                        short_name = ndata.get("user", {}).get("shortName", "Unknown")
                        logger.info(
                            "Connected to Meshtastic node: %s (%s)",
                            short_name,
                            self._my_node_id,
                        )
                        break

            logger.info("Meshtastic service started successfully")
            return True

        except Exception as e:
            logger.error("Failed to start Meshtastic service: %s", e, exc_info=True)
            self._unsubscribe_all()
            self._available = False
            return False

    @property
    def available(self) -> bool:
        """Check if service is available and running"""
        return self._available

    def _on_receive(self, packet, interface=None):
        """
        Callback for incoming Meshtastic packets via PyPubSub.

        Args:
            packet: Meshtastic packet dict (keyword arg from PyPubSub)
            interface: SerialInterface instance (optional)
        """
        try:
            # Only process TEXT_MESSAGE_APP packets
            if packet.get("decoded", {}).get("portnum") != "TEXT_MESSAGE_APP":
                return

            decoded = packet.get("decoded", {})

            # Validate and sanitize untrusted mesh input
            from_id = _CONTROL_CHAR_RE.sub(
                "", str(packet.get("fromId", "Unknown"))[:_MAX_NODE_ID_LENGTH]
            )
            text = _CONTROL_CHAR_RE.sub(
                "", str(decoded.get("text", ""))[:_MAX_TEXT_LENGTH]
            )

            timestamp = packet.get("rxTime", time.time())
            if not isinstance(timestamp, (int, float)) or not (
                0 < timestamp < 4_102_444_800
            ):
                timestamp = time.time()

            channel = packet.get("channel", 0)
            if not isinstance(channel, int) or not (0 <= channel < _MAX_CHANNELS):
                channel = 0

            # Extract signal metrics
            snr = packet.get("rxSnr")
            rssi = packet.get("rxRssi")
            hop_limit = packet.get("hopLimit")

            msg = MeshtasticMessage(
                sender=from_id,
                text=text,
                timestamp=timestamp,
                channel=channel,
                snr=snr,
                rssi=rssi,
                hop_limit=hop_limit,
            )

            with self._messages_lock:
                self._messages.append(msg)
                logger.info(
                    "Received Meshtastic message from %s (ch=%d, SNR=%.1f): %s",
                    from_id,
                    channel,
                    snr if snr is not None else 0.0,
                    text[:50],
                )

            # Notify WebSocket clients (capture ref for thread safety)
            callback = self._ws_callback
            if callback:
                callback(
                    "meshtastic_message",
                    {
                        "sender": from_id,
                        "text": text,
                        "timestamp": timestamp,
                        "channel": channel,
                        "snr": snr,
                        "rssi": rssi,
                    },
                )

        except Exception as e:
            logger.error("Error processing Meshtastic packet: %s", e)

    def _on_connection(self, interface=None, topic=None):
        """
        Callback for connection events via PyPubSub.

        Args:
            interface: SerialInterface instance (keyword arg from PyPubSub)
            topic: MQTT topic (unused for serial)
        """
        try:
            logger.info("Meshtastic connection event")
            if interface is not None and interface.myInfo:
                logger.debug(
                    "Connection confirmed: my_node_num=%s", interface.myInfo.my_node_num
                )
        except Exception as e:
            logger.error("Error in connection callback: %s", e)

    def _on_node_info_updated(self, node=None, interface=None):
        """
        Callback for node info updates via PyPubSub.

        Args:
            node: Node info dict (keyword arg from PyPubSub, named 'node' not 'node_info')
            interface: SerialInterface instance (optional)
        """
        try:
            if not node:
                return

            node_id = node.get("user", {}).get("id", "Unknown")
            short_name = node.get("user", {}).get("shortName", "Unknown")
            long_name = node.get("user", {}).get("longName", "Unknown")
            last_heard = node.get("lastHeard", time.time())
            snr = node.get("snr")

            # Extract position if available
            position = None
            pos_data = node.get("position", {})
            if pos_data and "latitude" in pos_data:
                position = {
                    "lat": pos_data.get("latitude"),
                    "lon": pos_data.get("longitude"),
                    "alt": pos_data.get("altitude"),
                }

            # Extract device metrics if available
            device_metrics = node.get("deviceMetrics", {})
            battery_level = device_metrics.get("batteryLevel")
            voltage = device_metrics.get("voltage")
            channel_utilization = device_metrics.get("channelUtilization")
            air_util_tx = device_metrics.get("airUtilTx")

            mesh_node = MeshtasticNode(
                node_id=node_id,
                short_name=short_name,
                long_name=long_name,
                last_heard=last_heard,
                snr=snr,
                position=position,
                battery_level=battery_level,
                voltage=voltage,
                channel_utilization=channel_utilization,
                air_util_tx=air_util_tx,
            )

            with self._nodes_lock:
                self._nodes[node_id] = mesh_node
                nodes_count = len(self._nodes)
                logger.debug("Updated node info: %s (%s)", short_name, node_id)

            # Notify WebSocket clients (capture ref for thread safety)
            callback = self._ws_callback
            if callback:
                callback(
                    "meshtastic_node_updated",
                    {
                        "node_id": node_id,
                        "short_name": short_name,
                        "long_name": long_name,
                        "last_heard": last_heard,
                        "snr": snr,
                        "position": position,
                        "battery_level": battery_level,
                        "voltage": voltage,
                        "channel_utilization": channel_utilization,
                        "air_util_tx": air_util_tx,
                        "nodes_count": nodes_count,
                    },
                )

        except Exception as e:
            logger.error("Error processing node info: %s", e)

    def send_message(
        self, text: str, channel: int = 0, destination: Optional[str] = None
    ) -> bool:
        """
        Send a text message to the mesh.

        Args:
            text: Message content
            channel: Channel index (default: 0)
            destination: Optional specific node ID (broadcast if None)

        Returns:
            True on success

        Raises:
            RuntimeError: If service not available
        """
        if not self._available or self._interface is None:
            raise RuntimeError("Meshtastic service not available")

        try:
            if destination:
                self._interface.sendText(
                    text, destinationId=destination, channelIndex=channel
                )
                logger.info(
                    "Sent message to %s (ch=%d): %s", destination, channel, text[:50]
                )
            else:
                self._interface.sendText(text, channelIndex=channel)
                logger.info("Broadcast message (ch=%d): %s", channel, text[:50])
            return True

        except Exception as e:
            logger.error("Failed to send message: %s", e)
            raise

    def get_messages(
        self,
        limit: Optional[int] = None,
        sender: Optional[str] = None,
        channel: Optional[int] = None,
    ) -> list[MeshtasticMessage]:
        """
        Get recent messages with optional filters.

        Args:
            limit: Maximum messages to return
            sender: Filter by sender node ID
            channel: Filter by channel

        Returns:
            List of MeshtasticMessage objects
        """
        with self._messages_lock:
            messages = list(self._messages)

        # Apply filters
        if sender:
            messages = [m for m in messages if m.sender == sender]
        if channel is not None:
            messages = [m for m in messages if m.channel == channel]

        # Apply limit
        if limit:
            messages = messages[-limit:]

        return messages

    def get_nodes(self) -> list[MeshtasticNode]:
        """
        Get all known mesh nodes.

        Returns:
            List of MeshtasticNode objects
        """
        with self._nodes_lock:
            return list(self._nodes.values())

    def get_status(self) -> MeshtasticStatus:
        """
        Get current service status.

        Returns:
            MeshtasticStatus object
        """
        if not self._available or self._interface is None:
            return MeshtasticStatus(connected=False)

        # Extract local node info from tracked nodes
        node_id = self._my_node_id
        short_name = None
        long_name = None
        battery_level = None
        voltage = None
        channel_util = None
        air_util_tx = None

        if node_id:
            with self._nodes_lock:
                my_node = self._nodes.get(node_id)
            if my_node:
                short_name = my_node.short_name
                long_name = my_node.long_name
                battery_level = my_node.battery_level
                voltage = my_node.voltage
                channel_util = my_node.channel_utilization
                air_util_tx = my_node.air_util_tx

        with self._nodes_lock:
            nodes_count = len(self._nodes)

        return MeshtasticStatus(
            connected=True,
            device=self._device_path,
            node_id=node_id,
            short_name=short_name,
            long_name=long_name,
            battery_level=battery_level,
            voltage=voltage,
            channel_utilization=channel_util,
            air_util_tx=air_util_tx,
            nodes_count=nodes_count,
        )

    def set_ws_callback(self, callback: Callable[[str, dict], None]):
        """
        Register a WebSocket callback for real-time updates.

        Args:
            callback: Function(event_type: str, data: dict)
        """
        self._ws_callback = callback
        logger.debug("WebSocket callback registered for Meshtastic")

    def _unsubscribe_all(self) -> None:
        """Remove all PyPubSub subscriptions if registered."""
        if not pub or not self._subscribed:
            return
        try:
            pub.unsubscribe(self._on_receive, "meshtastic.receive")
            pub.unsubscribe(self._on_connection, "meshtastic.connection.established")
            pub.unsubscribe(self._on_node_info_updated, "meshtastic.node.updated")
            self._subscribed = False
        except Exception as e:
            logger.warning("Error unsubscribing PyPubSub callbacks: %s", e)

    def stop(self):
        """Shut down the Meshtastic service"""
        if not self._available:
            return

        logger.info("Shutting down Meshtastic service")

        self._unsubscribe_all()

        # Close the serial interface
        if self._interface:
            try:
                self._interface.close()
            except Exception as e:
                logger.error("Error closing Meshtastic interface: %s", e)

        self._interface = None
        self._available = False
