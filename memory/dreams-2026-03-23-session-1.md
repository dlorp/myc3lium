# OFF-HOURS DREAMS: Session 1 (2026-03-23 00:00 Alaska)

**Session ID:** a95d58ec-dfcf-4872-a9e4-4b1364fd70eb
**Timestamp:** 2026-03-23 07:00 UTC (2026-03-22 23:00 Alaska)
**Rotation:** RESEARCH or PROJECT REVIEW (switched to PROJECT REVIEW + IDEATION due to search API downtime)

---

## PROJECT CONTEXT REVIEW

From yesterday's work (2026-03-22):
- **myc3lium:** Full stack operational! Dual-radio mesh (HaLow 900 MHz + LoRa 915 MHz) → BATMAN-adv → Reticulum encrypted overlay → React/Vite GUI with FastAPI backend
- **PR #44:** GUI live integration complete, security reviewed, awaiting CI completion and merge
- **Recent repos:** OBD2-TUI, EJ22-tracker, garage-buddy, NES/GBA ROM tools, PSX tools, ASCII demoscene, terrain generators

---

## DREAM 1: OBD2 Save State Manager (PSX Memory Card Aesthetic)

**Motivation:** OBD2 DTCs (diagnostic trouble codes) are ephemeral — they clear when you fix the issue or disconnect the battery. But what if you could save snapshots of your car's "state" like PSX memory card saves?

**Concept:**
- TUI that connects to OBD2 adapter (ELM327)
- Periodic polling (configurable: every 5min, 1hr, daily)
- Save "snapshots" of:
  - All active DTCs (P0xxx codes)
  - Freeze frame data (conditions when code was set)
  - Live sensor data (RPM, coolant temp, MAF, O2 sensors, etc.)
  - Calculated stats (fuel trim, ignition timing)
- Storage format: `.mcr`-inspired binary format (PSX memory card aesthetic)
- Visualization: PSX memory card manager UI in terminal
  - Grid of save slots (15 blocks like PSX)
  - Each snapshot shows: timestamp, DTC count, critical sensors
  - Compare two snapshots side-by-side (diff view)
  - Export to JSON for r³LAY integration

**Tech Stack:**
- Rust (tokio for async polling)
- `ratatui` TUI framework
- `obd` crate or raw AT commands to ELM327
- Custom binary serialization (PSX .mcr homage)
- Optional: SQLite for query-able history

**Aesthetic:**
- PSX blue gradient background
- Memory card grid icons (animated when saving)
- Monospace font, 4:3 aspect ratio feel
- Sound effects (optional): PSX "save complete" beep

**Use Case:**
- Track intermittent issues over time
- Compare sensor values before/after repairs
- Log data for r³LAY automotive category
- Share snapshots with mechanics (export to JSON)

**Next Steps:**
- Prototype ELM327 connection in Rust
- Design binary snapshot format (.obd extension?)
- Build PSX memory card TUI layout

---

## DREAM 2: NES Tile Atlas Generator (Procedural ROM Art)

**Motivation:** NES CHR-ROM tiles are 8x8 pixel art masterpieces. What if you could generate procedural "fake ROMs" that look authentic but are algorithmically created?

**Concept:**
- Input: Pattern rules (e.g., "dungeon walls", "forest tiles", "sci-fi corridors")
- Output: NES CHR-ROM format (8x8 tiles, 2bpp encoding, 4-color palettes)
- Algorithm:
  - WFC (Wave Function Collapse) for tile adjacency rules
  - Cellular automata for organic patterns (caves, trees)
  - Symmetry constraints (vertical/horizontal flip for walls)
  - Palette cohesion (enforce NES palette constraints)
- Export formats:
  - `.chr` file (loadable in Mesen, FCEUX)
  - PNG atlas (256 tiles, 16x16 grid)
  - JSON metadata (tile IDs, tags, adjacency rules)

**Advanced Features:**
- **Tile Mutator:** Take existing ROM's CHR data, mutate it slightly → generate variations
- **Palette Swap Engine:** Apply different NES palettes to same tiles
- **Animated Tiles:** Generate frame sequences (water, fire, spinning coins)
- **Metatile Builder:** Combine 2x2 or 4x4 tiles into coherent scenes

**Aesthetic:**
- NES color palette (52 colors)
- Scanline CRT shader (optional)
- Famicon-style UI borders

**Use Case:**
- Indie game devs (NES homebrew)
- Procedural roguelikes (generate dungeons on the fly)
- Art projects (NES-style generative art)
- Game preservation (study authentic tile patterns)

