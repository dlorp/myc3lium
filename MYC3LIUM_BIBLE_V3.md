# MYC3LIUM — Project Bible v3

**Tagline:** Resilient Off-Grid Lattice — portable-first, operator-centric, sensor-rich, intelligence-capable.

**Last Updated:** 2026-03-15

---

## Executive Summary

**MYC3LIUM** (my-SEE-lee-um) is a portable off-grid communication lattice designed for field operations, intelligence gathering, and resilient networking in contested or infrastructure-denied environments.

**Core capabilities:**
- Triple-radio mesh (LoRa, WiFi HaLow, 802.11s)
- SDR intelligence collection (satellite, RF spectrum)
- Encrypted messaging (Reticulum LXMF + Meshtastic)
- Tactical mapping (ATAK integration)
- Environmental sensor aggregation
- Local LLM agents for data parsing and natural language interface
- Teletext-style operator interface with modern shader rendering

**Philosophy:** Inspired by distributed biological networks, MYC3LIUM creates autonomous, self-healing communication lattices that persist through infrastructure loss and adapt to hostile environments.

---

## Philosophy & Design Principles

### 1. Decentralization
No node is authoritative. Every node contributes routing awareness. Network topology emerges from local decisions.

### 2. Adaptation
Routing adjusts automatically when links degrade. Multi-band radios allow graceful failover across transport layers.

### 3. Persistence
Nodes tolerate network fragmentation and reconnect without operator intervention. Store-and-forward ensures message delivery despite intermittent connectivity.

### 4. Low Signature
Nodes operate quietly with opportunistic routing and multi-band capability. Passive monitoring modes (GHOST) minimize RF footprint.

### 5. Field Resilience
Hardware and software designed for off-grid operation. Battery-powered portability, offline-first architecture, encrypted-by-default communications.

### 6. Intelligence-Native
Intelligence gathering (SIGINT, sensor fusion, satellite) is first-class, not bolted-on. Local LLM agents parse and contextualize data streams.

### 7. Operator-Centric
Terse commands, tactical interface, minimal cognitive load. System assumes technical operator under time pressure.

---

## System Architecture

### Layered Stack

```
┌─────────────────────────────────────┐
│  Operator Interface (Teletext GUI)  │
│  + Local LLM Agents                 │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│  ATAK Integration & TAK Overlay     │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│  Reticulum Encrypted Overlay        │
│  (Identity, LXMF, Store-Forward)    │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│  BATMAN-adv Layer 2 Routing         │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│  802.11s / WiFi HaLow / LoRa        │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│  SDR Physical Layer (300Hz-2.3GHz)  │
└─────────────────────────────────────┘
```

**Graceful degradation:** Each layer can operate independently if others fail. If Reticulum overlay is unavailable, BATMAN-adv continues local routing. If all mesh fails, LoRa provides emergency long-range backup.

---

## Node Types & Roles

### V3 Unified Node Taxonomy

MYC3LIUM reconciles abstract operational roles with specific hardware designators:

| V1 Role | V2 Designator | Function | Form Factor |
|---------|---------------|----------|-------------|
| **Anchor** | **SPORE** | High-capability portable node with SDR, multi-radio, compute | Portable (can be vehicle-mounted) |
| **Seed** | **HYPHA** | Lightweight handheld for hiking/scouting | Packable/wearable |
| **Sensor** | **FROND** | High-throughput camera/sensor node | Vehicle/drone-mounted |
| **Relay** | **SPORE** | Opportunistic mesh relay | Quick-deploy, solar |
| **Monitor** | **RHIZOME** | Environmental sensor pod | Ruggedized, long-life |
| **Passive** | **GHOST** | Low-signature listener | Stealth monitoring |

### Node Naming Convention

```
TYPE-ID // "callsign"
```

Examples:
- `SPORE-01 // "Raven"` - Main portable node
- `HYPHA-03 // "Ranger"` - Handheld operator unit
- `FROND-02 // "Watcher"` - Camera node
- `SPORE-07` - Relay (no callsign needed)
- `RHIZOME-12 // "Storm"` - Weather sensor pod
- `removed-node` - Passive monitor (stealth, no callsign)

**Callsigns:** Short, tactical, memorable. Used in voice/text comms. Optional for infrastructure nodes (SPORE, RHIZOME).

---

## Hardware Specification

### SPORE (Main Portable Node)

**Status:** Primary development platform (actual hardware ordered)

**Core:**
- Raspberry Pi 4 (4GB RAM)
- 21700 battery HAT (Waveshare UPS or PiSugar 3 Plus)
- 7-10" touchscreen (1024×600 or 800×480)
- Portable enclosure (Pelican-style or tactical case)

