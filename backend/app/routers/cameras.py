"""Camera stream endpoints — heartbeat discovery, registry, and MJPEG proxy.

ESP32 cameras register via POST /api/cameras/heartbeat. The registry
tracks health and serves camera metadata to the frontend. The proxy
endpoint re-streams MJPEG from the ESP32 through the authenticated
backend so browsers on the AP network can view the feed.
"""

import asyncio
import ipaddress
import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx
from fastapi import APIRouter, HTTPException, Path, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.models import CameraStream
from app.services.camera_service import CameraService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

# Separate ungated router for heartbeat (ESP32 has no JWT)
heartbeat_router = APIRouter(prefix="/api/cameras", tags=["cameras"])

# Global camera service — set by main.py
_camera_service: Optional[CameraService] = None

# Allowed source subnets for heartbeat (SLIP and BATMAN)
HEARTBEAT_ALLOWED_PREFIXES = ("192.168.1.", "10.13.", "127.0.0.1")

# Allowed camera networks — stream_url host must be on one of these (SSRF prevention)
ALLOWED_CAMERA_NETWORKS = [
    ipaddress.ip_network("192.168.1.0/24"),  # SLIP link
    ipaddress.ip_network("10.13.0.0/16"),  # BATMAN mesh
]

# Max cameras to prevent memory exhaustion on Pi
MAX_CAMERAS = 16

# Max concurrent MJPEG proxy streams per camera
MAX_CONCURRENT_STREAMS = 2

CAMERA_ID_PATTERN = r"^[a-zA-Z0-9_-]{1,64}$"

# Per-camera stream semaphores
_stream_semaphores: dict[str, asyncio.Semaphore] = {}


def set_camera_service(service: CameraService) -> None:
    """Inject camera service (called by main.py)."""
    global _camera_service
    _camera_service = service


def _get_service() -> CameraService:
    if not _camera_service:
        raise HTTPException(status_code=503, detail="Camera service not initialized")
    return _camera_service


def _validate_stream_url(url: str) -> bool:
    """Validate stream_url points to an allowed camera network (SSRF prevention)."""
    parsed = urlparse(url)
    if parsed.scheme != "http" or not parsed.hostname:
        return False
    try:
        ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return False
    return any(ip in net for net in ALLOWED_CAMERA_NETWORKS)


def _build_snapshot_url(stream_url: str) -> str:
    """Construct snapshot URL from stream URL via proper URL parsing."""
    parsed = urlparse(stream_url)
    return urlunparse(parsed._replace(path="/snapshot"))


# -- Heartbeat (ungated — ESP32 has no JWT) --

# ESP32 uses 32-bit unsigned integers
_UINT32_MAX = 2**32 - 1


class HeartbeatPayload(BaseModel):
    """Heartbeat from ESP32 camera firmware."""

    node_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    stream_url: str = Field(..., max_length=512)
    resolution: Optional[str] = Field(None, max_length=32)
    fps: Optional[int] = Field(None, ge=1, le=120)
    free_heap: Optional[int] = Field(None, ge=0, le=_UINT32_MAX)
    free_psram: Optional[int] = Field(None, ge=0, le=_UINT32_MAX)
    uptime_s: Optional[int] = Field(None, ge=0, le=_UINT32_MAX)
    camera: Optional[bool] = None


