# MYC3LIUM WebUI Development Roadmap

**Goal:** Build a teletext-style tactical interface with CRT shader effects, accessible via browser on any device in the mesh.

**Tech Stack:** FastAPI (backend) + Three.js (rendering) + WebSocket (live data)

**Design Reference:** BBC Ceefax teletext + tactical UIs + cyberpunk aesthetics

---

## Visual Design Principles (From Mockups)

### Color Palette
```
Primary:
#00FFFF  Cyan (active threads, good status)
#FF00FF  Magenta (warnings, highlights)
#FFFF00  Yellow (alerts, callsigns)
#00FF00  Green (status indicators, telemetry)

Secondary:
#0080FF  Blue (info panels, borders)
#FFFFFF  White (primary text)
#808080  Gray (secondary text, inactive)
#000000  Black (background)

Accent:
#FF8000  Orange (degraded status)
#FF0000  Red (critical alerts)
```

### Typography
- **Font:** IBM VGA 8×16 or Perfect DOS VGA 437
- **Rendering:** Bitmap font atlas (pre-rendered characters)
- **Grid:** 80 columns × 25 rows (classic teletext)
- **Character size:** 8×16 pixels (scalable)

### CRT Effects (From Test Layout Mockup)
```
Effects Stack:
├── Scanlines (horizontal lines, 50% opacity)
├── Phosphor glow (RGB color separation)
├── Vignette (darker edges)
├── Chromatic aberration (RGB offset)
├── Curvature (barrel distortion, subtle)
├── Flicker (random brightness variation, 1-2%)
└── Bloom (bright text glow)
```

**Shader Modes:**
- **LINEAR:** Straight scanlines, no curvature
- **RADI:** Radial gradient vignette
- **CONI:** Conical gradient (vintage monitor)
- **DIAM:** Diamond-shaped vignette

### Layout System (Multi-Panel)

**Responsive Grid (Based on Image 3):**
```
Desktop (1920×1080+):
┌─────────────────┬─────────────────┐
│  Panel 1        │  Panel 2        │
│  (50% width)    │  (50% width)    │
├─────────────────┼─────────────────┤
│  Panel 3        │  Panel 4        │
│  (50% width)    │  (50% width)    │
└─────────────────┴─────────────────┘

Tablet (768×1024):
┌─────────────────┐
│  Panel 1 (full) │
├─────────────────┤
│  Panel 2 (full) │
├─────────────────┤
│  Panel 3 (full) │
└─────────────────┘

Mobile (Phone):
Single panel view, swipe to navigate
```

---

## Phase 1: Core Rendering Engine (Week 1-2)

### Objective
Build Three.js teletext character renderer with CRT shader pipeline.

### Tasks

**1.1 Three.js Scene Setup**
- [ ] Create WebGL canvas (full viewport)
- [ ] Set up orthographic camera (2D rendering)
- [ ] Configure scene + renderer
- [ ] Add window resize handler

**1.2 Bitmap Font Atlas**
- [ ] Generate font atlas from IBM VGA 8×16 font
- [ ] Create texture (256 chars, 8×16 each)
- [ ] Load as Three.js texture
- [ ] Implement character lookup (ASCII → UV coords)

**1.3 Character Grid Renderer**
- [ ] Create instanced mesh (80×25 quads)
- [ ] Vertex shader: position characters in grid
- [ ] Fragment shader: sample font atlas
- [ ] Support foreground/background colors (8-bit palette)

**1.4 CRT Shader Pass**
- [ ] Set up EffectComposer (post-processing)
- [ ] Scanline shader (horizontal lines)
- [ ] Phosphor glow shader (RGB separation)
- [ ] Vignette shader
- [ ] Chromatic aberration
- [ ] Screen curvature (barrel distortion)
- [ ] Bloom pass (selective glow)
- [ ] Combine all passes

**Deliverable:** Static teletext page with CRT effects (no data, just rendering)

---

## Phase 2: Backend API (Week 2-3)

