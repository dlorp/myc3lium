# myc3lium ESP32 Handheld Node System — Design Document

**Version:** 1.0  
**Date:** 2026-03-20  
**Status:** Draft  

---

## 1. System Overview

```
                        ┌─────────────────────────┐
                        │   RPi4 Main Node        │
                        │  ┌───────────────────┐  │
                        │  │ HT-HC01P HaLow    │  │
                        │  │ AP: myc3-mesh      │  │
                        │  └───────┬───────────┘  │
                        │          │               │
                        │  ┌───────┴───────────┐  │
                        │  │ myc3-router        │  │
                        │  │ (node registry,    │  │
                        │  │  polarization mgr, │  │
                        │  │  flash server)     │  │
                        │  └───────────────────┘  │
                        └────────┬──┬─────────────┘
                     HaLow 900MHz│  │USB/Serial
                    ┌────────────┘  │(flash only)
                    │               │
        ┌───────────┴──┐    ┌──────┴──────────┐
        │ Variant A     │    │ Variant B        │
        │ ESP32-S3 CAM  │    │ Heltec V3        │
        │ + HT-HC01P    │    │ SX1262 LoRa      │
        │ (headless)    │    │ + OLED            │
        │               │    │ + USB-C           │
        │ RHCP/LHCP ant │    │ RHCP/LHCP ant    │
        └───────────────┘    └──────────────────┘
```

### Handheld Variants

| Feature | Variant A: ESP32-S3 CAM | Variant B: Heltec V3 |
|---|---|---|
| MCU | ESP32-S3 | ESP32-S3 |
| Radio | HT-HC01P HaLow (built-in) | SX1262 LoRa 915MHz |
| Display | None (headless) | 0.96" OLED (SSD1306) |
| Camera | Yes (OV2640) | No |
| USB | Micro-USB (flash only) | USB-C (flash + charge) |
| Battery | LiPo via external PMIC | LiPo via onboard charger |
| Antenna | Dual CP switchable | Dual CP switchable |
| Config | WebUI only | OLED + buttons + WebUI |

---

## 2. Firmware Architecture

### 2.1 Shared Component Layer

Both variants share a common firmware core built on ESP-IDF (v5.x) with the following modules:

```
firmware/
├── main/
│   ├── main.c                    # Entry point, variant dispatch
│   └── Kconfig.projbuild         # Build-time variant selection
├── components/
│   ├── myc3_core/                # ── Shared ──
│   │   ├── node_identity.c/h     # UUID, node type, polarization state
│   │   ├── config_store.c/h      # NVS-backed persistent config
│   │   ├── power_mgmt.c/h        # Sleep modes, wake sources
│   │   ├── ota_update.c/h        # OTA from RPi
│   │   └── heartbeat.c/h         # Periodic check-in to router
│   ├── myc3_polarization/        # ── Shared ──
│   │   ├── antenna_switch.c/h    # RF switch control (GPIO)
│   │   ├── pol_detect.c/h        # RSSI-based polarization detection
│   │   └── pol_report.c/h        # Report polarization to router
│   ├── myc3_webui/               # ── Shared ──
│   │   ├── webserver.c/h         # Lightweight HTTP server (esp_http_server)
│   │   ├── captive_portal.c/h    # DNS redirect for setup
│   │   ├── ws_handler.c/h        # WebSocket for live status
│   │   └── www/                  # Embedded HTML/JS/CSS (gzipped)
│   │       ├── index.html
│   │       ├── wizard.js
│   │       └── style.css
│   ├── myc3_halow/               # ── Variant A only ──
│   │   ├── ht_hc01p_driver.c/h   # HT-HC01P UART/SPI driver
│   │   ├── halow_mesh.c/h        # S1G mesh join/management
│   │   └── halow_scan.c/h        # Channel/RSSI scanning
│   ├── myc3_lora/                # ── Variant B only ──
│   │   ├── sx1262_driver.c/h     # SX1262 SPI driver
│   │   ├── lora_mesh.c/h         # LoRa mesh protocol
│   │   └── lora_scan.c/h         # RSSI scanning for polarization
│   └── myc3_display/             # ── Variant B only ──
│       ├── oled_driver.c/h       # SSD1306 I2C driver
│       └── ui_screens.c/h        # Status, config, polarization screens
├── partitions.csv                # OTA-capable partition table
└── CMakeLists.txt
```

### 2.2 Build Variants

