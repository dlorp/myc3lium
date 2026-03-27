# obd2view - Terminal OBD2 Diagnostic Monitor

**Status:** Prototype (2025-03-23)  
**Aesthetic:** PSX Gran Turismo HUD + Metro map density  
**Philosophy:** Local-first, no cloud, DIY automotive diagnostics

## Vision

A terminal-based OBD2 scanner that feels like a PS1 game HUD. Real-time sensor data, DTC reading, performance logging — all in your terminal, all local, all yours.

## Features

### Core Functionality
- **Live Data Dashboard** (Mode 01)
  - Engine RPM, speed, coolant temp, intake temp
  - Throttle position, fuel pressure, MAF/MAP
  - O2 sensor voltages, fuel trims
  - ASCII art gauges with PSX color palette (#0000CD blue, #00FF00 green, #FF0000 red)

- **DTC Reader** (Mode 03)
  - Read/clear diagnostic trouble codes
  - Built-in DTC definitions (P0xxx, C0xxx, B0xxx, U0xxx)
  - Freeze frame data capture (Mode 02)

- **Performance Metrics**
  - 0-60 timer (using speed PID)
  - Fuel economy tracking
  - Session statistics

- **Data Logging**
  - Local SQLite database
  - CSV export for analysis
  - Session replay

### UI Layout (PSX-inspired)

```
┌─────────────────────────────────────────────────────────────┐
│ OBD2VIEW v0.1.0          ELM327 @ /dev/ttyUSB0    [LIVE]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│  │    RPM    │  │   SPEED   │  │   TEMP    │  │  LOAD   │ │
│  │           │  │           │  │           │  │         │ │
│  │   2450    │  │   65 mph  │  │   195°F   │  │  42.5%  │ │
│  │  ████░░░  │  │  ███████░ │  │  ██████░  │  │  ███░░  │ │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘ │
│                                                             │
│  THROTTLE: 32%  │  MAF: 12.4 g/s  │  FUEL TRIM: +2.3%     │
│  O2 BANK1: 0.76V │ FUEL PRES: 58psi │ INTAKE: 72°F        │
│                                                             │
│ ┌─ DTCS ───────────────────────────────────────────────┐   │
│ │ P0420: Catalyst System Efficiency Below Threshold    │   │
│ │ P0171: System Too Lean (Bank 1)                      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ [1] LIVE  [2] FREEZE  [3] DTCS  [4] LOG  [Q] QUIT         │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Language:** Rust (performance, safety, serial I/O)
- **TUI:** `ratatui` (terminal UI framework)
- **Serial:** `tokio-serial` (async OBD2 comms)
- **Database:** SQLite via `rusqlite` (local session storage)
- **Protocol:** ELM327 AT commands

## OBD2 Protocol Basics

### ELM327 AT Commands
```
ATZ          - Reset
ATE0         - Echo off
ATL0         - Linefeeds off
ATH1         - Headers on
ATSP0        - Auto protocol
```

### OBD2 PIDs (Mode 01 - Live Data)
```
010C - Engine RPM (2 bytes, formula: ((A*256)+B)/4)
010D - Vehicle Speed (1 byte, km/h)
0105 - Coolant Temp (1 byte, °C = A - 40)
010F - Intake Air Temp (1 byte, °C = A - 40)
0111 - Throttle Position (1 byte, % = A*100/255)
0104 - Calculated Load (1 byte, % = A*100/255)
0106/0107/0108/0109 - Fuel Trim (1 byte, % = (A-128)*100/128)
```

### Mode 03 - DTCs
```
03 - Request DTCs
Format: 43 02 01 33 00 00 00 00
  → 2 codes stored
  → P0133 (O2 Sensor Circuit Slow Response)
```

## Development Roadmap

### Phase 1: Basic Connection
- [ ] ELM327 serial connection
- [ ] AT command initialization
- [ ] Protocol auto-detection
- [ ] PID query/response parsing

### Phase 2: Live Dashboard
- [ ] Mode 01 polling loop
- [ ] Basic gauge rendering
- [ ] Real-time updates (5Hz)
- [ ] PSX color scheme

### Phase 3: DTC Support
- [ ] Mode 03 DTC reading
- [ ] DTC definition lookup
- [ ] Freeze frame capture
- [ ] Code clearing

### Phase 4: Logging
- [ ] SQLite schema
- [ ] Session recording
- [ ] CSV export
- [ ] Data replay

### Phase 5: Polish
- [ ] Performance metrics (0-60)
- [ ] Fuel economy calculator
- [ ] Config file (~/.obd2viewrc)
- [ ] Multiple vehicle profiles

## Hardware Compatibility

**Tested:**
- ELM327 v1.5 USB (FTDI chipset)
- OBDLink SX (USB, professional grade)

**Supported Protocols:**
- ISO 15765-4 (CAN)
- ISO 14230-4 (KWP2000)
- ISO 9141-2
- SAE J1850 PWM/VPW

**Target Vehicles:**
- OBD2-compliant (1996+ US, 2001+ EU)
- Focus: Subaru EJ22/EJ25 platforms

## Why This Exists

- **Local-first:** No cloud, no telemetry, your data
- **DIY culture:** Learn your car, own your diagnostics
- **Tool-first:** Solve real problems (DTC reading costs $100+ at shops)
- **Aesthetic joy:** Because terminal tools can look good

## References

- [ELM327 Datasheet](https://www.elmelectronics.com/wp-content/uploads/2016/07/ELM327DS.pdf)
- [OBD2 PID List](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [SAE J1979 Spec](https://www.sae.org/standards/content/j1979_202104/)
- Gran Turismo (PS1) - UI inspiration

---

**Next Steps:**
1. Set up Rust project skeleton
2. Implement ELM327 serial wrapper
3. Build PID parser
4. Prototype ASCII gauges
5. Test with real vehicle (2000 Subaru Impreza 2.2L)
