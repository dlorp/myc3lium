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
- **P600** - Satellite tracking
- **P700** - Network event log
- **P800** - Command interface

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
- Waveshare SX1262 LoRa HAT (915 MHz)
- Heltec HT-HC01P WiFi HaLow (902-928 MHz)
- Battery HAT (UPS or PiSugar 3 Plus)
- 7-10" touchscreen

See [MYC3LIUM_BIBLE_V3.md](MYC3LIUM_BIBLE_V3.md) for full hardware specifications.

---

## Tech Stack

**Backend:**
- Reticulum Network Stack (mesh routing)
- FastAPI (REST + WebSocket API)
- Python 3.9+

**Frontend:**
- React + TypeScript
- Three.js (teletext renderer)
- Vite (build system)

**Networking:**
- BATMAN-adv (Layer 2 mesh)
- Reticulum (encrypted overlay)
- LXMF (messaging)
- Meshtastic bridge

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

**Phase 4 Complete:** All core pages implemented with production polish
- ✅ WebUI (9 pages)
- ✅ Component library (8 components)
- ✅ Deployment automation
- ✅ Multi-protocol bridge (Reticulum + Meshtastic + ATAK)
- ✅ Hardware configuration scripts

---

## License

See LICENSE file.

---

**MYC3LIUM** - _Making decentralized mesh networking as easy as mycelium growth._