```cmake
# CMakeLists.txt — variant selection
set(MYC3_VARIANT "$ENV{MYC3_VARIANT}")  # "cam" or "heltec"

if(MYC3_VARIANT STREQUAL "cam")
    set(EXTRA_COMPONENT_DIRS "components/myc3_halow")
    add_compile_definitions(MYC3_VARIANT_CAM=1)
elseif(MYC3_VARIANT STREQUAL "heltec")
    set(EXTRA_COMPONENT_DIRS "components/myc3_lora" "components/myc3_display")
    add_compile_definitions(MYC3_VARIANT_HELTEC=1)
endif()
```

### 2.3 State Machine

```
    ┌──────────┐
    │  BOOT    │
    └────┬─────┘
         │ Read NVS config
         ▼
    ┌──────────┐    No config     ┌──────────────┐
    │ CONFIG?  ├─────────────────►│ SETUP MODE   │
    └────┬─────┘                  │ (AP + WebUI) │
         │ Has config             └──────┬───────┘
         ▼                               │ Config saved
    ┌──────────┐                         │
    │ CONNECT  │◄────────────────────────┘
    │ to mesh  │
    └────┬─────┘
         │ Connected
         ▼
    ┌──────────────┐
    │ POL_DETECT   │  Sweep RHCP/LHCP, measure RSSI
    └────┬─────────┘
         │ Best polarization selected
         ▼
    ┌──────────────┐
    │ OPERATIONAL  │◄──── Heartbeat loop
    │              │      (report status,
    │  Radio active│       polarization,
    │  WebUI avail │       battery %)
    │  Low-power   │
    │  sleep cycles│
    └──────────────┘
```

---

## 3. Antenna Polarization Detection

### 3.1 Hardware Design

Each handheld has a **dual-feed circularly polarized antenna** with an RF switch:

```
                ┌─────────────────────┐
                │  Patch/Helix Antenna │
                │  ┌───────┐          │
                │  │ RHCP  │ Feed A   │
                │  │ port  ├──────┐   │
                │  └───────┘      │   │
                │  ┌───────┐      │   │
                │  │ LHCP  │ Feed B   │
                │  │ port  ├──┐   │   │
                │  └───────┘  │   │   │
                └─────────────┼───┼───┘
                              │   │
                         ┌────┴───┴────┐
                         │ RF Switch   │
                         │ (SKY13351)  │
                         │             │
                         │ CTRL ──► GPIO │
                         └──────┬──────┘
                                │ RF_OUT
                                ▼
                         Radio module
                    (HT-HC01P or SX1262)
```

**RF Switch:** SKY13351-378LF (SPDT, DC–6GHz, 0.5dB IL)
- GPIO HIGH → RHCP feed selected
- GPIO LOW  → LHCP feed selected

### 3.2 GPIO Pin Assignments

| Signal | ESP32-S3 CAM (Variant A) | Heltec V3 (Variant B) |
|---|---|---|
| ANT_SW_CTRL | GPIO 14 | GPIO 2 |
| ANT_SW_VDD | GPIO 15 (enable) | GPIO 3 (enable) |
| RSSI_READ | Via HT-HC01P AT cmd | Via SX1262 register |

### 3.3 Detection Algorithm (RSSI-Based)

```c
// pol_detect.c — Polarization detection via RSSI comparison

#define POL_SAMPLES       10
#define POL_SWEEP_MS      100    // ms between samples
#define POL_MARGIN_DB     3      // minimum dB difference to declare winner
#define POL_RECHECK_MIN   30     // re-check interval in minutes

typedef struct {
    pol_state_t current;         // RHCP, LHCP, or UNKNOWN
    int8_t rssi_rhcp;            // avg RSSI on RHCP
    int8_t rssi_lhcp;            // avg RSSI on LHCP
    uint32_t last_check;         // timestamp
    bool locked;                 // user override (manual selection)
} pol_status_t;

pol_state_t pol_detect_best(void) {
    int32_t rhcp_sum = 0, lhcp_sum = 0;
    
    // Phase 1: Sample RHCP
    antenna_switch_set(POL_RHCP);
    vTaskDelay(pdMS_TO_TICKS(50));  // settling time
    for (int i = 0; i < POL_SAMPLES; i++) {
        rhcp_sum += radio_get_rssi();   // abstracted per variant
        vTaskDelay(pdMS_TO_TICKS(POL_SWEEP_MS));
    }
    
    // Phase 2: Sample LHCP
    antenna_switch_set(POL_LHCP);
    vTaskDelay(pdMS_TO_TICKS(50));
    for (int i = 0; i < POL_SAMPLES; i++) {
        lhcp_sum += radio_get_rssi();
        vTaskDelay(pdMS_TO_TICKS(POL_SWEEP_MS));
    }
    
    int8_t avg_rhcp = rhcp_sum / POL_SAMPLES;
    int8_t avg_lhcp = lhcp_sum / POL_SAMPLES;
    
    if (abs(avg_rhcp - avg_lhcp) < POL_MARGIN_DB) {
        return POL_UNKNOWN;  // too close to call; use last known or default
    }
    
    return (avg_rhcp > avg_lhcp) ? POL_RHCP : POL_LHCP;
}
```

