# Research: Automotive + Electronics + Retro Gaming (2026-03-26)

**Session:** Deep Work Session 1/6 (23:00)  
**Search count:** 20/20 (EN/JP/CN/KR multi-language)  
**Focus:** EJ22 maintenance, OBD2 tools, Sensor Watch, F91W mods, PS1 save formats, retro preservation

---

## 🚗 Automotive Research

### EJ22 Engine (Subaru Boxer)

**Key findings:**
- **Reliability factors** (Reddit analysis):
  - Built like old truck motors (loose tolerances, machined well)
  - Low output, doesn't rev high (stock)
  - Proper head gaskets (vs. later EJ25 issues)
  - Minimal cost-cutting design choices
- **Specs:** 2.2L, 4-cylinder boxer, SOHC, 126-160hp (version-dependent)
- **Maintenance resources:**
  - Workshop manuals available (EnginesWork, ultraligero.net)
  - Electrical system docs (car-inform.com)

**Project opportunity:** EJ22 maintenance tracker TUI (next-due service intervals, common issues database)

### OBD2 Diagnostic Tools

**Python libraries found:**
1. **python-OBD** (brendan-w/python-OBD)
   - Auto-connects to USB/RF ports
   - Command-based API (`obd.commands.SPEED`)
   - Parses OBD-II sensor data
2. **pyobd** variants:
   - barracuda-fsh/pyobd (supports DexDrive, PSEmuPro saves)
   - Bleem!/VGS memory card formats

**Japanese source:**
- Qiita article: 車のデータで遊ぶ (Playing with car data)
- OBD2コネクタ搭載が義務化 (OBD2 connector mandatory worldwide)
- CAN通信解析 (CAN bus communication analysis)

**Project opportunity:** OBD2 TUI dashboard (live sensor readings, DTC code lookup, logging)

---

## ⚡ Electronics Research

### Sensor Watch (Joey Castillo)

**Hardware:**
- F-91W board replacement
- Microchip SAM L22 microcontroller (built-in segment LCD controller)
- Open-source firmware (Movement community project)

**Performance:**
- Sensor Watch Lite: 2.4 years battery life (optimized firmware)
- Test results: >2x improvement over previous generation

**Resources:**
- GitHub: joeycastillo/Sensor-Watch
- Official docs: joeycastillo.github.io/Sensor-Watch-Documentation

**Project opportunity:** Sensor Watch face development (custom displays, data loggers)

### Casio F91W Mods

**Findings:**
1. **LED upgrade mods:**
   - Stock LED: green, extremely dim (电球時代並み)
   - Common mods: white/blue LED replacement
   - Instructables: no-solder LED mod tutorial
   - YouTube: soldering-based LED upgrades
2. **Japanese sources:**
   - チープカシオバックライト改造 (Cheap Casio backlight mod)
   - 緑色のLED球が暗すぎる問題 (Green LED too dark issue)
3. **Advanced:**
   - Sensor Watch mod kit (WatchUSeek forums)
   - Etsy: prebuilt modded F-91W with backlight spreader

**Project opportunity:** F91W mod guide compilation (LED upgrade, backlight spreader, alternative firmwares)

---

## 🎮 Retro Gaming Research

### PlayStation 1 Save Files

**Formats found:**
- **.MCR/.MC** — Raw memory card format (131,072 bytes, 128KB)
- **.GME** — DexDrive format
- **.MCD** — Bleem! format
- **.PSV** — PSP/Vita format
- **VMP** — Vita format

**Tools discovered:**
1. **save-file-converter** (GitHub: euan-forrester/save-file-converter)
   - Converts between MiSTer, flash carts, Switch Online, emulators
   - Supports .srm ↔ .sav conversion
   - Multi-platform: NES/SNES/GBA/N64/TG16/SMS/Genesis/Neo Geo/PS1
   - PSP save decryption
2. **PSXGameEdit** (PS3DevWiki)
   - PlaySaver/PSEmuPro support
   - Single game saves
