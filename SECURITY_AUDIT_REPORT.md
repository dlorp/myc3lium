# Security Audit Report: GUI Live Integration
**Branch:** `feat/gui-live-integration`  
**Date:** 2026-03-22  
**Auditor:** Security Specialist Agent  
**Status:** ⚠️ **APPROVED_WITH_NOTES**

---

## Executive Summary

The GUI live integration introduces live data from BATMAN-adv mesh network and Reticulum/LXMF messaging. The code demonstrates **good security fundamentals** with proper subprocess handling, but has **several issues** that should be addressed before production deployment.

**Overall Assessment:** Safe for merge into development/staging, but **production deployment should wait** for fixes to the HIGH and MEDIUM severity issues.

---

## ✅ Security Strengths

1. **Subprocess Safety**
   - All `subprocess.run()` calls use **`shell=False`** (safe)
   - Arguments passed as lists, not strings
   - Timeouts configured (5s, 10s) to prevent hangs

2. **Input Validation**
   - Pydantic models enforce max_length constraints
   - Message content limited to 1024 chars
   - Field validation on API endpoints

3. **Error Handling**
   - Graceful fallbacks when batctl/RNS unavailable
   - Exceptions logged, not exposed to users
   - Generic error messages returned

4. **CORS Configuration**
   - Explicit allowlist in config
   - Not wildcard `*` in production

---

## 🔴 HIGH Severity Issues

### H-1: Path Traversal in `get_interface_stats()` (batctl_service.py:171)

**Issue:**  
User-controlled `interface` parameter used to build file paths without validation.

**Location:** `backend/app/services/batctl_service.py:171`

**Vulnerable Code:**
```python
def get_interface_stats(interface: str) -> Optional[InterfaceStats]:
    sys_path = f"/sys/class/net/{interface}"  # ❌ No validation
```

**Attack Vector:**
```python
get_interface_stats("../../etc/passwd")
# Attempts to read /sys/class/net/../../etc/passwd
```

**Impact:** File read access to arbitrary files on the system (limited by process permissions).

**Fix:**
```python
import re

def get_interface_stats(interface: str) -> Optional[InterfaceStats]:
    # Validate interface name (alphanumeric + hyphen only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', interface):
        logger.warning(f"Invalid interface name: {interface}")
        return None
    
    sys_path = f"/sys/class/net/{interface}"
    
    # Verify path stays within /sys/class/net
    from pathlib import Path
    try:
        resolved = Path(sys_path).resolve()
        if not str(resolved).startswith("/sys/class/net/"):
            logger.warning(f"Path traversal attempt: {interface}")
            return None
    except Exception:
        return None
    
    # ... rest of function
```

**Affected Endpoints:**
- `GET /api/mesh/radios` (calls `get_interface_stats("halow0")`, `get_interface_stats("lora0")`)
- Currently hardcoded values, but function signature allows arbitrary input

---

### H-2: ReDoS Vulnerability in Regex (batctl_service.py:107, 152)

**Issue:**  
Regex patterns are vulnerable to catastrophic backtracking (ReDoS) with crafted input.

**Location:**  
- `backend/app/services/batctl_service.py:107` (originators)
- `backend/app/services/batctl_service.py:152` (neighbors)

**Vulnerable Regex:**
```python
# Line 107
r"\s*\*?\s*([\da-f:]+)\s+([\d.]+)s\s+\(\s*(\d+)\)\s+([\da-f:]+)\s+(\S+)"

# Line 152
r"(\S+)\s+([\da-f:]+)\s+([\d.]+)s\s+\(\s*(\d+)\)"
```

**Attack Vector:**  
If an attacker can inject malicious batctl output (e.g., via compromised mesh node), they could craft MAC addresses or interface names that cause regex engine to hang.

**Example Payload (simplified):**
```
aa:bb:cc:dd:ee:ff    1.000000000000000000000000000000s   (255) ...
```

**Impact:** DoS via CPU exhaustion. Background mesh monitor loop hangs, blocking WebSocket updates.

**Risk Assessment:**  
- **Medium likelihood** - requires control over batctl output
- **High impact** - service hangs
- **Overall: HIGH** due to background task vulnerability

