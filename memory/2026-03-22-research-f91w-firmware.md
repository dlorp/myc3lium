# Hardware Research: Casio F91W Firmware & Mods (2026-03-22 02:00-03:00 Alaska)

## Session Metadata
- **Session ID**: a95d58ec-dfcf-4872-a9e4-4b1364fd70eb
- **Type**: Off-hours deep work (Session 4: RESEARCH rotation)
- **Focus**: F91W custom firmware, Pluto watch, Sensor Watch
- **Searches**: 3 (13 remaining in budget)

## Research Summary

### Pluto Watch Project

**Overview:**
Pluto is a programmable digital watch that reuses the Casio F91W case and LCD but replaces the PCB entirely.

**Hardware:**
- **MCU**: MSP430FR6972 (16MHz, 64KB FRAM, 2KB SRAM, integrated LCD controller)
- **Compass**: MAG3110 (I²C, powered from GPIO to enable shutdown)
- **IR Receiver**: TSOP57338 (38kHz, for software updates/TOTP transfer)
- **PCB Thickness**: 0.6mm (critical for fit)
- **Finish**: ENIG (gold) for corrosion resistance
- **Power**: CR2016 coin cell (>1 year battery life)

**Software Features:**
- Multiple time bases (decimal, binary, hex)
- Multiple alarms with RTTTL ringtones
- Multiple countdown timers
- Stopwatch
- Compass
- Speedometer (distance → time → km/h)
- TOTP (RFC 6238, WIP)
- Menu-driven interface
- Infrared updates (WIP)

**Key Technical Decisions:**
1. **LCD Controller**: MSP430FR6972 has integrated segment LCD driver (critical for 0.6mm PCB)
2. **No Accelerometer**: Even "ultra-low power" draws ~30µA continuous (kills CR2016 in <6 months)
3. **No Radio**: nRF24L01 requires external balun/antenna (no space). CC430 (sub-1GHz) needs large antenna.
4. **Compass over Accel**: Dedicate space to useful peripheral (compass) vs. power-hungry always-on sensor
5. **IR vs. BLE**: IR receiver is same size as nRF24 but no external components

**Manufacturing Notes:**
- PCB from Elecrow (0.6mm, castellated vias surcharge)
- Some vias not covered by solder mask (insulate bottom with tape)
- Outline traced from flatbed scan (eliminates photo distortion)
- Designed in KiCad (DXF import for outline)

**Repositories:**
- **Hardware**: https://github.com/carrotIndustries/pluto
- **Software**: https://github.com/carrotIndustries/pluto-fw
- **Related**: https://github.com/travisgoodspeed/goodwatch (more buttons + radio)

### Sensor Watch (Related Project)

**Overview:**
Another F91W board-swap project (mentioned in search results, not deeply researched this session).

**Key Differences from Pluto:**
- More sensors (temperature, light, accelerometer?)
- Different MCU/firmware architecture
- Focus on sensor expansion vs. Pluto's minimalism

**Reference:**
- Mentioned on Hacker News: https://news.ycombinator.com/item?id=37058171

### F91W LCD Constraints

**Why F91W Specifically:**
- Original attempt: Casio W800, F-201, DB-36
- Problem: All use 5-mux LCDs + need 5Vpp drive voltage
- No MCU exists with both: 5V LCD boost + 5-mux capability
  - RL78 family (Renesas): Has 5V boost but only 1/2/3/4/8-mux
  - EPSON MCUs: Can do 5-mux + 5V but not enough segment pins in QFN64
- F91W uses simpler LCD compatible with MSP430FR6972

**LCD Reverse Engineering:**
- Apply square wave to all pins
- Invert one pin at a time
- Few segments light = SEG pin, many segments = COM (backplane) pin
- F91W segments: Some "independent" segments driven as one (to save pins)

### Power Budget Analysis

**EnergyTrace Profiling:**
- Used MSP430FR4133 LaunchPad with EnergyTrace
- Tool: https://github.com/carrotIndustries/energytrace-util
- Goal: Verify >1 year battery life estimate

**Power-Saving Techniques:**
1. **GPIO Power Control**: MAG3110 + TSOP57338 powered from GPIO (shutdown when unused)
2. **FRAM vs. Flash**: FRAM = zero write penalty (vs. Flash erase cycles)
3. **LCD Optimization**: Segment LCD has minimal quiescent current
4. **RTC Clock**: Low-power RTC runs continuously (MSP430 ultralow LPM)

## Connections to F91W-FIRMWARE-STUDIO Project

