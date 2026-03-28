# Security Review: PR #46 - Meshtastic Live Mesh Integration

**Reviewer:** Security Specialist Agent  
**Date:** 2026-03-27  
**PR:** [#46](https://github.com/dlorp/myc3lium/pull/46)  
**Branch:** `feat/meshtastic-integration` → `main`

## Executive Summary

**VERDICT: ❌ ISSUES FOUND — 2 HIGH, 3 MEDIUM, 2 LOW**

PR #46 introduces Meshtastic live mesh integration with significant security gaps. **DO NOT MERGE** until critical issues are addressed.

---

## 🔴 HIGH Severity Issues

### 🔴 HIGH-1: Unrestricted CORS Configuration

**Location:** `backend/app/main.py:26-33`

**Issue:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False with allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Risk:**
- **Cross-Site Request Forgery (CSRF)** — Any website can make requests to the API
- **Data exfiltration** — Malicious sites can read Meshtastic node data, messages, and network topology
- **No origin validation** — Broadcast from any domain

**Impact:**
If the API is exposed on a public IP or accessible via port forwarding:
1. Attacker creates malicious webpage at `evil.com`
2. User visits `evil.com` while on the same network
3. JavaScript on `evil.com` reads `/api/meshtastic/messages` and exfiltrates private mesh communications
4. Can also read node locations via `/api/meshtastic/nodes` (GPS coordinates)

**Fix:**
```python
# Option 1: Development — Local only
cors_origins = ["http://localhost:5173", "http://localhost:3000"]

# Option 2: Production — Specific domains
cors_origins = [
    "https://myc3lium.yourdomain.com",
    "http://192.168.1.100:5173"  # Pi IP on local network
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],  # Only what's needed
    allow_headers=["content-type"],
)
```

**Validation:**
```bash
# Test CORS restriction
curl -H "Origin: https://evil.com" http://localhost:8000/api/meshtastic/status
# Should return 403 Forbidden or no CORS headers
```

---

### 🔴 HIGH-2: No Authentication on Sensitive Endpoints

**Locations:**
- `backend/app/routers/meshtastic.py:57-78` — `/status`
- `backend/app/routers/meshtastic.py:82-108` — `/nodes`
- `backend/app/routers/meshtastic.py:112-152` — `/messages`
- `backend/app/routers/meshtastic.py:156-185` — `/send` (WRITE operation!)
- `backend/app/routers/meshtastic.py:191-237` — `/ws` (WebSocket)

**Issue:**
All endpoints are completely unauthenticated. Anyone with network access can:
- ✅ Read all mesh messages
- ✅ Read node locations (GPS coordinates)
- ✅ **SEND messages to the mesh** (DoS, spam, impersonation)
- ✅ Subscribe to real-time WebSocket updates

**Risk:**
- **Message injection** — Attacker sends spam or malicious messages to mesh
- **Privacy violation** — Location tracking of mesh nodes
- **Network disruption** — Flood mesh with messages (limited by hardware, but still a vector)

**Example Attack:**
```python
# Spam the mesh network
import requests
for i in range(100):
    requests.post("http://192.168.1.100:8000/api/meshtastic/send", json={
        "text": f"SPAM MESSAGE {i}",
        "channel": 0
    })
# All mesh nodes receive 100 messages
```

**Fix:**
```python
# Add API key authentication
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Validate API key from environment"""
    expected_key = os.environ.get("MESHTASTIC_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.post("/send", dependencies=[Depends(verify_api_key)])
async def send_message(request: SendMessageRequest):
    # ... existing code
```

**Alternative: Network-Level Protection**
If API is only for local dashboard, firewall it:
```bash
# Only allow localhost + local network
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw deny 8000
```

---

## 🟡 MEDIUM Severity Issues

### 🟡 MEDIUM-1: Hardcoded Serial Device Path

**Location:** `backend/app/services/meshtastic_service.py:105`

**Issue:**
```python
def __init__(self, device_path: str = "/dev/ttyUSB1", max_messages: int = 100):
```

**Risk:**
- **Device enumeration attack** — Malicious library could scan `/dev/tty*` for devices
- **Portability** — Fails if device is at `/dev/ttyUSB0` or `/dev/serial/by-id/...`
- **No validation** — What if `device_path` contains `../../../etc/passwd`?

**Fix:**
```python
import os
from pathlib import Path

def __init__(self, device_path: str = "/dev/ttyUSB1", max_messages: int = 100):
    # ... existing code
    
    # Validate device_path is a real device
    resolved = Path(device_path).resolve()
    if not resolved.exists():
        raise ValueError(f"Device not found: {device_path}")
    if not str(resolved).startswith("/dev/"):
        raise ValueError(f"Invalid device path: {device_path} (must be in /dev/)")
    if not (resolved.is_char_device() or resolved.is_block_device()):
        raise ValueError(f"Not a device: {device_path}")
    
    self._device_path = str(resolved)
```

**Environment Variable:**
```python
# In main.py
import os
device_path = os.environ.get("MESHTASTIC_DEVICE", "/dev/ttyUSB1")
meshtastic_service = MeshtasticService(device_path=device_path)
```

---

### 🟡 MEDIUM-2: Missing Rate Limiting

**Locations:**
- `backend/app/routers/meshtastic.py:156` — `/send` endpoint
- `backend/app/routers/meshtastic.py:191` — WebSocket connections

**Issue:**
No rate limiting on:
1. **Message sending** — Can flood mesh with unlimited messages
2. **WebSocket connections** — Can exhaust server resources with mass connections

**Risk:**
- **Denial of Service (DoS)** — Exhaust radio bandwidth or server memory
- **Mesh network disruption** — LoRa has strict duty cycle limits (EU: 1% airtime)

**Fix:**
```bash
# Install slowapi
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/send")
@limiter.limit("10/minute")  # Max 10 messages per minute per IP
async def send_message(request: Request, msg: SendMessageRequest):
    # ... existing code
```

---

### 🟡 MEDIUM-3: No Input Validation on Message Content

**Location:** `backend/app/routers/meshtastic.py:158`

**Issue:**
```python
class SendMessageRequest(BaseModel):
    text: str  # No length limit, no sanitization
    channel: int = 0
    destination: Optional[str] = None
```

**Risk:**
- **Buffer overflow** — Meshtastic has message size limits (~200 bytes for text)
- **Injection attacks** — Special characters could break parsers on receiving nodes
- **Channel abuse** — Invalid channel numbers

**Fix:**
```python
from pydantic import BaseModel, Field, validator

class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    channel: int = Field(default=0, ge=0, le=7)  # Meshtastic supports 0-7
    destination: Optional[str] = Field(default=None, regex=r"^![0-9a-f]{8}$")  # !12345678 format
    
    @validator('text')
    def validate_text(cls, v):
        # Remove control characters
        import re
        cleaned = re.sub(r'[\x00-\x1F\x7F]', '', v)
        if not cleaned:
            raise ValueError("Message cannot be empty after sanitization")
        return cleaned.strip()
```

---

## 🟢 LOW Severity Issues

### 🟢 LOW-1: Frontend Rapid Polling (5s Interval)

**Location:** `frontend/src/pages/P100.jsx:78`

**Issue:**
```javascript
const refreshInterval = setInterval(fetchMeshData, 5000) // Poll every 5s for live updates
```

**Risk:**
- **Battery drain** on mobile/tablet dashboards
- **Unnecessary API calls** when WebSocket already provides real-time updates
- **Race conditions** between polling and WebSocket events

**Recommendation:**
Remove polling entirely — WebSocket provides real-time updates:
```javascript
// Remove this:
// const refreshInterval = setInterval(fetchMeshData, 5000)

// WebSocket already handles live updates:
const unsubMeshUpdate = wsClient.on('mesh_update', () => {
  console.log('[P100] Mesh update received, refreshing data')
  fetchMeshData()  // Only fetch on actual update
})
```

---

### 🟢 LOW-2: Missing Dependency Integrity Check

**Location:** `backend/requirements.txt` (missing!)

**Issue:**
No `meshtastic>=2.0.0` dependency pinned in `requirements.txt`. Only referenced in comment.

**Risk:**
- **Supply chain attack** — Malicious package version could be installed
- **Dependency confusion** — No integrity hash verification

**Fix:**
```bash
# backend/requirements.txt
# Add:
meshtastic==2.5.7  # Pin specific version
pyserial==3.5
```

**Better: Use hash verification**
```bash
pip freeze > requirements.txt
pip-audit  # Check for known vulnerabilities
```

---

## 📋 Dependency Review

**Meshtastic Python Library:**
- **Version:** Not pinned (should be `meshtastic>=2.0.0`)
- **Trust:** Official Meshtastic project (https://github.com/meshtastic/python)
- **Vulnerabilities:** None known (as of 2026-03-27)
- **Recommendation:** Pin to `meshtastic==2.5.7` (latest stable)

**PySerial:**
- **Version:** `pyserial>=3.5`
- **Trust:** Widely used, maintained library
- **Recommendation:** Pin to `pyserial==3.5`

---

## 🔒 Security Recommendations

### Immediate (Block Merge):
1. ✅ **Restrict CORS** to specific origins (HIGH-1)
2. ✅ **Add authentication** to `/send` endpoint (HIGH-2)
3. ✅ **Add rate limiting** to prevent DoS (MEDIUM-2)

### Before Production:
4. ✅ **Validate device path** (MEDIUM-1)
5. ✅ **Add input validation** on message content (MEDIUM-3)
6. ✅ **Pin dependency versions** with integrity checks (LOW-2)

### Nice-to-Have:
7. ✅ **Remove rapid polling** in favor of WebSocket-only (LOW-1)
8. ✅ **Add logging** for security events (failed auth, rate limits)
9. ✅ **Implement HTTPS** if exposing API externally

---

## ✅ What's Done Well

1. **Service architecture** — Good separation of concerns (service layer + router)
2. **Error handling** — Graceful fallback when Meshtastic unavailable
3. **WebSocket design** — Clean event-based architecture
4. **Pydantic models** — Strong typing on API responses
5. **Lazy imports** — Meshtastic library only loaded if available

---

## 📝 Summary

| Severity | Count | Critical Path |
|----------|-------|---------------|
| 🔴 HIGH | 2 | CORS + No Auth |
| 🟡 MEDIUM | 3 | Device validation, Rate limiting, Input validation |
| 🟢 LOW | 2 | Polling, Dependencies |

**Recommendation:**  
**DO NOT MERGE** until HIGH-1 and HIGH-2 are resolved.

MEDIUM issues should be addressed before production deployment.

---

## 📎 References

- Meshtastic Security Best Practices: https://meshtastic.org/docs/overview/encryption/
- OWASP API Security Top 10: https://owasp.org/www-project-api-security/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/

---

**Next Steps:**

1. Fix HIGH-1: Restrict CORS to specific origins
2. Fix HIGH-2: Add API key authentication to `/send` and `/ws`
3. Fix MEDIUM-2: Implement rate limiting
4. Re-submit for security review

**Estimated effort:** 2-3 hours for HIGH + MEDIUM fixes.