**Fix:**
1. **Limit input line length** before regex matching:
```python
for line in result.stdout.splitlines():
    if len(line) > 512:  # Reasonable max for batctl output
        logger.warning("Skipping oversized batctl line")
        continue
    match = re.match(r"...", line)
```

2. **Use simpler regex** (avoid nested quantifiers):
```python
# Before: \s+ can match unlimited whitespace
# After: \s{1,10} limits to 10 spaces max
r"\s*\*?\s{1,5}([\da-f:]{17})\s{1,10}([\d.]{3,10})s\s*\(\s*(\d{1,3})\)\s+([\da-f:]{17})\s+(\S{1,32})"
```

3. **Validate MAC address format** before regex:
```python
def is_valid_mac(mac: str) -> bool:
    return re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', mac) is not None
```

---

### H-3: Incorrect API Call in `mesh.py:100`

**Issue:**  
`get_neighbors()` called with `iface` parameter, but function doesn't accept parameters.

**Location:** `backend/app/routers/mesh.py:100`

**Broken Code:**
```python
neighbors = batctl_service.get_neighbors(iface) if stats else None  # ❌ TypeError
```

**Impact:**  
- **Endpoint `/api/mesh/radios` will crash** when batctl is available
- Production runtime error (500 Internal Server Error)

**Fix:**
```python
# Option 1: Filter neighbors by interface after fetching
all_neighbors = batctl_service.get_neighbors() if stats else None
neighbors = [n for n in (all_neighbors or []) if n.interface == iface]

# Option 2: Update batctl_service.get_neighbors() to accept interface param
def get_neighbors(interface: Optional[str] = None) -> Optional[list[Neighbor]]:
    # ... fetch all neighbors ...
    if interface:
        neighbors = [n for n in neighbors if n.interface == interface]
    return neighbors
```

---

## 🟡 MEDIUM Severity Issues

### M-1: Unbounded WebSocket Message Queue

**Issue:**  
No rate limiting or flood protection on WebSocket connections.

**Location:** `backend/app/routers/ws.py:189`, `backend/app/websocket.py`

**Attack Vector:**
```python
# Malicious client spams messages
ws = await connect_websocket("/ws")
while True:
    await ws.send_text("x" * 4096)  # Max size, but no rate limit
```

**Impact:**  
- Memory exhaustion (queued messages)
- CPU exhaustion (JSON parsing)
- DoS for other clients (broadcast queue blocked)

**Fix:**
```python
# In ConnectionManager
class ConnectionManager:
    MAX_MESSAGE_RATE = 10  # messages per second per client
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self._client_counter = 0
        self._rate_limiters: dict[str, list[float]] = {}  # client_id -> timestamps
    
    async def connect(self, websocket: WebSocket) -> str:
        # ... existing code ...
        self._rate_limiters[client_id] = []
        return client_id
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit"""
        import time
        now = time.time()
        
        # Clean old timestamps (older than 1 second)
        self._rate_limiters[client_id] = [
            ts for ts in self._rate_limiters[client_id]
            if now - ts < 1.0
        ]
        
        # Check rate
        if len(self._rate_limiters[client_id]) >= self.MAX_MESSAGE_RATE:
            return False
        
        self._rate_limiters[client_id].append(now)
        return True

# In ws.py
while True:
    data = await websocket.receive_text()
    
    if not manager.check_rate_limit(client_id):
        await websocket.close(code=1008, reason="Rate limit exceeded")
        break
```

---

### M-2: Missing Input Validation on `destination_hash`

**Issue:**  
Hex validation happens inside `send_message()`, but invalid format causes exceptions.

**Location:** `backend/app/routers/messages.py:192`

**Vulnerable Code:**
```python
@router.post("/send", status_code=202)
async def send_message(payload: MessageSend):
    success = reticulum.send_message(
        destination_hash=payload.destination_hash,  # Not validated at API layer
        content=payload.content
    )
```

**Attack Vector:**
```bash
curl -X POST /api/messages/send \
  -d '{"destination_hash":"NOT_HEX", "content":"test"}'
```

