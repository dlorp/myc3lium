# MYC3LIUM Phase 4 - Friday Hardware Deployment Guide

**Hardware Arrives:** Friday Morning (00:00 UTC)  
**Setup Window:** 4 hours (Friday 00:00 - 04:00 UTC)  
**Status:** READY FOR PRODUCTION

---

## Quick Start (5 minutes)

```bash
# 1. Clone repo
git clone <repo-url> myc3lium && cd myc3lium

# 2. Run full setup
bash deployment/setup-all.sh

# 3. Verify integration
bash deployment/tests/integration-test.sh

# 4. Start WebUI
npm --prefix frontend start
```

---

## Hardware Checklist

- [ ] P400 Sensor Grid (12 nodes)
- [ ] P500 Camera Stream (2 feeds)
- [ ] P700 Node Log Display
- [ ] P800 Network Status
- [ ] Reticulum Bridge (backend connectivity)
- [ ] Deployment scripts verified

---

## Component Status

### Frontend Pages (All Green)

| Page | Status | Feature | Commit |
|------|--------|---------|--------|
| **P400** | ✅ READY | Sensor grid, sorting, export | feat/phase4-sprint1-p400 |
| **P500** | ✅ READY | Camera stream, live feed | feat/phase4-sprint1-p500 |
| **P700** | ✅ READY | Node log, filters, search | feat/phase4-sprint1-p700 |
| **P800** | ✅ READY | Network map, topology | main |

### Backend (Verified)

- ✅ `backend/reticulum_bridge.py` - Mesh connectivity
- ✅ API routes for P400 (`/api/sensors`)
- ✅ API routes for P500 (`/api/camera`)
- ✅ WebSocket connection pool
- ✅ CSV export (P400, P700)

### Deployment Package

- ✅ `deployment/README.md` - Setup overview
- ✅ `deployment/DEPLOYMENT.md` - Detailed steps
- ✅ `deployment/API.md` - API documentation
- ✅ `deployment/MANIFEST.md` - Complete file manifest
- ✅ `deployment/setup-all.sh` - Automated setup
- ✅ `deployment/tests/integration-test.sh` - Validation

---

## Setup Steps (Detailed)

### Step 1: Environment Setup (1 min)

```bash
cd myc3lium

# Copy environment
cp .env.example .env

# Edit .env with Friday hardware addresses
# Key variables:
# - RETICULUM_INTERFACE=<hardware-serial-port>
# - CAMERA_RTMP_URL=<Friday-camera-url>
# - NODE_IDS=P400-01,P400-02,...,P400-12
```

### Step 2: Backend Setup (2 min)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Verify Reticulum bridge
python -c "from reticulum_bridge import Bridge; print('✓ Bridge importable')"

# Start backend
python app.py
```

### Step 3: Frontend Setup (1 min)

```bash
cd frontend

# Install dependencies
npm install

# Verify pages exist
ls -l src/pages/P400.* src/pages/P500.* src/pages/P700.*

# Start dev server
npm start
```

### Step 4: Integration Test (1 min)

```bash
# Run full integration test
bash deployment/tests/integration-test.sh

# Expected output:
# ✓ Backend imports OK
# ✓ API routes responsive
# ✓ WebSocket connected
# ✓ CSV export working
```

---

## Friday Timeline

### 00:00-00:15 - Hardware Connection
- Connect LoRa modem to serial port
- Connect camera streams
- Verify power supply

### 00:15-00:30 - Backend Bootstrap
```bash
python backend/app.py
# Watch for: "Reticulum Bridge initialized"
# Watch for: "WebSocket server ready"
```

### 00:30-00:45 - Frontend Deploy
```bash
npm --prefix frontend run build
npm --prefix frontend start
# Watch for: "Listening on :3000"
```

### 00:45-01:00 - Integration Verify
```bash
bash deployment/tests/integration-test.sh
# All tests must pass
```

### 01:00-04:00 - Live Monitoring
- Monitor P400 sensor readings (should show >6 nodes)
- Monitor P500 camera feeds (should show 2 streams)
- Monitor P700 event log (should show continuous entries)
- Monitor P800 network topology (should show mesh formation)

---

## Emergency Recovery

### If Backend Won't Start
```bash
# Check Reticulum connection
python -c "from reticulum_bridge import Bridge; b = Bridge(); print(b.status())"

