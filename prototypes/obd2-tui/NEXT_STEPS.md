# Next Steps for OBD2-TUI

## Immediate (Week 1)

### 1. Complete Core Modules
- [ ] Finish `src/elm327/commands.rs` - AT command builders
- [ ] Finish `src/elm327/parser.rs` - Response parsing utilities
- [ ] Implement `src/elm327/dtc.rs` - DTC read/clear functions
- [ ] Add integration tests for serial communication

### 2. Set Up Project Structure
- [ ] Create `Cargo.toml` with dependencies:
  ```toml
  [dependencies]
  ratatui = "0.26"
  crossterm = "0.27"
  tokio = { version = "1.36", features = ["full"] }
  tokio-serial = "5.4"
  serde = { version = "1.0", features = ["derive"] }
  serde_json = "1.0"
  csv = "1.3"
  chrono = "0.4"
  ```
- [ ] Set up CI/CD (GitHub Actions for Rust lint/test)
- [ ] Create `.gitignore` for Rust projects

### 3. Minimal TUI Prototype
- [ ] Basic ratatui app structure with event loop
- [ ] Single-panel layout showing RPM in real-time
- [ ] Keyboard input handling (Q to quit)
- [ ] Mock serial port for development (no hardware needed yet)

**Goal:** Running TUI that displays mock RPM data at 10 Hz refresh

---

## Short Term (Weeks 2-3)

### 4. Full Dashboard Implementation
- [ ] Multi-panel layout (sensors, DTCs, status)
- [ ] Live graphing with sparklines (ratatui widgets)
- [ ] Gauge visualization for RPM/speed
- [ ] Color-coded alerts (green/yellow/red thresholds)
- [ ] Navigation between dashboard/DTC viewer/logger

### 5. DTC Functionality
- [ ] Embed standard P0xxx code database (JSON)
- [ ] DTC read and display with descriptions
- [ ] Clear codes with confirmation prompt
- [ ] Freeze frame capture and display

### 6. PSX Visual Theme
- [ ] Define color palette constants
- [ ] Custom border styles (geometric, PSX-inspired)
- [ ] Optional scan-line overlay effect
- [ ] Smooth animations for value changes

**Goal:** Fully functional dashboard with DTCs, no hardware yet

---

## Medium Term (Weeks 4-5)

### 7. Hardware Integration
- [ ] **Acquire ELM327 adapter** (Bluetooth or USB, ~$15-25)
  - Recommended: BAFX Products or OBDLink adapters
  - Verify compatibility with tokio-serial
- [ ] Test with actual vehicle (1996+ OBD-II compliant)
- [ ] Debug protocol detection edge cases
- [ ] Optimize polling strategy for real ECU response times
- [ ] Handle connection dropouts gracefully

### 8. Data Logger
- [ ] Implement CSV recording with timestamps
- [ ] Session management (start/stop/pause)
- [ ] File rotation and compression (gzip)
- [ ] Playback mode for reviewing past sessions
- [ ] Export utilities (Markdown reports, summary stats)

### 9. Configuration System
- [ ] TOML config file parsing
- [ ] Per-vehicle profiles (save VIN-specific settings)
- [ ] Unit preferences (imperial/metric toggle)
- [ ] Custom PID definitions
- [ ] Hot-reload on SIGHUP

**Goal:** Working with real hardware, logging data to CSV

---

## Long Term (Weeks 6-8)

### 10. Advanced Features
- [ ] Multi-ECU support (some vehicles have multiple)
- [ ] Manufacturer-specific PIDs (Subaru SSM, etc.)
- [ ] Alert thresholds with notifications
- [ ] Plugin system for custom decoders
- [ ] GPS integration (correlate data with location)

### 11. Performance Optimization
- [ ] Profile with `cargo flamegraph`
- [ ] Optimize PID polling scheduler
- [ ] Reduce memory allocations in hot paths
- [ ] Benchmark against target metrics (<16ms frame time)

### 12. Documentation & Release
- [ ] User guide (installation, hardware setup, usage)
- [ ] Developer docs (architecture, contributing)
- [ ] Demo video or GIF (asciinema recording)
- [ ] GitHub README with screenshots
- [ ] Release v0.1.0 with prebuilt binaries (Linux/macOS/Windows)

### 13. Community & Ecosystem
- [ ] Post to /r/rust, Hacker News, automotive forums
- [ ] Gather feedback and bug reports
- [ ] Consider Subaru-specific features (AVCS, boost, etc.)
- [ ] Explore STN1110/2120 support (faster variants)

**Goal:** Public release with documentation and community traction

---

## Stretch Goals (Post-v1.0)

- **Web Dashboard:** Optional WebSocket server for phone/tablet viewing
- **CAN Bus Analysis:** Raw CAN frame viewer for reverse engineering
- **Sensor Calibration:** Custom scaling for aftermarket sensors
- **Data Visualization:** External tool for plotting CSV logs (Python/gnuplot)
- **OBD Simulator Mode:** Test without hardware (virtual ECU)
- **Multi-Language Support:** Translations for UI strings

---

## Testing Checklist

### Unit Tests
- [x] PID decoding accuracy (all common PIDs)
- [ ] AT command builders
- [ ] Protocol detection logic
- [ ] CSV export format validation
- [ ] DTC parser correctness

### Integration Tests
- [ ] Mock serial port (simulated ELM327 responses)
- [ ] Full command/response cycle
- [ ] Connection timeout handling
- [ ] Multi-frame response assembly

### Hardware Tests (with real vehicle)
- [ ] Protocol auto-detection (ISO, KWP, CAN)
- [ ] All supported PIDs read correctly
- [ ] DTC read/clear functionality
- [ ] Connection stability over time
- [ ] Battery safety (don't drain vehicle battery)

### UI/UX Tests
- [ ] Keyboard navigation works smoothly
- [ ] No flicker/tearing in terminal
- [ ] Error messages are clear and actionable
- [ ] Config changes take effect without restart
- [ ] Graceful degradation on connection loss

---

## Research & Learning

- [ ] Read ELM327 datasheet thoroughly
- [ ] Study OBD-II standard (SAE J1979)
- [ ] Review Subaru-specific PIDs and SSM protocol
- [ ] Explore ratatui examples and patterns
- [ ] Benchmark tokio-serial performance limits

---

## Decision Points

1. **Language choice:** Rust confirmed (performance + safety)
2. **TUI framework:** ratatui confirmed (mature, well-documented)
3. **Async runtime:** tokio confirmed (industry standard)
4. **Data format:** CSV confirmed (universal, simple)
5. **Theme:** PSX aesthetic confirmed (blue/gray, scan-lines)

**No blockers identified.** Path forward is clear.

---

## Resources

- **ELM327 Datasheet:** https://www.elmelectronics.com/wp-content/uploads/2017/01/ELM327DS.pdf
- **OBD-II PIDs:** https://en.wikipedia.org/wiki/OBD-II_PIDs
- **ratatui Book:** https://ratatui.rs/
- **tokio-serial:** https://docs.rs/tokio-serial/latest/tokio_serial/

**Hardware:**
- BAFX Products Bluetooth OBD2 (~$25): Amazon B005NLQAHS
- OBDLink MX+ (~$100, faster, more reliable): ScanTool.net
- Budget USB ELM327 (~$10): eBay/AliExpress (quality varies)

---

**Current Status:** Concept phase complete. Ready to begin implementation.

**Next Session:** Start with `Cargo.toml` and minimal TUI prototype.