**Tech Stack:**
- Rust for performance (WFC + CA are CPU-heavy)
- `image` crate for PNG export
- Custom NES 2bpp encoder
- CLI + optional TUI (ratatui)

**Next Steps:**
- Implement WFC in Rust (start simple: 3x3 grid)
- Parse existing .chr files for training data
- Build NES palette constraint system

---

## DREAM 3: F91W Sensor Watchface Protocol (Sensor Watch + BLE)

**Motivation:** Sensor Watch is a hackable Casio F91W PCB replacement with sensors. But what if you could stream live data to/from it via BLE for off-watch visualization?

**Concept:**
- **On-watch:** Custom Sensor Watch firmware (C)
  - BLE UART service (Nordic UART or custom GATT)
  - Stream sensor data: temp, lux, accelerometer, pressure (if modded)
  - Receive commands: change watchface, trigger actions
- **Off-watch:** Companion TUI/GUI (Rust or Python)
  - Connect via BLE (bluez on Linux, CoreBluetooth on Mac)
  - Real-time graphs (temperature over time, step count)
  - Watchface designer: Preview changes before flashing
  - Data logger: SQLite database of sensor history

**Protocol Design:**
```
WATCH → HOST:
  T:23.5       # Temperature (°C)
  L:120        # Lux (light intensity)
  A:0.2,0.1,-9.8  # Accelerometer (x,y,z in m/s²)
  B:85         # Battery %

HOST → WATCH:
  F:02         # Switch to watchface ID 02
  S:1          # Start logging (1=on, 0=off)
  C:RRGGBB     # Set LED color (if modded)
```

**Aesthetic:**
- Terminal UI with ASCII art watch outline
- Live updating digits (ncurses-style refresh)
- Graph panels (sparklines for sensors)
- GameBoy 4-color palette option

**Use Cases:**
- DIY fitness tracking (log steps, sleep movement)
- Environment monitoring (room temp, light exposure)
- Watchface development (test without flashing)
- Data export for r³LAY "electronics" category

**Tech Stack:**
- **Firmware:** Sensor Watch SDK (C), BLE library (custom or adapt existing)
- **Host:** Rust (`btleplug` for BLE) + `ratatui` TUI
- **Storage:** SQLite for sensor logs
- **Optional:** Web dashboard (WASM + charts.js)

**Challenges:**
- F91W battery life (BLE is power-hungry → need sleep modes)
- BLE range (limited to ~10m indoors)
- Sensor Watch hardware mods (BLE module + antenna)

**Next Steps:**
- Research Sensor Watch BLE capabilities (hardware limitations)
- Prototype UART protocol (simple temp streaming)
- Build mock TUI with fake data (validate UX)

---

## DREAM 4: Procedural Metro Map Generator (HDLS Transit System)

**Motivation:** Transit maps are beautiful constraint-based designs. HDLS (the ARG lore project) needs a metro system. What if you could procedurally generate schematic metro maps?

**Concept:**
- Input: City geography (node coordinates, districts)
- Algorithm:
  - Generate lines connecting key nodes (A* pathfinding)
  - Simplify to 45° and 90° angles only (schematic style)
  - Color assignment (max 12 lines, distinct hues)
  - Station spacing (avoid overcrowding)
  - Interchange detection (transfer stations)
- Output:
  - SVG map (scalable, clean)
  - PNG render (print-ready)
  - JSON metadata (line IDs, station names, connections)

**Aesthetic Styles:**
- **London Underground** (Harry Beck classic, strict angles)
- **Tokyo Metro** (curved lines, dense)
- **Retro CRT** (phosphor glow, scanlines)
- **ASCII Art** (pure terminal rendering, box-drawing chars)

**Advanced Features:**
- **Time-based Animation:** Show network growth over decades
- **Ridership Heatmap:** Line thickness = passenger volume
- **Disruption Simulator:** Red X's for closed stations
- **Multi-modal:** Buses, trams, ferries (different line styles)

**Use Cases:**
- HDLS world-building (t3rra1n integration)
- Procedural city generators (game dev)
- Data visualization (represent any network as a metro map)
- Art prints (generative transit posters)

**Tech Stack:**
- Rust for generation (petgraph for graph algorithms)
- SVG rendering (`svg` crate)
- Optional: WebAssembly for interactive web version
- Color palette from real metro systems (TfL, MTA, Tokyo)

**Next Steps:**
- Implement schematic angle snapping (45°/90° only)
- Build simple graph → SVG pipeline
- Study real metro map design rules (spacing, legibility)