### Objective
FastAPI server providing real-time mesh data.

### Tasks

**2.1 FastAPI Setup**
- [ ] Create FastAPI app
- [ ] CORS configuration (allow mesh access)
- [ ] Serve static files (WebUI)
- [ ] Health check endpoint

**2.2 Data Models (Pydantic)**
```python
class Node:
    id: str              # "SPORE-01"
    callsign: str        # "Nexus"
    type: str            # "SPORE", "HYPHA", "FROND", etc.
    position: tuple      # (lat, lon, alt)
    battery: int         # 0-100%
    status: str          # "ONLINE", "DEGRADED", "OFFLINE"
    
class Thread:
    src: str             # Source node ID
    dst: str             # Destination node ID
    radio: str           # "LoRa", "HaLow", "WiFi"
    rssi: int            # Signal strength (dBm)
    quality: str         # "GOOD", "FAIR", "DEGRADED"
    
class SensorReading:
    node: str            # "RHIZOME-02"
    timestamp: int       # Unix timestamp
    temp: float          # Celsius
    humidity: int        # Percent
    pressure: int        # hPa
    aqi: int             # Air quality index
```

**2.3 REST Endpoints**
```python
GET  /api/status              # System overview
GET  /api/mesh/nodes          # All nodes
GET  /api/mesh/threads        # All connections
GET  /api/mesh/topology       # Full graph (nodes + threads)
GET  /api/sensors             # Latest sensor readings
GET  /api/satellite/passes    # Upcoming passes
GET  /api/messages            # LXMF inbox
POST /api/messages/send       # Send message
GET  /api/camera/streams      # Active FROND streams
```

**2.4 WebSocket (Live Updates)**
```python
WS   /ws
# Push events:
- mesh.node.update
- mesh.thread.update
- sensor.reading
- message.received
- satellite.aos (acquisition of signal)
- satellite.los (loss of signal)
```

**2.5 Reticulum Integration**
- [ ] Connect to Reticulum daemon (RNS)
- [ ] Query mesh topology
- [ ] Subscribe to node/thread events
- [ ] LXMF message handling
- [ ] Convert RNS data → API models

**Deliverable:** Working API with mock data (real Reticulum integration in Phase 5)

---

## Phase 3: Frontend Framework (Week 3-4)

### Objective
React app with page system and live data.

### Tasks

**3.1 React Setup**
- [ ] Create React app (Vite)
- [ ] Three.js integration
- [ ] WebSocket client
- [ ] State management (Zustand or Context)

**3.2 Page System**
```javascript
const pages = {
  100: StatusPage,      // System overview
  200: LatticeMapPage,  // Mesh topology graph
  201: NodeListPage,    // All nodes table
  300: MessagesPage,    // LXMF inbox
  400: SensorGridPage,  // Telemetry from RHIZOME nodes
  500: CameraPage,      // FROND live streams
  600: SatellitePage,   // Pass predictions
  700: NodeLogPage,     // Event log
  800: CommandPage      // CLI interface
};
```

**3.3 Navigation**
- [ ] Number key input (P100, P200, etc.)
- [ ] Touch/click navigation
- [ ] Breadcrumb trail
- [ ] Page history (back/forward)

**3.4 Component Library**
```javascript
// Teletext Components
<TeletextPanel>         // Bordered panel with header
<TeletextText>          // Colored text block
<StatusBar>             // Horizontal colored bar
<ProgressBar>           // Battery/signal strength
<Sparkline>             // Mini graph (telemetry)
<CommandInput>          // Bottom command bar
<NodeBadge>             // Node ID + callsign + status
<ThreadIndicator>       // Connection quality dots
```

**Deliverable:** Multi-page UI with mock data and page navigation

---

## Phase 4: Advanced Visualizations (Week 4-5)

### Objective
Build complex data visualizations (topology graph, sensor grids, camera streams).

### Tasks

**4.1 Lattice Topology Graph (P200)**

