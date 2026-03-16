# myc3lium - Implementation Roadmap

**Total Timeline:** 14 weeks (part-time, ~15-20 hours/week)  
**Phases:** 7 phases, each 2 weeks  
**Validation:** Each phase must pass acceptance criteria before proceeding

---

## Phase 1: Core GUI Framework + Shader Foundation
**Duration:** 2 weeks  
**Goal:** Basic PyQt6 application with teletext rendering working

### Tasks

**Week 1:**
1. Set up development environment
   - Install PyQt6, ModernGL, dependencies
   - Create project structure (`src/`, `shaders/`, `data/`)
   - Configure EGLFS for Pi 4 (edit `/boot/config.txt`)

2. Basic PyQt6 window
   - `src/main.py` - Entry point
   - `src/ui/main_window.py` - Main window class
   - Run in dev mode (X11/Wayland)

3. Shader pipeline foundation
   - Load GLSL shaders (text.vert, text.frag)
   - Create FBO (framebuffer object) chain
   - Render simple triangle test

**Week 2:**
4. Teletext character renderer
   - 40×25 character grid
   - Monospace font atlas (bitmap font → GPU texture)
   - Fragment shader: 8-color palette quantization
   - Render "Hello, World" in teletext style

5. CRT post-processing
   - `shaders/crt.frag` - Scanlines, vignette, phosphor glow
   - FBO pipeline: Text → CRT → Screen
   - Toggle effects on/off (for debugging)

6. Page navigation framework
   - `src/ui/page_manager.py` - Page routing
   - Implement P100 (main menu) with hardcoded text
   - Number key navigation (P100, P200, etc.)

### Deliverables
- ✅ PyQt6 app runs on Pi 4 (EGLFS, no desktop)
- ✅ Teletext 40×25 grid renders text
- ✅ CRT shader effects work
- ✅ P100 main menu displays
- ✅ Number keys navigate between placeholder pages

### Acceptance Criteria
- [ ] 60 FPS rendering on Pi 4
- [ ] Text readable in teletext style
- [ ] Scanlines visible
- [ ] P100 → P200 navigation works

---

## Phase 2: Map Rendering + GPS Integration
**Duration:** 2 weeks  
**Goal:** Display ATAK MBTiles maps with GPS position overlay

### Tasks

**Week 3:**
1. MBTiles loader
   - `src/core/map_engine.py` - SQLite reader
   - Query tiles by zoom/x/y
   - Load tile images (PNG/JPEG) from database

2. Web Mercator projection
   - `src/utils/web_mercator.py` - Lat/lon ↔ tile coords
   - Calculate visible tiles for viewport
   - Handle zoom levels (0-18)

3. Tile atlas GPU texture
   - 4096×4096 atlas (256 tiles, 256×256 each)
   - LRU eviction policy
   - Upload tiles to GPU

**Week 4:**
4. Map rendering shader
   - `shaders/map.vert` - Map vertex shader (projection)
   - `shaders/map.frag` - Teletext color quantization (Bayer dithering)
   - Render tiles from atlas

5. GPS integration
   - `src/utils/gps.py` - gpsd interface
   - Read position from LoRa HAT GNSS
   - Overlay ◉ icon on map

6. Zoom/pan controls
   - Touch gestures: pinch zoom, drag pan
   - Keyboard: Arrow keys (pan), +/- (zoom)
   - Smooth transitions

7. Implement P400 (map page)
   - Full-screen map view
   - Status bar with GPS coords
   - Layer toggles

### Deliverables
- ✅ ATAK MBTiles load and display
- ✅ Teletext color quantization on map tiles
- ✅ GPS position overlays on map
- ✅ Zoom/pan gestures work
- ✅ P400 map page functional

### Acceptance Criteria
- [ ] OSM tiles render in teletext palette
- [ ] GPS position updates in real-time
- [ ] Pinch zoom responds smoothly
- [ ] <200ms tile load latency

---

## Phase 3: Mesh Networking Integration
**Duration:** 2 weeks  
**Goal:** Connect to Reticulum, display mesh topology, overlay nodes on map

### Tasks

**Week 5:**
1. Reticulum daemon setup
   - Install RNS (Reticulum Network Stack)
   - Configure `~/.reticulum/config` for LoRa, HaLow, WiFi
   - Test LoRa HAT as RNode (flash firmware if needed)
   - Test HaLow via AutoInterface

