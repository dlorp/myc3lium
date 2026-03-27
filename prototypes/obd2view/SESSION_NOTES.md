# obd2view - Session Notes

**Created:** 2026-03-23 00:00-01:00 AKST (Session 2 of deep work rotation)  
**Session ID:** a95d58ec-dfcf-4872-a9e4-4b1364fd70eb  
**Status:** Foundation complete, ready for protocol implementation

---

## What Is This?

A terminal-based OBD2 diagnostic monitor with PSX Gran Turismo aesthetic. Think shop-quality diagnostics in your terminal, for free, with style.

**Philosophy:**
- Local-first (no cloud, no telemetry)
- DIY culture (learn your car, own your data)
- Tool-first (solve real problem: $100+ shop scans)
- Aesthetic joy (terminal tools can look good)

---

## Current Status

### ✅ Complete
- Project structure (Rust + Cargo)
- Config system (TOML, ~/.obd2viewrc)
- PID parser (Mode 01 live data)
  - RPM, speed, coolant temp, intake temp
  - Throttle position, engine load, MAF, fuel pressure
  - O2 sensors, fuel trim (short/long)
  - Unit tests passing
- DTC parser (Mode 03 trouble codes)
  - 60+ common P0xxx codes
  - C0xxx (chassis), B0xxx (body), U0xxx (network) support
  - Multi-code response parsing
  - Unit tests passing
- Architecture documentation
- Development roadmap

### ❌ Not Yet Implemented
- ELM327 serial communication (next priority)
- OBD2Manager polling loop
- TUI rendering (ratatui)
- SQLite database schema
- Session logging

---

## Key Files

```
prototypes/obd2view/
├── README.md              # Vision, features, UI mockup
├── architecture.md        # System design, data flow
├── NEXT_STEPS.md         # Implementation roadmap
├── Cargo.toml            # Dependencies
├── src/
│   ├── main.rs           # CLI entry point
│   ├── config.rs         # TOML config system
│   ├── protocol/
│   │   ├── pid.rs        # ✅ Mode 01 parser (complete)
│   │   ├── dtc.rs        # ✅ Mode 03 parser (complete)
│   │   └── elm327.rs     # ❌ Serial protocol (stub)
│   ├── obd2/mod.rs       # ❌ Manager (stub)
│   ├── data/mod.rs       # ❌ SQLite (stub)
│   └── ui/mod.rs         # ❌ TUI (stub)
└── SESSION_NOTES.md      # This file
```

---

## Next Steps (Priority Order)

### 1. ELM327 Protocol (Highest Priority)
**Goal:** Connect to hardware, send/receive commands

**Tasks:**
- Implement `ELM327::new()` - serial port + initialization (ATZ, ATE0, etc.)
- Implement `send_command()` - write/read with ">" prompt detection
- Implement `query_pid()` - Mode 01 query with hex parsing
- Add timeout handling (1-2s max)
- Integration tests with mock serial

**Testing:**
```bash
# Manual verification with real ELM327
screen /dev/ttyUSB0 38400
ATZ            # → "ELM327 v1.5"
ATE0           # → "OK" (echo off)
010C           # → "41 0C 26 1A" (RPM query)
```

### 2. TUI Dashboard
**Goal:** Visual live data display