**Based on Image 3 (Top-Left Panel):**
```
Features:
- Nodes as colored squares (color = type)
- Threads as lines (color = quality)
- Callsigns next to nodes
- Radio type labels on threads
- GPS coordinates below nodes
- Animated data flow (particles along threads)
```

**Implementation:**
- [ ] Force-directed graph layout (D3.js or custom)
- [ ] Render with Three.js (2D in 3D space)
- [ ] Node click → show details
- [ ] Thread hover → show RSSI/latency
- [ ] Animated "data packets" along threads

**4.2 Sensor Grid (P400)**

**Based on Image 3 (Bottom-Left Panel):**
```
Table Layout:
NODE          TEMP  HUMIDITY  PRESSURE  AQI   STATUS
SPORE-01      6.4°C   87%     1013mb   <15   [sparkline]
RHIZOME-02//    6.3°C   69%     1007mb   <10   [sparkline]
Ravine Stream
```

**Implementation:**
- [ ] Real-time table updates
- [ ] Color-coded status (green = good, yellow = warning, red = critical)
- [ ] Sparklines (mini temp/humidity graphs)
- [ ] Scrollable if >10 sensors
- [ ] Click row → detailed sensor view

**4.3 Live Camera Stream (P500)**

**Based on Image 3 (Top-Right Panel):**
```
Features:
- JPEG stream from FROND node
- Overlay: Node ID, GPS, signal strength
- Stream controls: pause, snapshot, quality
```

**Implementation:**
- [ ] Motion JPEG stream (HTTP multipart)
- [ ] Canvas overlay (HUD with telemetry)
- [ ] Auto-reconnect on disconnect
- [ ] Thumbnail mode (low bandwidth)
- [ ] Fullscreen toggle

**4.4 Node Log (P700)**

**Based on Image 3 (Bottom-Right Panel):**
```
Real-time event log:
- THREAD UP HYPHA-03 : PROPAGATE = 06:00 NEAR CASTLE LAKE
- THREAD REGENERATE FROND-02 : ROUTE PATH UPDATED
- SENSOR PUSH RHIZOME-02 : TEMP DETECTED 6.4°C
```

**Implementation:**
- [ ] Auto-scrolling log (newest at bottom)
- [ ] Color-coded event types
- [ ] Filter by node/event type
- [ ] Export log to file
- [ ] Max 1000 entries (ring buffer)

**Deliverable:** All 4 panel types functional with live data

---

## Phase 5: Reticulum Integration (Week 5-6)

### Objective
Replace mock data with real Reticulum mesh data.

### Tasks

**5.1 Reticulum Python API**
- [ ] Install RNS on SPORE (Pi 4)
- [ ] Configure interfaces (LoRa, HaLow, WiFi)
- [ ] Start Reticulum daemon
- [ ] Test connectivity

**5.2 API Integration**
```python
# backend/reticulum_client.py
class ReticulumClient:
    def get_nodes(self) -> List[Node]:
        # Query RNS for known identities
        pass
    
    def get_threads(self) -> List[Thread]:
        # Get active links
        pass
    
    def send_message(self, dest: str, text: str):
        # LXMF send
        pass
    
    def on_message_received(self, callback):
        # Subscribe to LXMF
        pass
```

**5.3 WebSocket Event Push**
- [ ] RNS event → WebSocket → Frontend
- [ ] Node discovery → `mesh.node.update`
- [ ] Link quality change → `mesh.thread.update`
- [ ] Message received → `message.received`

**5.4 Field Testing**
- [ ] Deploy SPORE + HYPHA-A (HaLow)
- [ ] Verify WebUI shows live topology
- [ ] Send test messages
- [ ] Check position updates
- [ ] Validate battery status

**Deliverable:** WebUI connected to real Reticulum mesh

---

## Phase 6: Additional Features (Week 6-7)

### Objective
Add satellite tracking, SDR waterfall, LLM interface.

### Tasks