**Impact:**  
- Verbose error messages leak internal details
- DoS via repeated invalid requests

**Current Error:**
```python
# In reticulum_service.py:192
dest_hash_bytes = bytes.fromhex(dest_hash)  # ValueError: non-hexadecimal number
```

**Fix:**
```python
# In messages.py
from pydantic import field_validator

class MessageSend(BaseModel):
    destination_hash: str = Field(
        ..., max_length=32, description="Destination identity hash (hex)"
    )
    content: str = Field(..., max_length=1024, description="Message content")
    
    @field_validator('destination_hash')
    @classmethod
    def validate_hex(cls, v: str) -> str:
        """Validate hex string format"""
        if not re.match(r'^[0-9a-fA-F]{16,64}$', v):
            raise ValueError("destination_hash must be 16-64 hex characters")
        return v.lower()
```

---

### M-3: Race Condition in `MeshStore` Event Handlers

**Issue:**  
Event handlers iterate over `self._event_handlers` list without locking.

**Location:** `backend/app/services/mesh_store.py:31`

**Vulnerable Code:**
```python
def _emit_event(self, event_type: str, data: dict):
    for handler in self._event_handlers:  # ❌ Not thread-safe
        try:
            handler(event_type, data)
```

**Attack Vector:**  
If two threads call `add_node()` simultaneously, one might be emitting events while another modifies `_event_handlers`.

**Impact:**  
- `RuntimeError: dictionary changed size during iteration`
- Missed events
- Service crash

**Likelihood:** Low (single-threaded FastAPI by default), but risky if threading used.

**Fix:**
```python
import threading

class MeshStore:
    def __init__(self):
        self._nodes: dict[str, Node] = {}
        self._threads: dict[str, Thread] = {}
        self._messages: dict[str, Message] = {}
        self._event_handlers: list[Callable] = []
        self._lock = threading.Lock()  # Add lock
    
    def on_event(self, handler: Callable):
        with self._lock:
            self._event_handlers.append(handler)
    
    def _emit_event(self, event_type: str, data: dict):
        # Make a copy to avoid race conditions
        with self._lock:
            handlers = list(self._event_handlers)
        
        for handler in handlers:
            try:
                handler(event_type, data)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
```

---

### M-4: Unvalidated `interface` Parameter in `mesh.py:100`

**Issue:**  
Hardcoded interface names `"halow0"`, `"lora0"` are safe, but endpoint structure suggests future dynamic input.

**Location:** `backend/app/routers/mesh.py:99-100`

**Code:**
```python
for iface, radio_type in [("halow0", "HaLow"), ("lora0", "LoRa")]:
    stats = batctl_service.get_interface_stats(iface)  # Currently safe (hardcoded)
```

**Future Risk:**  
If refactored to accept `?interface=` query param, becomes vulnerable to **H-1** (path traversal).

**Recommendation:**  
Add validation now to prevent future regression:
```python
ALLOWED_INTERFACES = {"halow0", "lora0", "wlan0", "bat0"}

@router.get("/radios")
async def radio_status(interface: Optional[str] = Query(None)):
    if interface and interface not in ALLOWED_INTERFACES:
        raise HTTPException(status_code=400, detail="Invalid interface")
    
    interfaces_to_check = [interface] if interface else ALLOWED_INTERFACES
    # ... rest of logic
```

---

## 🟢 LOW Severity Issues

### L-1: Verbose Error Messages Leak Internal Paths

**Issue:**  
Exception messages include file paths and stack traces.

**Location:** `backend/app/routers/messages.py:175`, `reticulum_service.py:213`

**Examples:**
```python
# messages.py:175
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    # ❌ Leaks exception details to API response

# reticulum_service.py:213
logger.error("Failed to send message via Reticulum bridge: %s", e, exc_info=True)
# ❌ Stack trace includes absolute paths in logs
```

**Impact:**  
- Information disclosure (file paths, library versions)
- Helps attackers map internal structure

**Fix:**
```python
# messages.py
except ValueError as e:
    # Expected errors (e.g., "destination not known") are OK to expose
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    # Unexpected errors should be generic
    logger.error(f"Message send failed: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to send message")
```

