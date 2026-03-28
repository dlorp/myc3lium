# Phase 3: WebSocket Real-Time Updates — Implementation Plan

**Issue:** #47  
**PR:** #48 (`fix: Use PyPubSub for Meshtastic callbacks`)  
**Date:** 2026-03-28  
**Status:** Code complete, pending deployment & validation

---

## Table of Contents

1. [Root Cause Analysis](#1-root-cause-analysis)
2. [Implementation (Completed)](#2-implementation-completed)
3. [Deployment Steps](#3-deployment-steps)
4. [Testing Plan](#4-testing-plan)
5. [Rollback Plan](#5-rollback-plan)
6. [Success Metrics](#6-success-metrics)
7. [Future Work (Phase 4+)](#7-future-work-phase-4)

---

## 1. Root Cause Analysis

### Problem Statement

WebSocket connections to `/ws/meshtastic` were established successfully, but **no events were ever broadcast** to connected clients. The dashboard received zero real-time updates — no messages, no node info, no connection events.

### Root Cause

The Meshtastic Python library uses **PyPubSub** for its internal event system, **not instance attribute callbacks**. The original code assigned callbacks as instance attributes on the `SerialInterface` object:

```python
# ❌ BROKEN — These attributes are never checked by meshtastic
interface.onReceive = self._on_receive
interface.onConnection = self._on_connection
interface.onNodeInfoUpdated = self._on_node_info_updated
```

The meshtastic library publishes events to PyPubSub topics like `meshtastic.receive`, `meshtastic.connection.established`, and `meshtastic.node.updated`. Assigning to instance attributes had no effect — the callbacks were silently ignored.

### Three Bugs Identified and Fixed

#### Bug 1: Callback Registration (Critical)

Callbacks must be registered via `pub.subscribe()`, not instance attributes.

```python
# ✅ FIXED — Register via PyPubSub
from pubsub import pub

pub.subscribe(self._on_receive, "meshtastic.receive")
pub.subscribe(self._on_connection, "meshtastic.connection.established")
pub.subscribe(self._on_node_info_updated, "meshtastic.node.updated")
```

#### Bug 2: Callback Signatures (Critical)

PyPubSub passes arguments as **keyword arguments**, not positional. The original signatures used positional params, causing `TypeError` when PyPubSub tried to invoke them.

| Callback | Before (broken) | After (fixed) |
|----------|-----------------|---------------|
| `_on_receive` | `(self, packet, interface)` | `(self, packet, interface=None)` |
| `_on_connection` | `(self, interface, topic=None)` | `(self, interface=None, topic=None)` |
| `_on_node_info_updated` | `(self, interface, node_info)` | `(self, node=None, interface=None)` |

Note: PyPubSub sends `node` (not `node_info`) for the node update topic.

#### Bug 3: Missing WebSocket Broadcast in Node Updates (Moderate)

The `_on_node_info_updated` handler stored node data but **never called `_ws_callback()`** to notify WebSocket clients. Messages and connection events had this call, but node updates were silently swallowed.

```python
# ✅ FIXED — Added broadcast after node storage
if self._ws_callback:
    self._ws_callback(
        "meshtastic_node_updated",
        {
            "node_id": node_id,
            "short_name": short_name,
            "long_name": long_name,
            "last_heard": last_heard,
            "snr": snr,
            "position": position,
            "nodes_count": len(self._nodes),
        },
    )
```

---

## 2. Implementation (Completed)

### PR #48: `fix: Use PyPubSub for Meshtastic callbacks`

**Commit:** `090c0be`  
**Files changed:**

| File | Changes |
|------|---------|
| `backend/app/services/meshtastic_service.py` | +51 / -15 lines |
| `backend/requirements.txt` | +4 lines |

### Change Summary

1. **PyPubSub import** — Added conditional import with graceful fallback:
   ```python
   try:
       from pubsub import pub
   except ImportError:
       pub = None
   ```

2. **Callback registration** — Replaced instance attribute assignment with `pub.subscribe()` calls in `start()`.

3. **Signature fixes** — All three callbacks now accept keyword arguments with defaults, matching what PyPubSub provides.

4. **Node update broadcast** — Added `_ws_callback()` invocation in `_on_node_info_updated` to push node changes to WebSocket clients.

5. **Clean shutdown** — Added `pub.unsubscribe()` calls in `stop()` to prevent leaked subscriptions:
   ```python
   if pub:
       pub.unsubscribe(self._on_receive, "meshtastic.receive")
       pub.unsubscribe(self._on_connection, "meshtastic.connection.established")
       pub.unsubscribe(self._on_node_info_updated, "meshtastic.node.updated")
   ```

6. **Requirements update** — Added `pypubsub` to `backend/requirements.txt`.

### Architecture (Unchanged)

```
Meshtastic Radio (Heltec V3)
    │  USB Serial (/dev/ttyUSB1)
    ▼
SerialInterface (meshtastic lib)
    │  PyPubSub events
    ▼
MeshtasticService (singleton)
    │  _ws_callback()
    ▼
broadcast_to_websockets() → asyncio Queue
    │  Event processor task
    ▼
WebSocket pool → Connected clients
    │
    ▼
Dashboard (frontend)
```

---

## 3. Deployment Steps

### Prerequisites

- Heltec V3 connected to Pi via USB (`/dev/ttyUSB1`)
- Device in CLIENT mode with Meshtastic firmware
- SSH access to Pi: `ssh pi@myc3lium.local`
- Backend service (`myc3lium-backend`) running

### Step 1: Push & Pull

```bash
# On dev machine
cd ~/repos/myc3lium
git push origin main

# On Pi
ssh pi@myc3lium.local
cd ~/myc3lium
git pull origin main
```

### Step 2: Install Dependencies

```bash
# On Pi
cd ~/myc3lium
pip3 install -r backend/requirements.txt
```

Verify pypubsub is installed:

```bash
python3 -c "from pubsub import pub; print('PyPubSub OK')"
```

### Step 3: Restart Backend

```bash
# If using systemd
sudo systemctl restart myc3lium-backend

# Or manually
cd ~/myc3lium/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Verify Connection

```bash
# Check health endpoint
curl http://myc3lium.local:8000/health

# Expected:
# {"status":"healthy","live_data":true,"reticulum":false,"meshtastic":true}
```

### Step 5: Test WebSocket

```bash
# Quick WebSocket test (requires websocat or similar)
websocat ws://myc3lium.local:8000/api/meshtastic/ws

# Or with Python
python3 -c "
import asyncio, websockets

async def test():
    async with websockets.connect('ws://myc3lium.local:8000/api/meshtastic/ws') as ws:
        print('Connected! Waiting for events...')
        msg = await asyncio.wait_for(ws.recv(), timeout=30)
        print(f'Received: {msg}')

asyncio.run(test())
"
```

### Configuration

| Setting | Value | Location |
|---------|-------|----------|
| Serial device | `/dev/ttyUSB1` | `MeshtasticService.__init__` |
| Ring buffer size | 100 messages | `MeshtasticService.__init__` |
| CORS origins | `192.168.40.15:3000`, `192.168.40.19:3000`, `localhost:3000` | `backend/app/main.py` |
| API port | 8000 | uvicorn startup |

---

## 4. Testing Plan

### 4.1 Unit Tests — Callback Registration

Verify PyPubSub subscriptions are registered correctly.

```bash
cd ~/repos/myc3lium
python3 -m pytest tests/ -k "test_callback" -v
```

**Test cases:**

| Test | Description | Expected |
|------|-------------|----------|
| `test_pubsub_subscribe_called` | `start()` registers 3 pub.subscribe calls | 3 subscriptions active |
| `test_pubsub_unsubscribe_on_stop` | `stop()` removes all subscriptions | 0 subscriptions |
| `test_pubsub_fallback_no_pypubsub` | Service starts without pypubsub (graceful degradation) | Warning logged, no crash |
| `test_callback_keyword_args` | Callbacks accept keyword-only arguments | No TypeError |

### 4.2 Integration Tests — WebSocket Flow

End-to-end: packet received → WebSocket broadcast.

```bash
python3 -m pytest tests/ -k "test_websocket" -v
```

**Test cases:**

| Test | Description | Expected |
|------|-------------|----------|
| `test_ws_connect` | Client connects to `/api/meshtastic/ws` | 101 Switching Protocols |
| `test_ws_receive_message` | Simulate packet → verify WS broadcast | JSON with event=`meshtastic_message` |
| `test_ws_receive_node_update` | Simulate node info → verify WS broadcast | JSON with event=`meshtastic_node_updated` |
| `test_ws_multiple_clients` | 3 clients connected → all receive broadcast | All 3 get same event |
| `test_ws_disconnect_cleanup` | Client disconnects → pool shrinks | No stale connections |

### 4.3 Manual Tests — Walk-Around Test

**Setup:**
1. Backend running on Pi with Heltec V3 connected
2. Dashboard open in browser (`http://myc3lium.local:3000`)
3. Second Meshtastic node (handheld or another Heltec)

**Procedure:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open dashboard, check WebSocket indicator | Connected (green) |
| 2 | Send text message from second node | Message appears on dashboard within 1s |
| 3 | Walk second node to new location | Position updates on dashboard map |
| 4 | Move second node out of range | Node shows as stale after timeout |
| 5 | Return to range | Node reconnects, updates resume |
| 6 | Disconnect Heltec USB | Dashboard shows disconnected state |
| 7 | Reconnect USB, restart backend | WebSocket reconnects, data flows |

### 4.4 Performance Tests

**Multi-node load:**

```bash
# Simulate rapid node updates (use mock if hardware unavailable)
python3 -c "
from pubsub import pub
import time, json

for i in range(100):
    pub.sendMessage('meshtastic.receive', packet={
        'decoded': {
            'portnum': 'TEXT_MESSAGE_APP',
            'text': f'Load test message {i}'
        },
        'fromId': f'!node{i:04d}',
        'rxSnr': -5.0,
        'rxRssi': -90,
        'hopLimit': 3
    })
    time.sleep(0.01)  # 100 msgs in 1 second

print('Sent 100 messages')
"
```

**Metrics to capture:**

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Event latency (packet → WS) | < 100ms | Timestamp in packet vs WS receipt |
| Dashboard render latency | < 1s total | Visual observation + browser devtools |
| Memory (100 msgs in buffer) | < 50MB RSS | `ps aux | grep uvicorn` |
| Sustained 10 nodes updating | No dropped events | Count events sent vs received |
| WebSocket reconnect | < 5s | Kill and restart backend |

---

## 5. Rollback Plan

### If WebSocket Still Doesn't Work After Deploy

#### Immediate: Verify the Basics

```bash
# 1. Is PyPubSub installed?
python3 -c "from pubsub import pub; print(pub.getDefaultTopicMgr().getTopic('meshtastic.receive'))"

# 2. Is Meshtastic connected?
curl http://myc3lium.local:8000/api/meshtastic/status
# Check: "connected": true

# 3. Are callbacks registered? (check logs)
journalctl -u myc3lium-backend --since "5 min ago" | grep -i "pubsub\|callback\|subscribe"

# 4. Is the event processor running?
journalctl -u myc3lium-backend --since "5 min ago" | grep -i "event.processor"
```

#### Debug: Add Verbose Logging

```python
# Temporarily add to meshtastic_service.py start():
import logging
logging.getLogger("pubsub").setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
```

#### Fallback: Re-enable Polling

If real-time WebSocket can't be fixed quickly, the frontend already has a polling fallback:

```typescript
// frontend: re-enable 5s polling as temporary measure
useEffect(() => {
  const interval = setInterval(async () => {
    const res = await fetch('/api/meshtastic/messages?limit=10');
    const data = await res.json();
    setMessages(data);
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

This is a **temporary** measure. Polling at 5s intervals works but:
- Adds 0–5s latency to message display
- Increases API load (12 requests/min per client)
- Doesn't scale with multiple dashboard instances

#### Git Rollback

```bash
# Revert PR #48 if it causes regressions
git revert 090c0be
git push origin main

# On Pi
cd ~/myc3lium && git pull && sudo systemctl restart myc3lium-backend
```

---

## 6. Success Metrics

### Primary Criteria (Must Pass)

| Metric | Target | Status |
|--------|--------|--------|
| Packet → dashboard latency | < 1 second | ⬜ Pending deploy |
| Zero polling required | Remove 5s fallback entirely | ⬜ Pending validation |
| WebSocket stable under load | No dropped connections in 1hr test | ⬜ Pending test |
| Node position updates in real-time | Updates within 1s of movement | ⬜ Pending walk test |

### Secondary Criteria (Should Pass)

| Metric | Target | Status |
|--------|--------|--------|
| Multiple simultaneous clients | 3+ dashboards, all receive events | ⬜ Pending test |
| Clean reconnect after backend restart | Auto-reconnect within 5s | ⬜ Pending test |
| Memory stability | No growth over 1hr sustained use | ⬜ Pending test |
| Graceful degradation without radio | Service starts, reports unavailable | ✅ Verified |

### Definition of Done

Phase 3 is **complete** when:

1. ✅ PR #48 merged (PyPubSub callback fix)
2. ⬜ Deployed to Pi and backend running
3. ⬜ WebSocket receives live message events (manual test)
4. ⬜ WebSocket receives live node update events (walk test)
5. ⬜ Dashboard displays events within 1s (latency test)
6. ⬜ 5s polling fallback removed from frontend
7. ⬜ Stable for 1 hour continuous operation

---

## 7. Future Work (Phase 4+)

### Node Management & Pruning

- Expire stale nodes (no heartbeat in > 15 min)
- Track node online/offline transitions
- Node history and uptime stats
- Configurable TTL per node type

### Advanced Teletext Pages

| Page | Feature | Priority |
|------|---------|----------|
| P200 | Real-time intelligence feed (live with WebSocket) | High |
| P300 | Node detail view with signal graphs | Medium |
| P400 | Message log with search/filter | Medium |
| P500+ | Feature pages already in place | Low |

### Production Hardening

- **Authentication:** API key or JWT for WebSocket connections
- **Rate limiting:** Per-client event throttling
- **Connection limits:** Max WebSocket pool size (prevent DoS)
- **Health checks:** Watchdog for Meshtastic service reconnection
- **Monitoring:** Prometheus metrics for event throughput, latency, connection count
- **TLS:** WSS for encrypted WebSocket connections
- **Compression:** Per-message deflate for WebSocket frames

### Multi-Radio Support

- Support multiple Meshtastic devices simultaneously
- Channel-based routing (different radios on different frequencies)
- Failover: if primary radio disconnects, switch to secondary

---

## Troubleshooting Guide

### Common Issues

#### "PyPubSub not available" in logs

```bash
pip3 install pypubsub
# Verify:
python3 -c "from pubsub import pub; print('OK')"
```

#### WebSocket connects but no events

1. Check Meshtastic is connected: `curl /api/meshtastic/status`
2. Check logs for callback registration: `grep "Registered PyPubSub" logs`
3. Verify event processor is running: `grep "event_processor" logs`
4. Send a test message from another node and watch logs

#### "meshtastic.receive" topic not found

The meshtastic library may use different topic names in different versions. Check:

```python
python3 -c "
import meshtastic
print(f'Meshtastic version: {meshtastic.__version__}')
from pubsub import pub
print('Topics:', [t.getName() for t in pub.getDefaultTopicMgr().getAllTopics()])
"
```

#### Serial device not found

```bash
# Check USB devices
ls -la /dev/ttyUSB*
# If not present, check dmesg
dmesg | tail -20 | grep -i usb
# May need to replug or check USB cable
```

#### High memory usage

The ring buffer is capped at 100 messages. If memory grows, check for:
- WebSocket connection leaks (connections not cleaned up on disconnect)
- Node dict growing unbounded (add pruning — see Phase 4)

```bash
# Monitor memory
watch -n 5 'ps aux | grep uvicorn | grep -v grep'
```

---

*Document generated 2026-03-28. Updates should be made as deployment and testing proceed.*