**6.1 Satellite Pass Predictor (P600)**
```
Display:
- Next pass countdown
- Satellite name (NOAA 19, METEOR M2)
- Max elevation angle
- AOS/LOS times
- Auto-capture toggle
```

**Implementation:**
- [ ] pyorbital TLE tracking
- [ ] Calculate passes for next 48h
- [ ] WebSocket push on AOS/LOS
- [ ] Integration with SatDump

**6.2 RF Spectrum Waterfall (P501)**
```
Display:
- Live SDR waterfall (frequency vs time)
- Signal detection markers
- Zoom/pan controls
- Center frequency display
```

**Implementation:**
- [ ] SoapySDR FFT data → WebSocket
- [ ] Canvas-based waterfall renderer
- [ ] Color gradient (blue = low, red = high)
- [ ] Click to tune

**6.3 LLM Chat Interface (P800)**
```
Chat UI:
> What's the status of RHIZOME-02?

RHIZOME-02 // "Ravine Stream" is ONLINE.
Last report: 09:41 (1 min ago).
Temp: 6.3°C, Humidity: 69%, Pressure: 1007mb.
Battery: 72%. Thread GOOD.
```

**Implementation:**
- [ ] Text input at bottom
- [ ] Message history (chat log)
- [ ] llama.cpp backend
- [ ] Context: mesh status, sensor data, logs
- [ ] Natural language queries

**Deliverable:** Full feature set complete

---

## Phase 7: Polish & Optimization (Week 7-8)

### Objective
Performance tuning, mobile optimization, kiosk mode.

### Tasks

**7.1 Performance Optimization**
- [ ] Reduce WebSocket message size (CBOR instead of JSON)
- [ ] Lazy load pages (code splitting)
- [ ] Throttle render updates (60 FPS cap)
- [ ] Optimize shader passes (combine where possible)
- [ ] GPU texture compression

**7.2 Mobile Responsive**
- [ ] Single-panel layout on small screens
- [ ] Touch gestures (swipe between pages)
- [ ] Reduced CRT effects (save battery)
- [ ] Simplified UI (fewer details)

**7.3 Kiosk Mode (SPORE Physical Display)**
```bash
# Chromium kiosk launch script
chromium-browser \
  --kiosk \
  --app=http://localhost:8080 \
  --start-fullscreen \
  --disable-infobars \
  --no-first-run \
  --disable-session-crashed-bubble
```

**7.4 Accessibility**
- [ ] Keyboard navigation (tab, arrows, enter)
- [ ] High contrast mode (disable CRT effects)
- [ ] Screen reader support (ARIA labels)
- [ ] Adjustable font size

**7.5 Error Handling**
- [ ] WebSocket reconnect logic
- [ ] Offline mode (cached data)
- [ ] API timeout handling
- [ ] Graceful degradation (fallback to static data)

**Deliverable:** Production-ready WebUI

---

## Tech Stack Details

### Frontend
```
React 18 (UI framework)
Three.js (WebGL rendering)
EffectComposer (post-processing)
Zustand (state management)
Vite (build tool)
WebSocket API (live data)
```

### Backend
```
FastAPI (API server)
Uvicorn (ASGI server)
Pydantic (data validation)
RNS (Reticulum Network Stack)
LXMF (messaging)
pyorbital (satellite tracking)
SoapySDR (RF data)
llama.cpp (LLM inference)
```

### Deployment
```
SPORE (Raspberry Pi 4):
├── systemd service (FastAPI backend)
├── nginx reverse proxy (optional)
└── Chromium kiosk mode (physical display)

HaLow broadcast:
- WebUI accessible at http://spor3.local:8080
- Any device in mesh can connect
```

---

## File Structure

