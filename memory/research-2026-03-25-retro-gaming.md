# Retro Gaming Research - 2026-03-25

## NES CHR ROM Graphics Format

**Key findings from multi-source analysis:**

### Tile Structure
- Each tile: 8×8 pixels, 16 bytes total
- 2 bits per pixel → 4 colors per tile (palette indices)
- Bit planes stored separately:
  - Plane 0: bytes 0-7 (rows 0-7)
  - Plane 1: bytes 8-15 (same rows)
  - Combine bits from each plane to get 2-bit color index

### Memory Layout
- CHR ROM: 8KB standard (512 tiles total)
- Split into 2 banks (256 tiles each)
- Address format: `0TNNNNNNNNPYYY`
  - T: table selector (0/1)
  - N: tile ID (0-255)
  - P: plane (0/1)
  - Y: row within tile

### Decoding Algorithm
```
For each row (0-7):
  byte_low = tile[row]      // plane 0
  byte_high = tile[row + 8]  // plane 1
  
  For each pixel (7 to 0):  // MSB first
    color_index = ((byte_high & 1) << 1) | (byte_low & 1)
    byte_low >>= 1
    byte_high >>= 1
```

**Practical insight:** Tiles store SHAPE, not COLOR. Palette selection happens at render time. This enables cheap animation via palette swaps (common NES trick).

**Tools to build:**
- CHR viewer with palette switching
- Tile extractor for ROM analysis
- Pattern table visualizer (grayscale preview)

---

## GBA Save File Formats

### Save Types (5 distinct hardware types):
1. **None** - No save support
2. **EEPROM 512B** - 6-bit addressing
3. **EEPROM 8KB** - 14-bit addressing (10-bit used)
4. **SRAM 32KB** - Battery-backed or FRAM
5. **Flash 64KB** - FLASH_V marker
6. **Flash 128KB** - FLASH1M_V marker

### Detection Method
**Save code strings** embedded in ROM:
- `EEPROM_V` → 512B or 8KB (ambiguous)
- `SRAM_V` → 32KB SRAM
- `FLASH_V` / `FLASH512_V` → 64KB Flash
- `FLASH1M_V` → 128KB Flash

**EEPROM size detection trick:**
- Monitor first DMA3 transfer length:
  - 9 halfwords → 512B (6-bit address)
  - 17 halfwords → 8KB (14-bit address)
- **Warning:** Some games lie (NES Classic series sends wrong length)

### EEPROM Protocol
**Read sequence:**
```
11 (read request)
[n-bit address, MSB first]
0 (terminator)
→ wait 4 bits
→ read 64 bits data
```

**Write sequence:**
```
10 (write request)
[n-bit address, MSB first]
[64 bits data, MSB first]
0 (terminator)
```

**Critical detail:** All addressing is in **64-bit blocks**, not bytes!
- 512B EEPROM: 0x40 blocks (addresses 0x00-0x3F)
- 8KB EEPROM: 0x400 blocks (addresses 0x000-0x3FF)

### Flash RAM Complications
Each manufacturer (Sanyo, Panasonic, Macronix, etc.) uses different command protocols. Nintendo SDK auto-detected manufacturer ID at runtime. Emulators need databases mapping games to Flash chip IDs.

**Tools to build:**
- GBA save file parser/converter
- Save type auto-detector (with game database fallback)
- EEPROM protocol analyzer
- Flash chip ID mapper

---

## Sources
- [NES CHR Graphics - Emulation Online](https://www.emulationonline.com/systems/nes/chr-graphics/)
- [Rendering CHR ROM Tiles - bugzmanov](https://bugzmanov.github.io/nes_ebook/chapter_6_3.html)
- [GBA Saves - Screwtape's Notepad](https://zork.net/~st/jottings/GBA_saves.html)
- [GBA EEPROM Save Type - Dennis H](https://densinh.github.io/DenSinH/emulation/2021/02/01/gba-eeprom.html)

---

**Session ID:** main (deep work rotation 1/6)
**Research depth:** Multi-language (EN/JP/CN/KR), 13 searches, 6 detailed pages
