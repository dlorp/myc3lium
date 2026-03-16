# MYC3LIUM — Implementation Plan

**Document version:** 1.0  
**Last updated:** 2026-03-16  
**Status:** Active development — Phase 1 complete, Phase 2 in progress

---

## Executive Summary

MYC3LIUM is a portable off-grid mesh intelligence terminal built on Raspberry Pi 4 hardware with multi-band radio capability. The system renders a teletext-inspired tactical GUI through a browser-based WebUI (React + Three.js + FastAPI), providing mesh networking, satellite intelligence, RF monitoring, tactical mapping, and encrypted messaging.

This plan covers 12 weeks of development across 4 phases, building the 14-page WebUI to match design mockups and progressively connecting to real hardware. The approach is **GUI-first**: all pages are built with mock data before hardware integration begins, enabling parallel frontend and backend work streams.

**Current state:** Repository scaffold complete, FastAPI backend with WebSocket support operational, Three.js teletext grid renderer with CRT shaders functional. Development servers run at `localhost:3000` (frontend) and `localhost:8000` (backend).

---

## Architecture Overview

```
Frontend (React + Vite + Three.js)
  ├── TeletextGrid renderer (40×25 character grid)
  ├── CRT shader pipeline (scanlines, bloom, vignette)
  ├── Page system (P100–P800, number-key navigation)
  └── WebSocket client (live mesh data)

Backend (FastAPI + Uvicorn)
  ├── REST API (/api/mesh, /api/sensors, /api/messages, etc.)
  ├── WebSocket server (/ws — push events)
  ├── Pydantic v2 models (Node, Thread, SensorReading)
  └── Integration modules (Reticulum, SoapySDR, gpsd)
```

### Agent Orchestration System

The backend operates as a **nervous system** with specialized agents managing each subsystem:

- **RFAgent** - LoRa/HaLow radio configuration, RSSI monitoring, retransmit management
- **SDRAgent** - RTL-SDR tuning, spectrum scanning, signal detection
- **SensorAgent** - RHIZOME telemetry aggregation, anomaly detection
- **MessageAgent** - LXMF queue management, store-and-forward, encryption
- **SatelliteAgent** - Pass tracking via Gpredict, SatDump scheduling
- **LLMAgent** - Query processing, sensor data analysis, command parsing

Each agent runs as an asyncio task. The WebUI can spawn, kill, monitor, and configure agents through the API. This enables fine-grained control and independent restart of subsystems without full daemon restart.

---

## Completed Work

### PR #1 — Repository Scaffold ✅ DONE

**What:** Project foundation with CI/CD pipeline, linting, testing infrastructure.

**Why:** Establishes consistent development workflow and continuous quality checks before any feature code lands.

**How:**
- Frontend: React 18 + Vite scaffold, ESLint config, Vitest test runner
- Backend: FastAPI project structure, ruff + mypy linting, pytest + pytest-asyncio
- CI/CD: GitHub Actions workflow for lint, type-check, and test on every PR
- Scripts: `setup-dev.sh` and `run-dev.sh` for local development

### PR #2 — API Core + WebSocket ✅ DONE

**What:** FastAPI backend with REST endpoints, Pydantic models, WebSocket server, and mock data layer.

**Why:** Provides the data contract between frontend and backend. Mock data enables frontend development without hardware dependencies.

**How:**
- REST endpoints: `/api/status`, `/api/mesh/nodes`, `/api/mesh/threads`, `/api/sensors`, `/api/messages`
- WebSocket at `/ws` with push events: `mesh.node.update`, `mesh.thread.update`, `sensor.reading`, `message.received`
- Pydantic v2 models: Node, Thread, SensorReading with full validation
- Security hardening: connection limits, message size limits, string length validation, CORS configuration via config

### PR #3 — Teletext Grid Renderer ✅ DONE

**What:** Three.js-based teletext character grid with CRT shader post-processing pipeline.

**Why:** The core rendering engine that all page content displays through. Establishes the visual identity — teletext aesthetic with phosphor glow, scanlines, and vignette effects.

