# myc3lium ESP32 Handheld - Phase 1 Firmware Scaffold

## Overview

This is the Phase 1 implementation of the myc3lium handheld firmware, featuring:

1. **Directory structure** - Complete firmware organization for ESP-IDF
2. **CMake build system** - Variant-aware builds (halow or lora)
3. **Core components** - Shared configuration, state machine, and initialization
4. **Variant drivers** - Stub implementations for HT-HC01P (HaLow) and SX1262 (LoRa)
5. **Git-tracked** - Feature branch ready for review

## Directory Structure

```
firmware/
├── CMakeLists.txt              Top-level ESP-IDF build config
├── src/
│   ├── main.cpp                Entry point with state machine skeleton
│   ├── core/                   Shared components
│   │   ├── myc3_core.h         Core types and config API
│   │   └── myc3_core.cpp       NVS-backed config storage
│   ├── halow/                  Variant A: HT-HC01P driver
│   │   ├── halow_driver.h      HaLow interface (stub)
│   │   └── halow_driver.cpp    HaLow implementation (stub)
│   └── lora/                   Variant B: SX1262 driver
│       ├── lora_driver.h       LoRa interface (stub)
│       └── lora_driver.cpp     LoRa implementation (stub)
├── include/
│   └── myc3_config.h           Compile-time configuration macros
├── config/
│   ├── variant_halow.cmake     HaLow variant config (reference)
│   └── variant_lora.cmake      LoRa variant config (reference)
├── components/                 ESP-IDF component structure
│   ├── myc3_core/
│   ├── myc3_halow/
│   ├── myc3_lora/
│   └── main/
├── partitions.csv              OTA-capable partition table for ESP32-S3
└── PHASE_1_README.md           This file
```

## Building

### Prerequisites

- ESP-IDF v5.x (installed and sourced)
- ESP32-S3 toolchain
- CMake 3.16+

### Build Variants

Build for **HaLow (Variant A)**:
```bash
cd firmware
export MYC3_VARIANT=halow
idf.py build
```

Build for **LoRa (Variant B)**:
```bash
cd firmware
export MYC3_VARIANT=lora
idf.py build
```

### Flash

```bash
idf.py -p /dev/ttyUSB0 flash monitor
```

## State Machine

The firmware implements a boot-time state machine:

```
BOOT
  Load config from NVS
  UUID found?
    YES -> CONFIG
    NO  -> SETUP_MODE

CONFIG
  Validate configuration
  -> CONNECT

SETUP_MODE
  Serve WebUI on AP
  Wait for configuration
  (Phase 3 deliverable)

CONNECT
  Join myc3-mesh network
  -> POL_DETECT

POL_DETECT
  RSSI sweep for antenna polarization
  -> OPERATIONAL

OPERATIONAL
  Normal operation (heartbeat, radio active)
  Periodic polarization check-in
```

## Configuration (NVS)

Configuration is persisted in NVS (Non-Volatile Storage) under namespace `myc3`:

### Identity Keys
- `node_uuid` - RFC 4122 UUID (generated on first boot)
- `node_name` - Human-readable node name
- `node_role` - Node role: sensor/relay/endpoint/gateway
- `hw_variant` - Hardware variant: 0=halow, 1=lora

### Polarization Keys
- `pol_mode` - 0=auto, 1=rhcp, 2=lhcp
- `pol_current` - Current polarization (0=unknown, 1=rhcp, 2=lhcp)
- `rssi_rhcp`, `rssi_lhcp` - Last measured RSSI values
- `pol_interval` - Re-check interval in minutes (default: 30)

### Network Keys
- `mesh_ssid` - Mesh SSID (default: "myc3-mesh")
- `mesh_key` - Mesh pre-shared key
- `router_ip` - RPi router IP address

### Power Keys
- `sleep_enabled` - 0=off, 1=light, 2=deep
- `wake_interval` - Wake interval in seconds
- `tx_power` - TX power in dBm

## API Overview

### Core Functions (myc3_core.h)

```c
void myc3_core_init(void);
void myc3_core_load_config(myc3_config_t *config);
void myc3_core_save_config(const myc3_config_t *config);
void myc3_core_reset_config(void);
void myc3_core_set_state(node_state_t state);
node_state_t myc3_core_get_state(void);
void myc3_core_get_uuid(char *uuid_buf, size_t buf_len);
void myc3_core_set_node_name(const char *name);
```

### Variant A: HaLow Driver (halow_driver.h)

