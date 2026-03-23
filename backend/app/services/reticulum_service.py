"""
Reticulum + LXMF bridge for mesh messaging.
Falls back gracefully if RNS/LXMF not installed (e.g., Mac dev environments).

This service provides:
- Singleton ReticulumBridge for managing RNS/LXMF lifecycle
- Message send/receive via LXMF
- Status queries for interfaces, identity, and inbox
- WebSocket callback hooks for real-time updates
"""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Lazy imports — RNS/LXMF may not be installed on dev machines
_RNS = None
_LXMF = None
_IMPORT_ATTEMPTED = False


def _ensure_imports() -> bool:
    """
    Try to import RNS and LXMF modules.

    Returns:
        True if both modules successfully imported, False otherwise
    """
    global _RNS, _LXMF, _IMPORT_ATTEMPTED

    if _IMPORT_ATTEMPTED:
        return _RNS is not None

    _IMPORT_ATTEMPTED = True

    try:
        import RNS
        import LXMF

        _RNS = RNS
        _LXMF = LXMF
        logger.info("RNS and LXMF modules loaded successfully")
        return True
    except ImportError as e:
        logger.info("RNS/LXMF not installed — Reticulum features disabled: %s", e)
        return False


@dataclass
class LXMFMessage:
    """Incoming LXMF message"""

    source_hash: str  # hex string
    content: str
    timestamp: float
    title: Optional[str] = None


@dataclass
class ReticulumInterface:
    """Reticulum interface info"""

    name: str
    mode: str  # e.g., "full", "access_point", "boundary"
    enabled: bool
    clients: int = 0


@dataclass
class ReticulumStatus:
    """Current Reticulum bridge status"""

    available: bool = False
    identity_hash: Optional[str] = None  # hex string
    address_hash: Optional[str] = None  # LXMF delivery address (hex)
    inbox_count: int = 0
    transport_active: bool = False
    interfaces: list[ReticulumInterface] = field(default_factory=list)


