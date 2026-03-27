# ESP32-S3 CAM HaLow Firmware Setup

Complete step-by-step guide for flashing HaLow firmware to ESP32-S3 CAM.

## Part 1: Install ESP-IDF (on Mac)

```bash
# Create workspace
mkdir -p /Users/lorp/esp
cd /Users/lorp/esp

# Download ESP-IDF v5.2.2
git clone -b v5.2.2 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf

# Install tools
./install.sh esp32s3

# Activate environment (run this in every new terminal)
source export.sh
```

## Part 2: Download MorseMicro ESP32 SDK

```bash
cd /Users/lorp/esp
git clone https://github.com/MorseMicro/mm-iot-esp32.git
cd mm-iot-esp32

# Set environment variable
export MMIOT_ROOT=/Users/lorp/esp/mm-iot-esp32
```

## Part 3: Build USB Bridge Firmware

We'll use the STA Connect example modified for USB RNDIS networking.

```bash
cd /Users/lorp/esp/mm-iot-esp32/examples/sta_connect
idf.py set-target esp32s3
```

## Part 4: Configure Hardware Pins

The ESP32-S3 CAM connects to HT-HC01P via SPI. Run menuconfig:

```bash
idf.py menuconfig
```

**Navigation in menuconfig:**
- Use arrow keys to move
- Enter to select
- Space to toggle
- S to save, Q to quit

**Settings to configure:**

1. Go to: Component config → Morse Micro Shim Configuration

2. Set SPI pins (ESP32-S3 CAM to HT-HC01P):
   - SPI MOSI GPIO: 10
   - SPI MISO GPIO: 9
   - SPI CLK GPIO: 11
   - SPI CS GPIO: 8
   - IRQ GPIO: 21
   - RESET GPIO: 3
   - WAKE GPIO: 46
   - BUSY GPIO: 7

3. Set firmware files:
   - BCF File: bcf_mf15457.mbin
   - FW File: mm6108-rl.mbin
   - Chip Type: MM6108

4. Go to: Component config → USB CDC
   - Enable USB CDC (for serial communication)

5. Save and exit (S, then Q)

## Part 5: Build and Flash

```bash
# Build firmware
idf.py build

# Connect ESP32 via USB-C cable
# Find device (should be /dev/cu.usbmodem* or /dev/cu.usbserial*)
ls /dev/cu.usb*

# Flash (replace XXXXX with your device)
idf.py -p /dev/cu.usbmodemXXXXX flash

# Monitor output
idf.py -p /dev/cu.usbmodemXXXXX monitor
```

## Part 6: Verify HaLow Connection

After flashing, you should see:

```
Morse firmware version ...
Morse chip ID 0x206
STA state: CONNECTING
Link went Up
STA state: CONNECTED
```

If you see "PASS" messages, the HaLow module is working!

## Part 7: Configure for USB RNDIS (Network Bridge)

We need to modify the firmware to present as USB network device.

Edit file: `examples/sta_connect/main/src/sta_connect.c`

Add at top:
```c
#include "tinyusb.h"
#include "tusb_net.h"
```

This will be continued after basic connection works.

## Troubleshooting

**Build errors:**
- Make sure ESP-IDF is activated: `source /Users/lorp/esp/esp-idf/export.sh`
- Verify MMIOT_ROOT: `echo $MMIOT_ROOT`

**Flash errors:**
- Hold BOOT button on ESP32 while flashing
- Check USB cable supports data (not charge-only)

**No HaLow connection:**
- Verify HT-HC01P is fully inserted in adapter
- Check SPI pin configuration matches physical wiring
- Ensure BCF file matches your module version

## Next Steps

Once basic HaLow connection works:
1. Configure USB RNDIS networking
2. Set up IP forwarding between HaLow and USB
3. Connect to Raspberry Pi
4. Add to myc3lium as network interface
