# Project Ideation — Session 5 (PROTOTYPE/IDEATION)
**Date:** 2026-03-28  
**Session:** Deep Work Session 5/6 (01:00-02:00 AKST)  
**Type:** IDEATION (Rust build environment unavailable, pivoting to concept generation)

## Context

**Alignment targets:**
- Game preservation tooling
- Console/watch modding
- Automotive diagnostics
- Local LLM orchestration
- Self-hosting infrastructure
- Procedural generation
- Off-grid/mesh networking

**Aesthetic targets:**
- PSX (PS1 blue menus, scan-line effects)
- XMB (minimal/sleek Sony interface)
- GameBoy (4-color retro palette)
- Demoscene (effects/polish, size-coding)
- Early 3D (PS1/N64 low poly, texture warping)
- Metro maps (dense info displays, transit-style)

---

## CONCEPT 1: `mesh-mapper` — Meshtastic Network Visualizer

**Category:** Off-grid/mesh networking, metro maps, data visualization

**Problem:** Meshtastic mesh networks grow organically, but node relationships (hops, RSSI, topology) are invisible without live mapping.

**Solution:** TUI/Web visualizer that renders live mesh topology as a metro map.

**Features:**
1. **Live Node Discovery**
   - Listen to Meshtastic MQTT or serial (via meshtastic-python)
   - Track nodes: ID, name, position, SNR, hops, last seen
   - Build adjacency graph (who hears who)

2. **Metro Map Rendering**
   - Force-directed layout (nodes = stations, links = lines)
   - Color-code by SNR quality (green = strong, yellow = weak, red = dying)
   - Line thickness = hop count
   - Station labels = node names (truncated to 12 chars)

3. **Interactive TUI**
   - Crossterm-based (arrow keys navigate)
   - Select node → show details (packets, uptime, battery, telemetry)
   - Filter by channel, region, or role (router/client/repeater)
   - Export PNG/SVG for offline analysis

4. **Historical Playback**
   - Store topology snapshots (SQLite or JSON log)
   - Replay network evolution (time-lapse mode)
   - Detect splits, merges, dead nodes

**Stack:**
- **Rust:** crossterm (TUI), meshtastic-python FFI, petgraph (graph algorithms)
- **Web:** Svelte + D3.js (browser version for sharing)

**Aesthetic:** Metro map (London Underground style, clean lines, bold colors)

