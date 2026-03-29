"""Configuration management API endpoints."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException

from app.config_models import Myc3liumConfig
from app.services.config_service import RESTARTABLE_SERVICES, ConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

# Injected by main.py
config_service: ConfigService | None = None


@router.get("", response_model=Myc3liumConfig)
async def get_config() -> Myc3liumConfig:
    """Get the full system configuration."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    return config_service.config


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
    """Get a single configuration section."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    try:
        return config_service.get_section(section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{section}")
async def update_config_section(
    section: Literal["radio", "mesh", "display", "system"],
    updates: dict,
) -> dict:
    """
    Partially update a configuration section.

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


@router.post("/restart-service/{service_name}")
async def restart_service(service_name: str) -> dict:
    """
    Restart a system service (whitelisted services only).

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
        return {"status": "restarted", "service": service_name, "message": message}
    raise HTTPException(status_code=500, detail=message)


@router.post("/save-defaults")
async def save_defaults() -> dict:
    """Create the default config file (used by first-boot setup wizard)."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    config_service.create_default_config()
    return {"status": "created", "path": str(config_service.config_path)}
