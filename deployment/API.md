# 🍄 MYC3LIUM API Documentation

**Multi-Protocol Bridge API v2.0**

Complete REST API and WebSocket documentation for MYC3LIUM mesh network integration.

---

## Overview

The MYC3LIUM bridge provides unified access to multiple mesh protocols:

- **Reticulum** - Core mesh network transport
- **LXMF** - Encrypted messaging over Reticulum
- **Meshtastic** - Compatibility with existing Meshtastic devices
- **ATAK/TAK** - Cursor-on-Target tactical awareness
- **Camera Streams** - FROND video feeds

**Base URL:** `http://myc3.local/api` (via nginx) or `http://localhost:8000` (direct)

**WebSocket:** `ws://myc3.local/ws`

---

## WebUI Page Mapping

| Page | Endpoint Prefix | Purpose |
|------|----------------|---------|
| P200 | `/mesh/*` | Mesh topology & node discovery |
| P300 | `/messages/*` | Multi-protocol messaging |
| P400 | `/atak/*` | ATAK map & tactical data |
| P500 | `/cameras/*` | Camera stream management |
| P700 | `/events/*` | Network events & logs |

---

## Authentication

**API Key:** Meshtastic send and config mutation endpoints require `X-API-Key` header when `MESHTASTIC_API_KEY` is set. Auth is skipped in dev mode (no key configured).

**Protected endpoints:** `POST /api/meshtastic/send`, `PATCH /api/config/*`, `POST /api/config/*`

---

## REST API Endpoints

### General

#### `GET /`
Root endpoint, API info.

**Response:**
```json
{
  "service": "MYC3LIUM Multi-Protocol Bridge",
  "version": "2.0.0",
  "protocols": ["reticulum", "lxmf", "meshtastic", "atak", "camera"]
}
```

#### `GET /health`
Health check.

**Response:**
```json
{
  "status": "healthy",
  "live_data": true,
  "reticulum": true
}
```

#### `GET /identity`
Get node identity.

**Response:**
```json
{
  "hash": "abc123...",
  "uid": "MYC3LIUM-node-01"
}
```

---

### P200: Mesh Topology

#### `GET /mesh/stats`
Complete mesh statistics across all protocols.

**Response:**
```json
{
  "reticulum": {
    "transport": {
      "announce_table_size": 5,
      "destination_table_size": 12
    },
    "interfaces": [
      {
        "name": "LoRa Interface",
        "status": "online",
        "rxb": 1024000,
        "txb": 512000
      }
    ]
  },
  "meshtastic": {
    "node_count": 3,
    "nodes": [
      {
        "id": "!abc12345",
        "long_name": "Node Alpha",
        "rssi": -85,
        "snr": 8.5
      }
    ]
  },
  "total_nodes": 15
}
```

#### `GET /mesh/destinations`
All discovered nodes across all protocols.

**Response:**
```json
{
  "destinations": [
    {
      "hash": "abc123...",
      "timestamp": 1234567890.0,
      "hops": 2,
      "protocol": "reticulum",
      "name": null
    },
    {
      "hash": "!def45678",
      "timestamp": 1234567891.0,
      "hops": 0,
      "protocol": "meshtastic",
      "name": "Node Bravo"
    }
  ]
}
```

---

### P300: Messages

#### `GET /messages?limit=100`
Get message history from all protocols.

**Query Parameters:**
- `limit` (int): Max messages to return (default: 100)

**Response:**
```json
{
  "messages": [
    {
      "source": "abc123...",
      "content": "Hello mesh!",
      "timestamp": 1234567890.0,
      "protocol": "lxmf",
      "encrypted": true,
      "rssi": -95,
      "snr": 5.2
    },
    {
      "source": "!def45678",
      "content": "Message from Meshtastic",
      "timestamp": 1234567895.0,
      "protocol": "meshtastic",
      "hop_limit": 3
    }
  ],
  "total": 42
}
```

#### `POST /message/send`
Send message via specified protocol.

**Request Body:**
```json
{
  "destination": "abc123..." or "!meshtastic-id" or "^all",
  "content": "Hello from MYC3LIUM!",
  "protocol": "lxmf"
}
```

**Protocols:**
- `"lxmf"` - Encrypted LXMF message (default)
- `"reticulum"` - Raw Reticulum packet
- `"meshtastic"` - Meshtastic text message

**Destinations:**
- Reticulum: Hex hash (e.g., `"abc123..."`)
- Meshtastic: Node ID (e.g., `"!abc12345"`) or `"^all"` for broadcast

**Response:**
```json
{
  "status": "sent",
  "protocol": "lxmf"
}
```

#### `POST /announce`
Force announce presence on all protocols.

**Response:**
```json
{
  "status": "announced"
}
```

---

### P400: ATAK/CoT Integration

#### `POST /atak/position`
Send position update as Cursor-on-Target.