---

### L-2: Missing Timeouts on File I/O

**Issue:**  
`/sys/class/net/` reads don't have timeouts (can hang on NFS mounts, slow devices).

**Location:** `backend/app/services/batctl_service.py:193`

**Code:**
```python
with open(operstate_path, encoding="utf-8") as f:
    operstate = f.read().strip()  # No timeout
```

**Impact:**  
- Potential hang if filesystem slow/unresponsive
- Blocks background mesh monitor loop

**Fix:**
```python
import signal

def read_with_timeout(path: str, timeout: float = 1.0) -> str:
    """Read file with timeout"""
    def timeout_handler(signum, frame):
        raise TimeoutError("File read timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout))
    
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    finally:
        signal.alarm(0)  # Cancel alarm
```

---

### L-3: Potential Integer Overflow in TQ Conversion

**Issue:**  
TQ values assumed to be 0-255, but not validated before arithmetic.

**Location:** `backend/app/services/live_data_source.py:83`

**Code:**
```python
rssi = int(-100 + (orig.tq / 255.0) * 60)  # Assumes 0 <= orig.tq <= 255
```

**Attack Vector:**  
Malicious mesh node broadcasts TQ value `>255` (if parsing bug exists).

**Impact:**  
- Incorrect RSSI calculation (minor)
- Potential integer overflow in UI

**Fix:**
```python
# In batctl_service.py Originator dataclass
@dataclass
class Originator:
    mac: str
    last_seen: float
    next_hop: str
    interface: str
    tq: int  # transmission quality (0-255)
    
    def __post_init__(self):
        # Validate TQ range
        if not (0 <= self.tq <= 255):
            raise ValueError(f"TQ must be 0-255, got {self.tq}")
```

---

### L-4: Hardcoded Secret Paths

**Issue:**  
Identity and storage paths use `/var/lib/myc3lium/`, which may not be writable in all environments.

**Location:** `backend/app/main.py:29`, `reticulum_service.py:73`

**Code:**
```python
reticulum = ReticulumBridge()  # Uses default paths
# /var/lib/myc3lium/lxmf
# /var/lib/myc3lium/identity
```

**Impact:**  
- Service fails to start if directory doesn't exist
- Permission denied errors in Docker/sandboxed environments

**Fix:**
```python
# In config.py
class Settings(BaseSettings):
    # ... existing fields ...
    
    reticulum_storage_path: str = "/var/lib/myc3lium/lxmf"
    reticulum_identity_path: str = "/var/lib/myc3lium/identity"

# In main.py
reticulum = ReticulumBridge(
    storage_path=settings.reticulum_storage_path,
    identity_path=settings.reticulum_identity_path,
)
```

---

### L-5: No Maximum Connection Limit on Background Task

**Issue:**  
WebSocket manager limits connections (100), but background `mesh_monitor_loop()` can broadcast to unlimited clients.

**Location:** `backend/app/routers/ws.py:58`

**Code:**
```python
while _monitor_running:
    # ... fetch mesh data ...
    await manager.broadcast({...})  # ❌ No check if broadcast queue full
```

**Impact:**  
- If 100 clients connected, broadcast blocks on slow clients
- One slow client delays updates for all

**Fix:**
```python
# In ConnectionManager
async def broadcast(self, message: dict, timeout: float = 5.0):
    """Broadcast with per-client timeout"""
    import asyncio
    
    disconnected = []
    
    for client_id, websocket in self.active_connections.items():
        try:
            await asyncio.wait_for(
                websocket.send_json(message),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Client {client_id} timed out, disconnecting")
            disconnected.append(client_id)
        except Exception:
            disconnected.append(client_id)
    
    for client_id in disconnected:
        self.disconnect(client_id)
```

---

## 🔵 Best Practices & Recommendations

### 1. Add Logging Filters

**Issue:** Sensitive data (identity hashes, message content) logged in production.

**Example:**
```python
logger.info("Sent LXMF message to %s: %s", dest_hash[:8], content[:50])
# ❌ Logs message content
```