**How:**
- TeletextGrid React component: instanced mesh rendering of 40×25 character grid
- Font atlas: IBM VGA 8×16 bitmap font loaded as GPU texture
- CRT shader pipeline via EffectComposer: scanlines, phosphor glow, chromatic aberration, barrel distortion, bloom
- Configurable shader modes: LINEAR, RADIAL, CONIC, DIAMOND vignette types
- Test coverage with mock Canvas for CI

---

## Phase 2 — Page Framework + Core Pages (Weeks 3–5)

Build the page navigation system and the three foundational pages. All pages render through the teletext grid with mock data.

### PR #4 — Page Router + Navigation System

**What:** Client-side page routing with number-key and touch navigation across the full page map (P100–P800).

**Why:** Every subsequent page depends on the navigation framework. Users navigate by typing page numbers (teletext-style) or tapping touch zones.

**How:**
- React Router integration with page-number URL scheme (`/p/100`, `/p/200`, etc.)
- Zustand store for navigation state: current page, history stack, breadcrumb trail
- Number-key input handler: captures digit sequences, navigates on timeout or Enter
- Touch zone component: clickable regions within the teletext grid
- Page transition animations (fade/wipe rendered through shader uniforms)
- Bottom navigation bar component with contextual page links
- Keyboard shortcuts: ESC (back), F1–F8 (quick access), 0 (main menu)
- Mobile: swipe gestures for page history navigation

**Dependencies:** PR #3 (teletext grid)  
**Estimated effort:** 3–4 days

### PR #5 — P100 Dashboard (Main Menu)

**What:** System overview dashboard showing lattice status, radio health, battery, and navigation entry points to all subsystems.

**Why:** First page users see on boot. Provides at-a-glance system health and serves as the navigation hub.

**How:**
- Layout matching `mockups/status-dashboard.html` design
- Menu items: [200] Mesh Network, [300] Messaging, [400] Tactical Map, [500] Intelligence, [600] Configuration
- Live status summary per section (node count, unread messages, next sat pass, battery level)
- Radio status bars: LoRa, HaLow, WiFi — color-coded (cyan=good, yellow=fair, red=degraded, gray=offline)
- GPS lock indicator in header bar
- Clock display (from system time, later from GNSS)
- WebSocket subscription for real-time status updates
- Touch zones: tap menu item → navigate, tap radio bars → P103 radio detail

**Dependencies:** PR #4 (page router)  
**Estimated effort:** 2–3 days

### PR #6 — P200 Lattice Map (Mesh Topology)

**What:** Force-directed graph visualization of mesh topology showing nodes, threads (links), and routing paths.

**Why:** Core operational view. Operators need to see network topology, link quality, and routing at a glance to make deployment decisions.

**How:**
- Layout matching `mockups/lattice-map.html` design
- Force-directed graph layout (custom implementation or D3-force adapted for Three.js)
- Nodes rendered as colored squares: color = node type (SPORE=cyan, HYPHA=green, FROND=yellow, RHIZOME=blue)
- Threads rendered as lines: color = quality (cyan=GOOD, yellow=FAIR, orange=DEGRADED, gray=STORE-FORWARD)
- Callsign labels next to nodes, radio type labels on threads
- Animated data flow particles along active threads
- Click node → expand detail panel (ID, callsign, position, battery, uptime, radio info)
- Click thread → show RSSI, latency, hop count
- Route table display below graph
- Traffic summary bars (messages, data, overhead — last hour)
- Sub-pages: P201 (node list table), P202 (link quality matrix), P203 (traffic statistics)
- WebSocket: `mesh.node.update` and `mesh.thread.update` events update graph in real-time

**Dependencies:** PR #4 (page router), PR #2 (mesh API endpoints)  
**Estimated effort:** 5–7 days

---

## Phase 3 — Feature Pages (Weeks 5–8)

Build out remaining pages. Each page is self-contained with mock data, enabling parallel development.

### PR #7 — P300 Messaging (Inbox + Compose)

**What:** LXMF messaging interface with inbox, compose, channel views, and message history.

**Why:** Primary communication interface between mesh nodes. Operators send and receive encrypted messages through the lattice.