**Radios:**
- **LoRa**: Waveshare SX1262 HAT with GNSS (915 MHz, built-in GPS)
- **WiFi HaLow**: Heltec HT-HC01P (902-928 MHz, via USB-to-mPCIe adapter)
- **WiFi Mesh**: Pi 4 built-in BCM43455 (2.4/5GHz, 802.11s + BATMAN-adv)

**SDR:**
- Nooelec NESDR Smart XTR v2 (RTL-SDR)
- Ham It Up Plus upconverter
- Coverage: 300Hz-2.3GHz (with upconverter)

**Antennas:**
- LoRa: HAT antenna (915 MHz)
- WiFi HaLow: External dipole (902-928 MHz)
- WiFi mesh: Built-in + external (optional)
- SDR: 137 MHz V-dipole (satellites) + wideband

**Total Cost:** ~$380-505

**Battery Life Goals:**
- Idle (mesh only): 10-12 hours
- Active (map + messaging): 6-8 hours
- SDR active: 4-6 hours

**Deployment Options:**
1. **Portable basecamp** - Set up at camp, operate mesh + SDR
2. **Vehicle-mounted** - Power from vehicle, high-gain antennas
3. **Backpack-mobile** - Carry while hiking (reduced SDR use)

---

### HYPHA (Handheld Operator)

**Status:** Future development (Phase 8+)