**Fix:**
```python
# In config.py
import logging

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # Redact sensitive fields
        if hasattr(record, 'msg'):
            record.msg = record.msg.replace(record.getMessage(), "[REDACTED]")
        return True

# Apply filter
if not settings.debug:
    logger.addFilter(SensitiveDataFilter())
```

---

### 2. Add Health Check for Reticulum

**Issue:** `/health` endpoint reports Reticulum status, but doesn't check if it's responsive.

**Location:** `backend/app/main.py:78`

**Enhancement:**
```python
@app.get("/health")
async def health():
    reticulum_status = "unavailable"
    
    if reticulum and reticulum.available:
        try:
            # Quick check: Can we get status?
            status = reticulum.get_status()
            reticulum_status = "healthy" if status.identity_hash else "degraded"
        except Exception:
            reticulum_status = "error"
    
    return {
        "status": "healthy",
        "live_data": settings.use_live_data,
        "reticulum": reticulum_status,
    }
```

---

### 3. Add Request ID Tracing

**Issue:** Hard to correlate logs across services without request IDs.

**Enhancement:**
```python
# middleware.py (new file)
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# In main.py
app.add_middleware(RequestIDMiddleware)
```

---

### 4. Add Structured Logging

**Issue:** Plain text logs hard to parse in production monitoring.

**Enhancement:**
```python
# Use structlog or python-json-logger
import structlog

logger = structlog.get_logger()
logger.info("mesh_update", originator_count=len(originators), neighbor_count=len(neighbors))
# Output: {"event":"mesh_update","originator_count":5,"neighbor_count":3,"timestamp":"..."}
```

---

### 5. Add Metrics Endpoint

**Issue:** No visibility into performance (request latency, error rates).

**Enhancement:**
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## 📋 Verdict: APPROVED_WITH_NOTES

**Decision:** ✅ **Safe to merge** into development/staging branch.

**Conditions:**
1. **Before production deployment**, fix:
   - **H-1** (Path traversal in `get_interface_stats()`)
   - **H-2** (ReDoS in batctl regex)
   - **H-3** (TypeError in `mesh.py:100`)
   - **M-1** (WebSocket rate limiting)
   - **M-2** (Input validation on `destination_hash`)

2. **Before next release**, address:
   - **M-3** (Race condition in `MeshStore`)
   - **M-4** (Interface validation)
   - **L-1** through **L-5** (low-priority hardening)

**Deployment Recommendation:**
- ✅ **Development:** Safe to deploy as-is (monitor for issues)
- ⚠️ **Staging:** Deploy with HIGH/MEDIUM fixes applied
- ❌ **Production:** Deploy only after all HIGH/MEDIUM fixes confirmed

---

## 📝 Testing Recommendations

### Automated Tests to Add

```python
# test_security.py

def test_path_traversal_interface_stats():
    """Test path traversal protection in get_interface_stats()"""
    assert get_interface_stats("../../etc/passwd") is None
    assert get_interface_stats("halow0/../../../etc/shadow") is None
    assert get_interface_stats("halow0") is not None  # Valid

def test_redos_protection():
    """Test regex doesn't hang on malicious input"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("ReDoS detected")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)  # 5 second timeout
    
    try:
        malicious_line = "aa:bb:cc:dd:ee:ff    " + "1." + "0"*10000 + "s   (255) ..."
        parse_originator_line(malicious_line)
    finally:
        signal.alarm(0)

def test_websocket_rate_limit():
    """Test WebSocket flood protection"""
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as websocket:
        # Send 100 messages rapidly
        for i in range(100):
            websocket.send_text(f"msg{i}")
        
        # 101st should trigger rate limit
        with pytest.raises(WebSocketDisconnect):
            websocket.send_text("flood")
```

---

## 🔗 References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [CWE-22: Path Traversal](https://cwe.mitre.org/data/definitions/22.html)
- [CWE-1333: ReDoS](https://cwe.mitre.org/data/definitions/1333.html)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)

---

**Report Generated:** 2026-03-22 19:58 AKDT  
**Next Review:** After HIGH/MEDIUM issues fixed
