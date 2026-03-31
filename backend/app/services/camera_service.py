"""In-memory camera registry with heartbeat-driven discovery.

Cameras register via HTTP POST heartbeat from the ESP32 firmware.
The registry tracks camera health based on last_seen timestamps
and provides lookup for the MJPEG proxy and API endpoints.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from app.models import CameraStream

logger = logging.getLogger(__name__)

# Health thresholds (seconds since last heartbeat)
INACTIVE_THRESHOLD = 30
ERROR_THRESHOLD = 60

# Sweep interval (seconds)
SWEEP_INTERVAL = 10


class CameraService:
    """In-memory camera registry with automatic health sweeping."""

    def __init__(self) -> None:
        self._cameras: dict[str, CameraStream] = {}
        self._last_seen: dict[str, datetime] = {}
        self._metadata: dict[str, dict] = {}  # Extra heartbeat fields
        self._sweep_task: Optional[asyncio.Task] = None

    def start_sweep(self) -> None:
        """Start background health sweep task (call from startup event)."""
        if self._sweep_task is None:
            self._sweep_task = asyncio.create_task(self._sweep_loop())
            logger.info("Camera health sweep started (every %ds)", SWEEP_INTERVAL)

    async def stop_sweep(self) -> None:
        """Cancel background health sweep task (call from shutdown event)."""
        if self._sweep_task is not None:
            self._sweep_task.cancel()
            try:
                await self._sweep_task
            except asyncio.CancelledError:
                pass
            self._sweep_task = None
            logger.info("Camera health sweep stopped")

    async def _sweep_loop(self) -> None:
        """Periodically update camera status based on heartbeat freshness."""
        try:
            while True:
                await asyncio.sleep(SWEEP_INTERVAL)
                self._update_health()
        except asyncio.CancelledError:
            logger.info("Camera health sweep cancelled")
            raise

    def _update_health(self) -> None:
        """Check all cameras and update status based on last_seen age."""
        now = datetime.now(timezone.utc)
        for cam_id, last in list(self._last_seen.items()):
            cam = self._cameras.get(cam_id)
            if cam is None:
                continue

            age = (now - last).total_seconds()
            if age > ERROR_THRESHOLD and cam.status != "error":
                self._cameras[cam_id] = cam.model_copy(update={"status": "error"})
                logger.warning("Camera %s: error (no heartbeat for %.0fs)", cam_id, age)
            elif (
                INACTIVE_THRESHOLD < age <= ERROR_THRESHOLD and cam.status != "inactive"
            ):
                self._cameras[cam_id] = cam.model_copy(update={"status": "inactive"})
                logger.info("Camera %s: inactive (%.0fs since heartbeat)", cam_id, age)

    def register_heartbeat(
        self,
        node_id: str,
        stream_url: str,
        resolution: Optional[str] = None,
        fps: Optional[int] = None,
        **extra: object,
    ) -> CameraStream:
        """Register or update a camera from a heartbeat.

        Args:
            node_id: Camera node identifier (e.g., "m3l_cam_01")
            stream_url: URL of the MJPEG stream on the ESP32
            resolution: Stream resolution string (e.g., "QVGA")
            fps: Target frames per second
            **extra: Additional metadata (free_heap, uptime_s, etc.)

        Returns:
            The registered/updated CameraStream
        """
        now = datetime.now(timezone.utc)
        cam_id = node_id  # 1:1 mapping for now

        existing = self._cameras.get(cam_id)
        if existing:
            # Update existing camera
            cam = existing.model_copy(
                update={
                    "stream_url": stream_url,
                    "status": "active",
                    "resolution": resolution
                    if resolution is not None
                    else existing.resolution,
                    "fps": fps if fps is not None else existing.fps,
                    "last_frame": now,
                }
            )
        else:
            # New camera discovered
            cam = CameraStream(
                id=cam_id,
                node_id=node_id,
                name=f"Camera {node_id}",
                stream_url=stream_url,
                status="active",
                resolution=resolution,
                fps=fps,
                last_frame=now,
            )
            logger.info("New camera discovered: %s at %s", cam_id, stream_url)

        self._cameras[cam_id] = cam
        self._last_seen[cam_id] = now
        self._metadata[cam_id] = dict(extra)

        return cam

    def get_cameras(self) -> list[CameraStream]:
        """Return all registered cameras."""
        return list(self._cameras.values())

    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        """Return a specific camera by ID."""
        return self._cameras.get(camera_id)

    def get_camera_metadata(self, camera_id: str) -> dict:
        """Return extra heartbeat metadata for a camera (copy, not live reference)."""
        return dict(self._metadata.get(camera_id, {}))

    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the registry."""
        if camera_id in self._cameras:
            del self._cameras[camera_id]
            self._last_seen.pop(camera_id, None)
            self._metadata.pop(camera_id, None)
            logger.info("Camera removed: %s", camera_id)
            return True
        return False