**Concept:**
- Low-power SBC (ESP32 or similar)
- LoRa radio (915 MHz)
- HaLow or WiFi client
- Small display (3-5" e-ink or LCD with shader support)
- Optional camera
- Long battery life (>24 hours)

**Use case:** Hiking, scouting, field operations where SPORE stays at basecamp.

---

### FROND (Camera/Sensor Node)

**Status:** Future development (Phase 8+)

**Concept:**
- Hardware video encoder (H.264/H.265)
- CSI or USB camera
- HaLow or WiFi for high-throughput
- GPS
- Optional gimbal
- Vehicle or drone mounting

**Adaptive bitrate:** Switch between live stream (HaLow/WiFi) and thumbnail bursts (LoRa) based on link quality.

---

### SPORE (Opportunistic Relay)

**Status:** Future development (Phase 9+)

**Concept:**
- Minimal SBC (ESP32)
- LoRa + HaLow
- Solar + battery
- Quick-deploy form factor
- Store-and-forward only

---

### RHIZOME (Environmental Sensor)

**Status:** Future development (Phase 9+)

**Sensors:**
- **Atmosphere**: Temp, humidity, pressure, PM2.5/PM10, CO2, VOC
- **Hydrology**: Water level, turbidity, conductivity, temp
- **Soil**: Moisture, temp, pH
- **Weather**: Wind speed/direction, rainfall, solar irradiance

**Telemetry Modes:**
- **SLEEP/REPORT**: Deep sleep → periodic LoRa uplink (low power)
- **BURST**: High-frequency sampling on-demand (when HYPHA/FROND requests)
- **STORE-FORWARD**: Local buffering (microSD), retrieval on reconnect

**Payload Format:** CBOR compact encoding (see Appendix)

---

### GHOST (Passive Monitor)

**Status:** Future development (Phase 10+)

**Concept:**
- Low-power receive-only
- Wide-band SDR or targeted monitoring
- No TX (stealth)
- Store captured data locally
- Opportunistic upload when SPORE/HYPHA connects

---

## Software Stack

### Operating System
- Raspberry Pi OS 64-bit (Debian 12 Bookworm)
- EGLFS direct framebuffer (no X11/Wayland overhead)

### GUI Framework
- **PyQt6** (GPL v3, commercial license available)
- **ModernGL** (OpenGL ES 3.0 wrapper)
- **OpenGL ES 3.0** (Pi 4's VideoCore VI GPU)

### Mesh Networking
- **Reticulum Network Stack** (RNS v0.7.0+)
  - End-to-end encryption
  - Store-and-forward messaging
  - Multi-transport routing
- **LXMF** (encrypted messaging over Reticulum)
- **BATMAN-adv** (Layer 2 mesh routing)
- **802.11s** (WiFi mesh mode)
- **Meshtastic bridge** (compatibility with existing Meshtastic networks)

### SDR & Satellite
- **SoapySDR** (unified SDR API)
- **SatDump** (satellite decoder for NOAA APT, METEOR LRPT)
- **pyorbital** (satellite pass prediction)

### Maps & Navigation
- **MBTiles** (offline map tiles, SQLite-based)
- **ATAK integration** (optional FreeTAKServer)
- **gpsd** (GPS daemon)

### Data Formats
- **CBOR** (Concise Binary Object Representation for sensor payloads)
- **TOML** (configuration files)
- **SQLite** (message database, map tiles)

### LLM Agents (Future - Phase 11+)
- **llama.cpp** (local inference, CPU-based)
- **Qwen2.5-7B-Instruct** (Q4 quantized, ~4GB RAM)
- **Agent roles:**
  - **Data Parser**: Extract insights from sensor streams, SDR captures
  - **Query Interface**: Natural language questions about lattice status, sensor trends
  - **Anomaly Detection**: Flag unusual patterns in telemetry or RF activity
  - **Report Generation**: Summarize field operations for later review

**LLM Integration Points:**
- Chat interface in teletext GUI (P800 series pages)
- Automatic parsing of RHIZOME telemetry trends
- SDR signal classification and analysis
- Natural language queries: "Show me all nodes within 5km" / "What's the temperature trend at RHIZOME-03?"

---

## Teletext GUI

### Core UX Philosophy
**Grid-based teletext aesthetic** with modern shader rendering. Minimal, tactical, zero fluff.

**Character Grid:** 40 columns × 25 rows (teletext standard)

**Color Palette:**
```
#0B0F14  Deep black (background)
#1B2735  Slate blue (inactive)
#2F6F6F  Muted teal (active threads)
#A3D9C9  Signal green (highlights)
```

**Shader Pipeline:**
```
Content Layer
  ↓
Teletext Quantization (8-color palette, Bayer dithering)
  ↓
CRT Post-Processing (scanlines, vignette, phosphor glow)
  ↓
Framebuffer Output
```

### Page System

**Navigation:** Number keys (P100, P200, etc.) or touch zones

**100 Series: System & Menu**
- P100: Main menu
- P101: System status (uptime, CPU, RAM, battery)
- P102: Power/battery details
- P103: Radio status (all interfaces)

**200 Series: Mesh Network**
- P200: Lattice topology graph
- P201: Node list
- P202: Link quality (RSSI, latency)
- P203: Traffic statistics

**300 Series: Messaging**
- P300: Inbox
- P301: Compose message
- P302: Channels (Meshtastic + LXMF)
- P303: Message history

**400 Series: Maps**
- P400: **PRIMARY MAP VIEW** (ATAK tiles, full-screen)
- P401: Waypoint manager
- P402: Route planner
- P403: Layer toggles (OSM, satellite, topo)
- P404: Custom map creation (SDR overlays)

**500 Series: Intelligence**
- P500: Satellite tracker (pass predictions)
- P501: RF spectrum waterfall (live SDR)
- P502: Signal detection log
- P503: Camera feeds (FROND streams)

**600 Series: Configuration**
- P600: Radio config (LoRa, HaLow, WiFi)
- P601: Reticulum settings
- P602: Meshtastic settings
- P603: SDR parameters
- P604: Map sources
- P605: Display settings (CRT effects, brightness)

**700 Series: Sensors**
- P700: RHIZOME sensor grid (all nodes)
- P701: Individual sensor detail
- P702: Trend graphs (sparklines)
- P703: Alert thresholds

**800 Series: LLM Interface** (Future - Phase 11+)
- P800: Chat with local LLM agent
- P801: Query lattice status via NLP
- P802: Sensor data insights
- P803: SDR signal analysis reports

**900 Series: ARG/Lore** (Optional)
- P900: Recovered logs
- P901: Boot sequence fragments
- P902: Phantom thread reports
- P903: System anomalies

### Sample UI Cell (LATTICE MAP - P200)

```
┌──────────────────────────────────────┐
│LATTICE MAP─────────19:45──[5 CELLS]│
├──────────────────────────────────────┤
│                                      │
│ TOPOLOGY:                            │
│                                      │
│    ┌───HYPHA-03 (2.1km N)            │
│    │   LoRa -78dBm GOOD              │
│    │                                  │
│  ◉─┼───SPORE-07 (5.8km NE)           │
│ SPORE  HaLow -85dBm FAIR             │
│ (THIS) │                             │
│    └───RHIZOME-12 (1.2km W)            │
│        LoRa -82dBm GOOD              │
│                                      │
│ THREADS: 8 ACTIVE / 2 DEGRADED       │
│ STORE-FWD QUEUE: 3 msgs (42 KB)     │
│                                      │
│ [R] REGENERATE  [P] PROPAGATE        │
│                                      │
└[100]MENU─[201]NODES──────[203]STATS┘
```

---

## Networking Behavior

### Thread States

**GOOD**: RSSI > -80dBm, RTT < 100ms, packet loss < 5%
**FAIR**: RSSI -80 to -95dBm, RTT < 500ms, packet loss < 20%
**DEGRADED**: RSSI < -95dBm, RTT > 500ms, or packet loss > 20%

**Automatic demotion:** High-throughput streams (FROND video) automatically switch to thumbnail/burst mode when thread degrades.

### Routing Policies

**BATMAN-adv:**
- Handles local path discovery and fast reroute
- Layer 2 routing decisions (no IP overhead)
- Mesh topology visible to all participants

**Reticulum:**
- End-to-end encryption (identity-based)
- Store-and-forward for fragmented networks
- Cross-transport routing (LoRa ↔ HaLow ↔ WiFi)
- SPORE nodes act as trust anchors for key distribution

**Meshtastic Bridge:**
- Compatibility layer for existing Meshtastic devices
- Translates Meshtastic packets to internal LXMF format
- LoRa-only (Meshtastic protocol limitation)

### System Events (Terse Logging)

```
THREAD ESTABLISHED    - New link up
THREAD DEGRADED       - Link quality drop
PATH REGENERATED      - Alternative route found
CELL JOINED LATTICE   - Node discovery
PROPAGATION EVENT     - Store-and-forward relay
SIGNAL LOST           - Link down
```

---

## Environmental Sensing (RHIZOME)

### Sensor Groups

**Atmosphere:**
- Temperature: -40°C to +85°C (±0.5°C)
- Relative Humidity: 0-100% (±3%)
- Barometric Pressure: 300-1100 hPa (±1 hPa)
- Particulate Matter: PM2.5, PM10 (µg/m³)
- Gas: CO2 (ppm), VOC (ppb)

**Hydrology:**
- Water level: Ultrasonic or pressure sensor
- Turbidity: NTU (nephelometric turbidity units)
- Conductivity: µS/cm (dissolved solids)
- Water temp: -10°C to +50°C

**Soil:**
- Moisture: Volumetric water content (%)
- Temperature: -10°C to +50°C
- pH: 3-10 (optional, requires maintenance)

**Weather:**
- Wind speed: 0-50 m/s (anemometer)
- Wind direction: 0-360° (wind vane)
- Rainfall: mm/hour (tipping bucket)
- Solar irradiance: W/m² (pyranometer)

### Telemetry Modes

**SLEEP/REPORT:**
- Deep sleep (µA current draw)
- Wake on timer (configurable interval: 5 min - 24 hours)
- Sample sensors
- LoRa burst transmission to nearest relay
- Return to sleep

**BURST:**
- High-frequency sampling window
- Triggered by HYPHA/FROND proximity or manual request
- 1-second intervals for 5-60 minutes
- Real-time LoRa uplink

**STORE-FORWARD:**
- Local buffering on microSD (1-32 GB)
- Timestamped CBOR payloads with TTL tags
- Retrieval via SPORE or HYPHA on reconnect
- Automatic purge after TTL expires

### CBOR Payload Schema

See **Appendix A: CBOR Schemas**

---

## Camera & Livestream (FROND)

### Video Encoding

**Hardware:** CSI or USB camera with H.264/H.265 encoder
**Resolutions:** 1080p, 720p, 480p (adaptive)
**Bitrate:** 500 kbps (LoRa thumbnails) to 5 Mbps (HaLow/WiFi live)

### Adaptive Streaming Logic

```
IF SPORE reachable via HaLow/WiFi:
  OPEN STREAM (H.264/H.265, adaptive bitrate)
  Monitor thread quality
  IF thread degrades to FAIR:
    Reduce bitrate by 50%
  IF thread degrades to DEGRADED:
    Switch to thumbnail mode (JPEG bursts every 5s)
ELSE IF only LoRa available:
  Send thumbnail bursts (JPEG, 640×480, every 10s)
  Store full video locally for retrieval
END
```

### Chain of Custody

**Timestamp + Signature:** Every frame tagged with GPS time + cryptographic signature (Reticulum identity key)

**Use case:** ARG narrative (recovered footage), forensic integrity, tamper evidence

---

## Security & Identity

### Cryptographic Identities

**Reticulum-style:**
- Each node has Ed25519 identity key pair
- Public key hash = node identity
- All communications signed and encrypted end-to-end

**Trust Model:**
- SPORE nodes act as mission-level trust anchors
- Key distribution via authenticated bundles (OTA when SPORE has backhaul)
- Scheduled key rotation policies (configurable)

### Signed Telemetry

**All sensor data, video frames, and messages include:**
- Timestamp (GPS-synchronized when available)
- Source node identity (cryptographic)
- Payload hash
- Signature (Ed25519)

**Tamper evidence:** Signature verification fails if data modified

---

## HDLS ARG Integration

MYC3LIUM exists as both:
1. **Real technical system** (what you're building)
2. **Mysterious emergent infrastructure** (ARG narrative device)

### Narrative Framing

**In-universe:** MYC3LIUM was developed as an experimental communication system for remote extraction operations. After infrastructure collapse, the network persisted and exhibited unexpected emergent behavior.

### Recovered Log Fragments (Examples)

**Boot Sequence:**
```
LATTICE INIT... OK
THREAD SCAN... 3 CELLS DETECTED
PROPAGATION ID: x7f2de
SPORE-01 // "Raven" ONLINE
SYSTEM NOMINAL
```

**Field Note:**
```
HYPHA-06 // "Ranger" — Left basecamp 08:05.
Deployed SPORE-11 at ridge overlook.
RHIZOME-12 reporting storm edge approach.
FROND-02 stream quality DEGRADED, switching to thumbnails.
```

**Phantom Thread:**
```
THREAD ESTABLISHED: UNKNOWN CELL
ID: [REDACTED]
RSSI: -88dBm GOOD
LOCATION: 15.2km SW
QUERY FAILED — NO RESPONSE
THREAD PERSISTED 14 HOURS
THREAD LOST
```

**Research Note:**
```
"MYC3LIUM nodes continued routing after primary
comms infrastructure collapsed. Lattice stabilized
overnight. I didn't configure half of these paths.
The system appears to be negotiating routes
autonomously."
```

### Tone Guidelines

- **Terse and technical** (no conversational language)
- **Slightly uncanny** (emergent behavior, phantom threads)
- **Operational** (field reports, equipment logs)
- **Fragmentary** (incomplete data, redacted sections)

---

## Visual Identity

### Logo Concepts

**Avoid:**
- Mushrooms, fruiting bodies, overt biology
- Cartoon imagery

**Prefer:**
- Branching lattice diagrams
- Minimal node graphs
- Underground topology motifs
- Signal intelligence aesthetics

### UI Voice

**System messages:**
```
THREAD ESTABLISHED
CELL JOINED LATTICE
PATH REGENERATED
SIGNAL DEGRADED
PROPAGATION EVENT DETECTED
```

**Not conversational. No playful tone. Assume technical operator under time pressure.**

---

## Deployment Scenarios

### Portable Basecamp (Primary Use Case)

**Setup:**
1. Place SPORE in protective case at camp
2. Deploy LoRa antenna (vertical, elevated if possible)
3. Deploy WiFi HaLow antenna (omni or directional)
4. Connect battery HAT, power on
5. Wait for boot (LATTICE INIT)
6. Confirm P200 shows neighboring nodes

**Operations:**
- Monitor RHIZOME sensors (P700)
- Review satellite passes (P500)
- Send/receive messages (P300)
- View tactical map (P400)
- Run SDR spectrum scans (P501)

**Teardown:**
- Graceful shutdown (preserve store-and-forward queue)
- Disconnect antennas
- Pack in protective case

---

### Vehicle-Mounted (Secondary Use Case)

**Advantages:**
- Vehicle power (no battery anxiety)
- Higher-gain antennas (roof/hood mounts)
- Larger display (12V monitor)

**Setup:**
- Mount SPORE in vehicle (secure from vibration)
- External antennas on roof/hood
- Power from 12V outlet or battery (with voltage regulation)
- Display: 12V monitor or built-in touchscreen

**Use case:** Mobile basecamp, convoy communications, drive-up relay

---

### Backpack-Mobile (Tertiary Use Case)

**Constraints:**
- Battery life critical (disable SDR, reduce TX power)
- Smaller antenna (less range)
- No display (rely on HYPHA for status)

**Use case:** Scout carrying SPORE as mobile relay while hiking (HYPHA connects back to it)

---

## Map Integration & Tiling

### Offline Map System

**Format:** MBTiles (SQLite-based vector/raster tiles)

**Sources (from joshuafuller/ATAK-Maps):**
- OpenStreetMap (street map)
- OpenTopoMap (topographic)
- USGS (satellite imagery, topo, relief)
- OpenSeaMap (nautical charts)

**Storage:** `data/maps/*.mbtiles`

**Zoom Levels:** 0-18 (configurable per region)

### Custom Satellite Overlays

**Pipeline:**
1. **Capture:** RTL-SDR receives NOAA APT / METEOR LRPT pass
2. **Decode:** SatDump processes raw IQ data → georeferenced image (GeoTIFF)
3. **Tile:** `gdal2tiles.py` generates MBTiles from GeoTIFF
4. **Load:** Custom overlay appears in P403 (layer toggle)

**Use case:** Real-time weather imagery, environmental monitoring, ARG narrative (recovered satellite intel)

### Map Rendering (GPU Shader)

**Shader Pipeline:**
```glsl
// Load OSM tile from MBTiles
vec3 baseColor = texture(tileAtlas, uv).rgb;

// Quantize to teletext 8-color palette
vec3 teletextColor = quantizeTeletext(baseColor);

// Apply CRT scanlines
float scanline = sin(uv.y * resolution.y * 0.7) * 0.04;
teletextColor += vec3(scanline);

// Output
fragColor = vec4(teletextColor, 1.0);
```

**Overlays:**
- GPS position (◉)
- Mesh nodes (● color-coded by signal strength)
- Waypoints (★)
- RHIZOME sensors (S)
- FROND cameras (F)

---

## Local LLM Agents (Future - Phase 11+)

### Agent Roles

**1. Data Parser Agent**
- Ingests RHIZOME sensor streams
- Identifies trends, anomalies, correlations
- Outputs: "Temperature spike at RHIZOME-03 correlates with solar irradiance increase"

**2. Query Interface Agent**
- Natural language questions about lattice status
- Examples:
  - "How many nodes are within 5km?"
  - "What's the battery level on HYPHA-03?"
  - "Show me temperature trends for the last 6 hours"

**3. SDR Analysis Agent**
- Classifies detected signals (LoRa, WiFi, FSK, etc.)
- Flags unknown or unusual transmissions
- Outputs: "New signal 433.5 MHz FSK, 2-second bursts, unknown modulation"

**4. Report Generation Agent**
- Summarizes field operations for post-mission review
- Formats: Markdown, PDF, CBOR export
- Example: "Session 2026-03-15: 5 nodes active, 47 messages, 3 satellite passes captured, 2 RHIZOME alerts"

### LLM Integration in GUI

**P800 Series - Chat Interface**

**P800: Chat with Agent**
```
┌──────────────────────────────────────┐
│LLM AGENT───────────19:52─────────────│
├──────────────────────────────────────┤
│                                      │
│ > What's the status of RHIZOME-12?    │
│                                      │
│ RHIZOME-12 // "Storm" is ONLINE.      │
│ Last report: 19:48 (4 min ago).     │
│ Temp: 12.3°C, Humidity: 68%,        │
│ Wind: 8 m/s NW, Pressure: 1013 hPa. │
│ Battery: 72%. Thread GOOD.          │
│                                      │
│ > Any anomalies in the last hour?   │
│                                      │
│ Yes. RHIZOME-03 reported temperature  │
│ spike from 15°C to 22°C at 19:22.   │
│ Returned to baseline by 19:35.      │
│ Possible solar irradiance burst.    │
│                                      │
│ > Show me the graph                 │
│                                      │
│ [Redirecting to P702...]            │
│                                      │
└[ESC]BACK────────────────[CLEAR]CHAT┘
```

**P801: Lattice Query**
```
┌──────────────────────────────────────┐
│LATTICE QUERY───────19:52─────────────│
├──────────────────────────────────────┤
│                                      │
│ > List all nodes within 3km          │
│                                      │
│ HYPHA-03 // "Ranger" — 2.1km N       │
│ RHIZOME-12 // "Storm" — 1.2km W        │
│                                      │
│ Total: 2 nodes                       │
│                                      │
│ > Which have DEGRADED threads?       │
│                                      │
│ None. All threads GOOD or FAIR.      │
│                                      │
│ > Predict next satellite pass        │
│                                      │
│ NOAA 19 — AOS 20:34 (42 min)         │
│ Max elevation: 67° NE                │
│ Duration: 13 minutes                 │
│ Auto-capture: ENABLED                │
│                                      │
└[ESC]BACK────────────────────[P500]GO┘
```

**P802: Sensor Insights**
```
┌──────────────────────────────────────┐
│SENSOR INSIGHTS─────19:52─────────────│
├──────────────────────────────────────┤
│                                      │
│ ANALYSIS: Last 24 hours              │
│                                      │
│ Temperature range: 8.2°C - 18.7°C    │
│ Humidity: Stable 60-75%              │
│ Pressure: Falling trend (-3 hPa/6h)  │
│  → Storm system approaching          │
│                                      │
│ Wind: Increased from 3 to 12 m/s     │
│  → Gusts expected >15 m/s            │
│                                      │
│ RECOMMENDATION:                      │
│ Secure SPORE-07 (exposed ridge).     │
│ Monitor RHIZOME-12 for rainfall start. │
│                                      │
│ [EXPORT REPORT] [SET ALERT]          │
│                                      │
└[ESC]BACK──────────────────[700]GRID┘
```

### Chat with Local Information

**Data Sources for LLM:**
- Lattice topology (node list, positions, threads)
- Message history (LXMF, Meshtastic)
- RHIZOME telemetry (all sensor readings, stored in SQLite)
- SDR captures (signal logs, satellite images)
- GPS track (waypoints, routes)
- System logs (boot, errors, events)

**Query Examples:**
- "When was the last message from HYPHA-03?"
- "Which node has the lowest battery?"
- "What's the average temperature across all RHIZOME nodes?"
- "Show me the RF spectrum summary for 915 MHz"
- "Generate a mission report for today"

**Model:** Qwen2.5-7B-Instruct (Q4 quantized, ~4GB RAM)

**Inference:** llama.cpp (CPU-based, no GPU required on Pi 4)

**Performance:** ~2-5 tokens/sec on Pi 4 (acceptable for chat, not real-time)

**Privacy:** 100% local. No telemetry, no cloud.

---

## Implementation Roadmap

### Phase-by-Phase Plan (14 weeks total)

**Phase 1: Core GUI + Shaders** (2 weeks)
- PyQt6 + ModernGL setup
- Teletext character renderer (40×25 grid)
- CRT shader (scanlines, vignette, phosphor)
- Page navigation (P100-P103)

**Phase 2: Maps + GPS** (2 weeks)
- MBTiles loader (SQLite reader)
- Map rendering shader (teletext quantization)
- GPS integration (gpsd)
- P400 map page (zoom/pan, position overlay)

**Phase 3: Mesh Networking** (2 weeks)
- Reticulum daemon setup (LoRa, HaLow, WiFi)
- BATMAN-adv configuration
- P200 topology page (node graph, thread quality)
- Multi-radio routing tests

**Phase 4: Messaging** (2 weeks)
- Meshtastic bridge daemon
- LXMF integration (Reticulum)
- Message database (SQLite)
- P300 inbox, P301 compose

**Phase 5: SDR Integration** (2 weeks)
- SoapySDR waterfall shader (P501)
- Satellite pass prediction (P500)
- Auto-capture system (SatDump)
- Custom map overlay pipeline

**Phase 6: Configuration** (2 weeks)
- TOML config system
- P600-P605 config pages
- Battery monitoring (I2C)
- Power management (ECO/ULTRA_SAVE modes)

**Phase 7: Polish + Field Testing** (2 weeks)
- Performance optimization (60 FPS sustained)
- UI polish (transitions, error handling)
- Field testing (8+ hour session)
- Bug fixes, documentation

**Phase 8-10: Expansion Nodes** (6 weeks)
- HYPHA handheld prototype
- FROND camera node POC
- SPORE relay deployment
- RHIZOME sensor rig

**Phase 11: LLM Agents** (2 weeks)
- llama.cpp integration
- Qwen2.5-7B deployment
- P800-P803 chat interface
- Data parser + query agents

---

## CLI Reference

**Terse field commands** (usable from COMMAND CELL or SSH):

```bash
# Thread management
THREAD UP <node-id>
THREAD DOWN <node-id>
PROPAGATE <src> -> <dst>

# Messaging
SEND <node-id> <message>
BROADCAST <message>
INBOX

# Sensors
SENSOR PULL <scler-id>
SENSOR PUSH <scler-id> {cbor}
SENSOR ALERT <scler-id> <threshold>

# Video
STREAM OPEN <frond-id>
STREAM CLOSE <frond-id>
THUMBNAIL <frond-id>

# Diagnostics
DUMP LOGS <node-id>
PING <node-id>
TRACE <node-id>

# System
STATUS
REBOOT
SHUTDOWN
```

**Example session:**
```
> STATUS
LATTICE ONLINE, 5 CELLS, 8 THREADS
SPORE-01 // "Raven" — BATTERY 68%

> PROPAGATE HYPHA-03 -> SPORE-01
THREAD ESTABLISHED

> SENSOR PULL RHIZOME-12
RHIZOME-12 // "Storm": Temp 12.3°C, Humidity 68%, Wind 8 m/s NW

> STREAM OPEN FROND-02
FROND-02 STREAM OPEN → SPORE-01, BITRATE 2.5 Mbps
```

---

## Appendix A: CBOR Schemas

### RHIZOME Sensor Payload

```cbor
{
  "node": "RHIZOME-12",
  "ts": 1710532800,              # Unix timestamp
  "sensors": {
    "temp": 12.3,                # °C
    "rh": 68,                    # %
    "pressure": 1013,            # hPa
    "wind_speed": 8.0,           # m/s
    "wind_dir": 315              # degrees (NW)
  },
  "battery": 72,                 # %
  "sig": "ed25519:abc123..."     # Signature
}
```

### Heartbeat Payload

```cbor
{
  "node": "HYPHA-03",
  "ts": 1710532800,
  "lat": 61.2181,
  "lon": -149.9003,
  "battery": 85,
  "thread_quality": "GOOD",
  "sig": "ed25519:def456..."
}
```

### Video Frame Metadata

```cbor
{
  "node": "FROND-02",
  "ts": 1710532800,
  "frame_num": 1234,
  "codec": "h264",
  "resolution": "1080p",
  "bitrate": 2500000,            # bps
  "gps": {
    "lat": 61.2181,
    "lon": -149.9003,
    "alt": 125                   # meters
  },
  "sig": "ed25519:ghi789..."
}
```

---

## Appendix B: Regulatory Notes

**Frequency bands and power limits vary by region. Always comply with local regulations.**

**USA (FCC):**
- **915 MHz ISM**: LoRa, WiFi HaLow (FCC Part 15.247, max 1W EIRP)
- **2.4 GHz ISM**: WiFi mesh (FCC Part 15.247, max 1W EIRP)
- **137 MHz**: Satellite RX only (no TX)
- **Ham bands**: Require amateur radio license (no encryption allowed)

**Operators must:**
- Define per-deployment power masks
- Respect occupied channels (listen before transmit)
- Disable TX when required (GHOST mode)

---

## Appendix C: Repository Structure

```
myc3lium/
├── README.md
├── MYC3LIUM_BIBLE_V3.md
├── ARCHITECTURE.md
├── PAGES.md
├── ROADMAP.md
├── TECH_STACK.md
├── src/
│   ├── main.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── page_manager.py
│   │   └── widgets/
│   ├── shaders/
│   │   ├── text.vert
│   │   ├── text.frag
│   │   ├── map.vert
│   │   ├── map.frag
│   │   ├── crt.frag
│   │   └── waterfall.frag
│   ├── core/
│   │   ├── config.py
│   │   ├── mesh_manager.py
│   │   ├── map_engine.py
│   │   ├── sdr_engine.py
│   │   ├── message_router.py
│   │   └── llm_agent.py
│   ├── daemons/
│   │   ├── meshtastic_bridge.py
│   │   ├── sdr_manager.py
│   │   └── tile_cache.py
│   └── utils/
│       ├── web_mercator.py
│       ├── gps.py
│       └── satellite.py
├── data/
│   ├── maps/
│   ├── config/
│   │   ├── default.toml
│   │   └── user.toml
│   ├── messages.db
│   └── waypoints.geojson
├── firmware/
│   ├── hypha/
│   ├── frond/
│   ├── spore/
│   └── scler/
├── deploy/
│   ├── playbooks/
│   └── hardware/
├── arg/
│   └── recovered_logs/
└── docs/
```

---

## Appendix D: Expansion Modules

**Future capabilities** (not in 14-week roadmap):

**ECHO** - Spectrum monitoring subsystem
- Persistent RF monitoring across all bands
- Anomaly detection (new signals, pattern changes)
- Correlation with lattice events

**PHAROS** - Long-range beacon node
- High-power LoRa (max legal EIRP)
- Directional antennas
- Emergency broadcast mode

**VECTOR** - Directional routing optimization
- Beamforming for HaLow (if hardware supports)
- Adaptive antenna selection
- Link quality prediction

**SHADE** - Low probability of intercept (LPI) mode
- Frequency hopping
- Spread spectrum beyond standard LoRa
- Burst transmission minimization

---

## Appendix E: Glossary

**Lattice** - The MYC3LIUM mesh network

**Cell** - Individual node

**Thread** - Communication link between cells

**Colony** - Cluster of closely-connected nodes

**Propagation** - Store-and-forward relay event

**Regeneration** - Automatic path healing

**SPORE** - Main portable node 

**HYPHA** - Handheld operator node 

**FROND** - Camera/sensor node

**SPORE** - Opportunistic relay

**RHIZOME** - Environmental sensor pod

**GHOST** - Passive monitor node

**CBOR** - Concise Binary Object Representation (compact encoding)

**MBTiles** - SQLite-based map tile storage

**LXMF** - Lightweight Extensible Message Format (Reticulum messaging)

**BATMAN-adv** - Better Approach To Mobile Adhoc Networking (Layer 2 routing)

**RNS** - Reticulum Network Stack

**ATAK** - Android Team Awareness Kit (tactical mapping)

**TAK** - Team Awareness Kit (generic)

**SDR** - Software Defined Radio

**EIRP** - Effective Isotropic Radiated Power

**LPI** - Low Probability of Intercept

---

## Closing Philosophy

MYC3LIUM is not a traditional mesh network.

It is an **autonomous communication lattice** capable of surviving infrastructure loss and adapting dynamically to hostile environments.

In field deployments, the system should feel less like engineered technology and more like **an organism quietly maintaining connectivity beneath the surface.**

Operators interact with the system through terse commands and tactical interfaces.

The lattice responds, adapts, and persists.

**No node is authoritative. Every node contributes.**

**The network is the organism.**

---

**END MYC3LIUM PROJECT BIBLE V3**

*Last updated: 2026-03-15*  
*Version: 3.0*  
*Status: Design complete, implementation Phase 1 ready*
