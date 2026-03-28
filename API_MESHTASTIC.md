# Meshtastic API Reference

Quick reference for Meshtastic endpoints in the myc3lium backend.

## Base URL

```
http://localhost:8000/api/meshtastic
```

## Endpoints

### GET /status

Get current Meshtastic connection status and node info.

**Response:**
```json
{
  "connected": true,
  "device": "/dev/ttyUSB1",
  "node_id": "!a1b2c3d4",
  "short_name": "NODE1",
  "long_name": "Node One",
  "battery_level": 95,
  "voltage": 4.12,
  "channel_utilization": 2.3,
  "air_util_tx": 0.5,
  "nodes_count": 8
}
```

**Fields:**
- `connected` (bool) - Whether device is connected
- `device` (string) - Serial device path
- `node_id` (string) - Node ID in !12345678 format
- `short_name` (string) - Short name (4 chars)
- `long_name` (string) - Full node name
- `battery_level` (int) - Battery percentage (0-100)
- `voltage` (float) - Battery voltage
- `channel_utilization` (float) - Channel usage percentage
- `air_util_tx` (float) - Air time utilization
- `nodes_count` (int) - Number of known nodes

**Example:**
```bash
curl http://localhost:8000/api/meshtastic/status | jq
```

---

### GET /nodes

List all known mesh nodes.

**Response:**
```json
[
  {
    "node_id": "!a1b2c3d4",
    "short_name": "NODE1",
    "long_name": "Node One",
    "last_heard": 1711330000.123,
    "snr": 9.5,
    "position": {
      "lat": 37.7749,
      "lon": -122.4194,
      "alt": 50
    }
  }
]
```

**Fields:**
- `node_id` (string) - Node ID in !12345678 format
- `short_name` (string) - Short name
- `long_name` (string) - Full node name
- `last_heard` (float) - Unix timestamp of last contact
- `snr` (float|null) - Signal-to-noise ratio
- `position` (object|null) - GPS coordinates

**Example:**
```bash
curl http://localhost:8000/api/meshtastic/nodes | jq
```

---

### GET /messages

Get recent messages with optional filters.

**Query Parameters:**
- `limit` (int) - Max messages to return (default: 100)
- `sender` (string) - Filter by sender node ID
- `channel` (int) - Filter by channel index

**Response:**
```json
[
  {
    "sender": "!a1b2c3d4",
    "text": "Hello mesh!",
    "timestamp": 1711330000.123,
    "channel": 0,
    "snr": 9.5,
    "rssi": -85,
    "hop_limit": 3
  }
]
```

**Fields:**
- `sender` (string) - Sender node ID
- `text` (string) - Message content
- `timestamp` (float) - Unix timestamp
- `channel` (int) - Channel index
- `snr` (float|null) - Signal-to-noise ratio
- `rssi` (int|null) - Received signal strength
- `hop_limit` (int|null) - Remaining hops

**Examples:**
```bash
# Get last 10 messages
curl "http://localhost:8000/api/meshtastic/messages?limit=10" | jq

# Get messages from specific node
curl "http://localhost:8000/api/meshtastic/messages?sender=!a1b2c3d4" | jq

# Get messages on channel 0
curl "http://localhost:8000/api/meshtastic/messages?channel=0" | jq

# Combine filters
curl "http://localhost:8000/api/meshtastic/messages?channel=0&limit=5" | jq
```

---

### POST /send

Send a text message to the mesh.

**Request Body:**
```json
{
  "text": "Hello from API!",
  "channel": 0,
  "destination": "!a1b2c3d4"
}
```

**Fields:**
- `text` (string, required) - Message content
- `channel` (int, optional) - Channel index (default: 0)
- `destination` (string, optional) - Target node ID (broadcast if omitted)

**Response:**
```json
{
  "status": "sent",
  "text": "Hello from API!",
  "channel": 0,
  "destination": "!a1b2c3d4"
}
```

**Examples:**
```bash
# Broadcast message
curl -X POST http://localhost:8000/api/meshtastic/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello mesh!"}'

# Send to specific node
curl -X POST http://localhost:8000/api/meshtastic/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Direct message", "destination": "!a1b2c3d4"}'

# Send on different channel
curl -X POST http://localhost:8000/api/meshtastic/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Channel 1 message", "channel": 1}'
```

