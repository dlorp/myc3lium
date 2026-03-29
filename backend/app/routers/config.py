"""Configuration management API endpoints."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.config_models import Myc3liumConfigPublic
from app.services import backhaul_service, network_apply_service
from app.services.config_service import RESTARTABLE_SERVICES, ConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

# Injected by main.py
config_service: ConfigService | None = None

# Section type used across GET/PATCH endpoints
SectionName = Literal["radio", "mesh", "backhaul", "display", "system"]


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


@router.get("/backhaul/adapters")
async def get_backhaul_adapters() -> dict:
    """Detected USB WiFi adapters available for backhaul (no auth, read-only)."""
    adapters = backhaul_service.detect_usb_wifi_adapters()
    return {"adapters": adapters}


@router.get("/backhaul/status", dependencies=[Depends(verify_api_key)])
def get_backhaul_status() -> dict:
    """Current backhaul status — mode, IP, clients, signal.

    Sync handler — subprocess calls block, FastAPI runs in threadpool.
    """
    backhaul_config = config_service.config.backhaul if config_service else None
    return backhaul_service.get_status(backhaul_config)


@router.post("/apply-backhaul", dependencies=[Depends(verify_api_key)])
def apply_backhaul() -> dict:
    """Apply backhaul config to system (start AP, connect client, or disable).

    Sync handler — subprocess calls block, FastAPI runs in threadpool.
    """
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")

    backhaul_config = config_service.config.backhaul

    if not backhaul_config.enabled or backhaul_config.mode == "disabled":
        success, message = backhaul_service.disable_backhaul()
        return {"success": success, "message": message}

    if backhaul_config.mode == "client":
        success, message, used_iface = backhaul_service.apply_client_mode(backhaul_config)
    elif backhaul_config.mode == "ap":
        success, message, used_iface = backhaul_service.apply_ap_mode(backhaul_config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {backhaul_config.mode}")

    if not success:
        raise HTTPException(status_code=500, detail=message)

    # Apply or remove NAT based on config
    if used_iface:
        if backhaul_config.nat_enabled:
            nat_ok, nat_msg = backhaul_service.apply_nat(used_iface)
            if not nat_ok:
                logger.warning("NAT setup failed: %s", nat_msg)
        else:
            backhaul_service.remove_nat_rules(used_iface)

    return {"success": True, "message": message}


@router.post("/apply-network", dependencies=[Depends(verify_api_key)])
def apply_network() -> dict:
    """Apply BATMAN + Reticulum + Meshtastic config to running system.

    Sync handler — subprocess calls block, FastAPI runs in threadpool.
    """
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")

    result = network_apply_service.apply_network(config_service.config)
    if not result["success"]:
        raise HTTPException(status_code=500, detail="Network apply had errors")
    return result


@router.get("/{section}")
async def get_config_section(section: SectionName) -> dict:
    """Get a single configuration section (sensitive fields masked)."""
    if not config_service:
        raise HTTPException(status_code=503, detail="Config service unavailable")
    try:
        data = config_service.get_section(section)
        if section == "system" and "api_key" in data:
            data["api_key"] = "***" if data["api_key"] else ""
        if section == "backhaul":
            if "client_password" in data:
                data["client_password"] = "***" if data["client_password"] else ""
            if "ap_password" in data:
                data["ap_password"] = "***" if data["ap_password"] else ""
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{section}", dependencies=[Depends(verify_api_key)])
async def update_config_section(section: SectionName, updates: dict) -> dict:
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

    Available services: reticulum, myc3lium, lora-bridge, hostapd, dnsmasq
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