**Request Body:**
```json
{
  "lat": 61.2181,
  "lon": -149.9003,
  "callsign": "MYC3LIUM-01"
}
```

**Response:**
```json
{
  "status": "sent",
  "cot_xml": "<?xml version=\"1.0\"?>..."
}
```

#### `POST /atak/cot`
Send custom CoT event.

**Request Body:**
```json
{
  "uid": "MYC3LIUM-01",
  "type": "a-f-G-E-S",
  "lat": 61.2181,
  "lon": -149.9003,
  "hae": 100.0,
  "ce": 10.0,
  "le": 5.0,
  "callsign": "Node Alpha",
  "remarks": "MYC3LIUM mesh node"
}
```

**CoT Types:**
- `a-f-G-E-S` - Friendly ground equipment static
- `a-f-G-E-V` - Friendly ground equipment vehicle
- `a-f-A` - Friendly aircraft
- `a-h-G` - Hostile ground
- `b-m-p-s-p-loc` - Point of interest

**Response:**
```json
{
  "cot_xml": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>..."
}
```

---

### P500: Camera Streams

#### `GET /cameras`
List all registered camera streams.

**Response:**
```json
{
  "streams": [
    {
      "node_id": "abc123...",
      "stream_url": "rtsp://10.13.0.5:8554/stream",
      "name": "Front Camera",
      "format": "rtsp"
    }
  ]
}
```

#### `POST /cameras/register`
Register new camera stream from FROND node.

**Request Body:**
```json
{
  "node_id": "abc123...",
  "stream_url": "rtsp://10.13.0.5:8554/stream",
  "name": "Perimeter Camera"
}
```

**Response:**
```json
{
  "status": "registered"
}
```

#### `GET /cameras/{node_id}/stream`
Get camera stream info for playback.

**Response:**
```json
{
  "stream_url": "rtsp://10.13.0.5:8554/stream",
  "format": "rtsp"
}
```

**Formats:**
- `rtsp` - RTSP stream (use VLC or ffmpeg)
- `hls` - HLS stream (`.m3u8`)
- `http` - HTTP MJPEG or chunked

---

### P700: Network Events

#### `GET /events?limit=100`
Get recent network events.

**Query Parameters:**
- `limit` (int): Max events to return (default: 100)

**Response:**
```json
{
  "events": [
    {
      "type": "node_join",
      "timestamp": 1234567890.0,
      "data": {
        "node_id": "abc123...",
        "protocol": "reticulum"
      }
    },
    {
      "type": "message",
      "timestamp": 1234567895.0,
      "data": {
        "source": "!def45678",
        "protocol": "meshtastic"
      }
    }
  ]
}
```

**Event Types:**
- `node_join` - New node discovered
- `node_leave` - Node went offline
- `message` - Message received
- `announce` - Node announced
- `route_update` - Routing table changed
- `camera_registered` - New camera stream

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://myc3.local/ws');

ws.onopen = () => {
  console.log('Connected to MYC3LIUM bridge');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleUpdate(data);
};
```

### Message Format

All WebSocket messages follow this structure:

```json
{
  "type": "message_type",
  "page": "p300",
  "data": { ... }
}
```

**Pages:**
- `p200` - Topology updates
- `p300` - New messages
- `p400` - CoT events
- `p500` - Camera updates
- `p700` - Network events

### Event Types

#### Message Received
```json
{
  "type": "message",
  "page": "p300",
  "data": {
    "source": "abc123...",
    "content": "Hello!",
    "timestamp": 1234567890.0,
    "protocol": "lxmf"
  }
}
```

#### Node Discovered
```json
{
  "type": "node_discovered",
  "page": "p200",
  "data": {
    "id": "!abc12345",
    "long_name": "Node Alpha",
    "rssi": -85,
    "snr": 8.5,
    "last_seen": 1234567890.0
  }
}
```

#### CoT Event
```json
{
  "type": "cot_event",
  "page": "p400",
  "data": {
    "lat": 61.2181,
    "lon": -149.9003,
    "callsign": "Node Alpha"
  }
}
```

#### Camera Registered
```json
{
  "type": "camera_registered",
  "page": "p500",
  "data": {
    "node_id": "abc123...",
    "stream_url": "rtsp://10.13.0.5:8554/stream"
  }
}
```

---

## Protocol-Specific Details

### Reticulum/LXMF

**Identity Format:** 32-byte hex hash (64 characters)
```
abc123def456...
```

**Encryption:** All LXMF messages are end-to-end encrypted

**Store & Forward:** Messages stored for offline nodes, delivered when online

### Meshtastic

**Node ID Format:** `!` + 8 hex characters
```
!abc12345
```

**Broadcast:** Use `^all` as destination

**Radio Config:** Configured separately via Meshtastic app/CLI

**Limitations:** Text messages only (no binary data)

### ATAK/CoT

**UID Format:** Unique identifier (alphanumeric + hyphens)
```
MYC3LIUM-node-01
```

**Coordinate System:** WGS84 decimal degrees

**Required Fields:**
- `lat`, `lon` - Position
- `type` - CoT type code
- `uid` - Unique ID

**Optional Fields:**
- `hae` - Height above ellipsoid (meters)
- `ce` - Circular error (meters)
- `le` - Linear error (meters)
- `callsign` - Display name
- `remarks` - Notes

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error description"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Not found
- `500` - Internal server error

**Example:**
```json
{
  "detail": "Destination not found"
}
```

---

## Rate Limits

**No hard limits currently**, but best practices:

- Messages: Max 10/second per destination
- Announces: Max 1/5 minutes
- WebSocket: Max 100 messages/second

Excessive traffic may cause:
- Packet loss on LoRa
- Mesh congestion
- Memory overflow

---

## Integration Examples

### Send LXMF Message (Python)

```python
import requests

