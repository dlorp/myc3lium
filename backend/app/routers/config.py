"""Configuration management API endpoints."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.config_models import Myc3liumConfigPublic
from app.services.config_service import RESTARTABLE_SERVICES, ConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

# Injected by main.py
config_service: ConfigService | None = None


@router.get("")
async def get_config() -> dict:
    """Get the full system configuration (API key masked)."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    public = Myc3liumConfigPublic.from_config(config_service.config)
    return public.model_dump()


@router.get("/first-boot")
async def check_first_boot() -> dict:
    """Check if this is a first boot (no config file exists)."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    return {"first_boot": config_service.is_first_boot()}


@router.get("/{section}")
async def get_config_section(
    section: Literal["radio", "mesh", "display", "system"],
) -> dict:
    """Get a single configuration section (API key masked for system)."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    try:
        data = config_service.get_section(section)
        if section == "system" and "api_key" in data:
            data["api_key"] = "***" if data["api_key"] else ""
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{section}", dependencies=[Depends(verify_api_key)])
async def update_config_section(
    section: Literal["radio", "mesh", "display", "system"],
    updates: dict,
) -> dict:
    """
    Partially update a configuration section. Requires API key.

    Only provided fields are updated; others retain their current values.
    Changes are immediately persisted to disk.
    """
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    try:
        updated = config_service.update_section(section, updates)
        return {"status": "saved", "section": section, "config": updated}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to update configuration"
        ) from None


@router.post("/restart-service/{service_name}", dependencies=[Depends(verify_api_key)])
async def restart_service(service_name: str) -> dict:
    """
    Restart a system service. Requires API key. Whitelisted services only.

    Available services: reticulum, myc3lium-backend, lora-bridge
    """
    if service_name not in RESTARTABLE_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service. Allowed: {sorted(RESTARTABLE_SERVICES)}",
        )
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")

    success, message = ConfigService.restart_service(service_name)
    if success:
        return {"status": "restarted", "service": service_name}
    raise HTTPException(status_code=500, detail="Service restart failed")


@router.post("/save-defaults", dependencies=[Depends(verify_api_key)])
async def save_defaults() -> dict:
    """Create the default config file. Requires API key."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    config_service.create_default_config()
    return {"status": "created"}
