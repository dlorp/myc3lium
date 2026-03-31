"""Camera stream endpoints — RTSP/MJPEG feeds from mesh nodes.

Stub router for future camera integration.
Currently returns empty data; will be wired to camera discovery
service when FROND (camera) nodes are deployed.
"""

import logging

from fastapi import APIRouter, HTTPException, Path

from app.models import CameraStream

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("", response_model=list[CameraStream])
async def get_camera_streams():
    """
    Get all camera streams from mesh nodes.

    Returns active and inactive camera feeds from FROND-type nodes.
    Currently returns an empty list — awaiting camera node deployment.

    Returns:
        List of camera streams
    """
    return []


@router.get("/{camera_id}", response_model=CameraStream)
async def get_camera_stream(
    camera_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$"),
):
    """
    Get a specific camera stream by ID.

    Args:
        camera_id: Unique camera identifier

    Returns:
        Camera stream details

    Raises:
        HTTPException: 404 if camera not found
    """
    raise HTTPException(status_code=404, detail="Camera stream not found")