@heartbeat_router.post("/heartbeat", status_code=204)
async def camera_heartbeat(payload: HeartbeatPayload, request: Request):
    """
    Receive heartbeat from ESP32 camera node.

    The ESP32 POSTs this every 10 seconds. Updates the camera registry
    with current status, stream URL, and device metrics.

    This endpoint is intentionally ungated (no JWT) because the ESP32
    firmware doesn't have authentication credentials. Access is limited
    by source IP validation (SLIP/BATMAN subnets only).
    """
    svc = _get_service()

    # Reject heartbeats from non-mesh IPs
    client_ip = request.client.host if request.client else "unknown"
    if not any(client_ip.startswith(p) for p in HEARTBEAT_ALLOWED_PREFIXES):
        logger.warning(
            "Rejected camera heartbeat from non-mesh IP %s (node_id=%s)",
            client_ip,
            payload.node_id,
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    # Validate stream_url points to allowed camera subnet (SSRF prevention)
    if not _validate_stream_url(payload.stream_url):
        logger.warning(
            "Rejected heartbeat with invalid stream_url: %s (node_id=%s)",
            payload.stream_url,
            payload.node_id,
        )
        raise HTTPException(status_code=422, detail="Invalid stream URL")

    # Prevent memory exhaustion — reject if at max and this is a new camera
    if (
        svc.get_camera(payload.node_id) is None
        and len(svc.get_cameras()) >= MAX_CAMERAS
    ):
        raise HTTPException(status_code=429, detail="Camera limit reached")

    extra = {}
    if payload.free_heap is not None:
        extra["free_heap"] = payload.free_heap
    if payload.free_psram is not None:
        extra["free_psram"] = payload.free_psram
    if payload.uptime_s is not None:
        extra["uptime_s"] = payload.uptime_s
    if payload.camera is not None:
        extra["camera"] = payload.camera

    svc.register_heartbeat(
        node_id=payload.node_id,
        stream_url=payload.stream_url,
        resolution=payload.resolution,
        fps=payload.fps,
        **extra,
    )

    return None


# -- Camera list & detail --


@router.get("", response_model=list[CameraStream])
async def get_camera_streams():
    """
    Get all registered camera streams.

    Returns cameras discovered via heartbeat, with current health status.
    """
    return _get_service().get_cameras()


@router.get("/{camera_id}", response_model=CameraStream)
async def get_camera_stream(
    camera_id: str = Path(..., pattern=CAMERA_ID_PATTERN),
):
    """
    Get a specific camera by ID.

    Args:
        camera_id: Camera identifier (matches node_id from heartbeat)
    """
    cam = _get_service().get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam


# -- MJPEG proxy --


@router.get("/{camera_id}/stream")
async def proxy_camera_stream(
    camera_id: str = Path(..., pattern=CAMERA_ID_PATTERN),
):
    """
    Reverse-proxy MJPEG stream from ESP32 camera.

    The frontend can't reach the ESP32 directly (different subnet).
    This endpoint fetches the MJPEG stream from the camera's internal
    IP and re-streams it to the authenticated browser client.

    Limited to MAX_CONCURRENT_STREAMS per camera to protect the ESP32.
    """
    svc = _get_service()
    cam = svc.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    if cam.status == "error":
        raise HTTPException(status_code=503, detail="Camera offline")

    # Limit concurrent streams per camera (ESP32 has limited resources)
    sem = _stream_semaphores.setdefault(
        camera_id, asyncio.Semaphore(MAX_CONCURRENT_STREAMS)
    )
    if sem.locked():
        raise HTTPException(status_code=429, detail="Stream limit reached")

    # Acquire semaphore and open upstream connection BEFORE returning 200.
    # This ensures connect failures return a proper error status code.
    await sem.acquire()
    client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=300.0))
    try:
        resp = await client.send(
            client.build_request("GET", cam.stream_url), stream=True
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        await client.aclose()
        sem.release()
        logger.error("MJPEG proxy connect error for %s: %s", camera_id, e)
        raise HTTPException(status_code=502, detail="Camera stream unavailable") from e

    content_type = resp.headers.get(
        "content-type", "multipart/x-mixed-replace; boundary=frame"
    )

    async def stream_generator():
        try:
            async for chunk in resp.aiter_bytes(chunk_size=4096):
                yield chunk
        except (GeneratorExit, asyncio.CancelledError):
            logger.debug("MJPEG proxy client disconnected for %s", camera_id)
        finally:
            await resp.aclose()
            await client.aclose()
            sem.release()

    return StreamingResponse(stream_generator(), media_type=content_type)


@router.get("/{camera_id}/snapshot")
async def proxy_camera_snapshot(
    camera_id: str = Path(..., pattern=CAMERA_ID_PATTERN),
):
    """
    Proxy a single JPEG snapshot from the camera.
    """
    svc = _get_service()
    cam = svc.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    if cam.status == "error":
        raise HTTPException(status_code=503, detail="Camera offline")

    snapshot_url = _build_snapshot_url(cam.stream_url)

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            resp = await client.get(snapshot_url)
            resp.raise_for_status()
            return StreamingResponse(
                iter([resp.content]),
                media_type="image/jpeg",
                headers={"Content-Disposition": "inline; filename=snapshot.jpg"},
            )
        except httpx.HTTPError as e:
            logger.error("Snapshot proxy error for %s: %s", camera_id, e)
            raise HTTPException(status_code=503, detail="Camera unavailable") from e
