"""Satellite pass prediction endpoints — NOAA / METEOR-M tracking.

Stub router for future satellite pass integration.
Currently returns empty data; will be wired to orbital prediction
service when NOAA receiver hardware is integrated.
"""

import logging

from fastapi import APIRouter, HTTPException, Path

from app.models import SatellitePass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/satellites", tags=["satellites"])


@router.get("", response_model=list[SatellitePass])
async def get_satellite_passes():
    """
    Get upcoming satellite passes.

    Returns predicted passes for tracked satellites.
    Currently returns an empty list — awaiting orbital prediction service.

    Returns:
        List of upcoming satellite passes
    """
    return []


@router.get("/{pass_id}", response_model=SatellitePass)
async def get_satellite_pass(
    pass_id: str = Path(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$"),
):
    """
    Get a specific satellite pass by ID.

    Args:
        pass_id: Unique pass identifier

    Returns:
        Satellite pass details

    Raises:
        HTTPException: 404 if pass not found
    """
    raise HTTPException(status_code=404, detail="Satellite pass not found")
