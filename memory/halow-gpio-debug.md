# HaLow GPIO Configuration Debug Log
## HT-HC33 v1.0 Pin Configuration Research

### GPIO Variants from Heltec SDK

Source: `/Users/lorp/esp/ESP_HaLow/ESP_HaLow/libraries/wifi-halow/src/halow_config.h`

**Variant #1 (Lines 10-17):**
```c
#define CONFIG_MM_RESET_N  2 
#define CONFIG_MM_WAKE     1
#define CONFIG_MM_BUSY     46
#define CONFIG_MM_SPI_SCK  39  //clk
#define CONFIG_MM_SPI_MOSI 40  //cmd
#define CONFIG_MM_SPI_MISO 38  //d0
#define CONFIG_MM_SPI_CS   41  //d3
#define CONFIG_MM_SPI_IRQ  21  //d1
```

**Variant #2 (Lines 20-27) - ACTIVE in Heltec SDK:**
```c
#define CONFIG_MM_RESET_N 9 
#define CONFIG_MM_WAKE 7
#define CONFIG_MM_BUSY 8
#define CONFIG_MM_SPI_SCK 4
#define CONFIG_MM_SPI_MOSI 3
#define CONFIG_MM_SPI_MISO 5
#define CONFIG_MM_SPI_CS 2
#define CONFIG_MM_SPI_IRQ 6
```

**Variant #3 (Lines 30-37):**
```c
#define CONFIG_MM_RESET_N 8 
#define CONFIG_MM_WAKE 9
#define CONFIG_MM_BUSY 7
#define CONFIG_MM_SPI_SCK 4
#define CONFIG_MM_SPI_MOSI 3
#define CONFIG_MM_SPI_MISO 5
#define CONFIG_MM_SPI_CS 2
#define CONFIG_MM_SPI_IRQ 6
```

### Test Results

#### Attempt 1: MorseMicro Defaults (FAILED)
- **Config:** RESET=3, WAKE=8, BUSY=9, SCK=12, MOSI=11, MISO=13, CS=10, IRQ=5
- **Result:** Chip ID 0x0000, "104 Morse Chip Reset Unsuccessful"

#### Attempt 2: Variant #2 (FAILED)
- **Config:** RESET=9, WAKE=7, BUSY=8, SCK=4, MOSI=3, MISO=5, CS=2, IRQ=6
- **Build:** `young-wharf` session, completed 2026-03-22 02:59 AKDT
- **Flash:** 2026-03-22 03:03 AKDT
- **Result:** Chip ID 0x0000, "104 Morse Chip Reset Unsuccessful"

#### Attempt 3: Variant #1 (PENDING)
- **Config:** RESET=2, WAKE=1, BUSY=46, SCK=39, MOSI=40, MISO=38, CS=41, IRQ=21
- **Status:** Currently configured in sdkconfig, ready to build
- **Date:** 2026-03-22 03:16 AKDT

### Current sdkconfig Status

From `/Users/lorp/esp/mm-iot-esp32-morsemicro/examples/ap_mode/sdkconfig`:
```
CONFIG_MM_RESET_N=2
CONFIG_MM_WAKE=1
CONFIG_MM_BUSY=46
CONFIG_MM_SPI_SCK=39
CONFIG_MM_SPI_MOSI=40
CONFIG_MM_SPI_MISO=38
CONFIG_MM_SPI_CS=41
CONFIG_MM_SPI_IRQ=21
```

This matches **Variant #1** - ready to build and test.

### Analysis

**Variant #2 Comments:**
The Heltec SDK has Variant #2 as the active (uncommented) configuration. This suggests it's the "official" HC33 v1.0 pinout. However, it failed in testing.

**Pin Assignment Patterns:**
- Variants #2 and #3 share the same SPI pins but swap RESET/WAKE/BUSY
- Variant #1 uses completely different GPIO assignments (high-numbered pins)

**SPI Pin Grouping:**
- Variant #2/3: SPI uses GPIO 2-6 (consecutive, low-numbered)
- Variant #1: SPI uses GPIO 38-41 (consecutive, high-numbered)

**Hypothesis:**
Variant #1 may use the ESP32-S3's hardware SPI peripheral directly (HSPI/VSPI), while Variant #2/3 use software SPI or GPIO bit-banging. This could affect reliability.

### Next Steps

1. Build with Variant #1 (current sdkconfig)
2. Flash to ESP32-S3
3. Monitor serial output for MM6108 chip ID
4. If still fails, try Variant #3 (last option)
5. Document all results