**How:**
- P300 Inbox: message list with sender, timestamp, transport route, preview text
- P301 Compose: recipient selector, transport mode (Auto/LoRa/HaLow/WiFi), message editor, character counter, encryption indicator
- P302 Channels: group message channels
- P303 History: full message archive with search
- Layout matching `mockups/p300-messages.html`
- Unread message count in header
- Touch zones: tap message → expand, [R] reply → P301 with recipient pre-filled
- WebSocket: `message.received` event appends to inbox
- Backend: `POST /api/messages/send` for outbound messages

**Dependencies:** PR #4 (page router)  
**Estimated effort:** 4–5 days

### PR #8 — P400 Tactical Map

**What:** Full-screen map view with offline MBTiles rendering, GPS position, mesh node overlay, and waypoint management.

**Why:** Primary operational interface for field deployments. Operators need spatial awareness of their position, team positions, and waypoints.

**How:**
- P400 Main map: MBTiles tile rendering quantized to teletext color palette via shader
- GPS position marker (◉) with live updates
- Mesh node overlay (● with color = signal strength)
- Waypoint markers (★) with tap-to-detail
- Zoom/pan via touch gestures and keyboard
- Layer toggles: [√]OSM [√]Nodes [ ]Satellite
- Full-screen mode: tap map → hide all chrome
- P401 Waypoint manager: list, create, edit, share, navigate
- P402 Routes: point-to-point routing between waypoints
- P403 Layers: toggle map overlays
- P404 Custom maps: import external map data
- Layout matching `mockups/original-full-mockup.html` map panel
- Tile loader with LRU cache for smooth panning

**Dependencies:** PR #4 (page router)  
**Estimated effort:** 7–10 days

### PR #9 — P500 Intelligence (Satellite + Camera)

**What:** Satellite pass tracker with auto-capture scheduling, and camera stream viewer for FROND nodes.

**Why:** Intelligence gathering is a core mission capability. Satellite imagery provides weather data; camera streams provide real-time situational awareness.

**How:**
- P500 Satellite tracker: next pass countdown, AOS/LOS times, max elevation, auto-capture toggle
- Pass prediction display for NOAA 19, METEOR-M N2-3
- Last capture preview (JPEG thumbnail in teletext palette)
- Layout matching `mockups/p600-satellite.html`
- P503 Camera: MJPEG stream display from FROND nodes
- HUD overlay: node ID, GPS position, signal strength, timestamp
- Stream controls: pause, snapshot, quality toggle
- Auto-reconnect on connection drop
- Thumbnail mode for low bandwidth
- Layout matching `mockups/p500-camera.html`

**Dependencies:** PR #4 (page router)  
**Estimated effort:** 5–6 days

### PR #10 — P501 RF Spectrum + P700 Sensor Grid

**What:** SDR waterfall display for RF monitoring, and environmental sensor telemetry grid.

**Why:** RF awareness enables spectrum monitoring and signal detection. Sensor data from RHIZOME nodes provides environmental intelligence.

**How:**
- P501 RF Waterfall: canvas-based spectrum display, frequency/time axes, signal strength color gradient
- Frequency tuning controls, gain adjustment
- Detected signal markers with classification (LoRa, FSK, unknown)
- Layout matching `mockups/p501-spectrum-improved.html`
- P502 Signal log: detected signal history with timestamps
- P700 Sensor grid: table view of all RHIZOME sensor data
- Columns: Node, Temp, Humidity, Pressure, AQI, Status
- Sparkline mini-graphs per sensor (last 24h trend)
- Color-coded status indicators
- Layout matching `mockups/p700-sensor-grid-improved.html` and `mockups/sensor-grid.html`
- WebSocket: `sensor.reading` events update grid in real-time

**Dependencies:** PR #4 (page router)  
**Estimated effort:** 5–7 days

### PR #11 — P600 Configuration + P800 Command Interface

**What:** System configuration pages for radio parameters, and command-line interface for advanced operations.

**Why:** Operators need to tune radio settings per deployment. The command interface provides direct system control for diagnostics and advanced operations.

