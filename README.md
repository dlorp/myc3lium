# 🍄 MYC3LIUM

**Resilient off-grid mesh communication lattice**

Portable, operator-centric, sensor-rich, intelligence-capable.

---

## Overview

MYC3LIUM is a portable off-grid communication system designed for field operations, intelligence gathering, and resilient networking in contested or infrastructure-denied environments.

**Core capabilities:**
- Triple-radio mesh (LoRa, WiFi HaLow, 802.11s)
- Encrypted messaging (Reticulum LXMF + Meshtastic)
- Tactical mapping (ATAK integration)
- Environmental sensor aggregation
- Live camera feeds
- Teletext-style operator interface with modern shader rendering

---

## Quick Start

### Hardware Setup

See **[deployment/README.md](deployment/README.md)** for complete hardware deployment guide.

**TL;DR:**
```bash
# On your Raspberry Pi:
cd deployment
sudo ./setup-all.sh
```

### WebUI

Access the mesh interface at:
```
http://myc3.local
```

**Pages:**
- **P100** - System overview
- **P200** - Mesh topology map
- **P300** - Messages (LXMF + Meshtastic)
- **P400** - Sensor telemetry
- **P500** - Camera streams
- **P600** - System configuration
- **P700** - Network event log
- **P800** - Command interface
- **P900** - ARG / recovered logs

---

## First Boot / Field Deployment

On first power-on with a USB WiFi adapter plugged in, the Pi automatically broadcasts an access point:

| | |
|---|---|
| **SSID** | `myc3_m3sh` |
| **Default Password** | `myc3m3sh` |
| **URL** | `http://myc3.local` or `http://10.99.0.1` |

**Setup flow:**
1. Power on the Pi (headless, no monitor needed)
2. Connect your phone/laptop to the `myc3_m3sh` WiFi network
3. Open `http://myc3.local` (or `http://10.99.0.1` if mDNS doesn't resolve)
4. The setup wizard walks through hostname, radio, mesh, and backhaul configuration
5. **You must change the default AP password** before the system unlocks

After setup, use **P600** (System Configuration) for ongoing changes.

### Backhaul Modes

The USB WiFi adapter (`wlan1`) supports two modes — the onboard `wlan0` is reserved for BATMAN mesh:

- **AP mode** (default): Broadcasts a hotspot for operators to connect and access the mesh terminal. AP clients are bridged into the BATMAN mesh via `br0`.
- **Client mode**: Joins an existing WiFi network for internet uplink. Traffic is NAT-forwarded so mesh nodes can reach the internet.

Configure in P600 under "BACKHAUL / AP MODE" or via `POST /api/config/apply-backhaul`.

---

## Documentation

- **[deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - Complete deployment guide
- **[deployment/QUICKSTART.txt](deployment/QUICKSTART.txt)** - Quick reference card
- **[deployment/API.md](deployment/API.md)** - API documentation
- **[MYC3LIUM_BIBLE_V3.md](MYC3LIUM_BIBLE_V3.md)** - Full project specification
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[NETWORK_TOPOLOGY.md](NETWORK_TOPOLOGY.md)** - Network design

---

## Hardware

### Supported Platforms

**SPORE (Main Node):**
- Raspberry Pi 4 (4GB RAM)
- Waveshare SX1262 LoRa HAT (915 MHz, with GNSS)
- ESP32 USB board (Meshtastic LoRa integration)
- ESP32 USB HaLow board (routes via bat0)
- Battery HAT (UPS or PiSugar 3 Plus)

See [MYC3LIUM_BIBLE_V3.md](MYC3LIUM_BIBLE_V3.md) for full hardware specifications.

---

## Tech Stack

**Backend:**
- FastAPI + uvicorn (REST + WebSocket API)
- Pydantic (data validation + settings)
- Reticulum Network Stack (mesh routing)
- Meshtastic (PyPubSub integration)
- Python 3.11+

**Frontend:**
- React 18 + TypeScript
- Canvas2D teletext renderer + WebGL CRT shaders
- Zustand (state management)
- Vite (build system)

**Networking:**
- BATMAN-adv (Layer 2 mesh)
- Reticulum (encrypted overlay)
- LXMF (messaging)
- Meshtastic bridge (LoRa mesh)

---

## Development

### Frontend
```bash
cd frontend
npm install
npm run dev     # Dev server on :5173
npm test        # Run tests
npm run build   # Production build
```

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## Project Status

**v0.7.1** - Mesh isolation: AP clients isolated from BATMAN mesh by default

| Phase | Status | Details |
|-------|--------|---------|
| Core WebUI | Complete | 9 teletext pages (P100-P900), 11 reusable components, CRT shader pipeline |
| Deployment | Complete | Pi 4 auto-start (systemd), nginx reverse proxy, mDNS (`myc3.local`) |
| Live Integration | Complete | BATMAN + Reticulum + Meshtastic connected; 55+ real mesh nodes on lattice map |
| Security | Complete | API key auth, WS connection limits, input validation on radio packets, error sanitization |
| Configuration | Complete | TOML-based config system, headless setup via browser at `/setup`, P600 config hub |
| SDR | Deferred | No hardware yet - satellite/spectrum features are UI scaffolds |

---

## License

See LICENSE file.

---

**MYC3LIUM** - Get out there and make a mesh._