---

## DREAM 5: LoRa Packet Sniffer (Meshtastic Network Viz)

**Motivation:** LoRa mesh networks (Meshtastic) broadcast packets openly. What if you could passively sniff and visualize the network topology in real-time?

**Concept:**
- **Hardware:** LoRa radio (SX1262, SX1276) in promiscuous mode
- **Software:** Capture all packets on frequency (e.g., 915 MHz)
- **Decoding:** Parse Meshtastic protocol (protobuf)
  - Extract: Node IDs, positions (GPS), SNR, RSSI
  - Identify: Message types (text, position, telemetry)
- **Visualization:** Live TUI network graph
  - Nodes as circles (size = signal strength)
  - Edges as lines (animated on packet RX)
  - Map overlay (if GPS data available)
  - Packet inspector panel (hex dump + decoded fields)

**Aesthetic:**
- Cyberpunk terminal (green phosphor + scanlines)
- ASCII art map (if GPS data present)
- Real-time packet log (scrolling hex dump)
- Signal strength bars (RSSI meter)

**Privacy Note:**
- Meshtastic messages can be encrypted (AES256)
- Sniffer respects encryption (only shows metadata, not content)
- Use case: Network debugging, not eavesdropping

**Use Cases:**
- Meshtastic network troubleshooting (find dead zones)
- RF propagation analysis (SNR vs distance)
- Mesh topology research (how do nodes route?)
- Off-grid comms monitoring (ham radio + LoRa)

**Tech Stack:**
- Rust (async packet capture)
- `lora_phy` crate or raw SPI to SX126x
- Protobuf decoding (`prost` crate)
- `ratatui` for TUI
- Optional: Export to JSON for analysis

**Next Steps:**
- Test SX1262 in RX continuous mode (promiscuous)
- Decode Meshtastic protobuf schema
- Build packet capture loop (async Rust)

---

## DREAM 6: GBA Save File Time Machine (Pokemon Gen 3 Focus)

**Motivation:** You have a GBA save parser. What if you could track save file evolution over time and visualize changes?

**Concept:**
- **Input:** Multiple .sav files from same game (different timestamps)
- **Analysis:**
  - Diff engine: Compare saves byte-by-byte
  - Semantic diff: "Pikachu leveled 5 → 12", "Caught Zapdos", "Badge count 3 → 5"
  - Timeline view: Horizontal axis = time, vertical = progress
- **Visualization:**
  - TUI timeline (ncurses-style)
  - Each save = checkpoint on timeline
  - Highlight changes (green = progress, red = losses)
  - Drill down: View full save state at any point

**Pokemon Gen 3 Features:**
- Party Pokemon comparison (species, levels, moves)
- Pokedex completion % over time
- Item inventory diff
- Badge progression
- Playtime tracking

**Advanced:**
- **Save State Repair:** Detect corruption, offer fixes
- **Cheating Detection:** Flag impossible changes (instant level 100)
- **Export:** Generate progress report (markdown, PDF)

**Aesthetic:**
- GameBoy Advance color palette (4 shades per channel)
- GBA BIOS startup animation (optional Easter egg)
- Pixel art Pokemon sprites in TUI

**Use Cases:**
- Speedrun analysis (track route optimization)
- Nostalgia trips (review childhood saves)
- Save file forensics (lost data recovery)
- ROM hack testing (validate progression)

**Tech Stack:**
- Extend existing `gba-save-parser` (Rust)
- `ratatui` for TUI timeline
- SQLite for save history database
- Optional: Image export (timeline as PNG)

**Next Steps:**
- Implement byte-level diff algorithm
- Parse Pokemon data structures (party, Pokedex)
- Build timeline UI mockup

---

## SESSION SUMMARY

**Search APIs down:** SearXNG offline, Brave API missing key → pivoted to project review + ideation
**Projects reviewed:** 20+ repos (myc3lium, r³LAY, OBD2-TUI, NES/GBA tools, PSX tools, terrain generators)
**Dreams generated:** 6 concepts (OBD2 saves, NES tiles, F91W BLE, metro maps, LoRa sniffer, GBA save diff)
**Alignment check:** All ideas follow whitelist (tools, retro, procedural, local-first, DIY aesthetic)
**Next rotation (00:00):** PROTOTYPE or IDEATION

**Session end:** 2026-03-23 08:00 UTC (2026-03-23 00:00 Alaska)
**Duration:** 60 minutes
**Output:** 6 detailed project concepts for morning review