### 3.4 Adaptive Re-detection

- **On boot:** Full sweep (mandatory)
- **Every 30 min:** Quick sweep (5 samples per polarization)
- **On signal drop (>10dB):** Immediate full sweep
- **User override:** Manual lock via WebUI/OLED disables auto-detection

---

## 4. Persistent Configuration Format

Stored in NVS (Non-Volatile Storage) under namespace `myc3`:

```c
// config_store.h — NVS key definitions

// Identity
#define NVS_NODE_UUID       "node_uuid"       // char[37] — RFC 4122 UUID
#define NVS_NODE_NAME       "node_name"       // char[32] — human-readable
#define NVS_NODE_ROLE       "node_role"        // uint8_t  — enum below
#define NVS_VARIANT         "hw_variant"       // uint8_t  — 0=cam, 1=heltec

// Polarization
#define NVS_POL_MODE        "pol_mode"         // uint8_t  — 0=auto, 1=rhcp, 2=lhcp
#define NVS_POL_CURRENT     "pol_current"      // uint8_t  — last detected
#define NVS_POL_INTERVAL    "pol_interval"     // uint16_t — recheck minutes

// Network
#define NVS_MESH_SSID       "mesh_ssid"        // char[32] — default "myc3-mesh"
#define NVS_MESH_KEY        "mesh_key"         // char[64] — PSK
#define NVS_ROUTER_IP       "router_ip"        // uint32_t — RPi IP

// Power
#define NVS_SLEEP_ENABLED   "sleep_en"         // uint8_t  — 0=off, 1=light, 2=deep
#define NVS_WAKE_INTERVAL   "wake_int"         // uint16_t — seconds
#define NVS_TX_POWER        "tx_power"         // int8_t   — dBm

// Node Roles
typedef enum {
    ROLE_SENSOR     = 0,   // Passive sensor (cam captures, env data)
    ROLE_RELAY      = 1,   // Mesh relay / repeater
    ROLE_ENDPOINT   = 2,   // User-facing endpoint (interactive)
    ROLE_GATEWAY    = 3,   // Bridge to other networks
} node_role_t;
```

**JSON export** (for WebUI and router sync):

```json
{
  "node_uuid": "a1b2c3d4-e5f6-4789-abcd-ef0123456789",
  "node_name": "field-unit-07",
  "hw_variant": "cam",
  "role": "sensor",
  "polarization": {
    "mode": "auto",
    "current": "rhcp",
    "rssi_rhcp": -62,
    "rssi_lhcp": -74,
    "last_check": 1711000800
  },
  "network": {
    "mesh_ssid": "myc3-mesh",
    "router_ip": "192.168.71.1"
  },
  "power": {
    "sleep_mode": "light",
    "wake_interval_s": 60,
    "tx_power_dbm": 14,
    "battery_pct": 87
  },
  "firmware": {
    "version": "0.3.1",
    "build": "2026-03-20T18:00:00Z"
  }
}
```

---

## 5. Initial Setup Flow

### 5.1 First Boot Sequence

```
┌─────────────────────────────────────────────────────────┐
│ 1. Power on handheld                                    │
│    └─► No config in NVS → enter SETUP MODE              │
│                                                         │
│ 2. SETUP MODE                                           │
│    ├─► Variant A (CAM): Blink LED pattern (fast blue)   │
│    └─► Variant B (Heltec): OLED shows "myc3 SETUP"     │
│                                                         │
│ 3. Node starts Wi-Fi STA, scans for "myc3-mesh"        │
│    ├─► Found → Connect using default PSK                │
│    └─► Not found → Start AP "myc3-setup-XXXX"          │
│         (fallback, user connects phone/laptop)          │
│                                                         │
│ 4. Once on network, announce via mDNS:                  │
│    _myc3-setup._tcp.local  port 80                      │
│                                                         │
│ 5. RPi router detects new node via mDNS/broadcast       │
│    └─► Adds to "pending setup" list                     │
│                                                         │
│ 6. User opens WebUI:                                    │
│    http://myc3-setup-XXXX.local  (direct)               │
│    OR                                                   │
│    http://192.168.71.1/nodes/pending  (via RPi)         │
│                                                         │
│ 7. WebUI wizard runs (see §5.2)                         │
│                                                         │
│ 8. Config saved → reboot → OPERATIONAL                  │
└─────────────────────────────────────────────────────────┘
```

