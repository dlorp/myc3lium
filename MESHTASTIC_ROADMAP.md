# Meshtastic Integration Roadmap

**Status:** Phase 2 Complete (Live Data)  
**PR:** #46 (feat/meshtastic-integration)  
**Last Updated:** 2026-03-27 20:06 AKDT

---

## Phase 1: Backend Foundation ✅ COMPLETE

**Goal:** Establish backend Meshtastic service and API endpoints.

### Completed
- ✅ MeshtasticService (395 lines) - SerialInterface wrapper with callbacks
- ✅ Meshtastic API router (275 lines) - /api/meshtastic/* endpoints
- ✅ Node tracking with position data, SNR, battery levels
- ✅ Ring buffer for last 100 messages
- ✅ Device connection: Heltec V3 on /dev/ttyUSB1 (CLIENT mode)
- ✅ Deployed to Pi (192.168.40.19:8000)

### Key Files
- `backend/app/services/meshtastic_service.py`
- `backend/app/routers/meshtastic.py`
- `backend/app/main.py` (service initialization)

---

## Phase 2: Frontend Integration ✅ COMPLETE

**Goal:** Display live Meshtastic data on dashboard.

### Completed
- ✅ Meshtastic API functions (fetchMeshtasticStatus, fetchMeshtasticNodes)
- ✅ P100 dashboard wired to live node data
- ✅ LoRa status from channel utilization (3-5%)
- ✅ Active/total node display (5min activity window: 1/18)
- ✅ 5-second polling for live updates
- ✅ Debug logging for node staleness tracking

### Key Files
- `frontend/src/services/api.ts` (Meshtastic types + fetch functions)
- `frontend/src/pages/P100.jsx` (live data integration)
- `frontend/src/services/ws.ts` (event handlers stubbed)

### Current Display
```
LoRa  [TX/RX]     ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  4% Signal
[200] MESH ▸1/18 online
```

---

## Phase 3: Real-Time WebSocket Updates ⚠️ IN PROGRESS

**Goal:** True real-time updates without polling.

### Status
- ⚠️ WebSocket callbacks not triggering
- ✅ Frontend handlers registered (`meshtastic_node_added`, `meshtastic_node_updated`)
- ⚠️ Backend `_on_node_info_updated` callback not broadcasting

### Root Cause
Backend receives Meshtastic packets but callbacks don't trigger WebSocket broadcasts.

### Tasks
- [ ] Debug Meshtastic Python library callback registration
- [ ] Verify `interface.onNodeInfoUpdated` is being called
- [ ] Add broadcast logging to backend
- [ ] Test with mobile node (walk around, trigger updates)
- [ ] Remove 5s polling once WebSocket works

### Files to Fix
- `backend/app/services/meshtastic_service.py` (callback chain)
- `backend/app/routers/meshtastic.py` (broadcast logic)

---

## Phase 4: Node Management 📋 PLANNED

**Goal:** Clean node list, improve data quality.

### Tasks
- [ ] Node aging/pruning (remove nodes not seen in 24+ hours)
- [ ] Persistent node cache (survive backend restarts)
- [ ] Node metadata enrichment (SNR trends, reliability score)
- [ ] Manual node removal/blocking
- [ ] Node name customization (override Meshtastic names)

### Expected Outcome
Dashboard shows only relevant nodes, not historical clutter.

---

## Phase 5: Advanced Dashboard Features 📋 PLANNED

**Goal:** Full mesh visibility and control.

### P200 (Mesh Nodes Page)
- [ ] Full node list with details (SNR, position, battery, age)
- [ ] Sort/filter by activity, signal strength, distance
- [ ] Node detail view (packet history, stats)
- [ ] Visual signal strength indicator

### P300 (Messages Page)
- [ ] Display Meshtastic text messages
- [ ] Send messages from dashboard
- [ ] Message threading/replies
- [ ] Direct message support

### P400 (Map Page)
- [ ] Position-based node visualization
- [ ] GPS coordinates from node data
- [ ] Distance calculation
- [ ] Route visualization

### P100 (Dashboard Enhancements)
- [ ] WebSocket status indicator
- [ ] Node join/leave notifications
- [ ] Packet stats (throughput, error rate)
- [ ] Battery alerts for low nodes

---

## Phase 6: Production Hardening 📋 PLANNED

**Goal:** Reliable 24/7 operation.

### Tasks
- [ ] Systemd service for backend
- [ ] Auto-restart on crashes
- [ ] Log rotation
- [ ] Error alerting
- [ ] Performance monitoring
- [ ] Database for node history (SQLite)
- [ ] API rate limiting
- [ ] CORS security review

---

## Technical Debt

### High Priority
- **WebSocket broadcasts** - Callbacks not firing (Phase 3)
- **Node staleness** - 17/18 nodes are >5min old
- **Serial port locking** - Backend restart required if connection lost

### Medium Priority
- **TeletextGrid rendering bug** - Stale closure fix in commit 1839ea4 needs merge
- **API error handling** - Frontend silently catches errors (.catch(() => null))
- **Memory leaks** - Node cache grows indefinitely

### Low Priority
- **CORS configuration** - Currently wide-open (allow_origins=["*"])
- **WebSocket reconnection** - 1s delay too aggressive for production
- **Console logging** - Too verbose for production

---

## Success Metrics

### Phase 2 (Current)
- ✅ Backend API serving 18 nodes
- ✅ Dashboard showing live LoRa status (4% utilization)
- ✅ Node count updates every 5 seconds
- ✅ Active node filtering (1/18 within 5min)

### Phase 3 (Target)
- ⏱️ <1s latency from node join to dashboard update
- ⏱️ Zero polling (100% WebSocket-driven)
- ⏱️ Frontend console shows "Broadcasting node update" logs

### Phase 4 (Target)
- ⏱️ Node list matches ESP32 OLED count (±1 node)
- ⏱️ Persistent node cache across restarts
- ⏱️ Clean node list (no 2+ hour old nodes)

---

## Resources

### Hardware
- **Heltec V3 ESP32** - /dev/ttyUSB1 on Pi
- **Firmware:** Meshtastic 2.7.15.567b8ea (CLIENT mode)
- **Nodes visible:** 18 total (1 active, 17 stale)

### Backend
- **API Base:** http://192.168.40.19:8000
- **Endpoints:**
  - `/api/meshtastic/status` - Device status
  - `/api/meshtastic/nodes` - Node list
  - `/api/meshtastic/messages` - Message history (not used yet)
  - `/ws/meshtastic` - WebSocket (not working)

### Frontend
- **Dev Server:** http://192.168.40.15:3000
- **Polling Interval:** 5 seconds
- **Active Threshold:** 300 seconds (5 minutes)

### Documentation
- `PHASE2_MESHTASTIC_COMPLETE.md` - Backend implementation details
- `DEPLOY_MESHTASTIC.md` - Deployment procedures
- `API_MESHTASTIC.md` - API reference
- `QUICKSTART_MESHTASTIC.txt` - Quick start guide

---

## Next Actions

### Immediate (Tonight)
1. ✅ Commit frontend changes
2. ✅ Create PR #46
3. ✅ Write roadmap document (this file)
4. [ ] Run PR workflow (security + code review)

### Short-term (This Week)
5. [ ] Debug WebSocket callback chain
6. [ ] Add node aging/pruning
7. [ ] Merge TeletextGrid fix to main
8. [ ] Test with mobile Meshtastic node

### Medium-term (Next Week)
9. [ ] Implement P200 node list page
10. [ ] Add message display to P300
11. [ ] Position-based map on P400
12. [ ] Production systemd service

---

**Owner:** dlorp  
**Repository:** https://github.com/dlorp/myc3lium  
**Branch:** feat/meshtastic-integration  
**PR:** #46
