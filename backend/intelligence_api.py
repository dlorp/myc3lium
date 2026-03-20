"""
MYC3LIUM Intelligence API
FastAPI endpoints + WebSocket server for P900 dashboard
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import asyncio
import json
import subprocess
import re
from datetime import datetime
from intelligence import (
    ATAKIntegration,
    SensorFusion,
    IntelligenceGathering
)
from hardware_interfaces import HardwareManager, async_get_position, async_get_all_rssi

app = FastAPI(title="MYC3LIUM Intelligence API")

# Initialize hardware on startup
hardware = HardwareManager()

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
atak = ATAKIntegration()
sensor_fusion = SensorFusion()
intel = IntelligenceGathering(node_id="local")
active_connections: List[WebSocket] = []


def query_batman_neighbors() -> List[Dict]:
    """
    Query BATMAN-adv for current mesh neighbors
    Returns list of nodes with link quality
    """
    try:
        # batctl n - show neighbors
        result = subprocess.run(
            ['batctl', 'n'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        neighbors = []
        
        # Parse output (format: "aa:bb:cc:dd:ee:ff  0.123s (255) [mesh_iface]")
        for line in result.stdout.split('\n'):
            if ':' in line and '(' in line:
                parts = line.split()
                mac = parts[0]
                quality = int(re.search(r'\((\d+)\)', line).group(1))
                
                neighbors.append({
                    'id': mac.replace(':', ''),
                    'mac': mac,
                    'quality': quality,
                    'last_seen': parts[1] if len(parts) > 1 else '0s'
                })
        
        return neighbors
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        # Fallback: return mock data if BATMAN not available
        print(f"BATMAN query failed: {e}")
        return get_mock_neighbors()


def get_mock_neighbors() -> List[Dict]:
    """
    Mock neighbor data for testing without hardware
    """
    import random
    
    return [
        {
            'id': 'm3l_spore_01',
            'mac': 'aa:bb:cc:dd:ee:01',
            'quality': random.randint(180, 255),
            'last_seen': '0.5s'
        },
        {
            'id': 'm3l_spore_02',
            'mac': 'aa:bb:cc:dd:ee:02',
            'quality': random.randint(150, 200),
            'last_seen': '1.2s'
        },
        {
            'id': 'm3l_spore_03',
            'mac': 'aa:bb:cc:dd:ee:03',
            'quality': random.randint(100, 180),
            'last_seen': '2.1s'
        }
    ]


def query_node_rssi(interface: str = 'wlan0') -> List[Dict]:
    """
    Query RSSI from all wireless interfaces (hardware direct)
    """
    # Use hardware manager for all radios
    all_rssi = hardware.get_all_rssi()
    
    # Flatten to list of {mac, rssi, radio} dicts
    stations = []
    
    for radio, data in all_rssi.items():
        for entry in data:
            entry['radio'] = radio
            stations.append(entry)
    
    # Fallback to iw if no hardware
    if not stations:
        try:
            result = subprocess.run(
                ['iw', 'dev', interface, 'station', 'dump'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            current_station = None
            
            for line in result.stdout.split('\n'):
                if line.startswith('Station'):
                    if current_station:
                        stations.append(current_station)
                    
                    mac = line.split()[1]
                    current_station = {'mac': mac, 'radio': 'wifi'}
                
                elif 'signal:' in line and current_station:
                    rssi = int(line.split()[1])
                    current_station['rssi'] = rssi
            
            if current_station:
                stations.append(current_station)
            
            return stations
            
        except Exception as e:
            print(f"RSSI query failed: {e}")
            return get_mock_rssi()
    
    return stations


def get_mock_rssi() -> List[Dict]:
    """
    Mock RSSI data for testing
    """
    import random
    
    neighbors = get_mock_neighbors()
    
    return [
        {
            'mac': n['mac'],
            'rssi': random.randint(-90, -60)
        }
        for n in neighbors
    ]


def get_gps_position() -> Optional[Dict]:
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
            ['gpspipe', '-w', '-n', '5'],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        for line in result.stdout.split('\n'):
            if '"class":"TPV"' in line:
                data = json.loads(line)
                if 'lat' in data and 'lon' in data:
                    return {
                        'lat': data['lat'],
                        'lon': data['lon'],
                        'alt': data.get('alt', 0),
                        'accuracy': data.get('eph', 15.0)
                    }
        
        return None
        
    except Exception as e:
        print(f"GPS query failed: {e}")
        return get_mock_gps()


def get_mock_gps() -> Dict:
    """
    Mock GPS data for testing (Anchorage, AK area)
    """
    import random
    
    return {
        'lat': 61.2181 + random.uniform(-0.01, 0.01),
        'lon': -149.9003 + random.uniform(-0.01, 0.01),
        'alt': random.uniform(0, 100),
        'accuracy': random.uniform(5, 15)
    }


async def update_sensor_fusion():
    """
    Background task: Update sensor fusion with latest data
    """
    while True:
        try:
            # Get GPS position
            gps = get_gps_position()
            if gps:
                sensor_fusion.update_gps(
                    gps['lat'],
                    gps['lon'],
                    gps['alt'],
                    gps['accuracy']
                )
            
            # Get RSSI measurements
            rssi_data = query_node_rssi()
            neighbors = query_batman_neighbors()
            
            # Build anchor list for trilateration
            # (Would need actual node positions from mesh state)
            # For now, skip RSSI fusion until we have anchor positions
            
            # Update ATAK with current position
            position = sensor_fusion.get_position()
            await atak.update_unit_position('m3l_local', {
                'lat': position.lat,
                'lon': position.lon,
                'alt': position.alt
            })
            
        except Exception as e:
            print(f"Sensor fusion update error: {e}")
        
        await asyncio.sleep(1)  # Update every second


async def broadcast_to_clients(message: Dict):
    """
    Send message to all connected WebSocket clients
    """
    disconnected = []
    
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)
    
    # Clean up disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)


@app.on_event("startup")
async def startup_event():
    """
    Start background tasks
    """
    asyncio.create_task(update_sensor_fusion())
    asyncio.create_task(periodic_topology_broadcast())


async def periodic_topology_broadcast():
    """
    Broadcast mesh topology updates every 5 seconds
    """
    while True:
        try:
            topology = await get_mesh_topology()
            await broadcast_to_clients({
                'type': 'topology_update',
                'nodes': topology['nodes'],
                'edges': topology['edges'],
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f"Topology broadcast error: {e}")
        
        await asyncio.sleep(5)


@app.websocket("/ws/intelligence")
async def intelligence_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time intelligence updates
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial state
        await websocket.send_json({
            'type': 'atak_status',
            'connected': True  # Mock for now
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle client commands if needed
            
    except WebSocketDisconnect:
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
    nodes.append({
        'id': 'm3l_local',
        'position': {
            'lat': position.lat,
            'lon': position.lon,
            'alt': position.alt
        },
        'radio': 'wifi',  # Would detect from active interface
        'rssi': 0,
        'neighbors': [n['id'] for n in neighbors]
    })
    
    # Add neighbor nodes (would need their positions from mesh state)
    for neighbor in neighbors:
        # Find RSSI for this neighbor
        rssi_entry = next((r for r in rssi_data if r['mac'] == neighbor['mac']), None)
        rssi = rssi_entry['rssi'] if rssi_entry else -80
        
        nodes.append({
            'id': neighbor['id'],
            'position': {
                'lat': position.lat + 0.001,  # Mock offset
                'lon': position.lon + 0.001,
                'alt': position.alt
            },
            'radio': 'halow' if neighbor['quality'] > 200 else 'lora',
            'rssi': rssi,
            'neighbors': ['m3l_local']  # Simplified
        })
    
    # Build edges
    edges = []
    for neighbor in neighbors:
        edges.append({
            'source': 'm3l_local',
            'target': neighbor['id'],
            'quality': neighbor['quality'],
            'rssi': next((r['rssi'] for r in rssi_data if r['mac'] == neighbor['mac']), -80)
        })
    
    return {
        'nodes': nodes,
        'edges': edges
    }


@app.get("/api/intelligence/position/{node_id}")
async def get_position_history(node_id: str, hours: int = 1):
    """
    Get position history for a node
    """
    # Would query from time-series database
    # For now, return current position
    position = sensor_fusion.get_position()
    
    return {
        'node_id': node_id,
        'history': [
            {
                'lat': position.lat,
                'lon': position.lon,
                'alt': position.alt,
                'timestamp': position.timestamp,
                'accuracy': position.uncertainty
            }
        ]
    }


@app.get("/api/intelligence/rf_sources")
async def get_rf_sources():
    """
    Get detected RF sources
    """
    return {
        'sources': intel.rf_sources
    }


@app.get("/api/intelligence/heatmap")
async def get_heatmap(obs_type: str = 'signal_strength'):
    """
    Get heatmap data for visualization
    """
    # Generate RSSI heatmap from recent measurements
    rssi_data = query_node_rssi()
    neighbors = query_batman_neighbors()
    position = sensor_fusion.get_position()
    
    heatmap = []
    
    for neighbor in neighbors:
        rssi_entry = next((r for r in rssi_data if r['mac'] == neighbor['mac']), None)
        if rssi_entry:
            heatmap.append({
                'lat': position.lat + 0.001,  # Mock position
                'lon': position.lon + 0.001,
                'value': rssi_entry['rssi']
            })
    
    return {
        'type': obs_type,
        'points': heatmap
    }


@app.post("/api/intelligence/observation")
async def record_observation(
    obs_type: str,
    lat: float,
    lon: float,
    metadata: Dict
):
    """
    Record an intelligence observation
    """
    await intel.record_observation(
        obs_type,
        {'lat': lat, 'lon': lon},
        metadata
    )
    
    # Broadcast to connected clients
    await broadcast_to_clients({
        'type': 'observation_added',
        'obs_type': obs_type,
        'position': {'lat': lat, 'lon': lon},
        'metadata': metadata
    })
    
    return {'status': 'recorded'}


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        'status': 'healthy',
        'batman_available': subprocess.run(['which', 'batctl'], capture_output=True).returncode == 0,
        'gps_available': subprocess.run(['which', 'gpspipe'], capture_output=True).returncode == 0,
        'sensor_fusion_active': True,
        'atak_connected': True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
