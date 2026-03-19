#!/usr/bin/env python3
"""
MYC3LIUM Multi-Protocol Bridge
Connects multiple mesh protocols to unified WebUI

Protocols:
- Reticulum LXMF (encrypted messaging)
- Meshtastic (compatibility bridge)
- ATAK/TAK (Cursor-on-Target for tactical awareness)
- Camera Streams (FROND video feeds)

Routes to WebUI pages:
- P200: Mesh topology
- P300: Messages (LXMF + Meshtastic)
- P400: ATAK map view + sensor data
- P500: Camera streams
- P700: Network events
"""

import os
import sys
import time
import json
import asyncio
import logging
import struct
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# FastAPI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# Reticulum
import RNS
from RNS import Identity, Destination, Packet, Transport
import LXMF

# Meshtastic (install: pip3 install meshtastic)
try:
    import meshtastic
    import meshtastic.serial_interface
    import meshtastic.tcp_interface
    MESHTASTIC_AVAILABLE = True
except ImportError:
    MESHTASTIC_AVAILABLE = False
    logging.warning("Meshtastic not available - install with: pip3 install meshtastic")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/opt/myc3lium/logs/bridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

CONFIG = {
    'reticulum_config_path': '/home/myc3lium/.reticulum',
    'identity_path': '/home/myc3lium/.reticulum/storage/identities/myc3lium-node',
    'lxmf_storage': '/home/myc3lium/.reticulum/lxmf_storage',
    'api_host': '0.0.0.0',
    'api_port': 8000,
    'meshtastic_device': '/dev/ttyUSB0',  # Serial port or 'tcp:hostname'
    'atak_server': 'tcp://127.0.0.1:8087',  # FreeTAKServer CoT port
    'camera_streams': {},  # Populated from discovery
}

# ============================================================================
# Pydantic Models
# ============================================================================

class Message(BaseModel):
    destination: str
    content: str
    timestamp: Optional[float] = None
    protocol: Optional[str] = "lxmf"  # lxmf, meshtastic, atak
    
class MeshNode(BaseModel):
    hash: str
    name: Optional[str] = None
    last_seen: float
    hop_count: int
    interfaces: List[str]
    protocol: str  # reticulum, meshtastic
    
class CoTEvent(BaseModel):
    """Cursor-on-Target event for ATAK"""
    uid: str
    type: str  # a-f-G-E-S (friendly ground equipment static)
    lat: float
    lon: float
    hae: Optional[float] = 0.0  # Height above ellipsoid
    ce: Optional[float] = 9999999.0  # Circular error
    le: Optional[float] = 9999999.0  # Linear error
    callsign: Optional[str] = None
    remarks: Optional[str] = None
    
class CameraStream(BaseModel):
    node_id: str
    stream_url: str
    name: Optional[str] = "Camera"
    format: str = "rtsp"  # rtsp, http, hls
    
class NetworkEvent(BaseModel):
    type: str  # node_join, node_leave, message, announce, route_update
    timestamp: float
    data: Dict[str, Any]

# ============================================================================
# Meshtastic Bridge
# ============================================================================

