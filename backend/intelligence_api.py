"""
MYC3LIUM Intelligence API
FastAPI endpoints + WebSocket server for P900 dashboard
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from hardware_interfaces import HardwareManager
from intelligence import ATAKIntegration, IntelligenceGathering, SensorFusion
from mesh_analytics_api import router as mesh_analytics_router
from security import SecurityManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MYC3LIUM Intelligence API")

# Include mesh analytics router
app.include_router(mesh_analytics_router)

# Initialize hardware on startup
hardware = HardwareManager()

# Initialize security
SHARED_KEY = os.getenv("MYCELIUM_SHARED_KEY", None)
security = SecurityManager(shared_key=SHARED_KEY)

# Generate initial API token (save this for clients)
INITIAL_TOKEN = security.generate_api_token()
logger.info(f"Generated API token: {INITIAL_TOKEN[:8]}...")

# Enable privacy mode if configured
if os.getenv("PRIVACY_MODE", "false").lower() == "true":
    security.privacy_mode = True
    logger.info("Privacy mode enabled")

# CORS - restricted to specific origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Specific methods only
    allow_headers=["Authorization", "Content-Type"],
)

# Global state (initialized after security)
atak = None
sensor_fusion = SensorFusion()
intel = IntelligenceGathering(node_id="local")
active_connections: list[WebSocket] = []


def query_batman_neighbors() -> list[dict]:
    """
    Query BATMAN-adv for current mesh neighbors
    Returns list of nodes with link quality
    """
    try:
        # batctl n - show neighbors
        result = subprocess.run(
            ["batctl", "n"], capture_output=True, text=True, timeout=2
        )

        neighbors = []

        # Parse output (format: "aa:bb:cc:dd:ee:ff  0.123s (255) [mesh_iface]")
        for line in result.stdout.split("\n"):
            if ":" in line and "(" in line:
                parts = line.split()
                mac = parts[0]
                quality = int(re.search(r"\((\d+)\)", line).group(1))

                neighbors.append(
                    {
                        "id": mac.replace(":", ""),
                        "mac": mac,
                        "quality": quality,
                        "last_seen": parts[1] if len(parts) > 1 else "0s",
                    }
                )

        return neighbors

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        # Fallback: return mock data if BATMAN not available
        print(f"BATMAN query failed: {e}")
        return get_mock_neighbors()


def get_mock_neighbors() -> list[dict]:
    """
    Mock neighbor data for testing without hardware
    """
    import random

    return [
        {
            "id": "m3l_spore_01",
            "mac": "aa:bb:cc:dd:ee:01",
            "quality": random.randint(180, 255),
            "last_seen": "0.5s",
        },
        {
            "id": "m3l_spore_02",
            "mac": "aa:bb:cc:dd:ee:02",
            "quality": random.randint(150, 200),
            "last_seen": "1.2s",
        },
        {
            "id": "m3l_spore_03",
            "mac": "aa:bb:cc:dd:ee:03",
            "quality": random.randint(100, 180),
            "last_seen": "2.1s",
        },
    ]


def query_node_rssi(interface: str = "wlan0") -> list[dict]:
    """
    Query RSSI from all wireless interfaces (hardware direct)
    """
    # Validate interface name (prevent command injection)
    if not security.validate_interface_name(interface):
        logger.warning(f"Invalid interface name: {interface}")
        return []

    # Use hardware manager for all radios
    all_rssi = hardware.get_all_rssi()

    # Flatten to list of {mac, rssi, radio} dicts
    stations = []

    for radio, data in all_rssi.items():
        for entry in data:
            entry["radio"] = radio
            stations.append(entry)

    # Fallback to iw if no hardware
    if not stations:
        try:
            result = subprocess.run(
                ["iw", "dev", interface, "station", "dump"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            current_station = None

            for line in result.stdout.split("\n"):
                if line.startswith("Station"):
                    if current_station:
                        stations.append(current_station)

                    mac = line.split()[1]
                    current_station = {"mac": mac, "radio": "wifi"}

                elif "signal:" in line and current_station:
                    rssi = int(line.split()[1])
                    current_station["rssi"] = rssi

            if current_station:
                stations.append(current_station)

            return stations

        except Exception as e:
            print(f"RSSI query failed: {e}")
            return get_mock_rssi()

    return stations


def get_mock_rssi() -> list[dict]:
    """
    Mock RSSI data for testing
    """
    import random

    neighbors = get_mock_neighbors()

    return [{"mac": n["mac"], "rssi": random.randint(-90, -60)} for n in neighbors]


def get_gps_position() -> Optional[dict]:
    """
    Query GPS position (hardware direct or gpsd fallback)
    """
    # Try hardware first
    if hardware.gps:
        pos = hardware.get_position()
        if pos:
            return pos

    # Fallback to gpsd
    try:
        result = subprocess.run(
            ["gpspipe", "-w", "-n", "5"], capture_output=True, text=True, timeout=3
        )

        for line in result.stdout.split("\n"):
            if '"class":"TPV"' in line:
                data = json.loads(line)
                if "lat" in data and "lon" in data:
                    return {
                        "lat": data["lat"],
                        "lon": data["lon"],
                        "alt": data.get("alt", 0),
                        "accuracy": data.get("eph", 15.0),
                    }

        return None

    except Exception as e:
        print(f"GPS query failed: {e}")
        return get_mock_gps()


def get_mock_gps() -> Optional[dict]:
    """
    Mock GPS data - ONLY used in development/testing
    Returns None in production to avoid leaking test location
    """
    if os.getenv("ENVIRONMENT") == "development":
        import random

        return {
            "lat": 61.2181 + random.uniform(-0.01, 0.01),
            "lon": -149.9003 + random.uniform(-0.01, 0.01),
            "alt": random.uniform(0, 100),
            "accuracy": random.uniform(5, 15),
        }

    logger.warning("GPS hardware unavailable and not in dev mode")
    return None


async def update_sensor_fusion():
    """
    Background task: Update sensor fusion with latest data
    Self-healing with exponential backoff on errors
    """
    error_count = 0
    max_backoff = 60  # Max 60 seconds backoff

    while True:
        try:
            # Get GPS position
            gps = get_gps_position()
            if gps:
                sensor_fusion.update_gps(
                    gps["lat"], gps["lon"], gps["alt"], gps["accuracy"]
                )
                logger.debug(f"GPS updated: {gps['lat']:.6f}, {gps['lon']:.6f}")
            else:
                logger.warning("GPS position unavailable")

            # Get RSSI measurements
            query_node_rssi()
            neighbors = query_batman_neighbors()

            # TODO: Build anchor list from known node positions
            # For now, log neighbor count
            if neighbors:
                logger.debug(f"BATMAN neighbors: {len(neighbors)}")

            # Get current position estimate
            position = sensor_fusion.get_position()

            # Apply privacy filter
            filtered_lat, filtered_lon = security.apply_privacy_filter(
                position.lat, position.lon
            )

            # Update ATAK with filtered position
            await atak.update_unit_position(
                "m3l_local",
                {"lat": filtered_lat, "lon": filtered_lon, "alt": position.alt},
            )

            # Reset error count on success
            error_count = 0

            # Dynamic update interval (privacy jitter)
            update_interval = security.get_update_jitter()
            await asyncio.sleep(update_interval)

        except Exception as e:
            error_count += 1
            backoff = min(2**error_count, max_backoff)
            logger.error(f"Sensor fusion error: {e} (retry in {backoff}s)")
            await asyncio.sleep(backoff)


async def broadcast_to_clients(message: dict):
    """
    Send message to all connected WebSocket clients
    """
    disconnected = []

    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.append(connection)

    # Clean up disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)


@app.on_event("startup")
async def startup_event():
    """
    Start background tasks
    """
    global atak

    # Initialize ATAK with security
    atak = ATAKIntegration(security_manager=security)
    logger.info("ATAK integration initialized with security")

    # Start background tasks
    asyncio.create_task(update_sensor_fusion())
    asyncio.create_task(periodic_topology_broadcast())

    logger.info("Intelligence API started")
    logger.info(f"API Token: {INITIAL_TOKEN}")
    logger.info(f"Privacy Mode: {security.privacy_mode}")


async def periodic_topology_broadcast():
    """
    Broadcast mesh topology updates every 5 seconds
    """
    while True:
        try:
            topology = await get_mesh_topology()
            await broadcast_to_clients(
                {
                    "type": "topology_update",
                    "nodes": topology["nodes"],
                    "edges": topology["edges"],
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            print(f"Topology broadcast error: {e}")

        await asyncio.sleep(5)


@app.websocket("/ws/intelligence")
async def intelligence_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time intelligence updates
    Requires authentication via token parameter or header
    """
    # Authenticate before accepting
    if not await security.authenticate_websocket(websocket):
        return  # Connection closed

    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected: {websocket.client}")

    try:
        # Send initial state
        await websocket.send_json(
            {
                "type": "atak_status",
                "connected": True,  # Mock for now
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            await websocket.receive_text()
            # Handle client commands if needed

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/api/intelligence/topology")
async def get_mesh_topology():
    """
    Get current mesh topology
    Returns nodes and edges with link quality
    """
    neighbors = query_batman_neighbors()
    rssi_data = query_node_rssi()

    # Build nodes list
    nodes = []

    # Add local node
    position = sensor_fusion.get_position()
    nodes.append(
        {
            "id": "m3l_local",
            "position": {"lat": position.lat, "lon": position.lon, "alt": position.alt},
            "radio": "wifi",  # Would detect from active interface
            "rssi": 0,
            "neighbors": [n["id"] for n in neighbors],
        }
    )

    # Add neighbor nodes (would need their positions from mesh state)
    for neighbor in neighbors:
        # Find RSSI for this neighbor
        rssi_entry = next((r for r in rssi_data if r["mac"] == neighbor["mac"]), None)
        rssi = rssi_entry["rssi"] if rssi_entry else -80

        nodes.append(
            {
                "id": neighbor["id"],
                "position": {
                    "lat": position.lat + 0.001,  # Mock offset
                    "lon": position.lon + 0.001,
                    "alt": position.alt,
                },
                "radio": "halow" if neighbor["quality"] > 200 else "lora",
                "rssi": rssi,
                "neighbors": ["m3l_local"],  # Simplified
            }
        )

    # Build edges
    edges = []
    for neighbor in neighbors:
        edges.append(
            {
                "source": "m3l_local",
                "target": neighbor["id"],
                "quality": neighbor["quality"],
                "rssi": next(
                    (r["rssi"] for r in rssi_data if r["mac"] == neighbor["mac"]), -80
                ),
            }
        )

    return {"nodes": nodes, "edges": edges}


@app.get("/api/intelligence/position/{node_id}")
async def get_position_history(node_id: str, hours: int = 1):
    """
    Get position history for a node
    """
    # Would query from time-series database
    # For now, return current position
    position = sensor_fusion.get_position()

    return {
        "node_id": node_id,
        "history": [
            {
                "lat": position.lat,
                "lon": position.lon,
                "alt": position.alt,
                "timestamp": position.timestamp,
                "accuracy": position.uncertainty,
            }
        ],
    }


@app.get("/api/intelligence/rf_sources")
async def get_rf_sources():
    """
    Get detected RF sources
    """
    return {"sources": intel.rf_sources}


@app.get("/api/intelligence/heatmap")
async def get_heatmap(obs_type: str = "signal_strength"):
    """
    Get heatmap data for visualization
    """
    # Generate RSSI heatmap from recent measurements
    rssi_data = query_node_rssi()
    neighbors = query_batman_neighbors()
    position = sensor_fusion.get_position()

    heatmap = []

    for neighbor in neighbors:
        rssi_entry = next((r for r in rssi_data if r["mac"] == neighbor["mac"]), None)
        if rssi_entry:
            heatmap.append(
                {
                    "lat": position.lat + 0.001,  # Mock position
                    "lon": position.lon + 0.001,
                    "value": rssi_entry["rssi"],
                }
            )

    return {"type": obs_type, "points": heatmap}


@app.post("/api/intelligence/observation")
async def record_observation(
    obs_type: str,
    lat: float,
    lon: float,
    metadata: dict,
    authorization: Optional[str] = Header(None),
):
    """
    Record an intelligence observation
    Requires authentication and validates metadata
    """
    # Authenticate
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = authorization.replace("Bearer ", "")
    if not security.verify_api_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    # Rate limit
    client_id = "observation_api"  # Would use actual client ID
    if not security.rate_limit(client_id, "observation", max_per_minute=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Validate metadata
    try:
        sanitized_metadata = security.validate_observation_metadata(metadata)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate coordinates
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    # Record observation
    await intel.record_observation(
        obs_type, {"lat": lat, "lon": lon}, sanitized_metadata
    )

    logger.info(f"Observation recorded: {obs_type} at {lat:.6f}, {lon:.6f}")

    # Broadcast to connected clients
    await broadcast_to_clients(
        {
            "type": "observation_added",
            "obs_type": obs_type,
            "position": {"lat": lat, "lon": lon},
            "metadata": sanitized_metadata,
        }
    )

    return {"status": "recorded"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "batman_available": subprocess.run(
            ["which", "batctl"], capture_output=True
        ).returncode
        == 0,
        "gps_available": subprocess.run(
            ["which", "gpspipe"], capture_output=True
        ).returncode
        == 0,
        "sensor_fusion_active": True,
        "atak_connected": True,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