**Tasks:**
- ratatui setup (terminal init, event loop)
- Dashboard layout (4 gauges: RPM, speed, temp, load)
- ASCII art gauge rendering
- PSX color scheme (#0000CD, #00FF00, #FF0000)
- 60 FPS render loop

### 3. Everything Else
- OBD2Manager (high-level API + caching)
- SQLite logging
- DTC view
- Config editor

---

## Technical Details

### PID Parsing Examples

**RPM (0x010C):**
```
Response: 41 0C 26 1A
Parse: (0x26 * 256 + 0x1A) / 4 = 2438 rpm
```

**Speed (0x010D):**
```
Response: 41 0D 42
Parse: 0x42 = 66 km/h → 41 mph (imperial)
```

**Coolant Temp (0x0105):**
```
Response: 41 05 E1
Parse: 0xE1 - 40 = 185°C → 365°F
```

### DTC Parsing Example

**Response:** `43 02 01 33 04 20`
- Byte 0: `43` = Mode 03 response
- Byte 1: `02` = 2 codes stored
- Bytes 2-3: `01 33` = P0133 (O2 Sensor Circuit Slow Response)
- Bytes 4-5: `04 20` = P0420 (Catalyst System Efficiency Below Threshold)

---

## Hardware Requirements

**To test with real vehicle:**
- ELM327 v1.5+ USB adapter (~$20 on Amazon)
  - Prefer FTDI chipset (better Linux support)
  - OBDLink SX is professional-grade option
- OBD2-compliant vehicle (1996+ US, 2001+ EU)
- Linux system (macOS/WSL also work)
- Serial permissions: `sudo usermod -a -G dialout $USER`

**Mock testing (no hardware):**
- Use `mockall` crate for ELM327 trait mocking
- Simulate responses in unit tests
- Test parser logic independently

---

## Design Decisions

### Why Rust?
- Performance (60 FPS UI + 5 Hz polling)
- Safety (no segfaults in long-running daemon)
- Ecosystem (ratatui, tokio-serial are mature)
- Cross-platform (Linux/macOS/Windows)

### Why Local-First?
- Privacy (no telemetry, no cloud uploads)
- Reliability (works offline, always)
- Ownership (your car data is YOUR data)
- Cost (free vs. $100+ shop scans)

### Why PSX Aesthetic?
- Nostalgia (Gran Turismo HUD is iconic)
- Clarity (high contrast, readable at a glance)
- Fun (tools should spark joy, not dread)

---

## Alignment with dlorp's Values

✅ **Local-first:** No cloud, no APIs, offline-capable  
✅ **DIY culture:** Learn your car, own your tools  
✅ **Tool-first mindset:** Solve real problem (expensive diagnostics)  
✅ **Constraints = creativity:** PSX palette, ASCII art gauges  
✅ **Self-hosting:** Runs locally, no dependencies  
✅ **Automotive interest:** Perfect fit for EJ22 maintenance tracking  

---

## Related Projects

- **r³LAY:** TUI research assistant (automotive category)
- **garage-buddy:** Workshop tool tracker mockup
- **EJ22-tracker:** Maintenance log with visual TUI demo
- **OBD2-TUI:** Earlier prototype (merge/supersede with obd2view)

**Integration opportunity:** obd2view could feed diagnostic data into r³LAY's automotive knowledge base, creating a closed-loop learning system.

---

## Success Criteria

**MVP (Minimum Viable Product):**
- [ ] Connect to ELM327 adapter
- [ ] Display live RPM, speed, coolant temp
- [ ] Read and display DTCs
- [ ] Clear DTCs with confirmation
- [ ] Basic session logging

**Polish (Production Ready):**
- [ ] Config file editor in TUI
- [ ] Multiple vehicle profiles
- [ ] Performance metrics (0-60 timer)
- [ ] Fuel economy calculator
- [ ] Freeze frame analysis
- [ ] CSV export for analysis
- [ ] Binary releases (Linux, macOS)

---

## Resources

- [ELM327 Datasheet](https://www.elmelectronics.com/wp-content/uploads/2016/07/ELM327DS.pdf)
- [OBD2 PID List](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [SAE J1979 Spec](https://www.sae.org/standards/content/j1979_202104/)
- [Ratatui Book](https://ratatui.rs/)
- [tokio-serial Examples](https://github.com/berkowski/tokio-serial)

---

## Session Wrap-Up

**Time spent:** 35 minutes deep work + 20 minutes documentation  
**Output:** ~500 LOC, 15 KB docs, 13 files  
**Tests:** 6 unit tests passing  
**Blockers:** None (ready for next session)  
**Next session:** Implement ELM327 serial protocol OR build TUI mockup  

**Learnings:**
- OBD2 protocol is simpler than expected (good documentation)
- Rust ecosystem has excellent serial/TUI libraries
- PID formulas are straightforward (mostly bit shifts + offsets)
- DTC parsing is more complex (multi-code responses, empty code filtering)

**Notes for future self:**
- Test with real hardware ASAP (mock only gets you so far)
- Consider Protocol 6 (ISO 15765-4 CAN) as primary (most common on modern cars)
- Implement multi-PID requests early (reduces poll latency)
- Cache PIDs aggressively (200ms staleness = smooth UI)

---

**End of Session 2**
