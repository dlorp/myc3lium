# myc3lium - System Architecture

**Version:** 1.0  
**Target Platform:** Raspberry Pi 4 (4GB RAM)  
**Display:** 7-10" touchscreen (800x480 or 1024x600)  
**OS:** Raspberry Pi OS 64-bit (Debian-based)

---

## Overview

**myc3lium** - A portable mesh networking terminal with intelligence gathering capabilities, inspired by fungal mycelial networks. Unified teletext-style GUI with shader-rendered interface - no CLI required for normal operation.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │   PyQt6 Application (main_window.py)                   │ │
│  │   ├── Teletext Renderer (40×25 grid)                   │ │
│  │   ├── Map Renderer (ATAK MBTiles)                      │ │
│  │   ├── Shader Pipeline (OpenGL ES 3.0)                  │ │
│  │   └── Page Manager (P100-P605)                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────┐
│                     INTEGRATION LAYER                        │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐ │
│  │ Mesh Manager │ Map Engine   │ SDR Engine   │ Config   │ │
│  │ (Reticulum + │ (MBTiles +   │ (SoapySDR +  │ Manager  │ │
│  │  Meshtastic) │  GPS)        │  Satellites) │          │ │
│  └──────────────┴──────────────┴──────────────┴──────────┘ │
└─────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────┐
│                      HARDWARE LAYER                          │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐ │
│  │ LoRa HAT     │ WiFi HaLow   │ WiFi Mesh    │ RTL-SDR  │ │
│  │ (SX1262 +    │ (HT-HC01P)   │ (BCM43455)   │ (NESDR)  │ │
│  │  GPS)        │              │              │          │ │
│  └──────────────┴──────────────┴──────────────┴──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Process Model

### Main GUI Process
- **PyQt6 Application** (main process)
- OpenGL ES 3.0 rendering via EGLFS (no X11/Wayland)
- Event loop handles UI, touch input, page navigation
- ~300-400 MB RAM

### Background Daemons (systemd services)

**1. Reticulum Daemon (`rnsd`)**
- Multi-radio mesh routing
- Interfaces: LoRa (RNode), WiFi HaLow (AutoInterface), WiFi mesh (AutoInterface)
- Store-and-forward messaging
- ~200 MB RAM

**2. GPS Daemon (`gpsd`)**
- Reads GNSS from LoRa HAT
- Provides position to GUI and ATAK
- ~50 MB RAM

**3. Meshtastic Bridge (`meshtastic-bridge`)**
- Serial connection to LoRa radio for Meshtastic protocol
- Translates Meshtastic ↔ internal message format
- ~100 MB RAM

**4. SDR Manager (`sdr-manager`)**
- SoapySDR control
- Satellite pass scheduling
- Auto-capture and decode
- ~200 MB RAM (idle), ~800 MB (active)

**5. Map Tile Cache (`tile-cache`)**
- Pre-loads map tiles for offline use
- LRU eviction policy
- ~500 MB RAM

**6. Battery Monitor (`battery-mon`)**
- I2C communication with battery HAT
- Power management policies
- ~50 MB RAM

---

## Memory Budget (4GB Total)

```
OS baseline:              ~500 MB
GUI (PyQt6 + OpenGL):     ~400 MB
Reticulum daemon:         ~200 MB
GPS daemon:                ~50 MB
Meshtastic bridge:        ~100 MB
SDR manager (idle):        ~50 MB
Map tile cache:           ~500 MB
Battery monitor:           ~50 MB
System services:          ~150 MB
──────────────────────────────────
Used:                    ~2000 MB
Free headroom:           ~2000 MB
```

**SDR active:** +750 MB (FFT buffers, decoding)  
**Still fits:** ~1.25 GB free with everything running

---

## Data Flow