3. **Japanese tools:**
   - PS1セーブデータ確認ツール (PS1 Save Checker) — セーブエディター.com
   - Format detection (VMP, PSV, MCR, MCS, PS1, PSS, MCD, MCB, MC, PSM, PSX, GME, VGS, MEM)
   - mcr ↔ vmp converter (yyoossk.blogspot.com)

**Korean sources:**
- RG350 PS1 save data editing (Naver blog)
- Pcsx4all emulator performance notes

**Save structure:**
- MCR format: 131,072 bytes (15 blocks × 8,192 bytes/block)
- raphnet adapter: complete memory card read/write
- PSxMemCard Gen 1 hardware support

**Project opportunity:**
- PS1 save file parser (view save metadata, game titles, block usage)
- Save converter TUI (MCR ↔ VMP ↔ GME ↔ MCD)
- Save file hex viewer with annotations

### Retro Preservation Tools

**Tools found:**
1. **RetroMultiTools** (GitHub: SvenGDK/RetroMultiTools)
   - Cross-platform desktop utility
   - ROM management, inspection, modification, launching
   - NES ROM header repair (safe temp-file workflow)
   - Multi-language UI (EN/ES/FR/DE/PT/IT/JA/CN)
2. **save-file-converter** (see above)
3. **Hex Workshop tutorials** (reverse engineering save files)
   - File comparison workflow
   - Pattern detection

**Japanese resources:**
- レトロフリーク セーブデータ変換ツール (RetroFreak save converter) — セーブエディター.com
- Emulator ↔ RetroFreak format conversion

**Project opportunity:**
- ROM analysis TUI (header info, checksums, known dumps database)
- Save file reverse engineering toolkit (hex diff, pattern finder)
- Tile viewer for 8-bit/16-bit graphics (SNES, GB, NES, Genesis)

---

## 🏁 Motorsports (Bonus)

### IMSA/WEC 2026

**Schedule findings:**
- 2026 IMSA SportsCar Championship: 12-race calendar
- Reddit: IMS permanent IMSA race approved (community requested since 2006)
- Le Mans 24H 2026: fiawec.com official page

**Project opportunity:** Race calendar tracker (IMSA/WEC/Le Mans, timezone-aware, reminder integration)

---

## 🦀 Embedded Systems (Rust RTOS)

**Findings:**
1. **Rust-embedded ecosystem:**
   - awesome-embedded-rust (curated list)
   - Hubris OS (Oxide Computer, real-time OS)
   - Zephyr RTOS with Rust support
2. **Chinese sources:**
   - Ariel OS — Rust RTOS for IoT (GitHub trending, CSDN)
   - 支持 Arm Cortex-M, ESP32, RISC-V
   - 内存安全、低功耗物联网 (memory-safe, low-power IoT)
3. **Arm blog:**
   - Integrating Rust with FreeRTOS/Zephyr
   - Bare-metal vs. RTOS approaches

**Project opportunity:** RTOS comparison matrix (FreeRTOS, Zephyr, Hubris, Ariel OS) for Rust projects

---

## 🏠 Self-Hosting

### Proxmox VE

**GPU passthrough research:**
- **LXC container passthrough:**
  - simplehomelab.com guide (Plex/Jellyfin hardware transcoding)
  - GitHub: en4ble1337/GPU-Passthrough-for-Proxmox-LXC-Container (NVIDIA AI/ML workloads)
  - blog.kye.dev: Unprivileged LXC + Jellyfin GPU
- **Proxmox 8.2 compatibility:**
  - Reddit: works with older iGPUs
  - NVIDIA cards: driver installation required

**Project opportunity:** Proxmox GPU passthrough automation script (LXC config generator)

---

## 📡 Meshtastic (Off-Grid Comms)

**Findings:**
- **Official:** meshtastic.org — open-source, off-grid, decentralized mesh network
- **Hardware:** LoRa radios (affordable, low-power)
- **Use case:** Areas without reliable infrastructure
- **Seeed Studio:** Off-grid devices + GPS network support

