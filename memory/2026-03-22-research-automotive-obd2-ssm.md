# Automotive Research: Subaru OBD2/SSM Protocol (2026-03-22 02:00-03:00 Alaska)

## Session Metadata
- **Session ID**: a95d58ec-dfcf-4872-a9e4-4b1364fd70eb
- **Type**: Off-hours deep work (Session 4: RESEARCH rotation)
- **Focus**: Automotive diagnostics, OBD2, Subaru SSM protocol for EJ22
- **Searches**: 4 (20 remaining in budget)

## Research Summary

### Subaru Select Monitor (SSM) Protocol

**Protocol Specs:**
- **Interface**: ISO9141-2 K-line communication
- **Baud Rate**: 4800 bps, 8-N-1 (8 data bits, no parity, 1 stop bit)
- **Signal Level**: TTL (+5V), NOT standard ISO9141 voltage levels
- **Max Packet Size**: ~250 bytes (includes echoed request + response)

**Packet Structure:**
```
0x80                    // Header magic
[Destination]           // 0x10 = ECU, 0x18 = TCU, 0xF0 = Diagnostic tool
[Source]                // Same address space
[Data Size]             // Number of data bytes
[Command/Response]      // See commands below
[data...]               // Variable length
[Checksum]              // 8 LSB of sum of all packet bytes
```

**Known Commands:**
- `0xA0` - Block read (memory range)
- `0xA8` - Address read (specific addresses, up to multiple)
- `0xB0` - Block write (memory range) - **ROM write blocked on production ECUs**
- `0xB8` - Address write (SSM_Set function, offset-based)
- `0xBF` - ECU Init (returns capability bits + ECU ID)

**ECU ROM ID Format** (6 hex digits):
- Digit 1: Always 7 (Subaru marker?)
- Digit 2: Model year (0=1990, 2=1992, 4=1994...)
- Digits 3-4: Car/engine type (25=SVX/EG33, 31=Legacy/EJ20, 32=Legacy/EJ22)
- Digit 5: Market (1=Japan, 2=USA, 3=Europe, A=UK)
- Digit 6: ECU firmware revision

**Example EJ22 ROM IDs:**
- `703243` - 1991 EDM Legacy EJ22 (JECS D4 M37791)
- `7232A5` - 1992 UK Legacy EJ22
- `733257` - 1993 Canada Legacy EJ22
- `7432A1` - 1996 UK Legacy EJ22

**Key Technical Findings:**
1. **TTL Signal Levels**: Standard ISO9141 cables will NOT work. SSM uses TTL (+5V) levels, not RS-232 voltage levels.
2. **ROM Access**: ECU Init (0xBF) reads ROM ID from address 0x8C3D (not via command).
3. **Memory Restrictions**: Cannot read 0x00000000-0x00002000 (bootloader), 0x000FFB80-0xFFFF2000 (checksums/vectors), or 0xFFFF3FE4-0xFFFFFFFF (peripherals).
4. **SSM_Get/SSM_Set**: Address write (0xB8) is offset-based (offset = [AA_2][AA_3] * 4), not direct memory access.
5. **Capability Bits**: ECU Init response bytes 9-56 contain flags indicating which parameters are supported (Engine Load, Coolant Temp, AFR, Timing, MAF, etc.).

**Parameter Addresses** (via 0xA8 command):
- `0x000008` - Coolant Temperature (°C = value - 40)
- `0x00000E/0x00000F` - Engine Speed (RPM = value / 4, 16-bit)
- `0x000010` - Vehicle Speed (km/h, direct)
- `0x000011` - Ignition Timing (degrees = (value - 128) / 2)
- `0x000013/0x000014` - Mass Air Flow (g/s = value / 100, 16-bit)
- `0x00001C` - Battery Voltage (V = value * 0.08)
- `0x000020` - Fuel Injection Pulse Width #1 (ms = value * 0.256)