---

### WS /ws

WebSocket endpoint for real-time updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/meshtastic');

ws.onopen = () => {
  console.log('Connected to Meshtastic stream');
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.type, msg.data);
};
```

**Message Types:**

#### status
Initial connection status:
```json
{
  "type": "status",
  "data": {
    "connected": true,
    "node_id": "!a1b2c3d4",
    "short_name": "NODE1",
    "nodes_count": 8
  }
}
```

#### meshtastic_message
New message received:
```json
{
  "type": "meshtastic_message",
  "data": {
    "sender": "!a1b2c3d4",
    "text": "Hello!",
    "timestamp": 1711330000.123,
    "channel": 0,
    "snr": 9.5,
    "rssi": -85
  }
}
```

#### pong
Keepalive response:
```json
{
  "type": "pong",
  "data": "ping"
}
```

**Keepalive:**
```javascript
// Send ping every 30 seconds
setInterval(() => {
  ws.send("ping");
}, 30000);
```

---

## Error Responses

### 503 Service Unavailable
Service not initialized or not connected:
```json
{
  "detail": "Meshtastic service not connected"
}
```

### 500 Internal Server Error
Failed to send message:
```json
{
  "detail": "Failed to send message: <error details>"
}
```

---

## Integration Examples

### Python

```python
import requests

# Get status
resp = requests.get("http://localhost:8000/api/meshtastic/status")
status = resp.json()
print(f"Connected: {status['connected']}, Nodes: {status['nodes_count']}")

# Send message
requests.post(
    "http://localhost:8000/api/meshtastic/send",
    json={"text": "Hello from Python!"}
)

# Get messages
resp = requests.get("http://localhost:8000/api/meshtastic/messages?limit=10")
messages = resp.json()
for msg in messages:
    print(f"[{msg['sender']}] {msg['text']}")
```

### JavaScript (Fetch)

```javascript
// Get status
const status = await fetch('http://localhost:8000/api/meshtastic/status')
  .then(r => r.json());
console.log(`Connected: ${status.connected}, Nodes: ${status.nodes_count}`);

// Send message
await fetch('http://localhost:8000/api/meshtastic/send', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'Hello from JS!' })
});

// Get messages
const messages = await fetch('http://localhost:8000/api/meshtastic/messages?limit=10')
  .then(r => r.json());
messages.forEach(msg => {
  console.log(`[${msg.sender}] ${msg.text}`);
});
```

### cURL

```bash
# Get status
curl -s http://localhost:8000/api/meshtastic/status | jq

# Get nodes
curl -s http://localhost:8000/api/meshtastic/nodes | jq

# Get messages (last 5)
curl -s "http://localhost:8000/api/meshtastic/messages?limit=5" | jq

# Send message
curl -X POST http://localhost:8000/api/meshtastic/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello mesh!"}' | jq
```

---

## Rate Limits

No rate limits currently enforced. However, Meshtastic itself has built-in air time limits:

- **Fair Access Policy:** ~10% air time per node
- **Duty Cycle:** Regional regulations (1-10% depending on frequency)
- **Retry Delays:** Automatic backoff on congestion

Recommended: Limit sends to ~1 message per 10 seconds for broadcast, more for direct messages.

---

## WebSocket Best Practices

1. **Reconnect on disconnect:** Network drops are common
2. **Keepalive:** Send ping every 30-60 seconds
3. **Buffer messages:** Handle bursts during reconnection
4. **Parse errors:** Not all messages are JSON (connection close, etc.)

Example with reconnect:
```javascript
let ws;

function connect() {
  ws = new WebSocket('ws://localhost:8000/ws/meshtastic');
  
  ws.onopen = () => console.log('Connected');
  ws.onclose = () => {
    console.log('Disconnected, reconnecting in 5s...');
    setTimeout(connect, 5000);
  };
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    handleMessage(msg);
  };
}

connect();
```

---

**Version:** 0.2.0  
**Base Path:** `/api/meshtastic`  
**Documentation:** See PHASE2_MESHTASTIC_COMPLETE.md