class ReticulumBridge:
    """
    Singleton bridge between Reticulum/LXMF and the FastAPI backend.

    Usage:
        bridge = ReticulumBridge()
        if bridge.start():
            status = bridge.get_status()
            bridge.send_message("a1b2c3...", "Hello mesh!")
            inbox = bridge.get_inbox()
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

    def __init__(
        self,
        storage_path: str = "/var/lib/myc3lium/lxmf",
        identity_path: str = "/var/lib/myc3lium/identity",
    ):
        """
        Initialize the bridge (only runs once due to singleton).

        Args:
            storage_path: Directory for LXMF message storage
            identity_path: Path to Reticulum identity file
        """
        # Avoid re-initialization if already started
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._available = False
        self._reticulum = None
        self._lxmf_router = None
        self._identity = None
        self._delivery_identity = None
        self._inbox: list[LXMFMessage] = []
        self._ws_callback: Optional[Callable] = None
        self._storage_path = storage_path
        self._identity_path = identity_path
        self._inbox_lock = threading.Lock()

    def start(self) -> bool:
        """
        Initialize Reticulum and LXMF router.

        Returns:
            True if started successfully, False if RNS/LXMF unavailable
        """
        if self._available:
            logger.info("ReticulumBridge already started")
            return True

        if not _ensure_imports():
            logger.warning("Cannot start Reticulum — RNS/LXMF not installed")
            return False

        try:
            # Initialize Reticulum instance
            self._reticulum = _RNS.Reticulum()

            # Load or create identity
            if os.path.exists(self._identity_path):
                try:
                    self._identity = _RNS.Identity.from_file(self._identity_path)
                    logger.info("Loaded Reticulum identity from %s", self._identity_path)
                except Exception as e:
                    logger.warning("Failed to load identity, creating new: %s", e)
                    self._identity = _RNS.Identity()
                    # Create parent directory if needed
                    os.makedirs(os.path.dirname(self._identity_path), exist_ok=True)
                    self._identity.to_file(self._identity_path)
            else:
                self._identity = _RNS.Identity()
                os.makedirs(os.path.dirname(self._identity_path), exist_ok=True)
                self._identity.to_file(self._identity_path)
                logger.info("Created new Reticulum identity at %s", self._identity_path)

            # Create LXMF router
            os.makedirs(self._storage_path, exist_ok=True)
            self._lxmf_router = _LXMF.LXMRouter(storagepath=self._storage_path)

            # Register delivery identity for receiving messages
            self._delivery_identity = self._lxmf_router.register_delivery_identity(
                self._identity, display_name="myc3lium"
            )

            # Register callback for incoming messages
            self._lxmf_router.register_delivery_callback(self._on_message)

            self._available = True
            logger.info(
                "Reticulum bridge started — Identity: %s",
                _RNS.hexrep(self._identity.hash, delimit=False),
            )
            return True

        except Exception as e:
            logger.error("Failed to start Reticulum bridge: %s", e, exc_info=True)
            self._available = False
            return False

    @property
    def available(self) -> bool:
        """Check if bridge is available and running"""
        return self._available

    def _on_message(self, message):
        """
        Callback for incoming LXMF messages.

        Args:
            message: LXMF.LXMessage object
        """
        try:
            msg = LXMFMessage(
                source_hash=_RNS.hexrep(message.source_hash, delimit=False),
                content=message.content.decode("utf-8", errors="replace"),
                timestamp=message.timestamp if message.timestamp else time.time(),
                title=(
                    message.title.decode("utf-8", errors="replace")
                    if message.title
                    else None
                ),
            )

            with self._inbox_lock:
                self._inbox.append(msg)
                logger.info(
                    "Received LXMF message from %s: %s",
                    msg.source_hash[:8],
                    msg.content[:50],
                )

            # Notify WebSocket clients
            if self._ws_callback:
                self._ws_callback(
                    "new_message",
                    {
                        "source": msg.source_hash,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "title": msg.title,
                    },
                )

        except Exception as e:
            logger.error("Error processing incoming LXMF message: %s", e)

    def send_message(self, dest_hash: str, content: str, title: str = "") -> bool:
        """
        Send an LXMF message to a destination.

        Args:
            dest_hash: Destination identity hash (hex string)
            content: Message content
            title: Optional message title

        Returns:
            True on success

        Raises:
            RuntimeError: If bridge not available
            ValueError: If destination not known (path requested automatically)
        """
        if not self._available:
            raise RuntimeError("Reticulum bridge not available")

        try:
            dest_hash_bytes = bytes.fromhex(dest_hash)
        except ValueError as e:
            raise ValueError(f"Invalid destination hash: {dest_hash}") from e

        # Try to recall destination identity
        dest_identity = _RNS.Identity.recall(dest_hash_bytes)

        if not dest_identity:
            # Request path and notify caller to retry
            logger.info("Destination %s not known — requesting path", dest_hash[:8])
            _RNS.Transport.request_path(dest_hash_bytes)
            raise ValueError(
                f"Destination {dest_hash[:8]} not known yet — "
                "path requested, retry in a few seconds"
            )

        # Create destination
        dest = _RNS.Destination(
            dest_identity,
            _RNS.Destination.OUT,
            _RNS.Destination.SINGLE,
            "lxmf",
            "delivery",
        )

        # Create and send LXMF message
        lxmf_msg = _LXMF.LXMessage(
            dest,
            self._delivery_identity,
            content.encode("utf-8"),
            title=title.encode("utf-8") if title else b"",
        )

        self._lxmf_router.handle_outbound(lxmf_msg)
        logger.info("Sent LXMF message to %s: %s", dest_hash[:8], content[:50])
        return True

    def get_inbox(self) -> list[LXMFMessage]:
        """
        Get all messages in the inbox.

        Returns:
            List of LXMFMessage objects (copy)
        """
        with self._inbox_lock:
            return list(self._inbox)

    def clear_inbox(self):
        """Clear all messages from inbox"""
        with self._inbox_lock:
            self._inbox.clear()
            logger.info("Inbox cleared")

    def set_ws_callback(self, callback: Callable[[str, dict], None]):
        """
        Register a WebSocket callback for real-time updates.

        Args:
            callback: Function(event_type: str, data: dict)
        """
        self._ws_callback = callback
        logger.debug("WebSocket callback registered")

    def get_status(self) -> ReticulumStatus:
        """
        Get current Reticulum bridge status.

        Returns:
            ReticulumStatus object
        """
        if not self._available:
            return ReticulumStatus(available=False)

        # Parse interfaces (simplified — full implementation would query RNS.Transport)
        interfaces = []
        # Note: Reticulum doesn't expose a clean interface list API
        # This would require parsing internal state or rnstatus output
        # For Phase 1, we return empty list; Phase 2 can expand this

        return ReticulumStatus(
            available=True,
            identity_hash=(
                _RNS.hexrep(self._identity.hash, delimit=False)
                if self._identity
                else None
            ),
            address_hash=(
                _RNS.hexrep(self._delivery_identity.hash, delimit=False)
                if self._delivery_identity
                else None
            ),
            inbox_count=len(self._inbox),
            transport_active=hasattr(_RNS.Transport, "identity")
            and _RNS.Transport.identity is not None,
            interfaces=interfaces,
        )

    def get_interfaces(self) -> list[ReticulumInterface]:
        """
        Get list of active Reticulum interfaces.

        Returns:
            List of ReticulumInterface objects (empty for Phase 1)

        Note:
            Full implementation requires parsing RNS internal state.
            This is a placeholder for Phase 2 expansion.
        """
        # TODO: Parse RNS.Transport.interfaces or subprocess call to rnstatus
        return []

    def stop(self):
        """Shut down the Reticulum bridge"""
        if self._available:
            logger.info("Shutting down Reticulum bridge")
            # RNS doesn't have a clean shutdown API — just mark unavailable
            self._available = False
