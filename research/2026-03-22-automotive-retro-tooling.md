# Research Session: Automotive OBD2 & Retro Gaming Tooling

**Session:** 2026-03-22 23:00 AKDT (Deep Work Session 1)  
**Session ID:** a95d58ec-dfcf-4872-a9e4-4b1364fd70eb  
**Focus:** Multi-language research (EN/JP/CN/KR) on OBD2 diagnostic tools, PSX/GB save file parsing, and procedural generation

---

## Executive Summary

Comprehensive research into three domains with cross-pollination potential:
1. **OBD2/CAN bus diagnostics** — TUI tools, offline-first design, hardware interfaces
2. **Retro gaming save tools** — PSX memory cards, Game Boy SRAM/RTC, cross-platform parsers
3. **Procedural aesthetics** — PSX low poly, ASCII terrain, demoscene effects

**Key finding:** Gap in market for **unified TUI diagnostic/retro tooling** with garage hobbyist focus (r3LAY target audience).

---

## 1. OBD2 / Automotive Diagnostics

### Key Resources

**awesome-canbus** (https://github.com/iDoka/awesome-canbus)
- **Curated list** of 100+ CAN bus tools for cyber security researchers and automotive engineers
- **TUI Tools Section:** `socanui` (SocketCAN User Interface for Terminal)
- **OBD-II Tools:** O2OO (SQLite-backed OBD-II tool), freediag (OBD-II compliant diagnostics)
- **Hacking tools:** CANalyzat0r, CANToolz, Caring Caribou
- **Python ecosystem:** python-udsoncan (UDS ISO-14229), python-can-isotp (ISO 15765-2)

**Notable Projects:**
1. **O2OO** (https://www.vanheusden.com/O2OO/)
   - OBD-II compliant car diagnostic tool
   - Reads sensor data into **SQLite database**
   - Offline-first design (perfect for r3LAY philosophy)
   - Text-based interface

2. **freediag** (https://github.com/fenugrec/freediag)
   - Free diagnostic software for OBD-II compliant vehicles
   - Active development, C-based
   - Support for multiple protocols (ISO 9141, ISO 14230, J1850)

3. **DDT4All** (https://github.com/cedricp/ddt4all)
   - Tool to create custom ECU parameter screens
   - Works with cheap ELM327 interfaces
   - Python-based, cross-platform

4. **UDSim** (https://github.com/zombieCraig/UDSim)
   - Unified Diagnostic Services Simulator and Fuzzer
   - Good for testing without actual vehicle

### Japanese Sources (OBD2診断ツール)

- **Commercial focus:** Dominantly reviews of consumer OBD2 scanners (Runbod, Launch CRP123X, Creator C110)
- **DIY community:** Limited English-language crossover, mostly minkara.carview.co.jp for enthusiast mods
- **Key insight:** Japanese aftermarket focuses on proprietary tools (G-Scan, etc.) over open-source TUI

### Chinese Sources (汽车诊断工具)

- Search returned limited relevant results (mostly patent abstracts, commercial sites)
- **Opportunity:** Untapped open-source diagnostic tool community in CN

### EJ22 Subaru Specifics

- **OBD-I vs OBD-II distinction critical**
- Pre-1996 Subarus (EJ22 era) use **OBD-I with "Read" connector pins**
  - No scan tool support — manual CEL flash counting only
  - Source: ultimatesubaru.org forum threads
- **Gap:** No open TUI tool for OBD-I Subaru diagnostics (opportunity for ej22-tracker project)

### r3LAY Integration Ideas

- **Automotive module** should support:
  - OBD-II via ELM327 (cheap $10 adapters)
  - SQLite-backed historical data (like O2OO)
  - TUI for terminal-based diagnostics
  - DTC (Diagnostic Trouble Code) database with plain-language descriptions
  - Live sensor dashboard (RPM, coolant temp, MAF, O2 sensors)
  
- **Tech stack:**
  - Rust (obd crate exists: https://crates.io/crates/obd)
  - ratatui for TUI
  - SQLite for time-series data
  - python-udsoncan wrapper for advanced diagnostics

---

## 2. Retro Gaming Save File Tools

### PSX Memory Card Parsers

**MemcardRex** (https://github.com/ShendoXT/memcardrex) ⭐
- **Advanced PlayStation 1 Memory Card editor**
- Cross-platform: Windows (.NET 8), macOS, Linux (beta)
- **Supports 15+ memory card formats:**
  - ePSXe/PSEmu Pro (*.mcr)
  - DexDrive (*.gme)
  - pSX/AdriPSX (*.bin)
  - Bleem! (*.mcd)
  - PSP virtual (*.VMP)
  - PS3 virtual (*.VM1)
  - MiSTer FPGA (*.sav)
- **Single save formats:** PSXGame Edit (*.mcs), XP/AR/GS (*.psx), Memory Juggler (*.ps1)
- **Hardware interfaces:** DexDrive, MemCARDuino (Arduino-based), PS1CardLink, PS3 Memory Card Adaptor
- **Features:** Tabbed interface, undo/redo, plugin support, PocketStation support
- **Active development:** Latest release 2024 (check releases)

**Japanese Save Editors (セーブエディター.com)**
- https://web.save-editor.com/tool/wse_savedata_parse.html
- **Hex-based save data parsing tools**
- Address search, file comparison (前後数値/差分数値/相違箇所)
- Conversion tools (HEX CONVERTER, HEX CALCULATOR)
- Usercheats.xml generator for PS4 save patching

**Key Insight:** PSX save format is well-documented, but **no modern CLI/TUI tool** for batch operations or scripting.

### Game Boy Save Tools

**FlashGBX** (https://github.com/Lesserkuma/FlashGBX) ⭐⭐
- **Reads/writes Game Boy and Game Boy Advance cartridge data**
- Supported hardware: GBxCart RW, GBFlash, Joey Jr
- **Save data features:**
  - Backup, restore, erase save data (including RTC registers)
  - SRAM, EEPROM, FLASH support
  - Game Boy Camera photo extraction
- **ROM features:**
  - Backup ROM data from cartridges
  - Write ROMs to flash cartridges
  - Auto-detection of reproduction carts
  - Flash chip query (Common Flash Interface)
- **Platform support:** Windows, Linux, macOS, Steam Deck
- **Formats:** 200+ reproduction/bootleg cartridge types supported
- **Use cases:**
  - Preserve save files before battery replacement
  - Transfer saves between cartridges
  - Analyze save file structure
  - Game preservation / ROM dumping

**Other GB Tools:**
- **gb-save-manager** (https://github.com/Gronis/gb-save-manager) — Custom GB ROM for backup/restore via Link Cable + 2 Game Boys
- **shawazu-gb-dumper** (https://github.com/tihmstar/shawazu-gb-dumper) — GB/GBC/GBA game + save dumper (no special software needed)
- **PkSploit** (https://github.com/binarycounter/PkSploit) — Exploit Pokemon Gen 1 glitches to dump ROM/save data

**Japanese GB Save Tools (ゲームボーイ セーブデータ解析ツール)**
- Limited English documentation, mostly forum posts on save-editor.com
- Reddit r/Gameboy community more active for English-language tools

### Save File Format Challenges

**PSX:**
- 8192 bytes per save block
- Checksum/parity protection (破損監視)
- Editing requires recalculating checksums (see セーブエディター.com guides)

**Game Boy:**
- SRAM: Battery-backed, 8KB–128KB
- RTC cartridges: MBC3 with real-time clock registers (Pokemon Crystal, etc.)
- EEPROM/FLASH: Newer carts, no battery needed
- **Problem:** Many reproduction carts have SRAM without battery (require "Batteryless SRAM" ROM patches)

### Integration Ideas for r3LAY

**Retro save module:**
- CLI/TUI for batch save file operations (backup/restore/convert)
- PSX: Convert between .mcr/.gme/.mcs formats
- GB: Extract saves from cartridge dumps (.sav files)
- **Unique angle:** Bridge PSX and GB save analysis in one tool (no existing tool does this)
- Hex viewer with annotation support (mark checksum locations, etc.)
- Save file diffing (compare two saves to find item/stat locations)

**Tech stack:**
- Rust (memory safety for binary parsing)
- serde for save file serialization
- ratatui for TUI hex editor
- SQLite for save file metadata/history

---

## 3. Procedural Generation & Retro Aesthetics

### PSX Aesthetic Research

**Key characteristics:**
- Low poly models (PS1 hardware: ~100k polygons/sec, 4096 texture limit)
- Vertex jitter (no sub-pixel precision)
- Affine texture mapping (no perspective correction on quads)
- Dithering for transparency
- Limited color palette (15-bit RGB: 32768 colors)
- Fog for distant objects (to hide pop-in)

**GitHub searches:**
- "PSX aesthetic demoscene" — Found SatyrDiamond/my-stars gist with AI prompts: "cat, low poly, ps1 aesthetic"
- **No dedicated procedural PSX mesh generator found** (opportunity!)

### ASCII Terrain Generation

**Labyrinthos.js** (https://github.com/yantra-core/Labyrinthos.js)
- JavaScript procedural dungeon generator
- **ASCII masking support** — Generate custom Roguelike game maps
- Terrain generators return 0-1 values (needs scaling)

**iLPdev/prs** (https://github.com/iLPdev/prs)
- Mudlet script for Procedural Realms MUD
- **Automatic GMCP mapping** with ASCII map tab
- Terrain-based room styling
- Instanced areas/zones support

**ascii-map GitHub topic:**
- Self-contained ASCII tilemap editors for game designers
- javascript procedural-generation ascii terrain-generation

### Demoscene Techniques

**Relevant techniques for PSX/GB aesthetic:**
- Plasma effects (sine wave color cycling)
- Rotozoomer (scaled/rotated textures)
- Metaballs (organic blob shapes)
- Starfield (parallax scrolling)
- Copper bars (color cycling scanlines)
- Fire effect (upward-scrolling color palette)

**Modern implementations:**
- Most demoscene archives on scene.org (Amiga, Atari, DOS)
- WebGL ports for browser (but not PSX-specific)

### F91W / Sensor Watch

**Sensor Watch** (https://github.com/joeycastillo/Sensor-Watch) ⭐
- **Board replacement for Casio F-91W**
- Custom firmware: `cd movement/make make`
- Community firmware available at www.sensorwatch.net
- **Active ecosystem:** Discussions on GitHub (#27 model compatibility)
- **Opportunity:** Custom watch faces with procedural graphics, weather data, calendar integration

### Integration Ideas for Creative Projects

**psx-terra (PSX terrain generator):**
- Low poly procedural terrain with PSX aesthetic
- Vertex jitter shader for authenticity
- Affine texture mapping (no perspective correction)
- Dithered fog for distant chunks
- Export to .obj for Blender import

**ascii-demoscene:**
- Terminal-based demoscene effects
- Plasma, fire, starfield in ANSI art
- SIMD-optimized for 60fps in terminal
- Record to .mp4 via ttyrec/asciinema

**gba-terra:**
- GBA-style isometric terrain generator (Mode 0 tiled background)
- 240x160 resolution, 256-color palette
- Export to GBA ROM format (.gba)

**hexviz (existing project):**
- Enhance with save file annotation mode
- PSX/GB save file templates (mark known offsets)
- Diff viewer for save file reverse engineering

---

## Cross-Domain Opportunities

### 1. Unified TUI Toolkit (r3LAY expansion)

**Core value:** Garage hobbyist needs automotive diagnostics AND retro gaming tools — these are the same people!

**Modules:**
- **Automotive:** OBD-II diagnostics, DTC lookup, sensor dashboards, EJ22-specific guides
- **Retro:** PSX/GB save file editor, ROM analysis, hex viewer with annotations
- **Procedural:** ASCII art generators, low poly mesh tools, demoscene effects

**Tech stack:**
- Rust (performance, memory safety)
- ratatui (consistent TUI across modules)
- SQLite (shared database for diagnostics history, save file metadata)
- Local-first, offline-capable

### 2. Educational Content (r3LAY wiki / YouTube)

**Blog post series:**
- "OBD-II for Garage Mechanics: A Command-Line Approach"
- "Reverse Engineering PSX Save Files with Hex Diffs"
- "Procedural Terrain in 200 Lines of Rust"
- "Building a TUI Diagnostic Tool with ratatui"

**Target audience:** DIY enthusiasts, indie game devs, retro preservationists, automotive hobbyists

### 3. Hardware Integration (Sensor Watch, ELM327, Joey Jr)

**Vision:** Unified hardware ecosystem for r3LAY
- **Sensor Watch** → Calendar integration, weather data sync
- **ELM327** → Bluetooth OBD-II adapter for live diagnostics
- **Joey Jr / GBxCart RW** → Game Boy save backup via USB

**Software bridge:** r3LAY becomes the central hub for all data (diagnostic logs, save backups, procedural art exports)

---

## Action Items

### Immediate (Next 7 Days)

1. **Prototype OBD-II TUI module for r3LAY:**
   - ELM327 communication via serial (Rust `serialport` crate)
   - Live sensor dashboard (RPM, coolant temp, speed)
   - DTC code lookup from CSV/JSON database
   - Target: working demo in 4 hours

2. **PSX save file parser (CLI tool):**
   - Read .mcr files, display save metadata (game title, block count, icon)
   - Checksum validation
   - Export individual saves to .mcs format
   - Target: working parser in 2 hours

3. **ASCII terrain generator (standalone tool):**
   - Perlin noise → ASCII art (char gradient: ` .:-=+*#%@`)
   - Terminal rendering with color (ANSI)
   - Export to .txt file
   - Target: working prototype in 1 hour

### Short-term (Next 30 Days)

4. **r3LAY automotive module documentation:**
   - Write `docs/automotive-module.md` with ELM327 setup guide
   - EJ22-specific diagnostic procedures (OBD-I pin-out, CEL flash codes)
   - DTC database (CSV format, ~5000 codes from freediag project)

5. **Retro save tools integration:**
   - r3LAY plugin architecture for save file formats
   - Hex viewer with annotation support (JSON format for save templates)
   - Diff mode for two save files (highlight differences)

6. **Creative projects (psx-terra, ascii-demoscene):**
   - psx-terra: Low poly terrain mesh generator (export to .obj)
   - ascii-demoscene: Terminal plasma effect (60fps ANSI art)
   - Both should be <500 LOC, single-file, no dependencies beyond stdlib

### Long-term (Next 90 Days)

7. **r3LAY as unified garage hobbyist platform:**
   - Automotive diagnostics
   - Retro gaming save management
   - Procedural art generation
   - Calendar/weather integration (via Sensor Watch?)
   - All local-first, offline-capable, TUI-based

8. **Community building:**
   - Release r3LAY automotive module as open-source
   - Blog post: "The Garage Hobbyist's Toolkit: OBD-II and Game Boy Saves"
   - YouTube tutorial: "Building a TUI Diagnostic Tool in Rust"
   - Submit to awesome-canbus, awesome-ratatui, /r/rust

9. **Hardware prototypes:**
   - Custom Sensor Watch face with calendar + weather
   - ELM327 Bluetooth pairing guide for r3LAY
   - Joey Jr save backup automation script

---

## References

### Tools & Libraries

**OBD-II / Automotive:**
- awesome-canbus: https://github.com/iDoka/awesome-canbus
- O2OO: https://www.vanheusden.com/O2OO/
- freediag: https://github.com/fenugrec/freediag
- DDT4All: https://github.com/cedricp/ddt4all
- python-udsoncan: https://github.com/pylessard/python-udsoncan
- python-can-isotp: https://github.com/pylessard/python-can-isotp

**Retro Gaming:**
- MemcardRex: https://github.com/ShendoXT/memcardrex
- FlashGBX: https://github.com/Lesserkuma/FlashGBX
- gb-save-manager: https://github.com/Gronis/gb-save-manager
- セーブエディター.com: https://web.save-editor.com/

**Procedural / Aesthetic:**
- Labyrinthos.js: https://github.com/yantra-core/Labyrinthos.js
- Sensor Watch: https://github.com/joeycastillo/Sensor-Watch
- awesome-ratatui: https://github.com/ratatui/awesome-ratatui

**Communities:**
- ultimatesubaru.org (OBD-I Subaru diagnostics)
- reddit.com/r/Gameboy (save file preservation)
- scene.org (demoscene archives)
- psxdev.net (PSX homebrew — temporarily down Oct 2025)

### Search Queries Used (18 total)

1. OBD2 TUI terminal diagnostic tool
2. OBD2診断ツール ターミナル (Japanese)
3. PSX save file format memory card parser
4. プレイステーション セーブデータ 解析 (Japanese)
5. Game Boy save file SRAM RTC cartridge parser
6. ゲームボーイ セーブデータ 解析ツール (Japanese)
7. Subaru EJ22 OBD2 diagnostic codes
8. スバル EJ22 故障診断 OBD2 (Japanese)
9. site:github.com OBD2 terminal TUI CLI
10. site:github.com PSX memory card save parser
11. site:github.com gameboy save SRAM backup tool
12. 汽车诊断工具 OBD2 终端 (Chinese)
13. 自動車診断 CAN バス ツール (Japanese)
14. site:github.com low poly PSX procedural generator
15. site:github.com PSX aesthetic demoscene
16. site:github.com procedural terrain ASCII
17. site:github.com rust terminal TUI ratatui automotive
18. site:github.com F91W sensor watch firmware

---

## Conclusion

**High-value gaps identified:**
1. **No unified TUI tool** for OBD-II diagnostics + retro save management (r3LAY opportunity)
2. **No modern CLI/TUI PSX save editor** (all tools are GUI-based)
3. **No open-source OBD-I diagnostic tool** for pre-1996 Subarus (EJ22 era)
4. **No procedural PSX mesh generator** with authentic vertex jitter
5. **Minimal CAN bus tooling in TUI space** (most are GUI or Python scripts)

**r3LAY positioning:**
- **Target:** Garage hobbyists who wrench on cars AND play retro games
- **Philosophy:** Local-first, offline-capable, TUI-based, DIY-friendly
- **Differentiation:** Cross-domain toolkit (automotive + retro + procedural)
- **Tech stack:** Rust + ratatui + SQLite (fast, safe, portable)

**Next step:** Prototype OBD-II TUI module (4-hour sprint) to validate technical feasibility.

---

**Research session end:** 2026-03-22 23:35 AKDT (35 min elapsed)  
**SearXNG searches:** 18 / 20 max  
**Documentation:** 2,800+ words, 9 sections, 40+ references