**Project opportunity:** Meshtastic relay node setup guide (hardware selection, config)

---

## 🎨 Procedural Generation

**Research:**
1. **Perlin/Simplex noise:**
   - redblobgames.com: Interactive terrain-from-noise tutorial
   - garagefarm.net: Perlin noise for textures (clouds, terrain, fire)
   - rtouti.github.io: Algorithm explanation
2. **Demoscene techniques:**
   - **Raymarching:** Inigo Quilez tutorials (raymarchingdf)
   - pouet.net: Ray marching vs. ray tracing discussion
   - blog.maximeheckel.com: SDF + lighting models + soft shadows

**Project opportunity:**
- Terrain generator TUI (Perlin/Simplex noise, ASCII output)
- Raymarching shader sandbox (SDF primitives, lighting experiments)

---

## 📊 Research Metrics

**Searches by category:**
- Automotive: 4 (EN, JP)
- Electronics: 4 (EN, JP)
- Retro gaming: 6 (EN, JP, CN, KR)
- Motorsports: 1 (EN)
- Embedded: 2 (EN, CN)
- Self-hosting: 1 (EN)
- Mesh networking: 1 (EN)
- Procedural gen: 2 (EN)

**Languages used:**
- English: 14
- Japanese: 4
- Chinese: 1
- Korean: 1

**Key resources:**
- GitHub repos: 10
- Official docs: 6
- Community forums (Reddit, WatchUSeek, CSDN): 8
- Japanese sites (Qiita, Blogger, セーブエディター.com): 5

---

## 🎯 Project Ideas Summary

**High priority (aligns with dlorp's interests):**
1. **OBD2 TUI dashboard** (Python, python-OBD library, live sensor data)
2. **PS1 save file parser + converter** (MCR/VMP/GME formats, hex viewer)
3. **Retro ROM analysis toolkit** (header inspection, tile viewer, known dumps DB)
4. **Sensor Watch firmware exploration** (custom faces, data logging)
5. **F91W LED mod guide** (compilation of techniques, backlight spreader)

**Medium priority:**
6. **EJ22 maintenance tracker** (service intervals, common issues)
7. **Terrain generator** (Perlin/Simplex noise, ASCII art output)
8. **Raymarching shader sandbox** (SDF primitives, demoscene effects)
9. **Proxmox GPU passthrough script** (LXC config automation)
10. **Meshtastic relay setup guide** (hardware, config)

**Low priority (exploration):**
11. **Race calendar tracker** (IMSA/WEC/Le Mans)
12. **RTOS comparison matrix** (Rust-focused)

---

## 🔗 Useful Links Archive

### Automotive
- https://github.com/brendan-w/python-OBD
- https://engineswork.com/engines/subaru-engine/ej22-engine.html
- https://qiita.com/hoto17296/items/85f052ff643b927f974e (JP: OBD2 Python)

### Electronics
- https://github.com/joeycastillo/Sensor-Watch
- https://www.instructables.com/Casio-F91W-LED-Light-Mod-Modification-No-Solder-No/
- https://haute-chrono.com/チープカシオのバックライト改造 (JP: F91W backlight mod)

### Retro Gaming
- https://github.com/euan-forrester/save-file-converter
- https://web.save-editor.com/tool/wse_ps1_save_checker.html (JP: PS1 save checker)
- https://github.com/SvenGDK/RetroMultiTools
- https://www.psdevwiki.com/ps3/PS1_Savedata

### Procedural Gen
- https://www.redblobgames.com/maps/terrain-from-noise/
- https://iquilezles.org/articles/raymarchingdf/
- https://blog.maximeheckel.com/posts/painting-with-math-a-gentle-study-of-raymarching/

### Other
- https://meshtastic.org/docs/introduction/
- https://www.simplehomelab.com/udms-11-gpu-passthrough-on-proxmox-lxc/
- https://zhuanlan.zhihu.com/p/2004206835880726673 (CN: Ariel OS)

---

**Next session:** PROTOTYPE or IDEATION (Session 2/6: 00:00)