### 5.2 WebUI Wizard Pages

The WebUI is a single-page app embedded in firmware (~40KB gzipped). Five wizard steps:

---

**Page 1 — Welcome & Identity**
```
┌─────────────────────────────────┐
│ 🍄 myc3lium Node Setup          │
│                                 │
│ Hardware: ESP32-S3 CAM          │
│ UUID: a1b2c3d4-...             │
│ Firmware: v0.3.1               │
│                                 │
│ Node Name: [field-unit-07    ]  │
│                                 │
│              [Next →]           │
└─────────────────────────────────┘
```

---

**Page 2 — Role Selection**
```
┌─────────────────────────────────┐
│ Select Node Role                │
│                                 │
│ ◉ Sensor                       │
│   Captures data, low power      │
│                                 │
│ ○ Relay                         │
│   Forwards mesh traffic         │
│                                 │
│ ○ Endpoint                      │
│   Interactive user device       │
│                                 │
│ ○ Gateway                       │
│   Bridge to external network    │
│                                 │
│       [← Back]    [Next →]      │
└─────────────────────────────────┘
```

---

**Page 3 — Antenna & Polarization**
```
┌─────────────────────────────────┐
│ Antenna Polarization            │
│                                 │
│ Detection Mode:                 │
│ ◉ Automatic (recommended)      │
│   RSSI sweep on boot + periodic │
│ ○ Manual RHCP                   │
│ ○ Manual LHCP                   │
│                                 │
│ ┌─ Live Test ──────────────┐    │
│ │ RHCP: ████████░░ -62 dBm│    │
│ │ LHCP: █████░░░░░ -74 dBm│    │
│ │                          │    │
│ │ ✓ RHCP selected (+12 dB) │    │
│ └──────────────────────────┘    │
│                                 │
│ Re-check interval: [30] min     │
│                                 │
│       [← Back]    [Next →]      │
└─────────────────────────────────┘
```

---

**Page 4 — Power & Network**
```
┌─────────────────────────────────┐
│ Power & Network Settings        │
│                                 │
│ Sleep Mode:                     │
│ ◉ Light Sleep (fast wake)      │
│ ○ Deep Sleep (max battery)     │
│ ○ Always On                    │
│                                 │
│ Wake Interval: [60] seconds     │
│ TX Power: [14] dBm              │
│                                 │
│ Mesh Network:                   │
│ SSID: [myc3-mesh           ]    │
│ Key:  [••••••••••           ]   │
│                                 │
│       [← Back]    [Next →]      │
└─────────────────────────────────┘
```

---

**Page 5 — Review & Deploy**
```
┌─────────────────────────────────┐
│ Review Configuration            │
│                                 │
│ Name:    field-unit-07          │
│ Role:    Sensor                 │
│ Antenna: Auto (RHCP detected)  │
│ Sleep:   Light, 60s interval   │
│ TX:      14 dBm                │
│ Mesh:    myc3-mesh             │
│                                 │
│ ┌──────────────────────────┐    │
│ │ ⚠ Device will reboot     │    │
│ │   and join mesh network  │    │
│ └──────────────────────────┘    │
│                                 │
│   [← Back]    [🚀 Deploy!]     │
└─────────────────────────────────┘
```

---

## 6. RPi Flash Automation

### 6.1 Flash Script

