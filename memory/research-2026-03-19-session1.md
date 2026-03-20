# Research Deep Dive — 2026-03-19 Session 1 (23:00 AKDT)

**Duration:** 32 minutes (23:03-23:35)
**Search Budget:** 20/20 searches utilized
**Languages:** EN, JP, CN, KR
**Domains:** 6 (automotive, embedded, retro gaming, procedural gen, self-hosting, demoscene)

---

## 🚗 Automotive Research

### OBD2 Diagnostics
- **ELM327 Arduino Integration** - [YouTube Tutorial](https://www.youtube.com/watch?v=kmZ2PUMOKB8)
  - DIY car gauge using modified Bluetooth ELM327 + Arduino
  - Based on OBDuino code
- **Korean DIY Guide** - Naver blog (아두이노 ODB2 ELM327 시뮬레이터)
  - Hands-on tutorial for OBD2 port scanner
  - Korean automotive community resource
- **KWP71 Scan Tool** - [GitHub: kaihara/kwp71scan](https://github.com/kaihara/kwp71scan)
  - Keyword Protocol 71 car scanner for Alfa Romeo 155
  - Arduino + L9637D interface

### Subaru EJ22
- **Official Repair Manual** - [ManualsLib](https://www.manualslib.com/manual/998349/Subaru-Ej22.html)
  - Subaru EJ22 engine official service documentation
  - Complete tear-down and rebuild procedures
- **Japanese Maintenance Forum** - [Kondo Engineering Blog](http://kondoengineering.com/ej22%E7%B6%9A%E3%81%8D%EF%BC%81/)
  - Cosworth EJ22 build notes
  - Baffle plate installation + GRB oil pump upgrades
  - WPC treatment procedures
- **Chinese Resources** - AutoHome forums (汽车之家)
  - Request thread for EJ22/EJ25 installation manuals
  - Community-driven technical support

### Motorsports (IMSA/WEC)
- **2026 LMDh Regulations** - [IMSA Official](https://www.imsa.com/news/2024/06/14/imsa-gtp-race-car-homologations-extended-through-2029/)
  - GTP homologations extended through 2029
  - LMP2 continuation through 2028
- **Hybrid Control Systems** - [Bosch Motorsport](https://www.bosch-motorsport.com/products-and-services/product-highlights/hybrid-system-lmdh/)
  - Hybrid control unit manages power delivery, torque coordination
  - Standardized gearbox casing across manufacturers
- **2026 Updates** - [Motorsport.com](https://www.motorsport.com/wec/news/wec-hypercar-and-imsa-gtp-who-is-introducing-updates-in-2026-and-who-isnt/10786522/)
  - Most manufacturers updating cars for 2026 season
  - Hypercar/GTP grid evolution

---

## 🔧 Embedded Systems & Hardware

### Sensor Watch (F91W Board Replacement)
- **Official Documentation** - [sensorwatch.net](https://www.sensorwatch.net/docs/movement/building/)
  - Building custom firmware for Movement
  - SAM L22 microcontroller platform
- **Face Development Guide** - [New Watch Face Tutorial](https://www.sensorwatch.net/docs/movement/newface/)
  - Single watch face design walkthrough
  - Blink LED example with options

### F91W Custom Firmware
- **Sensor Watch Mod Video** - [YouTube](https://www.youtube.com/watch?v=3y0CbBszH-Y)
  - Custom firmware installation demo
  - PCB replacement process
- **Pluto Project** - [GitHub: carrotIndustries/pluto](https://github.com/carrotIndustries/pluto)
  - Programmable digital watch using MSP430FR6972
  - F91W PCB replacement with compass + IR receiver
  - Software updates via 38 kHz infrared

### Microchip SAM L22
- **Official Datasheet** - [Microchip PDF](https://ww1.microchip.com/downloads/en/DeviceDoc/60001465A.pdf)
  - Ultra-low-power segment LCD microcontroller
  - Built-in SLCD controller
  - Optimized for battery-powered applications

---

## 🎮 Retro Gaming & Preservation

### NES Tools
- **Nixel (CHR Editor)** - [GitHub: xeinherjar/nixel](https://github.com/xeinherjar/nixel)
  - Web-based NES sprite/CHR data editor
  - Load ROM → edit tiles → export
  - Capstone project from Iron Yard Atlanta
- **CHR Extraction Tutorial** - [Adafruit Guide](https://learn.adafruit.com/how-to-hack-roms-to-add-your-own-sprites/editing-sprites)
  - NES cartridge CHR ROM structure (8x8 tiles)
  - Sprite data storage format
  - Pattern table editing

### Game Boy Advance
- **GBA ROM Explorer** - [GitHub: attilathedud/gba_explorer](https://github.com/attilathedud/gba_explorer)
  - View ROM entry point, debug info, game title, version
  - Identify specific game versions
- **GBA Architecture Analysis** - Reddit discussion
  - Highest point of mainstream 2D sprite/tile games
  - Refined SNES with 90s design lessons

### Save File Analysis
- **Saved Game Analyzer** - [RedDragonWebDesign Tool](https://www.reddragonwebdesign.com/projects/saved-game-analyzer/)
  - Web tool for binary save file reverse engineering
  - Diff/labeling for simple binary formats
  - Structure file creation workflow

---

## 🎨 Procedural Generation & Graphics

### PlayStation 1 Rendering
- **PS1 Affine Textures** - [Daniel Ilett Tutorial](https://danielilett.com/2021-11-06-tut5-21-ps1-affine-textures/)
  - PS1 couldn't do perspective-correct texture mapping
  - Wobbly textures from affine mapping
  - HLSL `noperspective` keyword implementation
- **PS1-Style Renderer** - [David Colson Blog](https://www.david-colson.com/2021/11/30/ps1-style-renderer.html)
  - Low poly models + low-res textures
  - Fog effects, affine texture mapping
  - Complete technical breakdown

### Signed Distance Fields
- **Distance Fields Guide** - [Philip Rideout (prideout.net)](https://prideout.net/blog/distance_fields/)
  - Overview of distance field algorithms
  - Cylinder/torus distance functions
  - Coordinate fields and Voronoi diagrams
  - Procedural terrain applications
- **Raymarching SDFs** - [Inigo Quilez](https://iquilezles.org/articles/raymarchingdf/)
  - Elegant way to represent and render 3D objects
  - SDF raymarching techniques

### Noise & Terrain
- **Noise & Fields Demo** - [promptsandmore.com](https://promptsandmore.com/demos/noise-fields.html)
  - Perlin/Simplex noise visualizer
  - Voronoi terrain generation
  - Flow field synthesis

---

## 🌐 Self-Hosting & Networking

### Meshtastic (LoRa Mesh)
- **Official Site** - [meshtastic.org](https://meshtastic.org/)
  - Open-source, off-grid, decentralized mesh network
  - Affordable, low-power devices
- **Off-Grid Communication Guide** - [Seeed Studio Blog](https://www.seeedstudio.com/blog/2025/10/14/off-grid-communication-lora-meshtastic/)
  - LoRa/Meshtastic for disaster recovery
  - Beyond-network connectivity

### Proxmox VE
- **GPU Passthrough to LXC** - [Forum Guide](https://forum.proxmox.com/threads/gpu-passthrough-to-container-lxc.132518/)
  - LXC → Docker GPU passthrough
  - Unprivileged container configuration
- **Jellyfin Hardware Acceleration** - [blog.kye.dev](https://blog.kye.dev/proxmox-gpu-passthrough)
  - GPU passthrough for media transcoding

### TrueNAS ZFS
- **L2ARC Documentation** - [TrueNAS Docs](https://www.truenas.com/docs/references/l2arc/)
  - Adaptive Replacement Cache (ARC) vs L2ARC
  - SSD cache performance tuning
- **L2ARC Tuning Guide** - [TrueNAS Forums](https://forums.truenas.com/t/l2arc-tuning-guide-and-common-misconceptions/33128)
  - Common misconceptions debunked
  - SLOG vs ZIL explanations

### Local LLM Orchestration
- **llamafile** - [Mozilla AI](https://www.mozilla.ai/open-tools/llamafile)
  - Single executable LLM (model weights + inference engine + runtime)
  - Privacy, convenience, offline capability
- **LlamaIndex Agents** - [Official Docs](https://developers.llamaindex.ai/python/framework/use_cases/agents/)
  - Framework for agentic systems
  - Quick agent building tools

---

## 🎨 Demoscene & UI Design

### Demoscene Effects
- **Copper Plasma** - [GitHub: mangobanaani/copperplasma](https://github.com/mangobanaani/copperplasma)
  - React TypeScript demoscene effects studio
  - 1980s/90s graphics nostalgia
  - Optimized Canvas/WebGL implementations
- **256 Bytes Archive** - [256bytes.untergrund.net](http://256bytes.untergrund.net/demo/latest)
  - Fire effects, plasma, Sierpinski demos
  - Minimal code footprint challenges
- **Revision 2025 Report** - [canmom.art](https://canmom.art/adventure/demoscene/revision-2025)
  - Plasma effects, raster/copper bars
  - Oldschool demo cliché techniques

### XMB Interface Design
- **Wikipedia Article** - [XrossMediaBar](https://en.wikipedia.org/wiki/XrossMediaBar)
  - Sony Computer Entertainment GUI
  - Icons spread horizontally, categories vertically
  - PSP/PS3/Blu-ray recorders
- **OpenXMB Reimplementation** - [GitHub: phenom64/OpenXMB](https://github.com/phenom64/OpenXMB)
  - Cross-platform PS3-style interface
  - SynOS/Ubuntu/macOS/Windows support
  - Smooth animations, dynamic background

---

## 📊 Statistics

- **Total Searches:** 20
- **Unique Domains:** 6
- **Languages:** 4 (EN, JP, CN, KR)
- **GitHub Repos Found:** 6
- **Official Documentation:** 4
- **Community Forums:** 3
- **Tutorial Videos:** 2

## 💡 Project Opportunities

1. **EJ22 Maintenance Tracker**
   - Integrate Japanese manual translations
   - Service interval calculator
   - Known issue database

2. **NES/GBA Unified Tile Viewer**
   - Single tool for ROM binary analysis
   - CHR data extraction
   - Sprite sheet export

3. **PS1 Mesh Generator**
   - Procedural low-poly models
   - Affine texture mapping shader
   - Export to PSX-compatible formats

4. **Demoscene TUI Effects Library**
   - Terminal-based plasma/copper bars
   - ASCII sparklines
   - Retro UI toolkit for CLIs

5. **Meshtastic Dashboard**
   - Off-grid network monitor
   - Node health visualization
   - Message relay TUI

6. **OBD2 Garage Companion**
   - Expand obd2-tui with EJ22 profiles
   - Japanese service manual integration
   - Diagnostic code database

---

## 🔗 Key Resources Bookmarked

**Automotive:**
- Subaru EJ22 Official Manual (ManualsLib)
- Korean Arduino OBD2 Tutorial (Naver)
- Bosch LMDh Hybrid System Docs

**Embedded:**
- Sensor Watch Development Docs
- Microchip SAM L22 Datasheet
- Pluto F91W Firmware (GitHub)

**Retro Gaming:**
- Nixel NES CHR Editor (GitHub)
- GBA ROM Explorer (GitHub)
- Saved Game Analyzer (Web Tool)

**Graphics:**
- Daniel Ilett PS1 Shader Tutorial
- David Colson PS1 Renderer Blog
- Inigo Quilez SDF Raymarching

**Demoscene:**
- Copper Plasma Effects (GitHub)
- OpenXMB Reimplementation (GitHub)

**Infrastructure:**
- Meshtastic Official Docs
- TrueNAS L2ARC Guide
- llamafile (Mozilla AI)

---

**Session Complete:** 23:35 AKDT
**Next Session:** 00:00 AKDT (PROTOTYPE/IDEATION)