### Messaging Flow
```
User → GUI → MessageRouter
              ↓
     ┌────────┴────────┐
     ↓                 ↓
Meshtastic         LXMF/Reticulum
(LoRa only)        (auto-routes: LoRa/HaLow/WiFi)
     ↓                 ↓
Serial Bridge      RNS Daemon
     ↓                 ↓
   Radio            Radio(s)
```

### Map Rendering Flow
```
MBTiles (SQLite) → Tile Loader → GPU Texture Atlas
                                      ↓
GPS Position ──────────────────→ Overlay Renderer
Mesh Nodes  ──────────────────→      ↓
Waypoints   ──────────────────→ Fragment Shader
                                 (Teletext Quantize)
                                      ↓
                                 CRT Post-FX
                                      ↓
                                  Framebuffer
```

### SDR Flow
```
RTL-SDR → SoapySDR → FFT Engine → Waterfall Shader → Display
                          ↓
                    Signal Detector → Alerts
                          ↓
         (On satellite pass) → APT/LRPT Decoder
                                      ↓
                              Georeferenced Image
                                      ↓
                               gdal2tiles.py
                                      ↓
                             Custom MBTiles → Map
```

---

## Module Structure

```
myc3lium/
├── src/
│   ├── main.py                    # Entry point
│   ├── ui/
│   │   ├── main_window.py         # PyQt6 main window
│   │   ├── page_manager.py        # Page navigation (P100-P605)
│   │   ├── widgets/               # Custom widgets
│   │   │   ├── teletext_text.py   # Character grid renderer
│   │   │   ├── map_view.py        # Map widget
│   │   │   └── waterfall.py       # SDR waterfall
│   │   └── input_handler.py       # Touch + keyboard
│   ├── shaders/
│   │   ├── text.vert              # Text vertex shader
│   │   ├── text.frag              # Text fragment shader
│   │   ├── map.vert               # Map vertex shader
│   │   ├── map.frag               # Map + teletext quantization
│   │   ├── crt.frag               # CRT post-processing
│   │   └── waterfall.frag         # SDR waterfall
│   ├── core/
│   │   ├── config.py              # TOML config loader
│   │   ├── message_router.py     # Meshtastic + LXMF
│   │   ├── mesh_manager.py       # Reticulum interface
│   │   ├── map_engine.py         # MBTiles + GPS
│   │   ├── sdr_engine.py         # SoapySDR control
│   │   └── battery.py            # Power management
│   ├── daemons/
│   │   ├── meshtastic_bridge.py  # Serial → internal msgs
│   │   ├── sdr_manager.py        # Background SDR control
│   │   └── tile_cache.py         # Map pre-loader
│   └── utils/
│       ├── web_mercator.py       # Map projection math
│       ├── gps.py                # gpsd interface
│       └── satellite.py          # Pass prediction
├── data/
│   ├── maps/                      # MBTiles storage
│   ├── config/
│   │   ├── default.toml           # Default settings
│   │   └── user.toml              # User overrides
│   ├── messages.db                # SQLite message store
│   └── waypoints.geojson          # Saved waypoints
├── assets/
│   ├── fonts/
│   │   └── teletext.ttf           # Monospace teletext font
│   └── palettes/
│       └── ceefax.json            # 8-color palette
└── systemd/
    ├── mesh-gui.service           # Main GUI
    ├── meshtastic-bridge.service
    ├── sdr-manager.service
    └── tile-cache.service
```

---

## Security Model

**Mesh Communications:**
- Reticulum: End-to-end encryption (built-in)
- Meshtastic: Optional AES encryption (configurable per channel)
- No plaintext by default

**Map Data:**
- Offline-first (no telemetry to tile providers)
- Custom overlays stored locally
- No cloud dependencies

**SDR:**
- Receive-only (no TX unless HackRF added later)
- Signal data stored locally
- No external uploads

**Configuration:**
- Files: 0600 permissions (user-only)
- No passwords in config (use key files)
- Backup encrypted with GPG (optional)

---

## Startup Sequence

