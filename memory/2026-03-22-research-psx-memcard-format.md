# Retro Gaming Research: PlayStation 1 Memory Card Format (2026-03-22 02:00-03:00 Alaska)

## Session Metadata
- **Session ID**: a95d58ec-dfcf-4872-a9e4-4b1364fd70eb
- **Type**: Off-hours deep work (Session 4: RESEARCH rotation)
- **Focus**: PSX save data formats (.MCR, .VM1, .PSV, .VMP)
- **Searches**: 4 (16 remaining in budget)

## Research Summary

### PS1 Memory Card Structure

**Physical Specs:**
- **Total Size**: 128 KB (131,072 bytes / 0x20000)
- **Block Size**: 8 KB (8,192 bytes / 0x2000)
- **Frame Size**: 128 bytes (0x80)
- **Total Blocks**: 16 (Block 0 = header/FAT, Blocks 1-15 = data)
- **Frames per Block**: 64

**Block 0 Layout** (Header/Directory/FAT):
```
Frame 0 (0x0000-0x007F): Header
  - 0x0000: "MC" magic (0x4D 0x43)
  - 0x007F: XOR checksum of frame

Frames 1-15 (0x0080-0x07FF): Directory entries
  Each frame describes one save slot:
  - 0x00: Available blocks flag (A0=open, 51=linked, 52=mid-link, 53=end-link, FF=unusable)
  - 0x04: Use byte (0x0020 = 1 block, 0x0040 = 2 blocks, max 0x01E0 = 15 blocks)
  - 0x08: Link order (0xFFFF if no link/end of chain)
  - 0x0A: Country code (BI=Japan, BA=America, BE=Europe)
  - 0x0C: Product code (10 bytes, e.g. "SLUS-12345")
  - 0x16: Identifier (8 bytes, e.g. "FF7-S01 ", "FFTA    ")
  - 0x1E-0x5E: Unused (0x00 padding)
  - 0x5F: XOR checksum

Frames 16-19: Unused (0x00 padding)
Frames 20-63: Filled with 0xFF
```

**Data Block Layout** (Blocks 1-15):
```
Frame 0 (0x0000-0x007F): Save metadata
  - 0x00: "SC" magic (0x53 0x43)
  - 0x02: Icon display flag (0x11=1 frame, 0x12=2 frames, 0x13=3 frames)
  - 0x03: Block count (1-15)
  - 0x04: Save title (64 bytes, Shift-JIS, e.g. "FF7/SAVE01/73:25")
  - 0x50: PocketStation MCIcon frame count (or 0x0000)
  - 0x52: PocketStation identifier ("MCX0", "MCX1", "CRD0", or 0x00000000)
  - 0x60: Color palette (32 bytes, 16 colors, 2 bytes/color, 4bpp CLUT)

Frame 1 (0x0080-0x00FF): Icon frame 1 (16x16, 4bpp, indexed to palette)
Frame 2 (0x0100-0x017F): Icon frame 2 (animation or PocketStation icon)
Frame 3 (0x0180-0x01FF): Icon frame 3 (animation or save data if unused)
Frames 4-63 (0x0200-0x1FFF): Save data (game-specific, may use CRC/compression)
```

**Save Identifier Format** (20 bytes):
- Country code (2) + Product code (10) + Identifier (8)
- Example: `BESCES-00868FF7-S01` (FF7 Europe save slot 1)
- Example: `BASCUS-94221FFTA` (FF Tactics USA)
- Example: `BISLPS-01686THESOLIT` (The Solitary Japan)

### File Formats

#### .MCR (ePSXe/PSEmu Format)
- Raw 131,072-byte memory card dump
- Identical to physical card structure
- Used by most emulators (ePSXe, PCSX, RetroArch)
- Can be read/written with MemcardRex, PSXGameEdit

#### .VM1 (PS3 Virtual Memory Card)
- Same 131,072-byte structure as .MCR
- Used in `dev_hdd0/savedata/vmc/`
- Can be renamed to .MCR for editing on PC

#### .PSV (PS3 Single Save Export)
- **Header**: 0x84 bytes
- **Data**: 0x2000 bytes (one 8KB block)
- **Total**: 8,324 bytes (displayed as 8 KB in XMB)

