# OBD2-TUI - Automotive Diagnostic Terminal Interface

**Concept:** Retro-styled terminal UI for OBD2 diagnostics and vehicle monitoring.

## Design Philosophy

- **PSX aesthetic:** Blue/gray palette, geometric UI elements, scan-line effects
- **Real-time data:** Live sensor feeds (RPM, coolant temp, MAF, O2 sensors)
- **DTC management:** Read/clear codes with detailed descriptions
- **Data logging:** CSV export for analysis, track trends over time
- **Zero dependencies on cloud:** Local-first, works offline

## Target Use Cases

1. **Home mechanic diagnostics** - Quick code reads without expensive scan tools
2. **Performance monitoring** - Track sensor data during test drives
3. **Maintenance tracking** - Log baseline values, detect degradation
4. **Learning tool** - Understand vehicle systems through real-time data

## Technical Stack (Proposed)

- **Language:** Rust (performance, safety) or Go (simplicity)
- **TUI framework:** ratatui (Rust) or bubbletea (Go)
- **OBD protocol:** ELM327 compatible (widely available adapters)
- **Serial comm:** tokio-serial or go-serial
- **Data viz:** Sparkline graphs, gauge clusters, status grids

## UI Layout Concept

```
┌─────────────────────────────────────────────────────────────┐
│ OBD2-TUI v0.1.0          [ELM327] CONNECTED     03:15:42 AM │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ENGINE STATUS               │  SENSOR LIVE FEED              │
│  ━━━━━━━━━━━━━              │  ━━━━━━━━━━━━━━━              │
│  RPM:     2450  ▂▃▅▇▆▄▃▂    │  MAF:      15.2 g/s            │
│  SPEED:     65 mph           │  O2 (B1S1): 0.45V  [LEAN]      │
│  COOLANT:  195°F  [OK]       │  FUEL PRES: 45 psi  [OK]       │
│  OIL TEMP: 210°F  [OK]       │  TIMING:     18° BTDC          │
│                               │                                │
│  FAULT CODES                 │  DATA LOGGING                  │
│  ━━━━━━━━━━━                │  ━━━━━━━━━━━━━                │
│  P0171 - System Too Lean     │  ● Recording to:               │
│         (Bank 1)             │    logs/2026-03-23_0315.csv    │
│  [C]lear  [D]etails          │  Duration: 00:12:34            │
│                               │  [S]top  [E]xport              │
└─────────────────────────────────────────────────────────────┘
[Q]uit  [R]efresh  [F]reeze  [L]og  [H]elp
```

## Key Features

### 1. Multi-Page Navigation
- **Dashboard:** Real-time sensor overview
- **DTC Viewer:** Detailed fault code analysis
- **Data Logger:** Time-series recording and playback
- **Freeze Frame:** Capture sensor state at fault occurrence
- **Vehicle Info:** VIN, calibration ID, protocol detection

### 2. Visual Design Elements
- **PSX-inspired color scheme:** `#0066CC`, `#003366`, `#FFFFFF`, `#FF3333`
- **Scan-line overlay:** Optional retro CRT effect
- **Gauge cluster mode:** Analog-style gauges for RPM/speed
- **Alert system:** Color-coded warnings (green/yellow/red)

### 3. Data Export
- **CSV format:** Timestamp, PID, value, unit
- **Session summaries:** Min/max/avg for each sensor
- **DTC history:** Track when codes appear/clear
- **Shareable reports:** Markdown export for forums/mechanics

### 4. Hardware Compatibility
- **ELM327 Bluetooth/USB/WiFi**
- **STN1110/2120 (faster variants)**
- **Auto-detect baud rate and protocol**
- **Support OBD-II standard PIDs + manufacturer-specific**

## Implementation Phases

### Phase 1: Core Engine (Week 1-2)
- Serial port communication
- ELM327 AT command handling
- PID request/response parsing
- Basic TUI with live RPM/speed display

### Phase 2: Full Dashboard (Week 3-4)
- Multi-sensor layout
- DTC read/clear functionality
- Real-time graphing (sparklines)
- Keyboard navigation

### Phase 3: Data Logging (Week 5-6)
- CSV recording with timestamps
- Playback mode for reviewing sessions
- Export utilities
- Freeze frame capture

### Phase 4: Polish & Extras (Week 7-8)
- PSX visual theme refinement
- Performance optimization
- Configuration system (units, refresh rate, PIDs)
- Documentation and examples

## Research Notes

**ELM327 Protocol Basics:**
- AT commands for setup (ATZ reset, ATSP auto-protocol)
- Mode 01: Live data (PIDs 00-FF)
- Mode 03: Read DTCs
- Mode 04: Clear DTCs
- Mode 09: Vehicle info (VIN, calibration)

**Common PIDs for EJ22:**
- 0C: Engine RPM
- 05: Coolant temperature
- 0D: Vehicle speed
- 10: MAF sensor
- 14/15: O2 sensors (Bank 1)
- 0B: Intake manifold pressure
- 11: Throttle position

**Data Rates:**
- Standard OBD: ~10-20 queries/sec
- Fast variants (STN): ~100 queries/sec
- Need smart polling strategy for smooth UI

## Prior Art & Inspiration

- **pyOBD:** Python-based, functional but dated UI
- **Torque Pro:** Android app, good UX but mobile-only
- **ScanTool.net:** Windows software, powerful but not FOSS
- **openxc:** Vehicle interface platform, more complex than needed

**Differentiation:**
- Terminal-native (SSH-friendly, lightweight)
- Aesthetic focus (PSX retro, not just functional)
- Local-first (no telemetry, no cloud)
- Hackable (config files, scriptable exports)

## Next Steps

1. **Prototype:** Build minimal ELM327 serial reader in Rust
2. **Test hardware:** Verify with actual ELM327 adapter + vehicle
3. **UI mockup:** Full ratatui implementation of dashboard
4. **Data flow:** Implement efficient PID polling strategy
5. **DTC database:** Embed standard P0xxx code descriptions
6. **Release:** GitHub repo, build instructions, demo video

## File Structure

```
obd2-tui/
├── src/
│   ├── main.rs
│   ├── elm327/        # Serial communication & protocol
│   ├── ui/            # TUI components
│   ├── logger/        # Data recording
│   └── dtc/           # Fault code database
├── assets/
│   └── dtc-codes.json # Standard OBD-II codes
├── docs/
│   ├── SETUP.md       # Hardware guide
│   └── PIDS.md        # Supported PIDs reference
└── Cargo.toml
```

---

**Prototype Status:** Concept documented, ready for implementation.

**Alignment Check:**
- ✅ Automotive (OBD2, EJ22 diagnostics)
- ✅ Retro aesthetic (PSX TUI design)
- ✅ Tool-first mindset (practical utility)
- ✅ Local-first (no cloud dependencies)
- ✅ DIY culture (open source, hackable)

**Estimated effort:** 6-8 weeks for feature-complete v1.0

**Hardware needed for testing:**
- ELM327 Bluetooth adapter (~$15)
- Vehicle with OBD-II port (1996+ in US)
- Optional: OBD-II simulator for development