1. **Boot** → Systemd starts background services
2. **rnsd** starts → Reticulum mesh comes online
3. **gpsd** starts → GPS fix acquired
4. **meshtastic-bridge** starts → LoRa channel opens
5. **sdr-manager** starts → Satellite pass schedule loaded
6. **tile-cache** starts → Pre-loads maps for offline use
7. **GUI launches** (EGLFS, no desktop environment)
8. **Page 100** displays (main menu)
9. User interacts → Pages navigate via number keys / touch

---

## Performance Targets

**GUI Responsiveness:**
- 60 FPS rendering (shader pipeline)
- <50ms touch → response latency
- <100ms page transition

**Mesh:**
- <1s message send latency (local)
- <5s multi-hop latency (3 hops)

**Maps:**
- <200ms tile load (from cache)
- <500ms zoom/pan response

**SDR:**
- Real-time waterfall (30 FPS minimum)
- <2s satellite pass start-to-display

**Battery:**
- Idle: 10-12 hours (mesh only)
- Active: 6-8 hours (map + messaging)
- SDR: 4-6 hours (continuous RX)

---

## Failure Modes & Recovery

**Radio Failure:**
- GUI shows offline indicator
- Messages queued until radio returns
- Auto-retry connection every 30s

**GPS Loss:**
- Last known position cached
- Dead reckoning if moving (optional)
- Manual position entry available

**SDR Failure:**
- Satellite pages show error
- Auto-disable SDR to save power
- Manual restart available

**Low Battery:**
- ECO mode auto-enables at 30%
- ULTRA_SAVE at 15%
- Graceful shutdown at 5%

**Map Corruption:**
- Tile cache rebuild on next boot
- Fallback to basic OSM tiles
- Re-download from config sources

---

## Future Expansion

**Phase 2 Features:**
- Camera integration (USB webcam)
- ATAK COT messaging (FreeTAKServer)
- Voice comms (codec2 over mesh)

**Phase 3 Features:**
- LLM agent (batch processing mode)
- Kismet integration (WiFi/BT mapping)
- HackRF TX (wideband monitoring → transmission)

**Phase 4 Features:**
- Multi-device sync (share maps/waypoints)
- Plugin system (community extensions)
- Desktop companion app (cross-platform)

---

## Dependencies

See **TECH_STACK.md** for complete list.

**Key Libraries:**
- PyQt6 (GUI framework)
- ModernGL (OpenGL wrapper)
- SoapySDR (SDR abstraction)
- RNS (Reticulum Network Stack)
- gpsd-py3 (GPS interface)
- Pillow (image processing)

**System Packages:**
- reticulum
- gpsd
- soapysdr
- rtl-sdr
- satdump (for decoding)

---

## Configuration Files

**Primary:** `data/config/user.toml`

See **CONFIG.md** for complete schema.

**Key sections:**
- `[display]` - Resolution, brightness, CRT effects
- `[radios]` - LoRa, HaLow, WiFi settings
- `[mesh]` - Reticulum interfaces
- `[maps]` - Tile sources, cache size
- `[sdr]` - Frequencies, gain, satellite list
- `[power]` - Battery policies, ECO modes

---

## Development vs Production

**Development (on desktop):**
- Uses X11/Wayland (not EGLFS)
- Mock GPS (fixed position)
- Mock radios (simulated mesh)
- Faster iteration

**Production (Pi 4):**
- EGLFS (direct framebuffer)
- Real hardware
- Systemd services
- Optimized build

---

## Build Process

See **ROADMAP.md** Phase 1 for setup.

**Quick start:**
```bash
# Install dependencies
sudo apt install python3-pyqt6 python3-opengl reticulum gpsd soapysdr

# Clone repo
git clone <repo-url> mesh-terminal-gui
cd mesh-terminal-gui

# Install Python packages
pip3 install -r requirements.txt

# Run in dev mode
python3 src/main.py --dev

# Build for production
./build.sh --pi4
```

---

**Next:** See **PAGES.md** for complete UI design.