**PSV Header Structure:**
```
0x00: " VSP" magic (0x00 0x56 0x53 0x50)
0x08: Key seed (0x14 bytes, AES-128-CBC encrypted, VTRM type 3)
0x1C: SHA-1 HMAC digest (0x14 bytes)
0x38: Format version (0x14 for PS1, 0x2C for PS2)
0x3C: Console type (0x01 for PS1, 0x02 for PS2)
0x40: Use byte (size displayed in XMB)
0x44: First slot offset (0x84 = start of "SC" area)
0x48: Savedata offset (relative to "SC" start)
0x64: File name (20 bytes, e.g. "BASCUS-94163FF7-S01")
0x84: "SC" savedata block (0x2000 bytes, same as .MCR/.VM1 data block)
```

**PSV Filename**: Product code + Identifier in hex
- Example: `BASCUS-94163FF7-S01` → `BASCUS-941634646372D533031.PSV`

#### .VMP (PSP Virtual Memory Card)
- **Total Size**: 129 KB (131,200 bytes / 0x20080)
- **Header**: 0x80 bytes (PSP-specific encryption)
- **Data**: 0x20000 bytes (same as PS1 card)

**VMP Header:**
```
0x00: " PMV" magic (0x00 0x50 0x4D 0x56)
0x0C: Key seed (0x14 bytes, AES-128-CBC)
0x20: SHA-1 HMAC digest (0x14 bytes)
0x34: Padding (0x4C bytes, 0x00)
0x80: "MC" magic (start of PS1 card data)
```

- Used for PS1 Classics on PSP/Vita
- Two cards per game: SCEVMC0.VMP (slot 1), SCEVMC1.VMP (slot 2)
- Stored in `dev_usb0/PSP/SAVEDATA/<SAVEDATA_DIRECTORY>/`

### Icon Format

**Specs:**
- **Resolution**: 16x16 pixels
- **Color Depth**: 4bpp (4-bit per pixel, 16 colors)
- **Palette**: 16 colors, 2 bytes each (RGB555 or similar)
- **Animation**: Max 3 frames (static = all 3 same frame)
- **Storage**: 128 bytes per frame (1 byte = 2 pixels)

**Encoding:**
- Left nibble (high 4 bits) = pixel N+1
- Right nibble (low 4 bits) = pixel N
- Row-major order (left to right, top to bottom)

**Tools:**
- MemcardRex: Export to BMP/GIF/JPEG/PNG
- PSXGameEdit: Edit icons, animate, replace palette
- GIMP: Import as .ico 4bpp, alpha 1-bit, 16 colors

### Tools & Software

**MemcardRex** (Open Source, Cross-Platform)
- Homepage: http://shendosoft.blogspot.com
- Source: https://github.com/ShendoXT/memcardrex
- **Supports**:
  - .MCR, .GME, .BIN, .MCD, .MEM, .MC, .DDF, .PS, .PSM, .MCI, .SRM
  - .VM1 (PS3 virtual), .VMP (PSP virtual), .PSV (PS3 single save)
  - .MCS, .PSX, .PS1, .MCB, .MCX, .PDA (single save formats)
- **Features**:
  - Icon viewer/exporter (BMP, GIF, JPEG, PNG)
  - Basic icon editor
  - Import/export single saves
  - Cross-platform (Windows, Linux, macOS via Mono)

**PSXGameEdit v1.60**
- Homepage: http://moberg-dybdal.dk/psxge/
- Download: http://moberg-dybdal.dk/psxge/psxge160.zip
- **Supports**:
  - .MC/.MCR (PlaySaver, PSEmuPro)
  - .GME (DexDrive)
  - .MCD (Bleem!)
  - .VGS (Virtual Game Station)
  - .PSX (X-Plorer, Action Replay, GameShark)
- **Features**:
  - Advanced icon editor (palette replace, flip, mirror, rotate, animation)
  - Import/export .ico format (4bpp, 16 colors)
  - Save slot management

**PSV Exporter**
- Download: http://www.ps2savetools.com/wpfb-file/psvexporter11-zip/
- Convert between PS3 .PSV and other formats

### Practical Workflows

#### Extracting Save from PS3
1. FTP to PS3: `dev_hdd0/savedata/vmc/mycard.VM1`
2. Rename to `mycard.MCR`
3. Open in MemcardRex or PSXGameEdit
4. Export individual save as .MCS/.PSX/.PSV
5. Edit or backup as needed

#### Injecting Save to PS3
1. Open `mycard.MCR` in MemcardRex
2. Import single save (.MCS/.PSX/.PSV)
3. Rename to `mycard.VM1`
4. FTP back to PS3: `dev_hdd0/savedata/vmc/`
5. Refresh XMB (copy another save to trigger database update)