**Hardware Notes:**
- **OBD-2 Pinout**: Pin 7 (K-line), Pin 4/5 (ground), Pin 16 (12V power)
- **SSM Connector**: 9-pin under dash (pre-OBD2 cars) shares same K-line signals
- **Adapter Requirements**: VAG-COM/ELM327 cables do NOT work (wrong voltage). Need TTL-level USB-UART adapter (FTDI FT232, CP2102, CH340) with custom pinout.

**Software Compatibility:**
- **JECScan**: Best compatibility for JECS ECUs (1990-1998)
- **FreeSSM**: Hit-or-miss on older ECUs
- **RomRaider**: Good for 1999+
- **EvoScan**: Connects but needs custom definition files

**ROM Dumping:**
- External tools (Snowmobile Select Monitor utility) can dump via 0xA0 block read
- Archive at alcyone.org.uk/ssm/ecuroms.html contains many dumped ROMs
- ROMs are 32KB (padded to 64KB in dumps, data starts at 0x8000)

## Connections to r3LAY Project

**Immediate Applications:**
1. **OBD2-TUI Enhancement**: Implement SSM protocol support for Subaru vehicles
2. **EJ22 Maintenance Tracker**: Real-time parameter logging (coolant temp, timing, AFR, MAF)
3. **Diagnostic Tool**: Read/clear DTC codes, monitor sensor health
4. **Data Logger**: Export CSV logs for performance analysis

**Technical Implementation:**
- Use FTDI FT232RL (TTL UART, 5V tolerant)
- Implement SSM packet parser in Rust/Go
- Create definition files for EJ22-specific parameters
- Build TUI with live gauges (ratatui framework)

**Garage Hobbyist Features:**
- Pre-trip sensor check (coolant, timing, AFR within range?)
- Data logging during drives (export to CSV/JSON)
- Fault code reader (no need for expensive scan tools)
- ROM ID verification (confirm ECU model matches car)

## References

### Primary Sources
- **RomRaider SSM Protocol Docs**: https://www.romraider.com/RomRaider/SsmProtocol
- **Alcyone SSM Archive**: http://www.alcyone.org.uk/ssm/
- **RS25 SSM Investigation**: https://www.rs25.com/threads/subaru-select-monitor-ssm-investigation.165108/

### ROM Archives
- Alcyone ECU ROM collection (703243, 7232A5, 733257, 7432A1 for EJ22)
- Disassembled code + hex dumps available
- Shared by community contributors

### Hardware
- FTDI FT232RL breakout boards (~$5-10)
- Custom OBD-2 breakout cable (pins 4, 5, 7, 16)
- 510Ω pull-up resistor to 12V (K-line idle state)

## Next Steps

1. **Prototype**: Build TTL-level OBD-2 adapter (FTDI + resistors)
2. **Test Bench**: Verify packet structure with spare ECU
3. **Software**: Implement SSM parser in Rust (r3LAY codebase)
4. **TUI**: Build live dashboard with ratatui
5. **Integration**: Add to obd2-tui and ej22-tracker projects

## Session Notes

**Search Strategy:**
- Multi-language search not needed (English sources dominant for automotive)
- Focused on protocol specs, ROM formats, hardware requirements
- Cross-referenced multiple sources (RomRaider, Alcyone, RS25 forums)
- Verified technical details (baud rate, packet structure, voltage levels)

**Key Insight:**
The critical discovery is that SSM uses **TTL voltage levels**, not standard ISO9141. This explains why cheap OBD-2 cables fail. A $5 FTDI board solves this.

**Community Resources:**
- Alcyone archive is a goldmine (ECU ROM dumps, protocol docs)
- RS25 forums have real-world debugging experiences
- RomRaider wiki is canonical reference for packet structure

**Time Breakdown:**
- Initial searches: 10 min
- Deep-dive web fetches: 15 min
- Technical analysis: 10 min
- Documentation: 10 min

---

**Total Search Budget Used**: 4/20
**Confidence Level**: High (multiple corroborating sources, community validation)
**Immediate Actionability**: High (clear hardware path, documented protocol)