```bash
#!/usr/bin/env bash
# myc3-flash.sh — Flash ESP32 handheld nodes from RPi4
# Usage: myc3-flash.sh <variant> [port]
#   variant: "cam" or "heltec"
#   port:    serial port (default: auto-detect)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIRMWARE_DIR="${SCRIPT_DIR}/firmware"
ESPTOOL="esptool.py"

VARIANT="${1:?Usage: myc3-flash.sh <cam|heltec> [port]}"
PORT="${2:-}"

# ── Validate variant ──
case "$VARIANT" in
    cam)
        CHIP="esp32s3"
        BAUD=921600
        BIN_DIR="${FIRMWARE_DIR}/cam"
        ;;
    heltec)
        CHIP="esp32s3"
        BAUD=921600
        BIN_DIR="${FIRMWARE_DIR}/heltec"
        ;;
    *)
        echo "❌ Unknown variant: $VARIANT (use 'cam' or 'heltec')"
        exit 1
        ;;
esac

# ── Auto-detect port ──
if [ -z "$PORT" ]; then
    PORT=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -n1)
    if [ -z "$PORT" ]; then
        echo "❌ No serial port found. Connect device and retry."
        exit 1
    fi
    echo "📡 Auto-detected port: $PORT"
fi

# ── Verify firmware files ──
for f in bootloader.bin partition-table.bin myc3_node.bin; do
    if [ ! -f "${BIN_DIR}/${f}" ]; then
        echo "❌ Missing: ${BIN_DIR}/${f}"
        echo "   Run 'make build VARIANT=${VARIANT}' first."
        exit 1
    fi
done

echo "═══════════════════════════════════════"
echo "  🍄 myc3lium Flash Tool"
echo "  Variant:  ${VARIANT}"
echo "  Port:     ${PORT}"
echo "  Chip:     ${CHIP}"
echo "═══════════════════════════════════════"
echo ""

# ── Generate unique node UUID ──
NODE_UUID=$(python3 -c "import uuid; print(uuid.uuid4())")
echo "🔑 Generated Node UUID: ${NODE_UUID}"

# ── Erase flash ──
echo "🧹 Erasing flash..."
$ESPTOOL --chip "$CHIP" --port "$PORT" --baud "$BAUD" erase_flash

# ── Flash firmware ──
echo "📦 Flashing firmware..."
$ESPTOOL --chip "$CHIP" --port "$PORT" --baud "$BAUD" \
    --before default_reset --after hard_reset \
    write_flash --flash_mode dio --flash_freq 80m --flash_size 8MB \
    0x0      "${BIN_DIR}/bootloader.bin" \
    0x8000   "${BIN_DIR}/partition-table.bin" \
    0x10000  "${BIN_DIR}/myc3_node.bin"

# ── Write initial NVS data (UUID + variant marker) ──
echo "📝 Writing initial config..."
python3 "${SCRIPT_DIR}/nvs_init.py" \
    --port "$PORT" \
    --uuid "$NODE_UUID" \
    --variant "$VARIANT"

echo ""
echo "✅ Flash complete!"
echo "   Node UUID: ${NODE_UUID}"
echo "   Power cycle the device to enter setup mode."
echo ""

# ── Register with router ──
ROUTER_IP="${MYC3_ROUTER_IP:-192.168.71.1}"
echo "📡 Pre-registering with router at ${ROUTER_IP}..."
curl -s -X POST "http://${ROUTER_IP}:8071/api/nodes/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"uuid\": \"${NODE_UUID}\",
        \"variant\": \"${VARIANT}\",
        \"firmware_version\": \"$(cat ${BIN_DIR}/version.txt)\",
        \"flashed_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
    }" && echo " ✓ Registered" || echo " ⚠ Router not reachable (will register on first connect)"
```

### 6.2 NVS Init Helper

```python
#!/usr/bin/env python3
# nvs_init.py — Write initial NVS partition with node UUID and variant

import argparse
import subprocess
import tempfile
import csv
import os

def create_nvs_csv(uuid: str, variant: str) -> str:
    """Generate NVS CSV for nvs_partition_gen.py"""
    rows = [
        ["key",          "type",      "encoding", "value"],
        ["myc3",         "namespace", "",         ""],
        ["node_uuid",    "data",      "string",   uuid],
        ["hw_variant",   "data",      "u8",       "0" if variant == "cam" else "1"],
        ["pol_mode",     "data",      "u8",       "0"],   # auto
        ["sleep_en",     "data",      "u8",       "1"],   # light sleep
        ["wake_int",     "data",      "u16",      "60"],
        ["tx_power",     "data",      "i8",       "14"],
        ["mesh_ssid",    "data",      "string",   "myc3-mesh"],
    ]
    
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--uuid", required=True)
    parser.add_argument("--variant", required=True, choices=["cam", "heltec"])
    args = parser.parse_args()

    csv_path = create_nvs_csv(args.uuid, args.variant)
    bin_path = csv_path.replace(".csv", ".bin")

    # Generate NVS binary
    subprocess.run([
        "python3", "-m", "esp_idf_nvs_partition_gen",
        "generate", csv_path, bin_path, "0x6000"
    ], check=True)

    # Flash NVS partition (at 0x9000, after partition table)
    subprocess.run([
        "esptool.py", "--chip", "esp32s3",
        "--port", args.port, "--baud", "921600",
        "write_flash", "0x9000", bin_path
    ], check=True)

    # Cleanup
    os.unlink(csv_path)
    os.unlink(bin_path)
    print(f"NVS initialized: UUID={args.uuid}, variant={args.variant}")

if __name__ == "__main__":
    main()
```

