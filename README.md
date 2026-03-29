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

Access the tactical interface:
```
http://<pi-ip>:8000
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
- 2x ESP32 USB boards (Meshtastic integration)
- Battery HAT (UPS or PiSugar 3 Plus)
- WiFi HaLow (Heltec HT-HC01P) - planned, not yet deployed

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
python main.py  # API server on :8000
```

---

## Project Status

**v0.2.0** - Live mesh integration

| Phase | Status | Details |
|-------|--------|---------|
| Core WebUI | Complete | 9 teletext pages (P100-P900), 8 reusable components, CRT shader pipeline |
| Deployment | Complete | Pi 4 auto-start (systemd), nginx reverse proxy, mDNS (`myc3.local`) |
| Live Integration | Complete | BATMAN + Reticulum + Meshtastic connected; 55+ real mesh nodes on lattice map |
| Security | Complete | API key auth, WS connection limits, input validation on radio packets, error sanitization |
| Configuration | In progress | TOML-based config system, headless setup via browser |
| SDR | Deferred | No hardware yet - satellite/spectrum features are UI scaffolds |

---

## License

See LICENSE file.

---

**MYC3LIUM** - _Making decentralized mesh networking as easy as mycelium growth._
