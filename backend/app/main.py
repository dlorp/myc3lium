"""FastAPI application entry point"""

import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.auth import get_current_user
from app.routers import config as config_router
from app.routers import auth_router, messages, mesh, meshtastic, nodes, threads, ws
from app.services.config_service import ConfigService
from app.services.live_data_source import LiveDataSource
from app.services.mesh_store import MeshStore
from app.services.meshtastic_bridge import (
    create_store_sync_callback,
    seed_meshtastic_nodes,
)
from app.services.meshtastic_service import MeshtasticService
from app.services.mock_data import MeshDataSource, MockMeshDataSource
from app.services.reticulum_service import ReticulumBridge

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MYC3LIUM API",
    description="Backend for MYC3LIUM - Mycelial Network Visualization",
    version="0.7.1",
)

# CORS middleware for frontend communication
# Allow all origins for mesh network - nodes may access from different IPs
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Reticulum bridge (gracefully no-ops on Mac)
reticulum = ReticulumBridge()
reticulum.start()

# Choose data source based on environment
data_source: MeshDataSource
if settings.use_live_data:
    logger.info("Using LiveDataSource (BATMAN + Reticulum)")
    data_source = LiveDataSource(use_live=True)
else:
    logger.info("Using MockDataSource (development mode)")
    data_source = MockMeshDataSource(seed=42)

# Initialize mesh store and connect to WebSocket broadcasting
mesh_store = MeshStore()
ws.set_mesh_store(mesh_store)

# Make mesh_store available to routers
nodes.mesh_store = mesh_store
messages.mesh_store = mesh_store
threads.mesh_store = mesh_store

# Make reticulum available to messages router
messages.reticulum = reticulum

# Make services available to mesh router
mesh.set_services(data_source, reticulum)

# Load initial data from chosen source
mesh_store.load_from_source(
    data_source.get_nodes(),
    data_source.get_threads(),
    data_source.get_messages(),
)

# Initialize config service
config_svc = ConfigService()
config_router.config_service = config_svc

# Auto-AP on first boot: if no config file exists and a USB WiFi adapter
# is detected, automatically enable AP mode so headless field deployments
# are reachable via myc3_m3sh hotspot.
if config_svc.is_first_boot():
    try:
        from app.config_models import BACKHAUL_DEFAULT_PASSWORD, BACKHAUL_DEFAULT_SSID
        from app.services.backhaul_service import (
            detect_optimal_ap_band,
            get_available_interface,
        )

        usb_iface = get_available_interface()
        if usb_iface:
            ap_band, ap_channel = detect_optimal_ap_band()

            logger.info(
                "First boot with USB WiFi adapter %s — enabling auto-AP "
                "(SSID: %s, band: %s, ch: %d)",
                usb_iface,
                BACKHAUL_DEFAULT_SSID,
                ap_band,
                ap_channel,
            )
            config_svc.create_default_config()
            config_svc.update_section(
                "backhaul",
                {
                    "enabled": True,
                    "mode": "ap",
                    "ap_ssid": BACKHAUL_DEFAULT_SSID,
                    "ap_password": BACKHAUL_DEFAULT_PASSWORD,
                    "ap_band": ap_band,
                    "ap_channel": ap_channel,
                },
            )
        else:
            logger.info("First boot, no USB WiFi adapter — skipping auto-AP")
    except Exception:
        logger.exception("Auto-AP setup failed — API starting without AP mode")


# Setup gate: block non-config API access until first-boot setup is complete.
# Skipped in dev mode (use_live_data=False) so local development isn't blocked.
async def require_setup_complete() -> None:
    """Dependency that rejects requests if setup wizard hasn't been completed.

    Skipped when: dev mode (use_live_data=False), no config service,
    or no config file exists (test environments).
    """
    if (
        settings.use_live_data
        and config_svc
        and not config_svc.is_first_boot()
        and not config_svc.is_setup_complete()
    ):
        raise HTTPException(
            status_code=403,
            detail="Setup not complete",
            headers={"X-Setup-Required": "true"},
        )


# Include routers — config and auth routers are ungated so setup wizard and login work
auth_and_setup_gate = [Depends(get_current_user), Depends(require_setup_complete)]
app.include_router(nodes.router, dependencies=auth_and_setup_gate)
app.include_router(messages.router, dependencies=auth_and_setup_gate)
app.include_router(threads.router, dependencies=auth_and_setup_gate)
app.include_router(ws.router)  # WebSocket — auth validated in handler (C3)
app.include_router(mesh.router, dependencies=auth_and_setup_gate)
app.include_router(meshtastic.router, dependencies=auth_and_setup_gate)
app.include_router(config_router.router)  # Ungated — needed by setup wizard
app.include_router(auth_router.router)  # Ungated — login must work before auth


# Initialize Meshtastic service
meshtastic_service = MeshtasticService()
meshtastic.set_service(meshtastic_service)  # Inject service into router