---

## 7. Backend Router Integration

### 7.1 RPi Router — Node & Polarization Manager

The RPi `myc3-router` service maintains a registry of all nodes and their polarization state:

```
RPi4 myc3-router
├── /api/nodes/register          POST  — Pre-register from flash script
├── /api/nodes/list              GET   — All known nodes + status
├── /api/nodes/{uuid}            GET   — Single node detail
├── /api/nodes/{uuid}/config     PUT   — Push config update
├── /api/nodes/pending           GET   — Nodes in setup mode
├── /api/polarization/map        GET   — Polarization state of all nodes
├── /api/polarization/diversity  POST  — Trigger diversity combining
└── /api/firmware/ota            POST  — Push OTA to specific node
```

### 7.2 Node Registry Schema

```python
# models.py — SQLite-backed node registry

@dataclass
class MeshNode:
    uuid: str                    # RFC 4122 UUID
    name: str                    # Human-readable name
    variant: str                 # "cam" or "heltec"
    role: str                    # sensor/relay/endpoint/gateway
    firmware_version: str
    
    # Polarization
    pol_mode: str                # auto/rhcp/lhcp
    pol_current: str             # rhcp/lhcp/unknown
    pol_rssi_rhcp: int           # dBm
    pol_rssi_lhcp: int           # dBm
    pol_last_check: datetime
    
    # Status
    last_seen: datetime
    battery_pct: int
    ip_address: str
    signal_rssi: int             # link RSSI to router
    
    # State
    state: str                   # pending/active/sleeping/offline
    registered_at: datetime
    flashed_at: datetime
```

### 7.3 Polarization-Aware Routing

The router tracks each node's polarization and uses this for **diversity combining** and **path optimization**:

```
┌─────────────────────────────────────────────────┐
│ Polarization Diversity Strategy                 │
│                                                 │
│ When RPi has dual-polarized antenna:            │
│                                                 │
│   Node reports RHCP ──► RPi uses RHCP port      │
│   Node reports LHCP ──► RPi uses LHCP port      │
│   Node reports UNKNOWN ──► RPi tries both,      │
│                             picks best           │
│                                                 │
│ For mesh relay paths:                           │
│                                                 │
│   A(RHCP) ──► B(relay) ──► RPi                  │
│   If B is RHCP-matched to both A and RPi,       │
│   route through B. Otherwise try C(LHCP).       │
│                                                 │
│ Combining (if RPi has dual-pol RX):             │
│   MRC (Maximal Ratio Combining):                │
│   combined_signal = w1*RHCP + w2*LHCP           │
│   where w_i = RSSI_i / (RSSI_1 + RSSI_2)       │
└─────────────────────────────────────────────────┘
```

### 7.4 Heartbeat Protocol

Nodes check in periodically via a compact binary message:

```c
// heartbeat.h — 16-byte heartbeat packet
typedef struct __attribute__((packed)) {
    uint8_t  magic;          // 0xC3 — myc3lium marker
    uint8_t  version;        // protocol version (1)
    uint8_t  uuid_short[4];  // first 4 bytes of UUID (for quick ID)
    uint8_t  state;          // operational state enum
    uint8_t  pol_current;    // 0=unknown, 1=rhcp, 2=lhcp
    int8_t   rssi_rhcp;      // last measured RHCP RSSI
    int8_t   rssi_lhcp;      // last measured LHCP RSSI
    uint8_t  battery_pct;    // 0-100
    int8_t   signal_rssi;    // link quality to router
    uint16_t uptime_min;     // minutes since boot
    uint16_t seq;            // sequence number
} myc3_heartbeat_t;          // 16 bytes total
```

---

## 8. Power Management

### 8.1 Sleep Strategy

| Mode | Wake Latency | Current Draw | Use Case |
|---|---|---|---|
| Active | — | ~120mA (radio TX) | Transmitting/receiving |
| Modem Sleep | <1ms | ~20mA | Between TX/RX windows |
| Light Sleep | ~1ms | ~0.8mA | Idle between heartbeats |
| Deep Sleep | ~200ms | ~10µA | Long-term deployment sensor |

### 8.2 Wake Sources

