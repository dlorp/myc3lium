# obd2view - OBD2 Diagnostic TUI Prototype

**Status:** Session 2 Complete (ELM327 + Manager + TUI implemented)  
**Created:** 2026-03-23 01:08 AKST  
**Lines of Code:** ~900 (excluding docs/tests)

## What Got Built

A functional OBD2 diagnostic monitor with PSX aesthetic. Core features:

### 1. ELM327 Protocol Layer (`src/protocol/elm327.rs`)
- Async serial I/O via `tokio-serial`
- Initialization sequence (ATZ, ATE0, ATL0, ATH1, ATSP0)
- Command/response parsing with timeout handling
- PID queries (Mode 01), DTC reading (Mode 03), clearing (Mode 04)
- Error handling for invalid responses

### 2. OBD2 Manager (`src/obd2/mod.rs`)
- High-level API wrapping ELM327
- PID value caching (200ms TTL = 5 Hz polling)
- Batch queries (multiple PIDs in single loop)
- DTC reading/clearing wrappers
- Connection lifecycle management

### 3. TUI Dashboard (`src/ui/mod.rs`)
- 2x2 gauge layout (RPM, Speed, Temp, Load)
- PSX color theme:
  - Blue borders (#0000CD - Gran Turismo vibes)
  - Green gauges (#00FF00 - normal state)
  - Yellow (60-80%), Red (>80%) warnings
- Live data polling at 60 FPS render, 5 Hz data refresh
- Imperial/metric unit conversion
- Keyboard controls (Q to quit)

### 4. Data Parsers
- **PID Parser** (`src/protocol/pid.rs`)
  - 11 common PIDs (RPM, speed, temperatures, throttle, MAF, fuel trim)
  - Unit conversions (imperial/metric)
  - Unit tests for edge cases
- **DTC Parser** (`src/protocol/dtc.rs`)
  - 60+ common code definitions (P0xxx, C0xxx, B0xxx, U0xxx)
  - Multi-code response parsing
  - Filter empty codes (0x0000)

### 5. Config System (`src/config.rs`)
- TOML-based config (~/.obd2viewrc)
- Device path, baud rate, units, theme, logging
- Default values for quick start

## What Works (Theoretically)

✅ Connect to ELM327 adapter  
✅ Initialize with AT commands  
✅ Query live PIDs (RPM, speed, temps, load)  
✅ Parse responses with validation  
✅ Render gauges with PSX aesthetic  
✅ Handle disconnects gracefully  
✅ Imperial/metric units  

## What's Missing

❌ Hasn't been compiled (Rust not installed on dev machine)  
❌ No hardware testing (requires ELM327 + vehicle)  
❌ SQLite logging (stub exists)  
❌ DTC view UI (only dashboard implemented)  
❌ Multi-PID batch optimization (one query per PID currently)  
❌ Performance metrics (0-60 timer, fuel economy)  

## How to Test

**Prerequisites:**
1. Rust toolchain (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
2. ELM327 v1.5+ USB adapter (~$20 on Amazon)
3. OBD2-compliant vehicle (1996+ US, 2001+ EU, 2004+ everywhere else)

**Build:**
```bash
cd prototypes/obd2view
cargo build --release
```

**Run:**
```bash
# List available serial devices
./target/release/obd2view --list-devices

# Connect to vehicle (plug ELM327 into OBD2 port, turn ignition ON)
./target/release/obd2view --device /dev/ttyUSB0

# Expected: Blue TUI with 4 gauges, live data updates
# Press Q to quit
```

**Mock Testing (No Hardware):**
```bash
# Unit tests (PID/DTC parsing)
cargo test --lib

# Note: Integration tests are ignored (require hardware)
cargo test -- --include-ignored
```

## Architecture Highlights

**Async Everything:**
- `tokio` for serial I/O (non-blocking reads)
- `tokio::select!` for timeout handling
- 60 FPS UI refresh without blocking data polling

**Caching Strategy:**
- 200ms TTL for PID values (5 Hz effective rate)
- Reduces serial bus chatter (OBD2 is slow)
- Cache invalidation on reconnect

**Error Handling:**
- ELM327 layer returns `ProtocolError` enum
- Manager layer converts to `anyhow::Result`
- UI layer degrades gracefully (shows "--" on error)

**PSX Aesthetic:**
- RGB color codes match PS1 system menu
- Gran Turismo HUD inspiration (dashboard gauges)
- Metro map information density (future views)

## Next Steps (Priority Order)

1. **Compile & Fix Errors** - Rust compiler will catch type issues
2. **Hardware Test** - Validate against real ELM327 + vehicle
3. **DTC View** - List trouble codes with descriptions
4. **Logger** - SQLite session recording + CSV export
5. **Optimization** - Multi-PID requests (reduce serial round-trips)
6. **Polish** - Config editor, performance metrics, binary releases

## Design Decisions

**Why async serial I/O?**
- ELM327 is slow (38400 baud = ~3.8 KB/s)
- Timeout handling critical (some ECUs don't respond to all PIDs)
- Non-blocking UI (60 FPS even if serial stalls)

**Why 5 Hz polling?**
- ECU data doesn't change faster than that (engine control loops ~10-50 Hz)
- Serial bus bandwidth limited (each PID = ~30ms round-trip)
- Balances responsiveness vs CPU usage

**Why PSX theme?**
- Nostalgia factor (Gran Turismo HUD = iconic)
- High contrast (easy to read in garage lighting)
- Aesthetic joy (terminal tools can look good)

**Why Rust?**
- Zero-cost async (no GC pauses during rendering)
- Type safety (PID parsing errors caught at compile time)
- Cross-platform (Linux, macOS, Windows with same code)

## Files

```
prototypes/obd2view/
├── README.md              (original vision doc)
├── README_PROTOTYPE.md    (this file)
├── architecture.md        (system design)
├── NEXT_STEPS.md         (implementation roadmap)
├── Cargo.toml            (dependencies)
├── .gitignore
└── src/
    ├── main.rs           (CLI entry point, 95 lines)
    ├── config.rs         (TOML config, 105 lines)
    ├── protocol/
    │   ├── mod.rs        (error types, 28 lines)
    │   ├── elm327.rs     (serial protocol, 150 lines)
    │   ├── pid.rs        (PID parser, 200 lines)
    │   └── dtc.rs        (DTC parser, 165 lines)
    ├── obd2/
    │   └── mod.rs        (manager, 120 lines)
    ├── data/
    │   └── mod.rs        (logging stub, 10 lines)
    └── ui/
        └── mod.rs        (TUI dashboard, 230 lines)
```

**Total:** ~1,100 lines (code + tests + docs)

## Why This Matters

**Problem:** OBD2 diagnostic scans cost $50-150 at shops. Budget scanners (~$20) have terrible UIs (2-line LCD, cryptic codes).

**Solution:** Open-source TUI with modern UX. Same $20 hardware, better software.

**For dlorp:**
- Aligns with automotive interest (EJ22 maintenance tracking)
- DIY culture (own your car data, no cloud BS)
- PSX aesthetic (retro gaming + automotive crossover)
- Fills gap in r³LAY ecosystem (automotive research assistant)

**For the Community:**
- Educational (learn OBD2 protocol, serial I/O, async Rust)
- Hackable (add custom PIDs, logging formats, views)
- Privacy-first (no telemetry, your data stays local)

## Demo Scenario (Once Hardware Tested)

```
$ obd2view --device /dev/ttyUSB0

┌──────────────────────────────────────────────────────┐
│          OBD2VIEW - Diagnostic Monitor               │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐                        │
│  │   RPM    │  │  SPEED   │                        │
│  │          │  │          │                        │
│  │  2450    │  │   65     │                        │
│  │ ████░░░  │  │ ███░░░   │                        │
│  └──────────┘  └──────────┘                        │
│                                                      │
│  ┌──────────┐  ┌──────────┐                        │
│  │   TEMP   │  │   LOAD   │                        │
│  │          │  │          │                        │
│  │  185°F   │  │  42.3%   │                        │
│  │ ███░░░   │  │ ██░░░░   │                        │
│  └──────────┘  └──────────┘                        │
│                                                      │
├──────────────────────────────────────────────────────┤
│ Press Q to quit | ● Connected                       │
└──────────────────────────────────────────────────────┘
```

**Gran Turismo vibes. In your garage. For $20.**

---

**Session 2 Complete.** Ready for hardware validation.