```
myc3lium-webui/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── models.py               # Pydantic models
│   ├── reticulum_client.py     # RNS integration
│   ├── websocket_handler.py    # WebSocket server
│   ├── satellite_tracker.py    # pyorbital wrapper
│   └── sdr_handler.py          # SoapySDR interface
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React app
│   │   ├── pages/
│   │   │   ├── P100_Status.jsx
│   │   │   ├── P200_Lattice.jsx
│   │   │   ├── P300_Messages.jsx
│   │   │   ├── P400_Sensors.jsx
│   │   │   ├── P500_Camera.jsx
│   │   │   ├── P600_Satellite.jsx
│   │   │   ├── P700_Log.jsx
│   │   │   └── P800_LLM.jsx
│   │   ├── components/
│   │   │   ├── TeletextRenderer.jsx
│   │   │   ├── CRTShader.jsx
│   │   │   ├── LatticeGraph.jsx
│   │   │   ├── SensorGrid.jsx
│   │   │   └── CommandInput.jsx
│   │   ├── shaders/
│   │   │   ├── scanlines.frag
│   │   │   ├── phosphor.frag
│   │   │   ├── vignette.frag
│   │   │   └── curvature.vert
│   │   ├── fonts/
│   │   │   └── vga_8x16_atlas.png
│   │   └── store/
│   │       └── meshStore.js    # Zustand state
│   ├── public/
│   └── vite.config.js
├── deploy/
│   ├── systemd/
│   │   └── myc3lium-api.service
│   └── kiosk.sh                # Chromium kiosk script
└── README.md
```

---

## Milestones

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1-2  | Phase 1   | Three.js teletext renderer + CRT shaders |
| 2-3  | Phase 2   | FastAPI backend with mock data |
| 3-4  | Phase 3   | React frontend with page navigation |
| 4-5  | Phase 4   | Advanced visualizations (graph, sensors, camera) |
| 5-6  | Phase 5   | Reticulum integration (live data) |
| 6-7  | Phase 6   | Satellite, SDR, LLM features |
| 7-8  | Phase 7   | Polish, optimization, kiosk mode |

**Total:** 8 weeks part-time (15-20 hours/week)

---

## Design System Reference

### Panel Header
```
┌─ MYC3LIUM ─══─ LATTICE ACTIVE ─══─ 09:57 ─┐
```

### Status Bar Colors
```
GOOD:     █████████████ (cyan)
FAIR:     █████▓▓▓▓▓▓▓▓ (yellow)
DEGRADED: ███▒▒▒▒▒▒▒▒▒▒ (orange)
OFFLINE:  ░░░░░░░░░░░░░ (gray)
```

### Node Badges
```
◉ SPORE-01 // "Nexus"     (cyan square = active)
□ HYPHA-03 // "Ranger"    (gray square = offline)
```

### Command Bar
```
COMMAND: THREAD LIST | SENSOR GRID | STREAM 89.1 ▐▌▐
```

---

## Shader Effects Configuration

**CRT Settings (Adjustable via P605):**
```javascript
const crtConfig = {
  scanlines: {
    enabled: true,
    opacity: 0.5,
    count: 480  // Match display height
  },
  phosphor: {
    enabled: true,
    rOffset: 1.0,   // Red shift
    gOffset: 0.0,   // Green shift
    bOffset: -1.0   // Blue shift
  },
  vignette: {
    enabled: true,
    intensity: 0.3,
    type: 'radial'  // 'radial', 'linear', 'conic', 'diamond'
  },
  curvature: {
    enabled: true,
    amount: 0.05    // Subtle barrel distortion
  },
  bloom: {
    enabled: true,
    threshold: 0.8,
    intensity: 1.2
  },
  flicker: {
    enabled: true,
    amount: 0.02
  }
};
```

---

## Next Steps

1. **Approve roadmap** - Confirm this matches vision
2. **Set up project structure** - Create repo, scaffold files
3. **Week 1 kickoff** - Start Phase 1 (Three.js renderer)
4. **Weekly check-ins** - Review progress, adjust timeline

**Ready to start building?** 🍄🔥

---

**END WEBUI ROADMAP**

*Last updated: 2026-03-15*  
*Status: Design approved, ready for implementation*