class MeshtasticBridge:
    """Translates Meshtastic packets to LXMF format"""
    
    def __init__(self, device: str):
        self.device = device
        self.interface = None
        self.message_callbacks = []
        self.node_callbacks = []
        self.nodes: Dict[str, Dict] = {}
        
    def start(self):
        """Initialize Meshtastic interface"""
        if not MESHTASTIC_AVAILABLE:
            logger.warning("Meshtastic not available, skipping")
            return
            
        try:
            logger.info(f"Connecting to Meshtastic device: {self.device}")
            
            if self.device.startswith('tcp:'):
                host = self.device.split(':')[1]
                self.interface = meshtastic.tcp_interface.TCPInterface(host)
            else:
                self.interface = meshtastic.serial_interface.SerialInterface(self.device)
                
            # Register callbacks
            self.interface.onReceive = self._on_receive
            self.interface.onConnection = self._on_connection
            
            logger.info("✅ Meshtastic bridge started")
            
        except Exception as e:
            logger.error(f"Failed to start Meshtastic: {e}")
            
    def _on_receive(self, packet, interface):
        """Handle received Meshtastic packet"""
        try:
            # Extract packet data
            from_id = packet.get('fromId', 'unknown')
            to_id = packet.get('toId', 'broadcast')
            
            # Update node info
            if from_id not in self.nodes:
                self.nodes[from_id] = {
                    'id': from_id,
                    'last_seen': time.time(),
                    'rssi': packet.get('rssi'),
                    'snr': packet.get('snr'),
                }
                
                # Notify node discovery
                for callback in self.node_callbacks:
                    callback(from_id, self.nodes[from_id])
            
            # Handle different packet types
            decoded = packet.get('decoded', {})
            portnum = decoded.get('portnum', '')
            
            if portnum == 'TEXT_MESSAGE_APP':
                # Text message
                text = decoded.get('payload', b'').decode('utf-8', errors='ignore')
                
                message = {
                    'source': from_id,
                    'destination': to_id,
                    'content': text,
                    'timestamp': time.time(),
                    'protocol': 'meshtastic',
                    'rssi': packet.get('rssi'),
                    'snr': packet.get('snr'),
                    'hop_limit': packet.get('hopLimit', 0),
                }
                
                # Notify callbacks
                for callback in self.message_callbacks:
                    callback(message)
                    
            elif portnum == 'POSITION_APP':
                # Position update - convert to CoT
                payload = decoded.get('payload', {})
                lat = payload.get('latitude', 0) / 1e7
                lon = payload.get('longitude', 0) / 1e7
                alt = payload.get('altitude', 0)
                
                logger.info(f"📍 Position update from {from_id}: {lat}, {lon}")
                
            elif portnum == 'NODEINFO_APP':
                # Node info
                payload = decoded.get('payload', {})
                user = payload.get('user', {})
                
                self.nodes[from_id].update({
                    'long_name': user.get('longName'),
                    'short_name': user.get('shortName'),
                    'hw_model': user.get('hwModel'),
                })
                
        except Exception as e:
            logger.error(f"Error processing Meshtastic packet: {e}")
            
    def _on_connection(self, interface, topic=None):
        """Handle Meshtastic connection events"""
        logger.info(f"Meshtastic connection event: {topic}")
        
    def send_text(self, text: str, destination: str = "^all") -> bool:
        """Send text message via Meshtastic"""
        try:
            if not self.interface:
                return False
                
            self.interface.sendText(text, destinationId=destination)
            logger.info(f"📤 Sent Meshtastic message to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Meshtastic message: {e}")
            return False
            
    def get_nodes(self) -> List[Dict]:
        """Get list of known Meshtastic nodes"""
        return list(self.nodes.values())

# ============================================================================
# ATAK/CoT Handler
# ============================================================================

class ATAKHandler:
    """Handles Cursor-on-Target (CoT) messages for ATAK integration"""
    
    def __init__(self):
        self.cot_callbacks = []
        self.tak_server = None
        self.own_uid = f"MYC3LIUM-{os.uname().nodename}"
        
    async def start(self):
        """Connect to FreeTAKServer (optional)"""
        try:
            # For now, just generate CoT locally
            # Full FreeTAKServer integration can be added later
            logger.info("ATAK/CoT handler initialized (local mode)")
            
        except Exception as e:
            logger.error(f"ATAK handler error: {e}")
            
    def create_cot_xml(self, event: CoTEvent) -> str:
        """Generate CoT XML from event"""
        now = datetime.now(timezone.utc)
        stale = datetime.fromtimestamp(now.timestamp() + 300, timezone.utc)  # 5 min stale
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<event version="2.0" uid="{event.uid}" type="{event.type}" time="{now.isoformat()}" start="{now.isoformat()}" stale="{stale.isoformat()}" how="m-g">
    <point lat="{event.lat}" lon="{event.lon}" hae="{event.hae}" ce="{event.ce}" le="{event.le}"/>
    <detail>
        <contact callsign="{event.callsign or event.uid}"/>
        <remarks>{event.remarks or ""}</remarks>
        <link uid="{self.own_uid}" type="a-f-G-E-S" relation="p-p"/>
    </detail>