API_URL = "http://myc3.local"

response = requests.post(f"{API_URL}/message/send", json={
    "destination": "abc123...",
    "content": "Hello from Python!",
    "protocol": "lxmf"
})

print(response.json())
```

### Send Meshtastic Broadcast (cURL)

```bash
curl -X POST http://myc3.local/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "^all",
    "content": "Emergency: Shelter in place",
    "protocol": "meshtastic"
  }'
```

### Send Position to ATAK (JavaScript)

```javascript
fetch('http://myc3.local/atak/position', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lat: 61.2181,
    lon: -149.9003,
    callsign: 'Mobile-1'
  })
})
.then(r => r.json())
.then(data => console.log('Position sent:', data));
```

### Register Camera Stream (Python)

```python
import requests

requests.post(f"{API_URL}/cameras/register", json={
    "node_id": "abc123...",
    "stream_url": "rtsp://192.168.1.100:8554/cam1",
    "name": "Driveway Camera"
})
```

### Listen to Real-Time Updates (JavaScript)

```javascript
const ws = new WebSocket('ws://myc3.local/ws');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.page === 'p300' && msg.type === 'message') {
    console.log('New message:', msg.data.content);
    addMessageToUI(msg.data);
  }
  
  if (msg.page === 'p200' && msg.type === 'node_discovered') {
    console.log('New node:', msg.data.id);
    updateTopologyMap(msg.data);
  }
  
  if (msg.page === 'p400' && msg.type === 'cot_event') {
    console.log('Position update:', msg.data);
    updateTacticalMap(msg.data);
  }
};
```

---

## Advanced Usage

### Protocol Translation

The bridge automatically translates between protocols:

**Meshtastic → LXMF:**
- Incoming Meshtastic text messages are converted to LXMF format
- Broadcast to Reticulum nodes
- Available in unified message history

**Position → CoT:**
- Meshtastic position updates converted to CoT XML
- Viewable in ATAK-compatible applications
- Integrated with P400 tactical map

### Multi-Hop Routing

Reticulum automatically handles routing:
- Selects best available path (LoRa, HaLow, BATMAN)
- Falls back to alternative routes
- Store-and-forward for offline nodes

### Camera Stream Transcoding

For RTSP streams, transcode to HLS for web playback:

```bash
ffmpeg -i rtsp://camera-url \
  -c:v libx264 -preset ultrafast \
  -f hls -hls_time 2 -hls_list_size 3 \
  /var/www/myc3lium/streams/camera.m3u8
```

Then register as HLS:
```json
{
  "stream_url": "http://node-ip/streams/camera.m3u8",
  "format": "hls"
}
```

---

## OpenAPI/Swagger Docs

Interactive API documentation available at:

```
http://myc3.local/docs
```

Try endpoints directly in your browser!

---

## Troubleshooting

### "Reticulum not initialized"
- Check Reticulum service: `systemctl status reticulum`
- View logs: `journalctl -u reticulum -n 50`

### "Meshtastic disabled"
- Install package: `pip3 install meshtastic`
- Check device: `ls /dev/ttyUSB*`
- Configure device path in `http://myc3.local/p/600` (Radio section)

### WebSocket disconnects
- Check backend service: `systemctl status myc3lium`
- Monitor logs: `tail -f /opt/myc3lium/logs/bridge.log`

### Messages not sending
- Verify destination is reachable: `rnprobe <hash>`
- Check protocol compatibility
- Review message format

---

## Version History

**v0.4.0** (2026-03-28)
- TOML configuration API (`/api/config`)
- Meshtastic bridge into unified mesh store
- Zod WebSocket validation
- API key auth on protected endpoints

**v0.3.0** (2026-03-28)
- Multi-protocol support (Reticulum, Meshtastic, ATAK)
- WebSocket hardening, device metrics, connection limits
- Camera stream management
- Page-specific routing (P200, P300, P400, P500, P700)

---

🍄 **Happy meshing with MYC3LIUM!**