# Reset USB serial
sudo killall -9 python && sleep 2 && python backend/app.py
```

### If Frontend Won't Load Pages
```bash
# Verify page files exist
ls frontend/src/pages/P400.tsx frontend/src/pages/P500.tsx frontend/src/pages/P700.tsx

# Clear cache
rm -rf frontend/node_modules/.vite

# Rebuild
npm --prefix frontend run build
```

### If WebSocket Disconnects
```bash
# Check backend logs
tail -f backend/logs/bridge.log

# Restart backend
pkill -f "python.*app.py" && sleep 2 && python backend/app.py
```

### If Sensors Not Reporting
```bash
# Verify modem on port
ls -l /dev/ttyUSB0  # or /dev/ttyACM0

# Check mesh nodes online (via P800)
# If 0 nodes: wait 30 seconds for mesh to form
# If still 0: reboot all P400 nodes

# Emergency node reset
python deployment/scripts/reset-all-nodes.py
```

---

## Success Criteria (Must Pass)

- ✅ All 4 PRs merged to main
- ✅ Deployment package committed
- ✅ Backend starts without errors
- ✅ Frontend loads all pages (P400, P500, P700, P800)
- ✅ P400 shows >6 sensor nodes
- ✅ P500 displays live camera feeds
- ✅ P700 displays event log with >50 entries
- ✅ P800 shows network topology with >8 nodes
- ✅ WebSocket connection stable (no disconnects in 1 min)
- ✅ CSV export works from P400 and P700

---

## Files Deployed

```
myc3lium/
├── backend/
│   ├── app.py                    (main server)
│   ├── reticulum_bridge.py       (mesh gateway)
│   ├── api/
│   │   ├── sensors.py            (P400 endpoints)
│   │   ├── camera.py             (P500 endpoints)
│   │   └── log.py                (P700 endpoints)
│   └── requirements.txt
├── frontend/
│   ├── src/pages/
│   │   ├── P400.tsx              (sensor grid)
│   │   ├── P400.utils.ts         (sorting, export)
│   │   ├── P400.test.tsx         (unit tests)
│   │   ├── P500.tsx              (camera stream)
│   │   ├── P700.tsx              (node log)
│   │   ├── P700.utils.ts         (filters, search)
│   │   └── P700.test.tsx         (unit tests)
│   └── package.json
├── deployment/
│   ├── README.md                 (overview)
│   ├── DEPLOYMENT.md             (detailed guide)
│   ├── API.md                    (endpoint docs)
│   ├── MANIFEST.md               (file listing)
│   ├── FRIDAY_SETUP_GUIDE.md     (THIS FILE)
│   ├── setup-all.sh              (automated setup)
│   ├── config/                   (configuration files)
│   ├── scripts/                  (utility scripts)
│   └── tests/
│       └── integration-test.sh   (validation)
└── .env.example                  (environment template)
```

---

## Git Branches (All Created)

```
feat/phase4-sprint1-p400     → P400 sensor grid polish
feat/phase4-sprint1-p500     → P500 camera stream live
feat/phase4-sprint1-p700     → P700 node log filters+search
<deployment-pr>              → Deployment package + this guide
```

---

## Post-Deployment Support

### Logs Location
- Backend: `backend/logs/bridge.log`
- Frontend: Browser DevTools Console
- System: `/var/log/myc3lium.log` (if syslog configured)

### Monitoring Commands
```bash
# Watch backend in real-time
tail -f backend/logs/bridge.log | grep -E "ERROR|WARNING|Connected"

# Check node status
curl http://localhost:8000/api/sensors/status

# Monitor WebSocket
watch 'curl -s http://localhost:8000/api/health | jq .ws_connections'
```

### Rollback Plan
If hardware fails, revert to main branch:
```bash
git checkout main
npm --prefix frontend install
python backend/app.py
```

---

## Contact & Escalation

- **Backend Issues:** Check `backend/logs/bridge.log` first
- **Page Not Loading:** Verify all P\* files in `frontend/src/pages/`
- **No Sensor Data:** Restart backend, wait 30s for mesh formation
- **Camera Feed Black:** Check camera RTMP URL in `.env`

---

**READY FOR FRIDAY DEPLOYMENT** ✓

*Last Updated: 2024-03-19T00:33 UTC*  
*Hardware Arrival: Friday 00:00 UTC*