</event>'''
        
        return xml
        
    def parse_cot_xml(self, xml_data: str) -> Optional[CoTEvent]:
        """Parse CoT XML into event object"""
        try:
            root = ET.fromstring(xml_data)
            
            point = root.find('point')
            detail = root.find('detail')
            contact = detail.find('contact') if detail is not None else None
            
            event = CoTEvent(
                uid=root.get('uid'),
                type=root.get('type'),
                lat=float(point.get('lat')),
                lon=float(point.get('lon')),
                hae=float(point.get('hae', 0)),
                ce=float(point.get('ce', 9999999)),
                le=float(point.get('le', 9999999)),
                callsign=contact.get('callsign') if contact is not None else None,
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing CoT XML: {e}")
            return None
            
    def send_position(self, lat: float, lon: float, callsign: str):
        """Send position as CoT event"""
        event = CoTEvent(
            uid=self.own_uid,
            type="a-f-G-E-S",  # Friendly ground equipment static
            lat=lat,
            lon=lon,
            callsign=callsign,
        )
        
        xml = self.create_cot_xml(event)
        
        # Notify callbacks
        for callback in self.cot_callbacks:
            callback(event, xml)
            
        return xml

# ============================================================================
# Camera Stream Manager
# ============================================================================

class CameraStreamManager:
    """Manages camera streams from FROND nodes"""
    
    def __init__(self):
        self.streams: Dict[str, CameraStream] = {}
        
    def register_stream(self, node_id: str, stream_url: str, name: str = None):
        """Register a camera stream"""
        stream = CameraStream(
            node_id=node_id,
            stream_url=stream_url,
            name=name or f"Camera {node_id[:8]}",
            format=self._detect_format(stream_url)
        )
        
        self.streams[node_id] = stream
        logger.info(f"📹 Registered camera stream: {node_id} -> {stream_url}")
        
    def _detect_format(self, url: str) -> str:
        """Detect stream format from URL"""
        if url.startswith('rtsp://'):
            return 'rtsp'
        elif url.endswith('.m3u8'):
            return 'hls'
        else:
            return 'http'
            
    def get_streams(self) -> List[CameraStream]:
        """Get all registered streams"""
        return list(self.streams.values())
        
    async def proxy_stream(self, node_id: str):
        """Proxy stream for WebUI (converts RTSP to HTTP chunks if needed)"""
        if node_id not in self.streams:
            raise HTTPException(404, "Stream not found")
            
        stream = self.streams[node_id]
        
        # For RTSP, we'd use ffmpeg to transcode
        # For now, just return stream URL for direct access
        return {"stream_url": stream.stream_url, "format": stream.format}

# ============================================================================
# Reticulum Manager (Enhanced)
# ============================================================================

class ReticulumManager:
    """Manages Reticulum network stack"""
    
    def __init__(self):
        self.reticulum = None
        self.identity = None
        self.lxmf_router = None
        self.destination = None
        self.known_destinations: Dict[bytes, Dict] = {}
        self.message_callbacks = []
        self.announce_callbacks = []
        
    def start(self):
        """Initialize Reticulum"""
        logger.info("🍄 Starting Reticulum...")
        
        config_path = CONFIG['reticulum_config_path']
        self.reticulum = RNS.Reticulum(configdir=config_path)
        
        # Load or create identity
        identity_path = Path(CONFIG['identity_path'])
        if identity_path.exists():
            logger.info(f"Loading identity from {identity_path}")
            self.identity = Identity.from_file(str(identity_path))
        else:
            logger.info("Creating new identity...")
            identity_path.parent.mkdir(parents=True, exist_ok=True)
            self.identity = Identity()
            self.identity.to_file(str(identity_path))
            logger.info(f"Identity saved to {identity_path}")
        
        # Create destination
        self.destination = RNS.Destination(
            self.identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            "myc3lium",
            "node"
        )
        
        self.destination.set_packet_callback(self._packet_received)
        
        logger.info(f"Destination: {RNS.prettyhexrep(self.destination.hash)}")
        
        # Initialize LXMF
        self._init_lxmf()
        
        # Start announce loop
        self._start_announce_loop()
        
        logger.info("✅ Reticulum started")
        
    def _init_lxmf(self):
        """Initialize LXMF messaging"""
        logger.info("Initializing LXMF...")
        
        self.lxmf_router = LXMF.LXMRouter(
            identity=self.identity,
            storagepath=CONFIG['lxmf_storage']
        )
        
        self.lxmf_router.register_delivery_callback(self._lxmf_delivery)
        self.lxmf_router.announce()
        
        logger.info(f"✅ LXMF: {RNS.prettyhexrep(self.lxmf_router.destination.hash)}")
        
    def _packet_received(self, data, packet):
        """Handle received packet"""
        try:
            logger.info(f"📦 Packet from {RNS.prettyhexrep(packet.destination_hash)}")
            
            message = data.decode('utf-8')
            
            for callback in self.message_callbacks:
                callback({
                    'source': RNS.prettyhexrep(packet.destination_hash),
                    'content': message,
                    'timestamp': time.time(),
                    'protocol': 'reticulum',
                    'rssi': packet.rssi if hasattr(packet, 'rssi') else None,
                    'snr': packet.snr if hasattr(packet, 'snr') else None,
                })
                
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            
    def _lxmf_delivery(self, message):
        """Handle LXMF message delivery"""
        try:
            logger.info(f"📨 LXMF message received")
            
            for callback in self.message_callbacks:
                callback({
                    'source': RNS.prettyhexrep(message.source_hash),
                    'content': message.content.decode('utf-8'),
                    'timestamp': message.timestamp,
                    'protocol': 'lxmf',
                    'encrypted': True,
                })
                
        except Exception as e:
            logger.error(f"Error processing LXMF: {e}")
            
    def _start_announce_loop(self):
        """Periodically announce presence"""
        def announce_loop():
            while True:
                try:
                    logger.debug("📢 Announcing...")
                    self.destination.announce()
                    if self.lxmf_router:
                        self.lxmf_router.announce()
                    time.sleep(300)
                except Exception as e:
                    logger.error(f"Announce error: {e}")
                    time.sleep(60)
                    
        import threading
        threading.Thread(target=announce_loop, daemon=True).start()
        
    def send_message(self, destination_hash: str, content: str) -> bool:
        """Send message to destination"""
        try:
            dest_hash = bytes.fromhex(destination_hash)
            packet = RNS.Packet(dest_hash, content.encode('utf-8'))
            packet.send()
            logger.info(f"📤 Sent to {destination_hash}")
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
            
    def send_lxmf_message(self, destination_hash: str, content: str) -> bool:
        """Send LXMF message"""
        try:
            dest_hash = bytes.fromhex(destination_hash)
            message = LXMF.LXMessage(
                destination=dest_hash,
                source=self.lxmf_router.destination,
                content=content.encode('utf-8'),
                title="MYC3LIUM"
            )
            self.lxmf_router.handle_outbound(message)
            logger.info(f"📤 LXMF to {destination_hash}")
            return True
        except Exception as e:
            logger.error(f"LXMF send error: {e}")
            return False
            
    def get_mesh_stats(self) -> Dict:
        """Get mesh statistics"""
        stats = {
            'transport': {
                'announce_table_size': len(Transport.announce_table) if hasattr(Transport, 'announce_table') else 0,
                'destination_table_size': len(Transport.destination_table) if hasattr(Transport, 'destination_table') else 0,
            },
            'interfaces': []
        }
        
        for interface in RNS.Transport.interfaces:
            stats['interfaces'].append({
                'name': str(interface),
                'status': 'online' if interface.online else 'offline',
                'rxb': interface.rxb if hasattr(interface, 'rxb') else 0,
                'txb': interface.txb if hasattr(interface, 'txb') else 0,
            })
            
        return stats
        
    def get_known_destinations(self) -> List[Dict]:
        """Get known destinations"""
        destinations = []
        
        if hasattr(Transport, 'destination_table'):
            for dest_hash, dest_data in Transport.destination_table.items():
                destinations.append({
                    'hash': RNS.prettyhexrep(dest_hash),
                    'timestamp': dest_data[0] if len(dest_data) > 0 else None,
                    'hops': dest_data[1] if len(dest_data) > 1 else None,
                    'protocol': 'reticulum',
                })
                
        return destinations

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(title="MYC3LIUM Multi-Protocol Bridge", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
rns_manager = ReticulumManager()
meshtastic_bridge = MeshtasticBridge(CONFIG['meshtastic_device'])
atak_handler = ATAKHandler()
camera_manager = CameraStreamManager()

# WebSocket connections
websocket_connections: Set[WebSocket] = set()

# Message aggregation (for P300)
message_history: List[Dict] = []
MAX_MESSAGE_HISTORY = 1000

# ============================================================================
# WebSocket
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    websocket_connections.add(websocket)
    
    logger.info(f"WebSocket connected (total: {len(websocket_connections)})")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info(f"WebSocket disconnected (remaining: {len(websocket_connections)})")

async def broadcast_to_websockets(message: Dict):
    """Broadcast to all WebSocket clients"""
    dead = set()
    
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except:
            dead.add(ws)
            
    websocket_connections.difference_update(dead)

# ============================================================================
# REST API
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "MYC3LIUM Multi-Protocol Bridge",
        "version": "2.0.0",
        "protocols": ["reticulum", "lxmf", "meshtastic", "atak", "camera"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "reticulum": "running" if rns_manager.reticulum else "stopped",
        "meshtastic": "running" if meshtastic_bridge.interface else "disabled",
        "websockets": len(websocket_connections),
        "message_history": len(message_history)
    }

# P200: Mesh Topology
@app.get("/mesh/stats")
async def mesh_stats():
    """P200: Complete mesh statistics"""
    rns_stats = rns_manager.get_mesh_stats()
    meshtastic_nodes = meshtastic_bridge.get_nodes()
    
    return {
        "reticulum": rns_stats,
        "meshtastic": {
            "node_count": len(meshtastic_nodes),
            "nodes": meshtastic_nodes
        },
        "total_nodes": len(rns_manager.get_known_destinations()) + len(meshtastic_nodes)
    }

@app.get("/mesh/destinations")
async def mesh_destinations():
    """P200: All mesh nodes across protocols"""
    rns_dests = rns_manager.get_known_destinations()
    mesh_nodes = meshtastic_bridge.get_nodes()
    
    # Convert Meshtastic nodes to unified format
    mesh_dests = [{
        'hash': node['id'],
        'timestamp': node['last_seen'],
        'hops': 0,  # Unknown for Meshtastic
        'protocol': 'meshtastic',
        'name': node.get('long_name'),
    } for node in mesh_nodes]
    
    return {
        "destinations": rns_dests + mesh_dests
    }

# P300: Messages (LXMF + Meshtastic)
@app.get("/messages")
async def get_messages(limit: int = 100):
    """P300: Get message history from all protocols"""
    return {
        "messages": message_history[-limit:],
        "total": len(message_history)
    }

@app.post("/message/send")
async def send_message(message: Message):
    """P300: Send message via specified protocol"""
    if message.protocol == "meshtastic":
        success = meshtastic_bridge.send_text(message.content, message.destination)
    elif message.protocol == "lxmf":
        success = rns_manager.send_lxmf_message(message.destination, message.content)
    else:
        success = rns_manager.send_message(message.destination, message.content)
    
    if success:
        return {"status": "sent", "protocol": message.protocol}
    else:
        raise HTTPException(500, "Send failed")

# P400: ATAK/CoT Integration
@app.post("/atak/position")
async def send_position(lat: float, lon: float, callsign: str):
    """P400: Send position update as CoT"""
    xml = atak_handler.send_position(lat, lon, callsign)
    
    # Broadcast to WebSocket
    await broadcast_to_websockets({
        'type': 'cot_event',
        'data': {'lat': lat, 'lon': lon, 'callsign': callsign}
    })
    
    return {"status": "sent", "cot_xml": xml}

@app.post("/atak/cot")
async def send_cot(event: CoTEvent):
    """P400: Send custom CoT event"""
    xml = atak_handler.create_cot_xml(event)
    return {"cot_xml": xml}

# P500: Camera Streams
@app.get("/cameras")
async def get_cameras():
    """P500: List all camera streams"""
    return {
        "streams": camera_manager.get_streams()
    }

@app.post("/cameras/register")
async def register_camera(node_id: str, stream_url: str, name: str = None):
    """P500: Register new camera stream"""
    camera_manager.register_stream(node_id, stream_url, name)
    
    # Notify WebSocket clients
    await broadcast_to_websockets({
        'type': 'camera_registered',
        'data': {'node_id': node_id, 'stream_url': stream_url}
    })
    
    return {"status": "registered"}

@app.get("/cameras/{node_id}/stream")
async def get_camera_stream(node_id: str):
    """P500: Get camera stream info"""
    return await camera_manager.proxy_stream(node_id)

# P700: Network Events
@app.get("/events")
async def get_events(limit: int = 100):
    """P700: Get recent network events"""
    # This would be populated from various callbacks
    return {"events": []}

@app.get("/identity")
async def get_identity():
    """Get node identity"""
    if not rns_manager.identity or not rns_manager.destination:
        raise HTTPException(500, "Reticulum not initialized")
        
    return {
        "hash": RNS.prettyhexrep(rns_manager.destination.hash),
        "uid": atak_handler.own_uid,
    }

@app.post("/announce")
async def announce():
    """Force announce on all protocols"""
    try:
        rns_manager.destination.announce()
        if rns_manager.lxmf_router:
            rns_manager.lxmf_router.announce()
        return {"status": "announced"}
    except Exception as e:
        raise HTTPException(500, str(e))

# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup():
    logger.info("🍄 MYC3LIUM Multi-Protocol Bridge starting...")
    
    # Start Reticulum
    rns_manager.start()
    
    # Start Meshtastic
    meshtastic_bridge.start()
    
    # Start ATAK handler
    await atak_handler.start()
    
    # Register message callback for aggregation
    def aggregate_message(msg):
        message_history.append(msg)
        if len(message_history) > MAX_MESSAGE_HISTORY:
            message_history.pop(0)
        
        # Broadcast to WebSocket
        asyncio.create_task(broadcast_to_websockets({
            'type': 'message',
            'page': 'p300',  # Messages page
            'data': msg
        }))
    
    rns_manager.message_callbacks.append(aggregate_message)
    meshtastic_bridge.message_callbacks.append(aggregate_message)
    
    # Register node discovery callback
    def node_discovered(node_id, node_data):
        asyncio.create_task(broadcast_to_websockets({
            'type': 'node_discovered',
            'page': 'p200',  # Topology page
            'data': {'id': node_id, **node_data}
        }))
    
    meshtastic_bridge.node_callbacks.append(node_discovered)
    
    logger.info("✅ All protocols initialized")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down bridge...")

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    Path("/opt/myc3lium/logs").mkdir(parents=True, exist_ok=True)
    
    uvicorn.run(
        app,
        host=CONFIG['api_host'],
        port=CONFIG['api_port'],
        log_level="info"
    )