```c
void halow_driver_init(void);
void halow_driver_deinit(void);
int halow_driver_get_rssi(void);
bool halow_driver_start_rx(void);
bool halow_driver_stop_rx(void);
bool halow_driver_transmit(const uint8_t *data, size_t len);
void halow_driver_set_tx_power(int8_t power_dbm);
bool halow_driver_join_mesh(const char *ssid, const char *key);
bool halow_driver_is_connected(void);
```

### Variant B: LoRa Driver (lora_driver.h)

```c
void lora_driver_init(void);
void lora_driver_deinit(void);
int lora_driver_get_rssi(void);
int lora_driver_get_snr(void);
bool lora_driver_start_rx(void);
bool lora_driver_stop_rx(void);
bool lora_driver_transmit(const uint8_t *data, size_t len);
void lora_driver_set_tx_power(int8_t power_dbm);
void lora_driver_set_frequency(lora_freq_t freq);
void lora_driver_set_bandwidth(lora_bandwidth_t bw);
bool lora_driver_join_mesh(const char *network_key);
bool lora_driver_is_connected(void);
```

## Compile Definitions

### HaLow Build (MYC3_VARIANT=halow)
- `MYC3_VARIANT_HALOW` - Variant A active
- `GPIO_ANT_SW_CTRL=14` - Antenna switch GPIO
- `GPIO_ANT_SW_VDD=15` - Antenna switch enable GPIO

### LoRa Build (MYC3_VARIANT=lora)
- `MYC3_VARIANT_LORA` - Variant B active
- `GPIO_ANT_SW_CTRL=2` - Antenna switch GPIO
- `GPIO_ANT_SW_VDD=3` - Antenna switch enable GPIO
- `GPIO_OLED_SDA=21` - OLED SDA pin
- `GPIO_OLED_SCL=22` - OLED SCL pin

## Partition Table

The `partitions.csv` defines an OTA-capable layout:

- **NVS** (0x9000, 28KB) - Encrypted configuration storage
- **PHY_INIT** (0x10000, 4KB) - PHY calibration data
- **FACTORY** (0x20000, 1968KB) - Initial firmware
- **OTADATA** (0x210000, 8KB) - OTA state
- **OTA_0** (0x220000, 1968KB) - OTA slot 0
- **OTA_1** (0x410000, 1968KB) - OTA slot 1

Total: 8MB ESP32-S3 flash

## Current Status

This is **Phase 1: Foundation** - a complete scaffold ready for Phase 2 (polarization detection).

### Implemented
- Directory structure per design doc
- CMake build system with variant selection
- NVS-backed configuration store
- State machine skeleton
- Core types and enums
- Driver stubs for both variants

### Stubbed (Next Phases)
- HaLow/LoRa radio initialization (Phase 4)
- Antenna polarization sweep (Phase 2)
- WebUI and setup flow (Phase 3)
- Power management (Phase 5)
- OTA updates (Phase 5)

## Testing

To verify the build compiles:

```bash
# Build for HaLow
export MYC3_VARIANT=halow
idf.py build 2>&1 | grep -E "(Building|Compiling|Error)"

# Build for LoRa
export MYC3_VARIANT=lora
idf.py build 2>&1 | grep -E "(Building|Compiling|Error)"
```

## Next Steps (Phase 2)

- [ ] Implement RF switch control (GPIO)
- [ ] RSSI reading abstraction (HaLow AT cmd / SX1262 register)
- [ ] Polarization sweep algorithm
- [ ] Periodic re-detection task
- [ ] Heartbeat packet format
- [ ] RPi router node registry integration

## Notes

- **No emoji in code** (AXIOM-037 constraint) - documentation only
- **ESP-IDF, not Arduino** - uses FreeRTOS and low-level drivers
- **Dual-variant** - Single firmware codebase, compile-time variant selection via `MYC3_VARIANT` env var
- **Git ready** - Feature branch `feature/phase-1-firmware-scaffold` with atomic commits

---

**Phase 1 Deliverables Checklist:**
- [x] Firmware directory structure
- [x] CMakeLists.txt with variant selection
- [x] main.cpp state machine skeleton
- [x] myc3_core.h/cpp shared core
- [x] myc3_config.h compile-time config
- [x] halow_driver.h/cpp stubs
- [x] lora_driver.h/cpp stubs
- [x] Partition table for OTA
- [x] Component-based organization
- [x] Git feature branch created

**Ready for Phase 2: Polarization Detection**
