# MYC3LIUM

**Portable off-grid mesh intelligence terminal**

MYC3LIUM (my-SEE-lee-um) is a resilient mesh network system for field operations, intelligence gathering, and tactical communications. Think of it as your personal SIGINT station that fits in a backpack.

## What It Does

- **Mesh Networking** - Multi-radio resilient comms (LoRa, WiFi HaLow, 802.11s)
- **Satellite Intelligence** - NOAA/METEOR weather satellite reception and decoding
- **RF Spectrum Monitoring** - Wide-band SDR scanning (300Hz-2.3GHz)
- **Tactical Mapping** - ATAK integration with offline map tiles
- **Environmental Sensing** - Distributed sensor pods (atmosphere, hydrology, weather)
- **Encrypted Messaging** - LXMF over Reticulum with store-and-forward
- **Local LLM Agents** - On-device intelligence analysis and natural language queries

All wrapped in a teletext-inspired GUI running on a Raspberry Pi 4.

## Node Types

MYC3LIUM uses a biological mesh taxonomy:

- **SPORE** - Main portable anchor/base station (Pi 4, multi-radio, SDR, compute, display)
- **HYPHA** - Lightweight handheld nodes (ESP32-S3, scouting, messaging)
- **FROND** - Camera/sensor nodes (high-throughput visual/data gathering)
- **RHIZOME** - Environmental sensor pods (atmosphere, weather, distributed sensing)

Each node type has a specific role, but all speak the same protocols (Reticulum LXMF, BATMAN-adv, encrypted end-to-end). All nodes can relay; there are no dedicated relay-only devices.

## Tech Stack

### Hardware (SPORE Base Node)
- Raspberry Pi 4 (4GB)
- SX1262 LoRa HAT (915 MHz, 5-50km range)
- Heltec HT-HC01P WiFi HaLow (902-928 MHz, 1km+ range)
- Pi 4 built-in WiFi (802.11s mesh backbone)
- RTL-SDR Blog V4 (satellite + spectrum monitoring)
- GPS module (u-blox based)
- Alfa AWUS036ACH (Kismet wardriving)
- 7-10" touchscreen display
- 21700 battery HAT (6-8h runtime)

**Total Cost:** ~$400-550 depending on options

### Software
- **GUI:** PyQt6 + ModernGL (teletext aesthetic with CRT shaders)
- **Mesh:** Reticulum + LXMF (encrypted messaging)
- **Layer 2:** BATMAN-adv (802.11s mesh routing)
- **Satellite:** SatDump + Gpredict (automated pass tracking)
- **SDR:** SoapySDR + RTL-SDR drivers
- **ATAK:** FreeTAKServer + PyTAK (tactical map integration)
- **LLM:** llama.cpp + Qwen2.5-7B-Instruct (Q4, ~4GB RAM)
- **GPS:** gpsd (position tracking)
- **Maps:** MBTiles (offline topo + satellite overlays)

## Project Status

**Current Phase:** Planning + Prototyping

✅ Complete architecture documentation  
✅ Hardware specs finalized  
✅ WebUI mockups (14 pages, teletext design)  
✅ Node taxonomy defined  
🔄 Hardware ordering in progress  
⏳ Firmware development (HYPHA ESP32-S3)  
⏳ SPORE base system build  
⏳ WebUI implementation (FastAPI + React)  

**Estimated Timeline:** 14-16 weeks part-time

## Repository Structure

```
myc3lium/
├── docs/               # Full project documentation
│   └── MYC3LIUM_BIBLE_V3.md  # Comprehensive design doc
├── mockups/            # WebUI design mockups
│   └── myc3lium-complete.html  # Interactive teletext GUI demo
├── firmware/           # Node firmware (ESP32, Pi)
├── backend/            # FastAPI server + Reticulum integration
├── frontend/           # React + Three.js WebUI
├── hardware/           # Schematics, BOM, assembly guides
└── scripts/            # Installation, setup, utilities
```

## Mockups

Check `mockups/myc3lium-complete.html` for an interactive demo of the WebUI design. Open it in a browser to explore all 14 pages:

- **P100** - Dashboard (system overview)
- **P101** - System Health (CPU, RAM, battery)
- **P200** - Lattice Map (animated mesh topology)
- **P202** - Link Quality (RSSI, SNR, packet loss)
- **P300** - LXMF Inbox (encrypted messages)
- **P400** - ATAK Map (terrain + nodes)
- **P401** - Waypoint Manager
- **P500** - Satellite Tracker (live pass predictions)
- **P501** - RF Spectrum Waterfall (SDR visualization)
- **P503** - Camera Feed (FROND livestream)
- **P600** - Radio Config (LoRa/HaLow/SDR params)
- **P700** - Sensor Grid (RHIZOME telemetry + sparklines)
- **P703** - Alert Thresholds (environmental monitoring)
- **P800** - Local LLM Chat (natural language queries)

Features 60 FPS rendering, CRT shader effects, and live animations.

## Design Philosophy

**Local-first** - No cloud dependencies, runs entirely offline  
**Resilient** - Self-healing mesh, store-and-forward messaging  
**Low-signature** - Minimal radio footprint, encrypted by default  
**Modular** - Add nodes as needed, scale horizontally  
**Open** - Built on open protocols (Reticulum, BATMAN-adv, LXMF)  

Inspired by mycelial networks: distributed, adaptive, persistent.

## Getting Started

**Hardware:**
1. Order components (see `hardware/BOM.md`)
2. Assemble SPORE base node
3. Flash RNode firmware on SX1262 HAT
4. Configure Reticulum triple-radio stack

**Software:**
1. Install Raspberry Pi OS Lite
2. Run setup script: `./scripts/install.sh`
3. Configure radios: `./scripts/configure-radios.sh`
4. Start WebUI: `systemctl start myc3lium-webui`

**First HYPHA Node:**
1. Flash ESP32-S3 HT-HC33 firmware
2. Pair with SPORE via WiFi HaLow
3. Test messaging + position updates

Detailed guides coming soon in `docs/`.

## Roadmap

**Phase 1: SPORE Base System** (Weeks 1-4)
- [ ] Pi 4 OS setup + dependencies
- [ ] LoRa HAT configuration (RNode firmware)
- [ ] WiFi HaLow driver integration
- [ ] BATMAN-adv mesh setup
- [ ] Reticulum stack deployment

**Phase 2: Intelligence Gathering** (Weeks 5-8)
- [ ] RTL-SDR satellite reception
- [ ] SatDump integration (APT/LRPT decoding)
- [ ] Spectrum monitoring (SoapySDR)
- [ ] Kismet wardriving setup
- [ ] MBTiles map pipeline

**Phase 3: WebUI** (Weeks 9-12)
- [ ] FastAPI backend (LXMF bridge)
- [ ] React + Three.js frontend
- [ ] Teletext renderer with CRT shaders
- [ ] Real-time data feeds (WebSocket)
- [ ] Page navigation + state management

**Phase 4: LLM Integration** (Weeks 13-14)
- [ ] llama.cpp deployment
- [ ] Qwen2.5-7B model quantization
- [ ] Chat interface (P800)
- [ ] Data parsing agents
- [ ] Natural language mesh queries

**Phase 5: HYPHA Nodes** (Weeks 15-16)
- [ ] ESP32-S3 firmware (Reticulum-ESP32)
- [ ] WiFi HaLow driver
- [ ] Camera integration
- [ ] LXMF messaging
- [ ] Field testing

## Contributing

This is a personal project but contributions/suggestions welcome. Open an issue or PR.

**Areas of interest:**
- Reticulum protocol optimization
- HYPHA firmware (ESP32-S3 + HaLow)
- WebUI improvements (Three.js shaders, teletext effects)
- ATAK integration (CoT messaging)
- Local LLM agents (data parsing, analysis)

## License

MIT License - see `LICENSE` file

Built with ❤️ for off-grid resilience and underground vibes.

---

**Project Name Etymology:**  
Mycelium = underground fungal network that connects plants, shares resources, and adapts to damage. Perfect metaphor for a resilient mesh network.

**Naming Convention:**  
MYC3LIUM uses `3` for `E` (following t3rra1n/r3LAY pattern). Shorthand: **myc3**