```c
// power_mgmt.c — Configure wake sources per role

void power_configure_wake(node_role_t role) {
    switch (role) {
        case ROLE_SENSOR:
            // Timer wake only (deep sleep capable)
            esp_sleep_enable_timer_wakeup(config.wake_interval * 1e6);
            // GPIO wake for external trigger (PIR, button)
            esp_sleep_enable_ext0_wakeup(GPIO_TRIGGER_PIN, 1);
            break;
            
        case ROLE_RELAY:
            // Light sleep only — must stay responsive
            // Wake on radio interrupt
            esp_sleep_enable_gpio_wakeup();
            gpio_wakeup_enable(GPIO_RADIO_IRQ, GPIO_INTR_LOW_LEVEL);
            break;
            
        case ROLE_ENDPOINT:
            // Light sleep, wake on button or radio
            esp_sleep_enable_gpio_wakeup();
            esp_sleep_enable_timer_wakeup(config.wake_interval * 1e6);
            break;
            
        case ROLE_GATEWAY:
            // No sleep — always active
            break;
    }
}
```

### 8.3 Battery Life Estimates (1000mAh LiPo)

| Role | Sleep Mode | Wake Interval | Est. Battery Life |
|---|---|---|---|
| Sensor | Deep | 5 min | ~30 days |
| Sensor | Deep | 1 min | ~14 days |
| Relay | Light | Always listening | ~2 days |
| Endpoint | Light | 30 sec | ~5 days |
| Gateway | None | — | ~8 hours |

---

## 9. Implementation Phases

### Phase 1 — Foundation (Weeks 1–3)

- [ ] ESP-IDF project scaffold with variant build system
- [ ] NVS config store (read/write/defaults)
- [ ] Basic Wi-Fi STA (connect to myc3-mesh)
- [ ] RPi flash script (`myc3-flash.sh` + `nvs_init.py`)
- [ ] Heartbeat packet (timer-based, JSON over HTTP fallback)
- [ ] RPi node registry (SQLite + REST API skeleton)

**Milestone:** Flash a device, have it join myc3-mesh and appear in registry.

### Phase 2 — Polarization (Weeks 4–5)

- [ ] RF switch GPIO driver (antenna_switch module)
- [ ] RSSI reading abstraction (HaLow AT cmd / SX1262 register)
- [ ] Polarization sweep algorithm
- [ ] Periodic re-detection task
- [ ] Polarization field in heartbeat
- [ ] RPi polarization map endpoint

**Milestone:** Node auto-detects RHCP vs LHCP on boot, reports to router.

### Phase 3 — WebUI & Setup (Weeks 6–8)

- [ ] Embedded HTTP server (esp_http_server)
- [ ] Captive portal DNS for setup mode
- [ ] WebUI wizard (5 pages, embedded HTML/JS)
- [ ] Live polarization test (WebSocket RSSI stream)
- [ ] mDNS announcement for discovery
- [ ] RPi "pending nodes" dashboard page

**Milestone:** End-to-end setup: flash → power on → WebUI config → operational.

### Phase 4 — Radio Integration (Weeks 9–12)

- [ ] **Variant A:** HT-HC01P driver (AT command set, S1G association)
- [ ] **Variant A:** HaLow mesh join/management
- [ ] **Variant B:** SX1262 LoRa driver (SPI, interrupt-based RX)
- [ ] **Variant B:** LoRa mesh protocol (time-slotted or ALOHA)
- [ ] **Variant B:** OLED UI screens (status, polarization, battery)
- [ ] Cross-variant mesh interop via RPi bridge

**Milestone:** Both variants operational on their respective radios, meshing through RPi.

### Phase 5 — Power & Polish (Weeks 13–15)

- [ ] Light/deep sleep implementation per role
- [ ] Wake source configuration
- [ ] Battery monitoring (ADC + fuel gauge if available)
- [ ] OTA update mechanism (RPi pushes firmware)
- [ ] Polarization diversity combining on RPi (if dual-pol antenna)
- [ ] Stress testing & range validation

**Milestone:** Field-deployable nodes with multi-day battery life.

### Phase 6 — Hardening (Weeks 16+)

- [ ] Encryption (TLS for WebUI, encrypted heartbeats)
- [ ] Authentication (PSK rotation, node certificates)
- [ ] Watchdog & crash recovery
- [ ] Logging & diagnostics (flash-backed ring buffer)
- [ ] Enclosure design integration
- [ ] Field deployment documentation

---

## 10. Open Questions & Decisions Needed

1. **Antenna hardware:** Dual-feed patch vs. switchable helical? Patch is flatter (better for handheld form factor), helix has better axial ratio.

2. **HT-HC01P RSSI access:** Need to confirm the AT command set supports per-packet RSSI readout. If not, polarization detection on Variant A may need a different approach (e.g., packet error rate comparison).

3. **LoRa mesh protocol (Variant B):** Use existing protocol (Meshtastic-compatible?) or custom? Custom gives polarization-awareness but fragments ecosystem.