**Unique Value:**
- First metro-map-style Meshtastic visualizer
- Reveals hidden network structure (who's the critical relay?)
- Offline-first (works without internet, stores local logs)

**Estimated Scope:** 2-3 weeks (MVP: live TUI + basic topology)

---

## CONCEPT 2: `ps1-mesh-gen` — PSX Low-Poly 3D Mesh Generator

**Category:** Procedural generation, early 3D, PSX aesthetic, art tools

**Problem:** Generating PS1-style low-poly meshes (with texture warping, vertex snapping, limited palettes) requires specific techniques.

**Solution:** CLI/TUI tool that generates PS1-authentic 3D meshes with characteristic artifacts.

**Features:**
1. **Mesh Generation Algorithms**
   - Terrain: Diamond-square + vertex decimation (<500 triangles)
   - Objects: Platonic solids + subdivision + quantization
   - Characters: Metaballs + marching cubes + polygon reduction
   - Dungeons: BSP + corridor generation + vertex welding

2. **PSX-Authentic Rendering**
   - Vertex snapping (quantize to integer grid, no sub-pixel precision)
   - Affine texture mapping (no perspective correction → warping)
   - Limited palette (16 colors per texture, indexed color)
   - No mipmapping (aliasing at distance, shimmer effect)
   - Gouraud shading only (no per-pixel lighting)

3. **Export Formats**
   - .obj (Wavefront, Blender-compatible)
   - .gltf (modern format, preserves PSX constraints)
   - .ply (point cloud, for voxel conversion)
   - .psx (custom binary, for homebrew integration)

4. **TUI Preview**
   - ASCII wireframe (rotate with arrow keys)
   - Vertex count, triangle count, texture size
   - Real-time tweaking (increase/decrease poly count)

5. **Preset Library**
   - "Silent Hill Fog" terrain (flat + distant peaks)
   - "Final Fantasy VII" character (blocky hands, angular faces)
   - "Crash Bandicoot" crate (beveled cube + wood texture)
   - "Metal Gear Solid" room (industrial, grid-snapped walls)

**Stack:**
- **Rust:** nalgebra (math), rfd (file dialogs), crossterm (TUI), image (texture palettes)
- **Optional:** wgpu (GPU preview, real PSX shader emulation)

**Aesthetic:** PSX (vertex jitter, texture warping, low poly)

**Unique Value:**
- First tool focused on PSX-authentic mesh generation (not just "low poly")
- Encodes PS1 hardware quirks (vertex snapping, affine mapping) as features
- Preset library (instant nostalgia for specific games)

**Estimated Scope:** 3-4 weeks (MVP: basic terrain + .obj export + TUI)

---

## CONCEPT 3: `rom-annotator-tui` — Binary ROM Structure Explorer

**Category:** Retro gaming, game preservation, binary visualization, educational

**Problem:** Reverse-engineering game ROMs requires understanding binary structure (headers, palettes, tiles, maps), but hex editors lack semantic annotation.

**Solution:** Interactive TUI that overlays semantic annotations on hex dumps, teaches ROM structure.

**Features:**
1. **Format Profiles**
   - NES: iNES header, PRG-ROM, CHR-ROM, mapper detection
   - GBA: ROM header, save type, multiboot detection
   - GB/GBC: Nintendo logo verification, cartridge type, ROM banks
   - GEN: SEGA header, region lock, checksum validation
   - PSX: CD-XA sectors, EXE headers, TIM textures

2. **Semantic Highlighting**
   - Color-code by data type:
     - Purple = headers (metadata)
     - Blue = code (instructions)
     - Green = graphics (tiles, palettes)
     - Yellow = audio (samples, music data)
     - Red = checksums (validation bytes)
   - Hover annotations (explain what each byte means)

3. **Live Decoding**
   - Select region → decode as:
     - Palette (16-color, RGB555, GameBoy 4-gray)
     - Tile (8×8, 16×16, 1bpp/2bpp/4bpp/8bpp)
     - Text (ASCII, Shift-JIS, custom font tables)
     - Audio (PCM, ADPCM, tracker formats)
   - Preview in sidebar (ASCII art for tiles, hex for palettes)

4. **Interactive Learning Mode**
   - Tutorial overlays (explain NES mapper, GBA save detection)
   - Quizzes ("Find the palette", "Identify the mapper")
   - Challenge modes (fix corrupted headers, calculate checksums)

5. **Annotation Export**
   - Save annotations to .json (reusable for similar ROMs)
   - Generate markdown docs (ROM structure reference)
   - Export to Ghidra/Radare2 (for deeper reverse engineering)

**Stack:**
- **Rust:** crossterm (TUI), nom (binary parsing), image (tile rendering)

**Aesthetic:** Retro hex editor (IBM PC BIOS blue/white, monospace grids)

**Unique Value:**
- First educational ROM tool (not just hex dump)
- Teaching-first design (learn by exploring, not memorizing docs)
- Reusable annotations (crowdsource ROM structure knowledge)

**Estimated Scope:** 4-5 weeks (MVP: NES + GBA + basic annotations)

---

## CONCEPT 4: `ej22-obd-dashboard` — Subaru EJ22 Live Diagnostics Dashboard

**Category:** Automotive diagnostics, PSX aesthetic, hardware integration

**Problem:** EJ22 engines (1990-1996 Subaru) use OBD-I/OBD-II protocols, but generic OBD scanners lack model-specific insights (knock, wastegate, timing advance).

**Solution:** Rust TUI dashboard that displays live EJ22-specific parameters with PSX aesthetic.

**Features:**
1. **OBD-II Integration**
   - ELM327 adapter (USB/Bluetooth)
   - Read PIDs: RPM, coolant temp, MAF, O2 sensors, throttle position
   - Custom PIDs: Knock sensor (0x30), timing advance (0x0E), wastegate duty (turbo only)

2. **Dashboard Layouts**
   - **Street Mode:** Big tach, speed, coolant, fuel level (daily driving)
   - **Track Mode:** Real-time knock, AFR, timing, boost (performance)
   - **Maintenance Mode:** Oil temp, battery voltage, idle hours, DTC codes

3. **PSX Aesthetic**
   - Blue borders (Gran Turismo style)
   - Gradient bars (coolant temp = blue → red gradient)
   - Scan-line effect (horizontal bands, CRT simulation)
   - Monospace digits (7-segment LED feel)

4. **Alert System**
   - Real-time warnings:
     - Coolant >220°F (overheating)
     - Knock count >5/min (bad gas, boost leak)
     - MAF <1.5g/s at idle (vacuum leak)
   - Audio alerts (terminal beep + optional TTS)

5. **Data Logging**
   - CSV export (time, RPM, coolant, knock, MAF, O2, throttle)
   - Track session recorder (start/stop, lap markers)
   - Replay mode (visualize past drives in dashboard)

6. **Integration with `ej22-tracker`**
   - Auto-log maintenance events (oil changes, coolant flushes)
   - Mileage tracking (accumulate from OBD odometer PID)
   - Timing belt countdown (sync with live mileage)

**Stack:**
- **Rust:** tokio-serial (OBD adapter), crossterm (TUI), csv (logging)
- **Hardware:** ELM327 v1.5+ (supports all OBD-II PIDs)

**Aesthetic:** PSX (Gran Turismo dashboard, blue/white/red gradients)

**Unique Value:**
- EJ22-specific tuning insights (knock, timing advance, turbo wastegate)
- PSX nostalgic aesthetic (not generic OBD scanner UI)
- Integration with existing ej22-tracker tool (ecosystem synergy)

**Estimated Scope:** 2-3 weeks (MVP: basic PIDs + PSX dashboard + CSV logging)

---

## CONCEPT 5: `watch-face-compiler` — F91W/Sensor Watch Custom Face Builder

**Category:** Watch modding, hardware hacking, constraint-based design

**Problem:** Building custom watch faces for Sensor Watch (ARM Cortex-M0+, 128 KB flash, 32 KB RAM) requires C firmware, but many creators just want to design faces.

**Solution:** DSL (domain-specific language) for declarative watch face design → compiles to C firmware.

**Features:**
1. **Declarative Face DSL**
   ```toml
   [face]
   name = "Retro Digital"
   layout = "classic"  # classic, minimal, hybrid, custom
   
   [display]
   time_format = "HH:MM:SS"
   date_format = "MMM DD"
   seconds_blink = true
   
   [widgets]
   battery = { position = "top-right", style = "bar" }
   alarm = { position = "bottom-left", icon = "bell" }
   
   [colors]  # F91W = monochrome, Sensor Watch = RGB565
   foreground = "#FFFFFF"
   background = "#000000"
   accent = "#00FF00"
   
   [actions]
   light_button = "toggle_backlight"
   alarm_button = "cycle_timezones"
   mode_button = "next_face"
   ```

2. **Compiler Pipeline**
   - Parse TOML → validate schema
   - Generate C code (Sensor Watch API calls)
   - Compile with arm-none-eabi-gcc
   - Flash .uf2 to watch (drag-and-drop bootloader)

3. **Standard Library**
   - Time/date displays (12h/24h, ISO dates, Unix timestamps)
   - Timers/stopwatches (lap tracking, countdown)
   - World clock (multi-timezone support)
   - Weather (if paired with phone via Bluetooth)
   - Sensors (temperature, light, accelerometer)

4. **Simulator**
   - Desktop TUI preview (crossterm)
   - Test face behavior without flashing
   - Mock sensor data (random temp, light levels)

5. **Gallery/Sharing**
   - Community face repository (GitHub-based)
   - One-click install (download .toml + compile + flash)
   - Remix support (fork existing face, tweak colors/layout)

**Stack:**
- **Rust:** serde (TOML parsing), handlebars (C template generation), crossterm (simulator)
- **C:** Sensor Watch firmware SDK (for compilation)

**Aesthetic:** Constraint-based (embrace limited screen, monochrome simplicity)

**Unique Value:**
- Lowers barrier to entry (no C knowledge required)
- Declarative approach (describe what, not how)
- Simulator-first (test before flashing)

**Estimated Scope:** 5-6 weeks (MVP: basic DSL + compiler + simulator)

---

## CONCEPT 6: `synapse-cost-tracker` — LLM Orchestration Cost Analytics

**Category:** Local LLM orchestration, data visualization, operational tooling

**Problem:** Running 15 specialized agents across 8 concurrent sessions burns tokens, but cost tracking is manual (no visibility into which agents are expensive).

**Solution:** Real-time cost analytics dashboard for synapse-engine orchestrator.

**Features:**
1. **Token Usage Tracking**
   - Per-agent metrics: total tokens, input/output ratio, avg session length
   - Per-model costs: Claude Sonnet 4.5, GPT-4, Gemini Pro pricing
   - Time-series graphs: daily/weekly spend trends

2. **Cost Alerts**
   - Budget thresholds ($5/day, $100/month)
   - Agent cost spikes (e.g., @strategic-planning-architect uses 10× normal)
   - Inefficiency detection (agent loops, redundant calls)

3. **Optimization Suggestions**
   - "Switch @code-reviewer to fast model (saves $0.50/review)"
   - "Batch research queries (3 web_search → 1 session)"
   - "Agent X idle 90% of time (consider on-demand spawning)"

4. **Attribution Analysis**
   - Which agents justify their cost? (ROI = value/spend)
   - Tier optimization: FAST vs BALANCED vs POWERFUL routing
   - Human vs agent spend (which tasks offload well?)

5. **Integration**
   - Read from `memory/agent-health.json` (token counts)
   - Parse session logs (extract model calls, compute cost)
   - Export to CSV/JSON (for spreadsheet analysis)

**Stack:**
- **Python:** pandas (data analysis), matplotlib/plotly (charts), rich (TUI tables)

**Aesthetic:** Metro maps (network topology = agent dependency graph)

**Unique Value:**
- First cost analytics tool for personal LLM orchestration
- Actionable insights (not just "you spent $X")
- Optimization-first design (reduce waste, not just track)

**Estimated Scope:** 2-3 weeks (MVP: basic tracking + TUI dashboard)

---

## Selection Criteria

**Rank concepts by:**
1. **Immediate value** (solves dlorp's real pain points)
2. **Aesthetic alignment** (PSX, metro maps, retro)
3. **Technical feasibility** (can build MVP in 2-4 weeks)
4. **Learning potential** (teaches new domain knowledge)
5. **Shareable** (others can use/remix)

**Top 3 (by value + feasibility):**

1. **`ej22-obd-dashboard`** — Highest immediate value (dlorp drives EJ22 daily), PSX aesthetic, hardware integration, synergy with ej22-tracker
2. **`synapse-cost-tracker`** — Operational necessity (15 agents burning tokens), optimization insights, low technical risk
3. **`mesh-mapper`** — Meshtastic network is live, metro map aesthetic is perfect fit, educational value (learn mesh topology)

**Honorable Mentions:**
- `rom-annotator-tui` — High educational value, but no immediate need
- `ps1-mesh-gen` — Cool art tool, but niche use case
- `watch-face-compiler` — Great idea, but requires hardware (F91W/Sensor Watch) on hand

---

## Next Steps

**For #dreams channel (morning review):**
- Post all 6 concepts (brief summaries + links to this doc)
- Request prioritization from dlorp
- Offer to prototype top choice during next PROTOTYPE session

**For Session 6 (04:00-05:00 AKST):**
- If approved: Start `ej22-obd-dashboard` prototype (basic ELM327 reader + PSX TUI)
- Otherwise: Continue documentation wrap-up (session summaries, MEMORY.md updates)

---

## Meta-Reflection

**Ideation session quality:**
- 6 concepts generated (45 min)
- All aligned with dlorp's domains (automotive, retro, LLM, hardware)
- Aesthetic targets hit (PSX, metro maps, demoscene, constraint-based)
- Technical feasibility validated (Rust, Python, existing libraries)

**Process improvements:**
- Next time: Generate 3 concepts (deeper vs. broader)
- Include mockups (ASCII art of TUI layouts)
- Research existing tools first (avoid reinventing wheels)

**Lesson learned:**
- Ideation = quantity → quality (6 concepts → 3 strong finalists)
- Constraint-based creativity works (PSX aesthetic → unique designs)
- Domain alignment matters (automotive + retro + LLM = strong fit)