2. Mesh manager module
   - `src/core/mesh_manager.py` - RNS Python API interface
   - Discover nodes on network
   - Get node positions (via announce packets)
   - Track link quality (RSSI, latency)

3. Implement P200 (mesh topology)
   - Display node list
   - Show routes (direct vs multi-hop)
   - Traffic statistics

**Week 6:**
4. Mesh overlay on map
   - Render mesh nodes (●) on P400
   - Draw links between nodes (lines)
   - Color by signal strength:
     - Green: >-80dBm
     - Yellow: -80 to -95dBm
     - Red: <-95dBm

5. Node details page (P201)
   - Node name, position, distance
   - Link quality graph
   - Last seen timestamp

6. Test multi-radio routing
   - LoRa: Long-range test (5+ km)
   - HaLow: Medium-range test (1+ km)
   - WiFi mesh: Local test (100m)
   - Verify auto-routing works

### Deliverables
- ✅ Reticulum mesh operational (all 3 radios)
- ✅ Nodes appear on map
- ✅ P200 topology page shows network
- ✅ Link quality visualized

### Acceptance Criteria
- [ ] 3 radios active simultaneously
- [ ] Mesh nodes render on map
- [ ] Multi-hop routing works
- [ ] <1s message propagation (1 hop)

---

## Phase 4: Messaging Workflow
**Duration:** 2 weeks  
**Goal:** Send/receive messages via Meshtastic and LXMF

### Tasks

**Week 7:**
1. Meshtastic bridge daemon
   - `src/daemons/meshtastic_bridge.py` - Serial ↔ internal msg format
   - Connect to LoRa radio via USB serial
   - Parse Meshtastic packets
   - Translate to internal format

2. LXMF integration
   - Use Reticulum's LXMF for encrypted messaging
   - Create LXMF destination
   - Send/receive LXMF messages

3. Message router
   - `src/core/message_router.py` - Unified messaging
   - Auto-select transport (Meshtastic vs LXMF)
   - Meshtastic: LoRa only (compatibility with existing Meshtastic nodes)
   - LXMF: Auto-route over LoRa/HaLow/WiFi (encrypted, multi-hop)

**Week 8:**
4. Message database
   - SQLite: `data/messages.db`
   - Schema: `messages` table (id, timestamp, sender, recipient, transport, body, encrypted)
   - Insert on send/receive
   - Query for inbox/history

5. Implement P300 (inbox)
   - Display messages sorted by timestamp
   - Show transport (LoRa, HaLow, WiFi)
   - Mark read/unread

6. Implement P301 (compose)
   - On-screen keyboard (touch)
   - Recipient selection (node list)
   - Transport selection (auto/manual)
   - Send button → MessageRouter

7. Test messaging
   - Meshtastic: Send to existing Meshtastic network
   - LXMF: Send between two mesh terminals
   - Verify encryption (LXMF)
   - Test multi-hop delivery

### Deliverables
- ✅ Meshtastic bridge operational
- ✅ LXMF messaging works
- ✅ P300 inbox displays messages
- ✅ P301 compose sends messages
- ✅ Message database stores history

### Acceptance Criteria
- [ ] Meshtastic messages send/receive
- [ ] LXMF messages encrypted
- [ ] Multi-hop LXMF delivery works
- [ ] <5s delivery (3 hops)

---

## Phase 5: SDR Integration
**Duration:** 2 weeks  
**Goal:** Satellite tracking, auto-capture, waterfall display

### Tasks

**Week 9:**
1. SoapySDR setup
   - Install SoapySDR + RTL-SDR driver
   - Test RTL-SDR with `SoapySDRUtil --find`
   - Test Ham It Up Plus upconverter

2. Satellite pass prediction
   - `src/utils/satellite.py` - Pyorbital TLE tracking
   - Download TLEs (NOAA, METEOR-M)
   - Calculate AOS/LOS times
   - Display next pass on P500

3. SDR manager daemon
   - `src/daemons/sdr_manager.py` - Background SDR control
   - Schedule satellite passes
   - Auto-start recording 2 min before AOS
   - Call SatDump for decoding

**Week 10:**
4. Waterfall shader
   - `shaders/waterfall.frag` - Real-time FFT waterfall
   - FFT: numpy.fft → GPU texture (scroll down each frame)
   - Color map: Signal strength → teletext palette

