# myc3lium Meshtastic Integration - PAUSED

**Last updated:** 2026-03-26 11:29 AKDT

## What This Is

**Goal:** Add Meshtastic community mesh network connectivity to myc3lium mesh system.

**Architecture:**
- **Existing:** myc3lium private mesh (BATMAN-adv: WiFi 2.4/5GHz + HaLow 900MHz → Reticulum encryption)
- **Adding:** Meshtastic gateway via Heltec V3 ESP32 LoRa device (USB to Pi)
- **Integration:** Dual-network system - private myc3lium mesh + public Meshtastic community network

## Current Status

### ✅ Phase 1 Complete (Hardware Setup)
- Heltec V3 flashed with Meshtastic firmware v2.7.15
- Connected to Raspberry Pi via `/dev/ttyUSB1`
- Role: CLIENT (full mesh participation)
- Node ID: `!7c5b4118`

### ✅ Phase 2 Complete (Backend Code - NOT DEPLOYED)
- **Files created:** 949 lines production code
  - `backend/app/services/meshtastic_service.py` (453 lines)
  - `backend/app/routers/meshtastic.py` (294 lines)
  - `test_meshtastic.py` (202 lines)
  - Updated `backend/app/main.py`
- **API endpoints:**
  - GET `/api/meshtastic/status`
  - GET `/api/meshtastic/nodes`
  - GET `/api/meshtastic/messages`
  - POST `/api/meshtastic/send`
  - WS `/ws/meshtastic`
- **Documentation:** DEPLOY_MESHTASTIC.md, API_MESHTASTIC.md, PHASE2_MESHTASTIC_COMPLETE.md

### ⏳ Phase 3 Pending (Frontend)
- WebSocket integration
- Message display UI
- Node visualization
- Send message interface

## Why We Paused

**Reason:** Waveshare SX1262 HAT hardware incompatibility discovered
- HAT is UART variant (proprietary protocol via onboard MCU)
- meshtasticd requires direct SPI access to SX1262 chip
- Architectural mismatch: HAT won't work with meshtasticd

**Solution chosen:** Use Heltec V3 USB device instead
- Works perfectly with Meshtastic firmware
- Dual-network capable (myc3lium + Meshtastic)

## Resume Instructions

**To pick up where we left off:**

```bash
# Deploy Phase 2 backend to Pi
cd ~/myc3lium
git add backend/ test_meshtastic.py *.md
git commit -m "feat: Meshtastic backend integration (Phase 2)"
git push

# On Pi (192.168.40.19, user: myc3@, password: okok):
ssh myc3@192.168.40.19
cd ~/myc3lium
git pull
pip3 install -r backend/requirements.txt
sudo systemctl restart myc3lium-backend
python3 test_meshtastic.py

# Verify API:
curl http://192.168.40.19:8000/api/meshtastic/status
```

**Then proceed to Phase 3 (Frontend integration):**
- Connect React frontend to `/ws/meshtastic` WebSocket
- Display messages in P300 (messaging page)
- Show nodes in P200 (mesh topology)
- Add send interface

## Key Files

**Backend (myc3lium repo):**
- `~/repos/myc3lium/backend/app/services/meshtastic_service.py`
- `~/repos/myc3lium/backend/app/routers/meshtastic.py`
- `~/repos/myc3lium/test_meshtastic.py`

**Planning docs:**
- `~/repos/myc3lium/plans/meshtastic-integration-2026-03-24.md`
- `~/repos/myc3lium/plans/waveshare-meshtastic-solutions-2026-03-24.md`
- `~/repos/myc3lium/DEPLOY_MESHTASTIC.md`

**Pi location:**
- myc3lium backend: `~/myc3lium/backend/`
- Heltec device: `/dev/ttyUSB1`

## Network Info

**Raspberry Pi:**
- IP: 192.168.40.19
- SSH: myc3@192.168.40.19 (password: okok)
- Backend: http://192.168.40.19:8000
- Frontend: http://192.168.40.19:3000

**Heltec V3:**
- Device: `/dev/ttyUSB1`
- Firmware: Meshtastic v2.7.15
- Node ID: `!7c5b4118`
- MAC: 24:58:7c:5b:41:18

## Reference Command

**To resume this project, say:**
> "Resume Meshtastic integration - deploy Phase 2 backend to Pi and test"

---

_Work paused after Phase 2 code complete, before Pi deployment._
