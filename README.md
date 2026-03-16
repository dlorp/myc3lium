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

## Quick Start

### Development Setup

```bash
# Clone the repository
git clone https://github.com/dlorp/myc3lium.git
cd myc3lium

# Run setup script (installs dependencies)
./scripts/setup-dev.sh

# Start development servers
./scripts/run-dev.sh
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Project Structure

```
myc3lium/
├── frontend/           # React + Vite + Three.js WebUI
│   ├── src/           # Source code
│   ├── package.json   # Dependencies
│   └── vite.config.js # Build config
├── backend/           # FastAPI + Uvicorn
│   ├── app/          # Application code
│   ├── tests/        # Test suite
│   ├── requirements.txt
│   └── pyproject.toml
├── firmware/          # ESP32 + HYPHA (coming soon)
├── docs/              # Documentation
├── mockups/           # Design mockups
├── scripts/           # Setup & dev scripts
├── .github/workflows/ # CI/CD
├── .gitignore
└── README.md
```

## Tech Stack

### Frontend
- **Framework:** React 18 + Vite
- **3D Graphics:** Three.js + React Three Fiber
- **Routing:** React Router
- **State:** Zustand
- **Build:** Vite (fast HMR, optimized builds)

### Backend
- **Framework:** FastAPI
- **Server:** Uvicorn (ASGI)
- **Validation:** Pydantic v2
- **Testing:** pytest + pytest-asyncio
- **Linting:** ruff + mypy

### Planned Integrations
- **Mesh:** Reticulum + LXMF (encrypted messaging)
- **SDR:** SatDump + SoapySDR (satellite + spectrum)
- **ATAK:** FreeTAKServer + PyTAK (tactical maps)
- **LLM:** llama.cpp + Qwen2.5-7B (local intelligence)

## Development

### Frontend Commands

```bash
cd frontend
npm run dev      # Start dev server (port 3000)
npm run build    # Production build
npm run lint     # ESLint check
npm test         # Run tests
```

### Backend Commands

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload  # Start dev server (port 8000)
ruff check .                   # Lint check
mypy app                       # Type check
pytest                         # Run tests
```

## CI/CD

GitHub Actions runs on every PR:

- **Frontend:** lint → build → test
- **Backend:** ruff → mypy → pytest
- **Blocks merge if any check fails**

See `.github/workflows/ci.yml` for details.

## Project Status

**Current Phase:** Repository Scaffold + Initial Development

✅ Complete architecture documentation  
✅ Hardware specs finalized  
✅ WebUI mockups (14 pages, teletext design)  
✅ Repository structure & CI/CD  
✅ Frontend scaffold (React + Three.js)  
✅ Backend scaffold (FastAPI)  
⏳ WebUI implementation  
⏳ Firmware development (HYPHA ESP32-S3)  
⏳ Hardware ordering & assembly  

**Estimated Timeline:** 14-16 weeks part-time

## Documentation

- **[MYC3LIUM_BIBLE_V3.md](./MYC3LIUM_BIBLE_V3.md)** - Complete design doc
- **[TECH_STACK.md](./TECH_STACK.md)** - Technology choices
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture
- **[ROADMAP.md](./ROADMAP.md)** - Development roadmap
- **[HYPHA_DEV_GUIDE.md](./HYPHA_DEV_GUIDE.md)** - ESP32 firmware guide
- **[WEBUI_ROADMAP.md](./WEBUI_ROADMAP.md)** - Frontend development plan
- **[PAGES.md](./PAGES.md)** - WebUI page specifications

## Mockups

Interactive teletext GUI demo: `mockups/myc3lium-complete.html`

Features all 14 pages with 60 FPS rendering, CRT shaders, and live animations.

## Design Philosophy

**Local-first** - No cloud dependencies, runs entirely offline  
**Resilient** - Self-healing mesh, store-and-forward messaging  
**Low-signature** - Minimal radio footprint, encrypted by default  
**Modular** - Add nodes as needed, scale horizontally  
**Open** - Built on open protocols (Reticulum, BATMAN-adv, LXMF)  

Inspired by mycelial networks: distributed, adaptive, persistent.

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