**How:**
- P600 Radio config: LoRa (frequency, bandwidth, spreading factor, TX power), HaLow, WiFi mesh settings
- Input fields rendered as teletext form elements
- [APPLY] validates and restarts relevant daemons
- [TEST CONNECTION] verifies radio connectivity before applying
- P601 Reticulum config, P602 Meshtastic config, P603 SDR config, P604 Map config, P605 Display/shader settings
- P800 Command interface: single-line input, scrolling log output
- Command parser for mesh CLI commands (THREAD, PROPAGATE, SENSOR, LATTICE, MSG, etc.)
- Layout matching `mockups/p800-llm-improved.html`
- Command history (up/down arrows)
- Auto-complete for node IDs and commands

**LLM Backend (Phase 4):**
- Model: **Phi-3-mini-4k Q4 quantized** (~2.5GB) via llama.cpp
- Constraint: 4GB Pi 4 RAM requires Q4 quantization (leaves headroom for OS + SDR)
- Fallback: TinyLlama-1.1B Q4 (~700MB) for tighter memory environments
- Use cases: Natural language command parsing, sensor data summarization, tactical decision support
- P800 interface: chat-style input with LLM responses rendered in teletext grid

**Dependencies:** PR #4 (page router)  
**Estimated effort:** 5–6 days

---

## Phase 4 — Hardware Integration + Polish (Weeks 9–12)

Connect the WebUI to real hardware. Replace mock data with live feeds.

### PR #12 — Reticulum + LXMF Integration

**What:** Connect backend to Reticulum Network Stack for live mesh data and LXMF messaging.

**Why:** Replaces mock mesh data with real node discovery, link quality, and routing information from live radio hardware.

**How:**
- `backend/app/integrations/reticulum_client.py`: RNS daemon connection
- Query real mesh topology: known identities, active links, routing table
- Subscribe to RNS events → push via WebSocket
- LXMF message send/receive through Reticulum
- Interface configuration: LoRa (RNodeInterface), HaLow (AutoInterface), WiFi mesh (AutoInterface)
- Meshtastic bridge module for LoRa Meshtastic device compatibility
- Graceful degradation: if RNS unavailable, fall back to mock data with status indicator

**Dependencies:** PR #7 (messaging pages), PR #6 (lattice map)  
**Estimated effort:** 5–7 days

### PR #13 — SDR + Satellite Integration

**What:** Connect SoapySDR for live RF spectrum data and satellite pass auto-capture with SatDump decoding.

**Why:** Enables real-time spectrum monitoring and scheduled weather satellite image capture — core intelligence capabilities.

**How:**
- `backend/app/integrations/sdr_client.py`: SoapySDR interface for RTL-SDR + Ham It Up upconverter
- FFT computation → WebSocket push for waterfall display
- Signal detection pipeline: threshold-based marker generation
- Satellite pass prediction via pyorbital/TLE data
- Auto-capture workflow: pre-warm SDR → record at AOS → SatDump decode → georeferenced image
- Decoded satellite images available as map overlay tiles
- SDR power management: auto-disable when not in use

**Dependencies:** PR #10 (spectrum/sensor pages)  
**Estimated effort:** 5–7 days

### PR #14 — GPS + Map Tile Integration

**What:** Connect gpsd for live GNSS position and integrate offline MBTiles tile loading.

**Why:** Real position data drives the tactical map and provides GPS timestamps for all telemetry.

**How:**
- `backend/app/integrations/gps_client.py`: gpsd interface via LoRa HAT GNSS module
- Position updates pushed via WebSocket to frontend map
- GPS fix quality indicator in header bar
- MBTiles SQLite reader: load offline map tiles by zoom/x/y
- Web Mercator projection utilities: lat/lon ↔ tile coordinates
- Tile LRU cache for smooth pan/zoom performance
- ATAK CoT message bridge (FreeTAKServer compatible) for tactical overlay

**Dependencies:** PR #8 (map pages)  
**Estimated effort:** 4–5 days

### PR #15 — Mobile Optimization + Kiosk Mode

**What:** Responsive layout for mobile/tablet access and Chromium kiosk configuration for the Pi 4 physical display.

**Why:** The WebUI must be accessible from any device in the mesh (phones, tablets, laptops) and run as a kiosk on the SPORE's physical touchscreen.

