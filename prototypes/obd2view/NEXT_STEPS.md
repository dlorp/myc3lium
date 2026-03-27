# obd2view - Next Steps

## Current Status (2026-03-23 01:35 AKST)

**Completed:**
- ✅ Project structure and architecture design
- ✅ Cargo.toml with dependencies
- ✅ Config system (TOML-based)
- ✅ PID parser with unit tests (RPM, speed, temps, etc.)
- ✅ DTC parser with common code definitions
- ✅ **ELM327 serial protocol** (async I/O, initialization sequence, command/response parsing)
- ✅ **OBD2Manager** (caching layer, batch PID queries, DTC reading/clearing)
- ✅ **TUI Dashboard** (ratatui 4-gauge layout, PSX color theme, live data polling)

**Not Yet Implemented:**
- ❌ SQLite database schema (data logging)
- ❌ DTC view UI (separate screen)
- ❌ Logger view UI (session history)
- ❌ Config editor TUI
- ❌ Multi-PID batch optimization (single request for multiple PIDs)
- ❌ Performance metrics (0-60 timer, fuel economy calculator)

**Compilation Status:**
- ⚠️ Untested (Rust not installed on this machine)
- Expected to compile with `cargo build` once dependencies are resolved
- Integration tests require real ELM327 hardware

## Priority Order

### 1. ELM327 Protocol (Highest Priority)
**Goal:** Connect to real hardware, send/receive commands

**Tasks:**
- [ ] Implement `ELM327::new()` - open serial port, send initialization sequence
- [ ] Implement `send_command()` - write to serial, read until ">" prompt
- [ ] Implement `query_pid()` - send Mode 01 query, parse hex response
- [ ] Add timeout handling (1-2 seconds max)
- [ ] Test with real ELM327 adapter

**Testing Strategy:**
```bash
# Manual test with screen/minicom
screen /dev/ttyUSB0 38400
ATZ            # Should respond "ELM327 v1.5"
ATE0           # Echo off
010C           # Query RPM, should get "41 0C XX XX"
```

### 2. OBD2Manager (Medium Priority)
**Goal:** High-level API for UI layer

**Tasks:**
- [ ] Connection wrapper around ELM327
- [ ] Implement PID caching (200ms staleness threshold)
- [ ] Multi-PID request optimization (batch queries)
- [ ] DTC reading wrapper
- [ ] Error handling + auto-reconnect

### 3. TUI Dashboard (Medium Priority)
**Goal:** Visual live data display

**Tasks:**
- [ ] Basic ratatui setup (terminal init, event loop)
- [ ] Dashboard layout (4 gauges: RPM, speed, temp, load)
- [ ] ASCII art gauge rendering (bar + value)
- [ ] PSX color scheme (#0000CD blue, #00FF00 green, #FF0000 red)
- [ ] Keyboard input (1-4 for views, Q for quit)
- [ ] 60 FPS render loop

**Gauge Design:**
```
┌───────────┐
│    RPM    │
│           │
│   2450    │
│  ████░░░  │  ← Progress bar (0-7000 rpm)
└───────────┘
```

### 4. DTC View (Low Priority)
**Goal:** Display trouble codes

**Tasks:**
- [ ] List view with scrolling
- [ ] Code + description display
- [ ] Freeze frame data (Mode 02)
- [ ] Clear codes confirmation dialog

### 5. Data Logging (Low Priority)
**Goal:** Persistent session storage

**Tasks:**
- [ ] SQLite schema (sessions, readings, dtcs tables)
- [ ] Session start/stop recording
- [ ] CSV export function
- [ ] Session replay viewer

### 6. Polish (Future)
**Goal:** Production-ready tool

**Tasks:**
- [ ] Config file editor in TUI
- [ ] Multiple vehicle profiles
- [ ] Performance metrics (0-60 timer)
- [ ] Fuel economy calculator
- [ ] Documentation + README updates
- [ ] Binary releases (Linux, macOS)

## Immediate Next Steps (Hardware Testing)

**Goal:** Validate prototype with real ELM327 hardware

**Requirements:**
1. Install Rust toolchain: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
2. Acquire ELM327 v1.5+ USB adapter (~$20)
3. Access to OBD2-compliant vehicle (1996+ US, 2001+ EU)
4. Serial permissions: `sudo usermod -a -G dialout $USER`

**Testing Sequence:**
```bash
# 1. Compile project
cd prototypes/obd2view
cargo build --release

# 2. List serial devices
./target/release/obd2view --list-devices

# 3. Run dashboard (connects to vehicle)
./target/release/obd2view --device /dev/ttyUSB0

# Expected behavior:
# - Blue PSX-themed TUI with 4 gauges
# - Live RPM, speed, temperature, load
# - Green gauges (normal), yellow (medium), red (high)
# - Press Q to quit
```

**Success Criteria:**
- ✅ Compiles without errors
- ✅ Connects to ELM327 (initialization sequence succeeds)
- ✅ Displays live RPM (updates ~5 Hz)
- ✅ All gauges render correctly
- ✅ No crashes or panics during 5-minute idle
- ✅ Keyboard input responsive (Q to quit)

## Hardware Requirements

**To test with real vehicle:**
- ELM327 v1.5+ USB adapter (~$20 on Amazon)
- OBD2-compliant vehicle (1996+ US)
- Linux system (macOS/WSL also work)
- Serial permissions: `sudo usermod -a -G dialout $USER`

**Mock Testing (No Hardware):**
- Use `mockall` crate for ELM327 trait mocking
- Simulate responses for unit tests
- Test parser logic independently

## Resources

- [ELM327 Command Reference](https://www.elmelectronics.com/wp-content/uploads/2016/07/ELM327DS.pdf)
- [OBD2 PID Cheat Sheet](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [Ratatui Book](https://ratatui.rs/)
- [tokio-serial Examples](https://github.com/berkowski/tokio-serial)

---

**Status:** Foundation complete, ready for protocol implementation. Next session should focus on ELM327 serial I/O.