5. Implement P501 (RF waterfall)
   - Live waterfall display
   - Frequency tuning controls
   - Gain adjustment
   - Signal detection overlay

6. Implement P500 (satellite tracker)
   - Next pass countdown
   - Auto-capture toggle
   - Last captured image preview
   - [ADD TO MAP] button → georeferenced overlay

7. Test satellite capture
   - Wait for NOAA/METEOR pass
   - Verify auto-capture works
   - Check decoded image quality
   - Add to map as overlay

### Deliverables
- ✅ SDR waterfall displays in real-time
- ✅ Satellite passes auto-capture
- ✅ P500 shows next pass countdown
- ✅ P501 waterfall page functional
- ✅ Decoded satellite images saved

### Acceptance Criteria
- [ ] Waterfall renders at 30 FPS
- [ ] Auto-capture starts 2 min before AOS
- [ ] SatDump decodes APT/LRPT
- [ ] Georeferenced image adds to map

---

## Phase 6: System Configuration
**Duration:** 2 weeks  
**Goal:** All settings configurable from GUI, power management

### Tasks

**Week 11:**
1. Configuration system
   - `src/core/config.py` - TOML config loader
   - `data/config/default.toml` - Default settings
   - `data/config/user.toml` - User overrides
   - Layered config: default < user < runtime

2. Implement P600-P605 (config pages)
   - P600: Radio settings (LoRa, HaLow, WiFi)
   - P601: Reticulum interfaces
   - P602: Meshtastic settings
   - P603: SDR parameters
   - P604: Map sources
   - P605: Display settings (CRT effects, brightness)

3. Apply configuration
   - [APPLY] button → write to `user.toml`
   - Restart daemons (Reticulum, Meshtastic, SDR)
   - Validate before applying

**Week 12:**
4. Battery monitoring
   - `src/core/battery.py` - I2C interface to battery HAT
   - Read voltage, current, percentage
   - Display on P102 (power page)

5. Power management
   - ECO mode (30% battery):
     - Disable WiFi mesh
     - Reduce LoRa TX power to 14dBm
     - Dim display to 50%
   - ULTRA_SAVE mode (15% battery):
     - LoRa RX only (no TX)
     - Disable HaLow
     - Display 25% brightness
     - SDR disabled
   - Auto-shutdown at 5%

6. Implement P101 (system status)
   - Uptime, CPU temp, RAM usage
   - Radio status indicators
   - Battery graph

7. Implement P102 (power/battery)
   - Battery percentage, voltage
   - Estimated runtime
   - Power mode selection
   - Charging status (if plugged in)

### Deliverables
- ✅ All config pages functional
- ✅ Settings persist to TOML files
- ✅ Battery monitoring works
- ✅ Power modes reduce consumption
- ✅ P101, P102 system pages complete

### Acceptance Criteria
- [ ] Config changes apply without reboot
- [ ] Battery percentage accurate
- [ ] ECO mode extends runtime 2x
- [ ] ULTRA_SAVE mode extends 3x

---

## Phase 7: Polish & Optimization
**Duration:** 2 weeks  
**Goal:** Bug fixes, performance tuning, field testing

### Tasks

**Week 13:**
1. Performance optimization
   - Profile GPU rendering (identify bottlenecks)
   - Optimize tile atlas updates (only upload changed tiles)
   - Reduce FFT waterfall CPU usage
   - Tune Python GIL for multi-threading

2. UI polish
   - Smooth page transitions (fade in/out)
   - Loading spinners (map tiles, messages)
   - Error messages (friendly, actionable)
   - Help overlay (press `?` on any page)

3. Accessibility
   - High-contrast mode (toggle CRT effects off)
   - Font size adjustment (40×25 → 30×20 for larger text)
   - Touch target size (min 44×44 pixels)

**Week 14:**
4. Field testing
   - Deploy to Pi 4 with all hardware
   - Test in outdoor environment
   - Battery life benchmarks:
     - Idle (mesh only): Measure runtime
     - Active (map + messaging): Measure runtime
     - SDR (satellite pass): Measure runtime
   - Range testing:
     - LoRa: Max range test
     - HaLow: Max range test
     - WiFi mesh: Max range test

