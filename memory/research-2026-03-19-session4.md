# Research Session 4 — March 19, 2026, 02:13-02:22 AKDT

**Focus Areas:** Automotive (OBD2 tools) + Retro Gaming (ROM/save parsers)  
**Search Count:** 6 queries (under 20-search limit)  
**Time:** 9 minutes

---

## 🚗 Automotive: OBD2 Terminal Tools

### CLI/TUI OBD2 Scanners (GitHub)
1. **obd-parser-cli** — https://github.com/evanshortiss/obd-parser-cli  
   CLI to read diagnostic data via ELM327 connections

2. **obd2-diagnostics-ai-cli** — https://github.com/Juandi-M/obd2-diagnostics-ai-cli  
   AI-enhanced OBD2 diagnostics CLI

3. **OBD2-Scantool** — https://github.com/AustinMurphy/OBD2-Scantool  
   Scantool for reading OBD2 info from cars

4. **obdium** — https://github.com/provrb/obdium  
   Free, open-source on-board diagnostics tool

5. **o3DIAG** — https://github.com/openw3rk-DEVELOP/o3DIAG  
   Open Source OBD-II diagnostic tool

6. **OBD_Diag_CMD** — https://github.com/karolinaklak/OBD_Diag_CMD  
   Car diagnostic CLI project

7. **canbus-tools** — https://github.com/ajouatom/canbus-tools  
   Curated list of CAN bus tools and resources

### Key Insights
- ELM327 is the de facto standard OBD2 interpreter IC
- Most tools use serial/USB/Bluetooth interfaces
- Terminal-based tools exist but are limited — **opportunity for TUI improvement**
- Integration with CAN bus analysis is important for advanced diagnostics
- Japanese forums (minkara.carview.co.jp) have EJ-specific content but requires deeper crawling

### Project Idea: **obd-tui**
- **Concept:** Modern TUI for OBD2 diagnostics using Rust + Ratatui
- **Features:**
  - Live PID monitoring (RPM, speed, temp, etc.)
  - DTC (trouble code) reading and clearing
  - Customizable dashboard layouts
  - Data logging to CSV
  - Support for multiple OBD protocols (CAN, ISO, etc.)
- **Tech Stack:** Rust, Ratatui, serialport crate, tokio async
- **Inspiration:** htop/bottom aesthetics for automotive data

---

## 🎮 Retro Gaming: ROM & Save File Tools

### Game Boy ROM/Save Parsers (GitHub)
1. **gameboy-rom-parser** — https://github.com/MarkMcCaskey/gameboy-rom-parser  
   Parser for [Super] GameBoy [Color] ROMs (Rust)

2. **awesome-gbdev** — https://github.com/gbdev/awesome-gbdev  
   Curated list of GB development resources  
   - Mentions GBCartRead, GBxCart-RW for reading ROMs/saves

3. **gameboy-roms** — https://github.com/merwaaan/gameboy-roms  
   Python script to parse GB/GBC ROMs, output HTML/JSON

4. **goombasav** — https://github.com/libertyernie/goombasav  
   Extract/replace GB SRAM data from Goomba emulator

5. **ROM-Metadata-Reader** — https://github.com/Wandmalfarbe/ROM-Metadata-Reader  
   Tool to read metadata from GB/GBC/GBA/NDS ROMs

6. **gbrom-tutorial** — https://github.com/travisgoodspeed/gbrom-tutorial  
   Tutorial for extracting GB ROM from die photographs (!)

### PSX/PS1 Model Extraction
1. **psxprev** — https://github.com/rickomax/psxprev  
   **PlayStation Files Previewer/Extractor**  
   - Extracts 3D models from PSX games
   - GUI tool for browsing and previewing game assets
   - Example: Action Man 2: Destruction X models

2. **awesome-game-file-format-reversing** — https://github.com/VelocityRa/awesome-game-file-format-reversing  
   Comprehensive list of game file format reverse engineering resources

### Project Ideas

#### **gb-save-inspector** (TUI)
- **Concept:** Terminal UI for inspecting/editing Game Boy save files
- **Features:**
  - Hex editor with SRAM structure highlighting
  - Automatic game detection (from ROM header)
  - Known save format templates (Pokemon, Zelda, etc.)
  - Checksum validation and repair
  - Batch save backup/restore
- **Tech Stack:** Rust, Ratatui, binrw for binary parsing

#### **psx-mesh-explorer** (CLI + TUI)
- **Concept:** Extract and analyze PSX 3D models from game files
- **Features:**
  - Scan game ISOs for model data
  - Extract meshes to OBJ/glTF format
  - TUI browser for assets
  - Low-poly mesh statistics (vertex count, triangle count)
  - Texture extraction
- **Tech Stack:** Rust, Ratatui, gltf crate for export
- **Research:** Study psxprev source code for format specs

---

## ⚙️ EJ22 Subaru Maintenance Resources

### English Resources
1. **Ultimate Subaru Forum** — https://www.ultimatesubaru.org/forum/topic/58892-legacy-ej22-timing-belt-interval-too-short/  
   Discussion on timing belt replacement intervals for EJ22

2. **Kevin's Autos** — https://kevinsautos.com/faq/when-should-a-subaru-timing-belt-be-replaced.html  
   Timing belt replacement guide for Subarus

### Japanese Resources
- **Green Line Japan** — https://greenline.jp/  
  Parts catalog for Subaru (EJ207, EJ20 models)
- **Minkara** (みんカラ) — Community forum (needs deeper exploration for EJ22-specific threads)

### Next Steps for EJ22 Research
- Search for "EJ22 タイミングベルト 交換" (timing belt replacement)
- Find Japanese service manuals via Yahoo Auctions Japan
- Look for forum posts on common EJ22 issues (head gasket, oil leaks)

---

## 📊 Session Summary

**Queries:** 6/20 used  
**Time:** 9 minutes  
**Key Outcomes:**
- Identified 13 GitHub repos for OBD2/retro gaming tools
- Discovered gap in modern TUI OBD2 tools → project opportunity
- Found psxprev for PSX model extraction → study for psx-mesh-gen project
- Confirmed EJ22 resources exist but need JP-language deep dive

**Next Research Session Ideas:**
- Deep dive on psxprev file formats
- Japanese forum crawl for EJ22 maintenance wisdom
- ROM format specifications for NES/GB/GBA
- OBD2 PID documentation (Mode 01/02 parameters)