#### PSP Export/Import
1. PS3: Copy save from VM1 to PSP (converts to .VMP)
2. Save appears in `dev_usb0/PSP/SAVEDATA/<GAME_DIR>/SCEVMC0.VMP`
3. Edit on PC with MemcardRex (supports .VMP)
4. Copy back to PSP, import to PS3 if needed

## Connections to Existing Projects

### psx-mcr-tool (Planned Enhancement)
**Features to Add:**
1. **Parser**: Read/write .MCR/.VM1/.PSV/.VMP formats
2. **Icon Extractor**: Export icons to PNG (with palette support)
3. **Save Manager**: List saves, export/import individual slots
4. **Validator**: Check checksums, detect corruption
5. **Converter**: .MCR ↔ .VM1 ↔ .PSV ↔ .VMP
6. **TUI**: Browse memory card contents (ratatui)

**Technical Stack:**
- Rust for parsing (bitflags, byteorder crates)
- Image crate for PNG export (palette conversion)
- Ratatui for TUI interface

### psx-terra (ARG Integration)
**Narrative Hooks:**
- Memory card corruption as plot device
- Hidden saves with ARG clues (custom identifiers)
- PocketStation integration (MCX0/MCX1/CRD0 icons)
- Fake "lost saves" from abandoned playthroughs

### Game Preservation Tooling
**Archive Applications:**
1. **Save Library**: Catalog saves by game/region/version
2. **Icon Atlas**: Build visual index of all PSX save icons
3. **Metadata Extractor**: Parse titles, timestamps, play time
4. **Checksum Validator**: Verify save integrity (detect tampering)

## Key Technical Findings

### Critical Details
1. **XOR Checksums**: Frames use simple XOR of all bytes (not CRC)
2. **Link Chains**: Multi-block saves use link pointers (frame offset 0x08)
3. **PocketStation**: Requires "P" in product code + MCX0/MCX1/CRD0 identifier
4. **Encryption**: .PSV/.VMP use AES-128-CBC (key seed in header)
5. **Compatibility**: .MCR and .VM1 are identical (just rename extension)

### Gotchas
- **Block 0 is invisible**: Not shown in XMB, purely metadata
- **Icon frame order**: Frame 1=static/first, 2=second, 3=third (or unused)
- **Shift-JIS encoding**: Save titles use Japanese text encoding
- **4bpp pixel packing**: Two pixels per byte (nibble order matters)
- **FAT allocation**: Available blocks byte uses upper/lower nibble flags

## References

### Primary Sources
- **PS3DevWiki - PS1 Savedata**: https://www.psdevwiki.com/ps3/PS1_Savedata
- **Raphnet PSX Memory Card Guide**: https://www.raphnet-tech.com/support/psx_memory_card_operations/
- **Joshua Walker's PSX Hardware Doc**: "Everything You Always Wanted to Know About PlayStation" (PDF)

### Tools
- **MemcardRex**: https://github.com/ShendoXT/memcardrex
- **PSXGameEdit**: http://moberg-dybdal.dk/psxge/
- **PSV Exporter**: http://www.ps2savetools.com/

### Community
- PS3Hax forums (save hacking discussions)
- PSXDev forums (hardware/format docs)
- Tortuga Cove (preservation community)

## Next Steps

1. **Prototype Parser**: Implement .MCR reader in Rust (psx-mcr-tool)
2. **Icon Extraction**: Build PNG exporter with palette support
3. **TUI Interface**: Browse saves, view icons, export/import
4. **Format Converter**: .MCR ↔ .PSV ↔ .VMP with encryption support
5. **Integration**: Add to psx-terra for ARG narrative devices

## Session Notes

**Search Strategy:**
- Targeted searches for format specs, file structure, tools
- Cross-referenced PS3DevWiki (canonical), Raphnet (hardware), community forums
- Verified byte offsets and magic numbers across multiple sources

**Key Insight:**
The PS1 memory card format is remarkably simple (FAT-like allocation, XOR checksums), but icon handling is nuanced (4bpp packing, palette-indexed, animation frames). Tools like MemcardRex handle the grunt work, but custom tooling enables preservation and ARG integration.

**Community Resources:**
- PS3DevWiki is exhaustive (byte-level documentation)
- MemcardRex is gold standard (open source, cross-platform)
- PSXGameEdit has best icon editor (palette manipulation)

**Time Breakdown:**
- Initial searches: 8 min
- Deep-dive web fetches: 12 min
- Format analysis: 12 min
- Documentation: 13 min

---

**Total Search Budget Used**: 4/20 (cumulative with automotive research)
**Confidence Level**: High (official specs, multiple tool confirmations)
**Immediate Actionability**: High (clear format, existing tools as reference)