5. Bug fixes
   - Fix issues found during field testing
   - Handle edge cases (GPS loss, radio failure, low battery)
   - Graceful degradation

6. Documentation
   - User manual (`docs/USER_MANUAL.md`)
   - Troubleshooting guide (`docs/TROUBLESHOOTING.md`)
   - API documentation (for future plugins)

### Deliverables
- ✅ 60 FPS sustained on Pi 4
- ✅ All pages functional and polished
- ✅ Field testing complete
- ✅ Battery life benchmarks documented
- ✅ User manual written

### Acceptance Criteria
- [ ] Zero crashes in 8-hour field test
- [ ] 6+ hours battery (active use)
- [ ] LoRa range >5km (urban)
- [ ] All pages <50ms response time

---

## Deployment Process

**Development → Production:**

1. **Development (desktop):**
   ```bash
   git clone <repo> mesh-terminal-gui
   cd mesh-terminal-gui
   pip3 install -r requirements.txt
   python3 src/main.py --dev
   ```

2. **Build for Pi 4:**
   ```bash
   ./build.sh --pi4
   # Creates: dist/mesh-terminal-gui-pi4.tar.gz
   ```

3. **Deploy to Pi 4:**
   ```bash
   scp dist/mesh-terminal-gui-pi4.tar.gz pi@192.168.1.100:~/
   ssh pi@192.168.1.100
   tar -xzf mesh-terminal-gui-pi4.tar.gz
   cd mesh-terminal-gui
   sudo ./install.sh
   ```

4. **Install systemd services:**
   ```bash
   sudo cp systemd/*.service /etc/systemd/system/
   sudo systemctl enable mesh-gui meshtastic-bridge sdr-manager tile-cache
   sudo systemctl start mesh-gui
   ```

5. **Configure EGLFS:**
   ```bash
   sudo nano /boot/config.txt
   # Add:
   # dtoverlay=vc4-kms-v3d
   # gpu_mem=256
   sudo reboot
   ```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **WiFi HaLow driver issues** | Medium | High | Have USB WiFi adapter as fallback |
| **SX1262 HAT incompatibility** | Low | High | Verify RNode firmware compatibility early (Phase 3) |
| **Pi 4 GPU performance** | Low | Medium | Optimize shaders, reduce texture size if needed |
| **Battery life too short** | Medium | Medium | Implement aggressive power management (ECO/ULTRA_SAVE) |
| **GNSS poor accuracy** | Low | Low | Allow manual position entry, use last known position |
| **MBTiles too large for storage** | Low | Low | Use regional tiles only, delete unused zoom levels |
| **Meshtastic protocol changes** | Low | Medium | Monitor Meshtastic releases, update bridge as needed |

---

## Success Metrics

**By end of Phase 7:**

**Functionality:**
- [ ] All 24 pages implemented
- [ ] 3 radios operational simultaneously
- [ ] Messaging works (Meshtastic + LXMF)
- [ ] Maps display offline ATAK tiles
- [ ] Satellite auto-capture functional
- [ ] System fully configurable from GUI

**Performance:**
- [ ] 60 FPS rendering
- [ ] <50ms UI response time
- [ ] 6+ hours battery (active)
- [ ] 10+ hours battery (idle)

**Reliability:**
- [ ] 8+ hours continuous operation (no crashes)
- [ ] Graceful degradation (radio failures)
- [ ] Auto-recovery (GPS loss, tile errors)

**Usability:**
- [ ] No CLI required for normal operation
- [ ] Touch-friendly (all targets >44px)
- [ ] Intuitive navigation (number keys + touch)

---

## Post-Launch Roadmap

**Version 2.0 Features** (Phases 8-10, +6 weeks):
- Camera integration (USB webcam → P503)
- ATAK COT messaging (FreeTAKServer)
- Voice comms (codec2 over mesh)

**Version 3.0 Features** (Phases 11-13, +6 weeks):
- Kismet integration (WiFi/BT wardriving)
- HackRF TX support (transmit capabilities)
- LLM agent (batch processing mode)

**Version 4.0 Features** (Phases 14-16, +6 weeks):
- Multi-device sync (share maps/waypoints)
- Plugin system (community extensions)
- Desktop companion app (monitor from laptop)

---

**Next:** See **TECH_STACK.md** for complete technology specifications.
