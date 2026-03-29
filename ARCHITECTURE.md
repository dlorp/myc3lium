# myc3lium - System Architecture

**Version:** 2.0
**Target Platform:** Raspberry Pi 4 (4GB RAM)
**Access:** Web browser via `http://myc3.local`
**OS:** Raspberry Pi OS 64-bit (Debian Bookworm)

---

## Overview

**myc3lium** is a portable mesh networking system with a web-based teletext-style UI served headless from a Raspberry Pi. The Pi runs backend services (FastAPI, Reticulum, Meshtastic) and serves a React frontend via nginx. Operators connect from any device on the mesh or local network.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Any Browser)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │   React 18 + TypeScript + Vite                         │ │
│  │   ├── Canvas2D Teletext Renderer (40x25 grid)          │ │
│  │   ├── WebGL CRT Shader (scanlines, phosphor, vignette) │ │
│  │   ├── Zustand Store (meshStore, navigationStore)       │ │
│  │   ├── WebSocket Client (real-time mesh events)         │ │
│  │   └── Page Router (P100-P900)                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         ↕ HTTP / WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 4                             │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │  nginx (port 80)                                  │       │
│  │  ├── Static files: /var/www/myc3lium/             │       │
│  │  ├── Proxy /api/* → localhost:8000                │       │
│  │  └── Proxy /ws   → localhost:8000/ws              │       │
│  └──────────────────────────────────────────────────┘       │
│                         ↕                                    │
│  ┌──────────────────────────────────────────────────┐       │
│  │  FastAPI + uvicorn (port 8000)                    │       │
│  │  ├── REST API (/api/nodes, /api/messages, etc.)   │       │
│  │  ├── WebSocket Server (/ws, /api/meshtastic/ws)   │       │
│  │  ├── MeshStore (in-memory state + event bus)      │       │
│  │  ├── MeshtasticService (serial radio integration) │       │
│  │  ├── MeshtasticBridge (radio → MeshStore sync)    │       │
│  │  ├── ReticulumBridge (RNS/LXMF messaging)        │       │
│  │  ├── LiveDataSource (BATMAN + Reticulum polling)  │       │
│  │  └── BatctlService (BATMAN-adv interface)         │       │
│  └──────────────────────────────────────────────────┘       │
│                         ↕                                    │
│  ┌──────────────┬──────────────┬──────────────────┐         │
│  │ rnsd         │ gpsd         │ Meshtastic       │         │
│  │ (Reticulum   │ (GPS from    │ (in-process via  │         │
│  │  daemon)     │  LoRa HAT)   │  SerialInterface)│         │
│  └──────────────┴──────────────┴──────────────────┘         │
│                         ↕                                    │
│  ┌──────────────┬──────────────┬──────────────────┐         │
│  │ LoRa HAT     │ ESP32 USB    │ WiFi Mesh        │         │
│  │ (SX1262 +    │ (Meshtastic  │ (BCM43455 +      │         │
│  │  GNSS)       │  radios)     │  BATMAN-adv)     │         │
│  └──────────────┴──────────────┴──────────────────┘         │
│     915 MHz        915 MHz        2.4 GHz                    │
│     1-10+ km       1-10+ km       50-200m                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Process Model

### On the Raspberry Pi

**1. nginx** (systemd service)
- Serves static frontend build from `/var/www/myc3lium/`
- Reverse proxy for API and WebSocket traffic
- ~20 MB RAM

**2. uvicorn + FastAPI** (systemd: `myc3lium-backend.service`)
- REST API endpoints for nodes, threads, messages, mesh status, config
- WebSocket server for real-time event broadcasting
- MeshtasticService runs in-process (serial reader thread + PyPubSub)
- MeshtasticBridge syncs radio nodes into MeshStore
- ~150-200 MB RAM

**3. Reticulum Daemon (`rnsd`)** (systemd: `reticulum.service`)
- Multi-radio mesh routing (LoRa, WiFi, BATMAN)
- Store-and-forward messaging via LXMF
- ~200 MB RAM

**4. GPS Daemon (`gpsd`)** (systemd)
- Reads GNSS from LoRa HAT serial
- Provides position to backend
- ~50 MB RAM

### On the Client

The React frontend runs entirely in the user's browser. The Pi only serves the static build files. All rendering (Canvas2D teletext grid, WebGL CRT shaders) happens client-side.

---

## Memory Budget (4GB Total)

```
OS baseline:              ~500 MB
nginx:                     ~20 MB
uvicorn + FastAPI:        ~200 MB
Reticulum daemon:         ~200 MB
GPS daemon:                ~50 MB
System services:          ~150 MB
──────────────────────────────────
Used:                    ~1120 MB
Free headroom:           ~2880 MB
```

Plenty of headroom for future services (SDR, LLM agents).

---

## Data Flow

### REST API Flow
```
Browser ──[HTTP]──→ nginx ──[proxy]──→ FastAPI
                                         │
                                    ┌────┴────┐
                                    │         │
                              MeshStore   MeshtasticService
                            (in-memory)   (serial radio)
                                    │         │
                                    └────┬────┘
                                         │
                                     Response
```

### WebSocket Event Flow
```
MeshtasticService                     MeshStore
  │ (PyPubSub)                          │ (event handlers)
  │                                     │
  └──→ MeshtasticBridge ──→ add/update ─┘
                                        │
                                   emit event
                                        │
                                   WS Router
                                        │
                                   broadcast()
                                        │
                              ┌─────────┼─────────┐
                              │         │         │
                          Client 1  Client 2  Client N
```

### Meshtastic Integration Flow
```
LoRa Radio ──[serial]──→ meshtastic library
                              │ (PyPubSub callbacks)
                              ├── _on_receive()        → message events
                              ├── _on_node_info()      → node discovery
                              └── _on_connection()     → connection status
                                        │
                                  MeshtasticBridge
                                        │
                              ┌─────────┴─────────┐
                              │                   │
                         MeshStore            WS broadcast
                       (add/update node)    (real-time to clients)
```

---

## Module Structure

```
myc3lium/
├── README.md
├── ARCHITECTURE.md                  # This file
├── MYC3LIUM_BIBLE_V3.md            # Full project specification
├── NETWORK_TOPOLOGY.md             # Network design
├── CHANGELOG.md
│
├── frontend/                        # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/              # Reusable teletext UI components
│   │   │   ├── TeletextPanel.tsx    # Bordered panel with header
│   │   │   ├── TeletextText.tsx     # Colored text with optional blink
│   │   │   ├── TeletextGrid.jsx     # Canvas2D 40x25 character renderer
│   │   │   ├── StatusBar.tsx        # Percentage bar with block chars
│   │   │   ├── ProgressBar.tsx      # Battery/signal indicator
│   │   │   ├── Sparkline.tsx        # Mini line graph (canvas)
│   │   │   ├── CommandInput.tsx     # Command bar with cursor
│   │   │   ├── NodeBadge.tsx        # Node ID + callsign + status
│   │   │   └── ThreadIndicator.tsx  # Signal quality dots
│   │   ├── pages/                   # Teletext page components
│   │   │   ├── P100.jsx            # System overview dashboard
│   │   │   ├── P200.jsx            # Lattice topology map
│   │   │   ├── P300.tsx            # Messages (LXMF + Meshtastic)
│   │   │   ├── P400.tsx            # Tactical map (ATAK)
│   │   │   ├── P500.tsx            # Camera streams / intelligence
│   │   │   ├── P600.tsx            # System configuration
│   │   │   ├── P700.tsx            # Network event log
│   │   │   ├── P800.tsx            # Command interface
│   │   │   └── P900.tsx            # ARG / recovered logs
│   │   ├── store/                   # Zustand state management
│   │   │   └── meshStore.ts        # Mesh network state + WS events
│   │   ├── services/                # API + WebSocket clients
│   │   │   ├── api.ts              # REST API fetch wrapper + types
│   │   │   ├── ws.ts               # WebSocket client with reconnect
│   │   │   └── validators.ts       # Zod schemas for WS data validation
│   │   └── router/
│   │       └── Router.jsx          # Page routing (/p/100, /p/200, etc.)
│   ├── public/
│   │   └── fonts/                   # IBM VGA teletext font
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                         # FastAPI + Python 3.11+
│   ├── app/
│   │   ├── main.py                  # FastAPI app, service wiring, startup
│   │   ├── config.py                # Pydantic Settings (env vars, .env)
│   │   ├── models.py                # Pydantic models (Node, Thread, Message, etc.)
│   │   ├── auth.py                  # API key authentication
│   │   ├── websocket.py             # ConnectionManager (limits, broadcast)
│   │   ├── routers/
│   │   │   ├── nodes.py             # CRUD /api/nodes
│   │   │   ├── threads.py           # CRUD /api/threads
│   │   │   ├── messages.py          # CRUD /api/messages + Reticulum send
│   │   │   ├── mesh.py              # /api/mesh/status, topology, radios
│   │   │   ├── meshtastic.py        # /api/meshtastic/* + WS endpoint
│   │   │   └── ws.py                # Main /ws endpoint + event broadcasting
│   │   └── services/
│   │       ├── mesh_store.py        # In-memory state store with event bus
│   │       ├── meshtastic_service.py # Serial radio integration (PyPubSub)
│   │       ├── meshtastic_bridge.py # Radio node → MeshStore sync
│   │       ├── reticulum_service.py # RNS/LXMF bridge (graceful fallback)
│   │       ├── live_data_source.py  # BATMAN + Reticulum data provider
│   │       ├── batctl_service.py    # BATMAN-adv subprocess interface
│   │       └── mock_data.py         # Development mock data generator
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── firmware/
│   ├── lora-bridge/                 # C - LoRa TAP bridge for SX1262 HAT
│   │   ├── lora-tap-bridge.c        # Main daemon (select loop)
│   │   ├── sx1262.c                 # SPI driver
│   │   ├── tap.c                    # TAP interface
│   │   ├── fragment.c               # Ethernet frame fragmentation
│   │   └── Makefile
│   └── esp32_cam/                   # ESP32-S3 MJPEG camera node
│       └── src/main.cpp
│
├── deployment/
│   ├── setup-all.sh                 # Master Pi setup script
│   ├── scripts/
│   │   ├── setup-pi4.sh             # Base system + dependencies
│   │   ├── setup-lora.sh            # LoRa HAT configuration
│   │   ├── setup-halow.sh           # WiFi HaLow setup
│   │   ├── setup-batman.sh          # BATMAN-adv mesh
│   │   └── deploy-webui.sh          # nginx + frontend deployment
│   ├── config/
│   │   └── reticulum.conf           # Reticulum network stack config
│   ├── backend/
│   │   └── reticulum_bridge.py      # Standalone multi-protocol bridge
│   └── tests/
│       └── test-all.sh              # Integration test suite
│
└── skills/                          # OpenClaw skill extensions
```

---

## Security Model

**Mesh Communications:**
- Reticulum: End-to-end encryption (Ed25519 identity keys)
- Meshtastic: Optional AES encryption per channel
- No plaintext by default

**API Security:**
- API key authentication (`X-API-Key` header) for Meshtastic send endpoint
- HMAC constant-time comparison to prevent timing attacks
- CORS configured for mesh network access
- WebSocket connection limits (MAX_CONNECTIONS=100)
- WebSocket message size validation (1024 bytes application, 4096 bytes protocol)
- Input validation on all radio packet data (control char stripping, range checks)
- Error responses sanitized (no internal details leaked)

**Network:**
- Firewall (ufw): only SSH, HTTP/S, Reticulum ports open
- Reticulum identity key stored locally, backup recommended
- No cloud dependencies, no telemetry

---

## Startup Sequence

1. **Boot** - Raspberry Pi OS starts systemd services
2. **rnsd** starts - Reticulum mesh routing comes online (LoRa, WiFi, BATMAN interfaces)
3. **gpsd** starts - GPS fix acquired from LoRa HAT GNSS
4. **myc3lium-backend** starts - uvicorn launches FastAPI app
   - Chooses data source (LiveDataSource on Pi, MockDataSource on Mac)
   - Initializes MeshStore with initial node/thread data
   - Starts MeshtasticService (connects to serial radio)
   - MeshtasticBridge seeds discovered nodes into MeshStore
   - Registers WebSocket callbacks for real-time event broadcasting
   - Starts mesh monitor loop (periodic BATMAN/Reticulum polling)
5. **nginx** starts - Serves frontend at `http://myc3.local`
6. **User opens browser** - React app loads, connects WebSocket, displays P100

---

## Performance Targets

**Frontend (client-side):**
- <200ms initial page load (static files from nginx)
- ~15 FPS Canvas2D teletext rendering (sufficient for text UI)
- <100ms page navigation (client-side routing)

**Backend:**
- <50ms REST API response (in-memory MeshStore)
- <100ms WebSocket event propagation (radio event to client)
- <1s Meshtastic node discovery (PyPubSub callback)

**Mesh:**
- <1s message send latency (local)
- <5s multi-hop latency (3+ hops)

**Battery:**
- Idle (mesh only): 10-12 hours
- Active (map + messaging): 6-8 hours

---

## Failure Modes & Recovery

**Radio Failure:**
- MeshtasticService logs warning, marks nodes as offline
- MeshStore retains last known state
- Auto-retry on service restart

**GPS Loss:**
- Last known position cached
- Nodes display without coordinates (position: null)

**Backend Crash:**
- systemd auto-restarts `myc3lium-backend.service`
- MeshStore repopulates from data source on startup
- WebSocket clients auto-reconnect (exponential backoff, max 10 attempts)

**Low Battery:**
- Battery metrics tracked from Meshtastic device reports
- Future: ECO mode at 30%, ULTRA_SAVE at 15%, graceful shutdown at 5%

---

## Future Expansion

**Phase 6: Configuration System** (in progress)
- TOML-based user configuration
- Web UI config pages (P600 series)
- First-boot setup wizard

**Phase 7: SDR Integration** (deferred - no hardware)
- SoapySDR waterfall shader
- Satellite pass prediction + auto-capture
- Custom map overlay pipeline

**Phase 8-10: Expansion Nodes**
- HYPHA handheld prototype (ESP32)
- FROND camera node
- RHIZOME environmental sensor pods

**Phase 11: LLM Agents**
- llama.cpp local inference
- Natural language mesh queries (P800 series)
- Sensor data analysis + report generation

---

## Dependencies

**Frontend:**
- React 18, react-router-dom
- Vite (build + dev server)
- Zustand (state management)
- Zod (runtime validation)
- TypeScript (strict mode)

**Backend:**
- FastAPI, uvicorn
- Pydantic (models + settings)
- meshtastic (>=2.0.0, PyPubSub integration)
- RNS (Reticulum Network Stack) - optional, graceful fallback
- LXMF (messaging over Reticulum) - optional

**System:**
- nginx (reverse proxy + static files)
- rnsd (Reticulum daemon)
- gpsd (GPS daemon)
- BATMAN-adv (Layer 2 mesh routing)
- ufw (firewall)

---

## Configuration

**Current:**
- Backend: Pydantic Settings loaded from environment variables + `.env` file
- Key settings: `MYC3LIUM_USE_LIVE_DATA`, `MESHTASTIC_API_KEY`, `MYC3LIUM_CORS_ORIGINS`
- Reticulum: Config file at `/home/myc3lium/.reticulum/config`

**Planned (Phase 6):**
- TOML-based user config at `/opt/myc3lium/config/myc3lium.toml`
- REST API for config read/write (`/api/config`)
- Web UI configuration pages (P600 series)
- First-boot setup wizard

---

## Development vs Production

**Development (on Mac):**
- `MockMeshDataSource` with simulated Anchorage-area nodes
- Meshtastic service starts if USB radio connected, otherwise skipped
- Reticulum unavailable (graceful no-op)
- Frontend dev server on `:5173`, backend on `:8000`

**Production (Pi 4):**
- `LiveDataSource` with real BATMAN + Reticulum data
- MeshtasticService connects to serial radio
- nginx serves frontend, proxies API
- systemd manages all services
- Accessible at `http://myc3.local`

---

**Next:** See [MYC3LIUM_BIBLE_V3.md](MYC3LIUM_BIBLE_V3.md) for complete project specification.