# M2: Security headers middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.on_event("startup")
async def start_mesh_monitor():
    """Start background mesh monitoring if live data is enabled."""
    # M4: Initialize auth database at startup, not import time
    from app.db import init_db

    try:
        init_db()
    except Exception:
        logger.exception("Auth database initialization failed — auth features unavailable")

    # Start BATMAN mesh before backhaul — bat0 must exist before br0 bridge setup
    if settings.use_live_data:
        from app.services import network_apply_service

        mesh_cfg = config_svc.config.mesh
        logger.info(
            "Starting BATMAN mesh (SSID: %s, ch: %d, band: %s)",
            mesh_cfg.batman_ssid,
            mesh_cfg.batman_channel,
            mesh_cfg.batman_band,
        )
        batman_result = network_apply_service.apply_batman(mesh_cfg)
        if batman_result["success"]:
            logger.info("BATMAN mesh active: %s", batman_result["details"])
        else:
            logger.error("BATMAN mesh failed: %s", batman_result["message"])

    # Apply backhaul config if enabled (auto-AP on first boot, or persisted config)
    backhaul = config_svc.config.backhaul
    if backhaul.enabled and backhaul.mode != "disabled":
        from app.services import backhaul_service

        logger.info("Applying backhaul config at startup (mode: %s)", backhaul.mode)
        captive = not config_svc.is_setup_complete()

        # Set captive portal flag BEFORE AP start so nginx is ready
        # when dnsmasq begins redirecting DNS
        if backhaul.mode == "ap" and captive:
            if backhaul_service.enable_captive_portal():
                logger.info("Captive portal flag set before AP start")
            else:
                logger.warning(
                    "Could not set captive portal flag — starting AP without captive"
                )
                captive = False

        if backhaul.mode == "ap":
            ok, msg, iface = backhaul_service.apply_ap_mode(backhaul, captive=captive)
        elif backhaul.mode == "client":
            ok, msg, iface = backhaul_service.apply_client_mode(backhaul)
        else:
            ok, msg, iface = False, "Unknown mode", None

        if ok and iface and backhaul.nat_enabled:
            backhaul_service.apply_nat(iface)
        if ok:
            logger.info("Backhaul active: %s", msg)
        else:
            logger.warning("Backhaul failed at startup: %s", msg)

        # Clean up stale captive portal flag if setup already complete
        if config_svc.is_setup_complete():
            from pathlib import Path

            if Path("/opt/myc3lium/run/captive-portal").exists():
                backhaul_service.disable_captive_portal()
                logger.warning("Cleaned up stale captive portal flag file")

    # Start event processor (needs running event loop)
    await meshtastic.start_event_processor()

    # Start Meshtastic service
    if meshtastic_service.start():
        logger.info("Meshtastic service started successfully")

        # Register WebSocket broadcast callback for real-time frontend updates
        meshtastic_service.add_ws_callback(meshtastic.broadcast_to_websockets)

        # Register MeshStore sync callback so Meshtastic nodes appear in /api/nodes
        local_node_id = meshtastic_service.my_node_id
        sync_cb = create_store_sync_callback(mesh_store, local_node_id)
        meshtastic_service.add_ws_callback(sync_cb)

        # Seed initial Meshtastic nodes into MeshStore
        initial_nodes = meshtastic_service.get_nodes()
        if initial_nodes:
            seeded = seed_meshtastic_nodes(mesh_store, initial_nodes, local_node_id)
            logger.info("Seeded %d Meshtastic nodes into MeshStore", seeded)
    else:
        logger.warning("Meshtastic service not available")

    # Production safety: warn if API key is missing on live systems
    from app.auth import API_KEY

    if settings.use_live_data and not API_KEY:
        logger.critical(
            "MESHTASTIC_API_KEY is not set but live data mode is active. "
            "The Meshtastic API is unprotected. Set this environment variable."
        )

    # Apply HaLow config if enabled
    halow_cfg = config_svc.config.halow
    if halow_cfg.enabled and settings.use_live_data:
        from app.services import network_apply_service

        logger.info("Applying HaLow config at startup (transport: %s)", halow_cfg.transport)
        halow_result = network_apply_service.apply_halow(halow_cfg)
        if halow_result["success"]:
            logger.info("HaLow transport active: %s", halow_result["details"])
        else:
            logger.warning("HaLow transport failed: %s", halow_result["message"])

    # Start session cleanup background task
    async def session_cleanup_loop() -> None:
        """Purge expired auth sessions every hour."""
        import asyncio

        from app.services.auth_service import cleanup_expired_sessions

        while True:
            await asyncio.sleep(3600)
            try:
                cleanup_expired_sessions()
            except Exception:
                logger.exception("Session cleanup failed")

    import asyncio

    asyncio.create_task(session_cleanup_loop())

    if settings.use_live_data:
        logger.info("Starting mesh monitor (live data enabled)")
        ws.set_data_source(data_source)
        asyncio.create_task(ws.mesh_monitor_loop())
    else:
        logger.info("Mesh monitor disabled (using mock data)")


@app.on_event("shutdown")
async def shutdown_services():
    """Clean up services on shutdown."""
    logger.info("Shutting down services...")

    # Stop Meshtastic service and release serial port
    if meshtastic_service and meshtastic_service.available:
        meshtastic_service.stop()
        logger.info("Meshtastic service stopped")

    # Tear down BATMAN mesh
    if settings.use_live_data:
        from app.services.network_apply_service import teardown_batman

        teardown_batman()

    logger.info("Shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MYC3LIUM API", "version": "0.7.1"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "live_data": settings.use_live_data,
        "reticulum": reticulum.available if reticulum else False,
    }