**Current Status:**
- Project exists at `~/repos/prototypes/F91W-FIRMWARE-STUDIO`
- Modified docs: IMPLEMENTATION.md, README.md, USAGE.md
- New file: PROJECT_SUMMARY.md (uncommitted)

**Enhancement Ideas:**
1. **Simulator**: Online simulator for testing firmware before flashing
2. **Module Library**: Pre-built firmware modules (TOTP, compass, ringtones)
3. **IR Programmer**: Software for infrared firmware updates
4. **Case Templates**: 3D models for custom backs/straps
5. **Battery Life Calculator**: Estimate runtime based on feature usage

**Technical Integration:**
- MSP430FR6972 development (TI Code Composer Studio examples)
- LCD segment driver code (understand register mapping)
- RTTTL parser (for alarm ringtones)
- I²C bit-bang implementation (for MAG3110 compass)

## Key Technical Findings

### Critical Design Constraints
1. **0.6mm PCB**: Non-negotiable for case fit (standard = 1.6mm)
2. **Castellated Vias**: For spring contacts (button springs)
3. **Battery Clearance**: Bottom side must be flat (desolder piezo spring)
4. **LCD Segment Count**: MSP430FR6972 has 116 segments (verify F91W needs <116)
5. **5V TTL Levels**: For IR receiver (38kHz carrier frequency)

### Fabrication Tips
- **Scanner Tracing**: Use flatbed scanner (no lens distortion) for outline
- **Inkscape + GIMP**: Correct camera distortion, trace outline, export DXF
- **Gold Finish**: ENIG required (original F91W is gold-plated for reliability)
- **Insulation**: Tape bottom of PCB (exposed vias contact battery)
- **Assembly**: Use microscope for 0402/0603 components (dense layout)

### Software Architecture
- **Interrupt-Driven**: RTC wakes MCU for updates (not polling loop)
- **State Machine**: Menu system, mode transitions
- **FRAM Persistence**: Settings survive power loss (no EEPROM needed)
- **IR Protocol**: Custom protocol for updates (38kHz modulation)

## References

### Primary Sources
- **Pluto Hardware**: https://github.com/carrotIndustries/pluto
- **Pluto Firmware**: https://github.com/carrotIndustries/pluto-fw
- **EEVblog Forum**: http://www.eevblog.com/forum/oshw/diy-watch-based-on-the-casio-f-91w/
- **Goodwatch (Alt Project)**: https://github.com/travisgoodspeed/goodwatch

### Component Datasheets
- **MSP430FR6972**: https://www.ti.com/lit/ds/symlink/msp430fr6972.pdf
- **MAG3110**: Freescale/NXP magnetometer (I²C)
- **TSOP57338**: Vishay 38kHz IR receiver

### Related Projects
- **Sensor Watch**: Board-swap with more sensors
- **Kepler F91W**: Open-source smartwatch mod (developer wants continuation)
- **Data Runner**: N-O-D-E's F91W mod (different approach)

### Community
- EEVblog forums (hardware discussions)
- Hacker News (project visibility)
- r/casio (mod showcase)

## Next Steps

1. **MSP430 Toolchain**: Install Code Composer Studio (TI's IDE)
2. **LCD Segment Mapping**: Reverse-engineer F91W LCD pinout
3. **Prototype PCB**: Design 0.6mm test board (Elecrow fab)
4. **IR Programmer**: Build transmitter circuit (38kHz modulation)
5. **Firmware Modules**: TOTP, compass, custom ringtones

## Session Notes

**Search Strategy:**
- Focused on Pluto (most complete, well-documented project)
- Skipped deep dive on Sensor Watch (save for future session)
- Prioritized hardware constraints (why F91W vs. other watches)

**Key Insight:**
The F91W is chosen NOT because it's iconic (though it is), but because its LCD is compatible with available MCUs. The 5-mux constraint eliminates most other Casio watches. The 0.6mm PCB thickness is the second critical constraint.

**Community Resources:**
- Pluto is gold standard (schematic, BOM, assembly notes, firmware)
- EEVblog forum has debugging discussions
- Goodwatch adds radio (if you need mesh/RF)

**Time Breakdown:**
- Initial search: 5 min
- Pluto deep-dive: 12 min
- Hardware analysis: 8 min
- Documentation: 10 min

---

**Total Search Budget Used**: 3/20 (cumulative: 7/20 across all topics)
**Confidence Level**: High (complete project with schematics, code, photos)
**Immediate Actionability**: Medium (requires PCB fab, SMD soldering skills)