4. **RPi dual-polarization:** Does the RPi HaLow setup support dual-pol RX? If single-pol only, diversity combining is node-side only (select best pol toward RPi).

5. **Cross-variant bridging:** When HaLow (Variant A) and LoRa (Variant B) nodes coexist, the RPi must bridge between protocols. Define packet format translation layer.

6. **Camera integration (Variant A):** Is the ESP32-S3 CAM camera used for anything in the mesh (image relay, QR code scanning for setup)? Or is it a future capability?

---

*End of design document.*

## 11. Design Decisions (2026-03-20)

**Following questions resolved:**

### 1. RF Switch Selection
**Decision:** SKY13351-374LF SPDT RF switch
- **Rationale:** Proven performance at sub-GHz frequencies, low insertion loss (~0.5dB at 900MHz), excellent isolation (>30dB), widely available from Skyworks
- **Alternative considered:** PE42441 (lower cost) - rejected due to higher insertion loss
- **Implementation:** Single GPIO toggles between RHCP/LHCP antenna ports

### 2. RSSI Sampling & Margin
**Decision:** 10 samples per polarization, 3dB decision margin
- **Rationale:** 
  - 10 samples balances detection speed (~2 seconds) with statistical confidence
  - 3dB margin provides clear polarization preference while avoiding excessive switching
  - Field tunable: reduce to 2dB if switching too slow, increase samples to 15 if high noise floor
- **Re-check intervals:** Every 30 minutes during operation + immediate sweep on >10dB signal drop

### 3. WebUI Hosting Strategy
**Decision:** Hybrid approach
- **Setup mode (initial):** ESP32 serves WebUI locally
  - Works in AP mode when not connected to myc3-mesh
  - Lightweight 5-page wizard (~50KB total)
  - Served from SPIFFS partition
- **Post-setup (operational):** RPi serves WebUI
  - Full-featured node management dashboard
  - Doesn't drain ESP32 battery
  - ESP32 announces itself via mDNS for discovery
- **Fallback:** ESP32 serves minimal status page if can't reach RPi
- **Rationale:** Maximizes setup reliability (works offline) while minimizing power consumption in field

### 4. UUID Generation
**Decision:** ESP32 generates UUID on first boot, derives from MAC address
- **Method:** `UUID = SHA256(MAC || "myc3-node" || chipID)[0:16]` - deterministic, collision-resistant
- **Storage:** Written to NVS (non-volatile storage) on first boot, immutable thereafter
- **Registration:** ESP32 self-registers with RPi router on first connection
- **Rationale:** 
  - Works offline (no RPi dependency for identity)
  - Deterministic UUIDs allow factory pre-registration if needed
  - 16-byte UUID matches compact heartbeat packet design

### 5. OTA Update Strategy
**Decision:** Hybrid pull/push model
- **Default (battery-friendly pull):**
  - ESP32 checks for updates every 6-12 hours (configurable per role)
  - Query: HTTP GET `http://rpi-node.local/api/ota/check?uuid=<node-uuid>&version=<current>`
  - Response: `{ "update_available": true, "url": "/ota/firmware-v1.2.bin", "size": 524288, "sha256": "..." }`
- **Urgent updates (push):**
  - RPi publishes retained MQTT message: `myc3/ota/push/<uuid>` with firmware URL
  - Deep sleep nodes check on wake cycles
  - Relay nodes wake immediately on MQTT event
- **Fallback:** Broadcast UDP wake packet (255.255.255.255:8883) with magic sequence for instant wake
- **Rationale:** Pull minimizes battery drain, push allows critical security updates

### 6. Power Profile Strategy
**Decision:** Role-based profiles with user override
- **Sensor nodes (default):**
  - Deep sleep with 30-60 min wake intervals
  - Wake → measure → transmit → sleep (10-30 sec active time)
  - Expected battery life: ~30 days on 1000mAh
- **Relay nodes (always-listening):**
  - Light sleep between packets (100ms wake latency)
  - CPU at 80MHz, radio RX always on
  - Expected battery life: ~2 days on 1000mAh
- **Gateway/powered nodes:**
  - No sleep, full performance (160MHz CPU)
  - Assumes external power or large battery (>5000mAh)
- **User override:** WebUI allows manual profile selection ("Max Battery" / "Balanced" / "Max Performance")
- **Rationale:** Different use cases demand different trade-offs; role detection with manual override covers 90% of scenarios

---

**Implementation impact:** These decisions finalize the firmware architecture. Ready to proceed to Phase 1 (scaffold + build system).