**How:**
- Responsive breakpoints: Desktop (1920×1080+, multi-panel), Tablet (768×1024, stacked panels), Mobile (single panel, swipe navigation)
- Touch gesture handler: swipe between pages, pinch zoom on map
- Reduced CRT effects on mobile (battery savings)
- Kiosk launch script: `scripts/kiosk.sh` for Chromium fullscreen
- systemd service: `myc3lium-webui.service` for auto-start on boot
- Offline mode: service worker caches frontend assets
- WebSocket reconnect logic with exponential backoff

**Dependencies:** All page PRs complete  
**Estimated effort:** 3–4 days

### PR #16 — Performance + Security Hardening

**What:** Performance optimization, security audit, and production hardening.

**Why:** The system must run within the Pi 4's 4GB RAM envelope at 60 FPS while maintaining security in contested environments.

**How:**
- Frontend: code splitting per page, lazy loading, shader pass optimization, GPU texture compression
- Backend: CBOR encoding option for WebSocket messages (reduce bandwidth), connection pooling, rate limiting
- Security: CSP headers, input sanitization audit, WebSocket authentication tokens, no plaintext secrets in config
- Memory profiling: verify total system fits within 2GB (leaving headroom for OS + SDR)
- Render budget: 60 FPS target with all CRT effects on Pi 4 GPU
- Load testing: simulate 10 concurrent mesh events/second

**Dependencies:** All prior PRs  
**Estimated effort:** 3–4 days

---

## Timeline

```
Week 3   ████ PR #4: Page Router + Navigation
Week 3-4 ████ PR #5: P100 Dashboard
Week 4-5 ██████ PR #6: P200 Lattice Map
Week 5-6 █████ PR #7: P300 Messaging
Week 5-7 ████████ PR #8: P400 Tactical Map        ← parallel with PR #7
Week 6-7 █████ PR #9: P500 Intelligence
Week 7-8 █████ PR #10: P501 Spectrum + P700 Sensors ← parallel with PR #9
Week 7-8 █████ PR #11: P600 Config + P800 Command
Week 9-10 █████ PR #12: Reticulum Integration
Week 9-10 █████ PR #13: SDR + Satellite Integration ← parallel with PR #12
Week 10-11 ████ PR #14: GPS + Map Integration
Week 11   ███ PR #15: Mobile + Kiosk
Week 12   ███ PR #16: Performance + Security
```

### Milestones

| Week | Milestone | Validation |
|------|-----------|------------|
| 3 | **Navigation Live** | Page routing works, number-key input functional |
| 5 | **Core Pages Complete** | P100, P200 render with mock data, WebSocket updates working |
| 8 | **All Pages Complete** | Full 14-page WebUI functional with mock data on desktop |
| 10 | **Hardware Connected** | Reticulum mesh live, SDR streaming, GPS position updating |
| 12 | **Field Ready** | Kiosk mode on Pi 4, mobile responsive, security hardened |

---

## Parallel Work Streams

The GUI-first approach enables two independent work streams after Phase 2:

**Stream A — Frontend Pages (Weeks 5–8)**
- PRs #7–#11 can proceed in parallel
- Each page is self-contained with mock data
- No hardware dependencies

**Stream B — Hardware Drivers (Weeks 5–8, preparation)**
- Reticulum daemon setup and configuration
- SoapySDR driver testing with RTL-SDR hardware
- gpsd configuration with LoRa HAT GNSS
- These can be validated independently before integration PRs

**Integration (Weeks 9–12)** merges Stream A and Stream B, replacing mock data providers with real hardware clients.

---

## Next 3 Tasks to Start

These are ready to begin immediately:

1. **PR #4 — Page Router + Navigation System**  
   Foundation for all page work. Blocks everything in Phase 2+.

2. **PR #5 — P100 Dashboard**  
   First visible page. Validates the full render pipeline (teletext grid → page content → CRT effects).

3. **PR #6 — P200 Lattice Map**  
   Most complex visualization. Early start surfaces rendering challenges.

---

## PR Workflow

Every PR follows the What/Why/How format:

### Template

```markdown
## What
One-line description of what this PR adds or changes.

## Why
Business/technical justification. What problem does this solve?

## How
Implementation details. Key design decisions and trade-offs.

## Testing
- [ ] Unit tests pass
- [ ] Manual testing steps documented
- [ ] CI green (lint + type-check + test)

## Security Checklist
- [ ] No secrets or credentials in code
- [ ] Input validation on all user-facing endpoints
- [ ] WebSocket messages validated against schema
- [ ] No new dependencies without justification
- [ ] CORS configuration unchanged (or justified)
```

### Review Requirements

- All PRs require security review before merge
- CI must pass: ESLint (frontend), ruff + mypy (backend), full test suite
- PRs that touch WebSocket handlers require connection limit verification
- PRs that add dependencies require license and supply-chain review
- Integration PRs (Phase 4) require hardware test sign-off

---

## Dependencies and Blockers

### Technical Dependencies

| Dependency | Required By | Status |
|------------|-------------|--------|
| React Router | PR #4 | Available (npm) |
| Zustand | PR #4 | Available (npm) |
| D3-force (or custom) | PR #6 | Evaluate during PR #6 |
| MBTiles reader | PR #8, #14 | Needs implementation |
| pyorbital | PR #9, #13 | Available (pip) |
| RNS (Reticulum) | PR #12 | Available (pip), needs Pi 4 for testing |
| SoapySDR | PR #13 | Available, needs RTL-SDR hardware |
| gpsd | PR #14 | Available, needs LoRa HAT |

### Hardware Dependencies

| Hardware | Required By | Status |
|----------|-------------|--------|
| Raspberry Pi 4 (4GB) | PR #15, #16 | Ordered |
| Waveshare SX1262 LoRa HAT | PR #12, #14 | Ordered |
| Heltec HT-HC01P (WiFi HaLow) | PR #12 | Ordered |
| Nooelec NESDR Smart XTR v2 | PR #13 | Ordered |
| Ham It Up Plus (upconverter) | PR #13 | Ordered |
| 7–10" touchscreen | PR #15 | Ordered |
| 21700 battery HAT | PR #15 | Ordered |

### Potential Blockers

- **Three.js performance on Pi 4 GPU:** CRT shader pipeline may need optimization for VideoCore VI. Mitigation: profile early in Phase 3, reduce shader passes if needed.
- **WiFi HaLow driver support:** HT-HC01P Linux driver maturity uncertain. Mitigation: 802.11s mesh works without HaLow; HaLow is additive.
- **Memory budget:** Full stack must fit in ~2GB to leave headroom. Mitigation: memory profiling in PR #16, CBOR encoding reduces WebSocket overhead.

---

## Design References

All page implementations should match the mockups in `/mockups/`:

| Page | Primary Mockup | Secondary Reference |
|------|---------------|---------------------|
| P100 | `status-dashboard.html` | `myc3lium-complete.html` |
| P200 | `lattice-map.html` | `enhanced-full-mockup.html` |
| P300 | `p300-messages.html` | — |
| P400 | `original-full-mockup.html` | `myc3lium-complete.html` |
| P500 | `p500-camera.html` | `p600-satellite.html` |
| P501 | `p501-spectrum-improved.html` | `p501-spectrum.html` |
| P600 | (follow PAGES.md spec) | — |
| P700 | `p700-sensor-grid-improved.html` | `sensor-grid.html` |
| P800 | `p800-llm-improved.html` | `p800-llm-chat.html` |

---

## Color Palette Reference

```
Primary:
  #00FFFF  Cyan     — active threads, good status, SPORE nodes
  #FF00FF  Magenta  — warnings, highlights
  #FFFF00  Yellow   — alerts, callsigns
  #00FF00  Green    — telemetry, status indicators

Secondary:
  #0080FF  Blue     — info panels, borders
  #FFFFFF  White    — primary text
  #808080  Gray     — secondary text, inactive
  #000000  Black    — background

Accent:
  #FF8000  Orange   — degraded status
  #FF0000  Red      — critical alerts
```

---

> `recovered_note: "The implementation proceeds. The lattice will grow."`
