# MYC3LIUM Hardware Bill of Materials (BOM)

**Complete parts list for building a SPORE node**

---

## Core Components

### 1. Raspberry Pi 4 (4GB RAM)
**Function:** Main compute unit, runs backend + WebUI

**Specs:**
- 1.5GHz quad-core ARM Cortex-A72
- 4GB LPDDR4 RAM
- Dual-band WiFi (2.4/5GHz) - used for mesh
- Bluetooth 5.0
- 40-pin GPIO header

**Where to Buy:**
- Official retailers: raspberrypi.com/products
- Amazon, Adafruit, SparkFun
- **Estimated Cost:** $55-75

**Notes:**
- Pi 5 compatible but not tested yet
- 4GB RAM recommended (2GB may work for basic operation)

---

## Radio Hardware

### 2. Waveshare SX1262 LoRaWAN/GNSS HAT
**Function:** Long-range LoRa mesh (2-10km) + GPS positioning

**Exact Part:** Waveshare SX1262 LoRaWAN Node Module Expansion Board
**Part Number:** Compatible with Raspberry Pi 5/4B/3B/Zero/Zero W/Zero 2W/Pico
**Purchased:** Mar 16, 2026 - **$35.99**

**Specs:**
- SX1262 LoRa transceiver
- 868/915 MHz bands (configurable)
- Built-in GNSS receiver (GPS)
- Magnetic CB antenna included
- SPI interface to Pi

**Where to Buy:**
- Amazon (Waveshare official)
- waveshare.com

**Driver/Software:**
- Reticulum RNode interface support
- Python libraries: `pyLoRa`, `RNS` (Reticulum)

---

### 3. Heltec WiFi HaLow Module (HT-HC01P)
**Function:** Medium-range mesh (1km) with high bandwidth (32.5Mbps)

**Exact Part:** Heltec WiFi HaLow Module Mini PCIe with Debug Board
**Model:** HT-HC01P
**Purchased:** Mar 16, 2026 - **$25.99**

**Specs:**
- IEEE 802.11ah (HaLow)
- 902-928 MHz frequency band
- 1km range (line of sight)
- 32.5 Mbps data rate
- Mini PCIe form factor

**Where to Buy:**
- Amazon (Heltec Automation official)
- heltec.cn

**Important Notes:**
- Requires USB adapter (see #4) - Pi doesn't have native Mini PCIe slot
- May need vendor driver installation (not in mainline Linux kernel)

---

### 4. Mini PCIe to USB Adapter
**Function:** Connect HaLow module to Raspberry Pi via USB

**Exact Part:** Mustpoint Mini PCIe WWAN Card to USB Adapter
**Purchased:** Mar 16, 2026 - **$13.99** (7% off)

**Specs:**
- Mini PCI Express to USB 2.0/3.0
- Supports 30mm and 50mm cards
- SIM slot (not used for HaLow)
- Plug-and-play on Linux

**Where to Buy:**
- Amazon (Mustpoint brand or equivalents)
- Any "Mini PCIe to USB adapter" works

**Alternatives:**
- Generic Mini PCIe to USB adapters (~$10-15)
- M.2 to USB adapters (if you have M.2 version of HaLow card)

---

## Camera Node (Optional)

### 5. Heltec ESP32-S3 CAM Board
**Function:** Remote HaLow camera node (streams to main Pi)

**Exact Part:** Heltec ESP32-S3 CAM Development Board with Wi-Fi HaLow
**Model:** ESP32-S3 with OV3660 Camera
**Purchased:** Mar 16, 2026 - **$34.90**

**Specs:**
- ESP32-S3 dual-core processor
- Wi-Fi HaLow (802.11ah) built-in
- OV3660 camera sensor
- 2.4GHz WiFi + BLE 5.0
- 1-2km range, 32 Mbps
- 8MB PSRAM, 16MB Flash

**Where to Buy:**
- Amazon (Heltec Automation)
- heltec.cn

**Use Cases:**
- Remote surveillance camera
- Wildlife/outdoor monitoring
- Streams RTMP to main Pi over HaLow mesh

---

## Power System

### 6. 18650 Battery UPS HAT (3-cell)
**Function:** Portable power, uninterruptible operation

**Specs (typical):**
- 3× 18650 lithium-ion cells
- 5V/3A output via GPIO header
- USB-C charging port
- Power indicators
- Automatic switchover (UPS mode)
- 6-12 hour runtime (depends on load)

**Recommended Models:**
- **Waveshare UPS HAT (C)** - 3× 18650, intelligent power management
- **PiSugar 3 Plus** - 3× 18650, app control, RTC

**Where to Buy:**
- Amazon, Adafruit, Waveshare
- **Estimated Cost:** $25-45

**Battery Notes:**
- 18650 cells NOT included (buy separately)
- Use protected cells (safer)
- Recommended capacity: 3000mAh+ per cell
- Total capacity: ~11.1V 3000mAh = 33Wh

---

## Additional Components

### 7. Touchscreen (Optional)
**Function:** Field operation display

**Recommended:**
- 7" 1024×600 HDMI touchscreen
- **Cost:** $40-60

**Alternatives:**
- SSH over WiFi (no screen needed)
- VNC remote desktop

---

### 8. Enclosure
**Function:** Weather protection, tactical portability

**Options:**
- **Pelican 1120 Case** - Waterproof, foam-lined (~$30)
- **Tactical admin pouch** - MOLLE-compatible (~$20)
- **3D printed custom case** - DIY, form-fitted

**Requirements:**
- Antenna pass-throughs (LoRa, HaLow)
- Ventilation (Pi gets warm)
- Access to USB/Ethernet ports

---

## Complete BOM Summary

| Component | Cost | Required |
|-----------|------|----------|
| Raspberry Pi 4 (4GB) | $55-75 | ✅ Yes |
| Waveshare SX1262 LoRa/GPS HAT | $36 | ✅ Yes |
| Heltec HaLow Module (HT-HC01P) | $26 | ✅ Yes |
| Mini PCIe to USB Adapter | $14 | ✅ Yes |
| 18650 UPS HAT (3-cell) | $25-45 | ✅ Yes |
| 18650 Batteries (3×) | $15-30 | ✅ Yes |
| MicroSD Card (32GB+) | $10 | ✅ Yes |
| Heltec ESP32-S3 CAM | $35 | ⚙️ Optional |
| Touchscreen (7") | $40-60 | ⚙️ Optional |
| Enclosure (Pelican/custom) | $20-50 | ⚙️ Optional |

**Total Cost (Basic):** ~$181-226  
**Total Cost (Full):** ~$286-401

---

## Assembly Notes

### Physical Stacking Order

1. **Bottom:** Raspberry Pi 4
2. **On GPIO:** LoRa HAT (stacks directly on 40-pin header)
3. **USB Port 1:** HaLow module (via Mini PCIe adapter)
4. **USB Port 2:** Reserved for storage/peripherals
5. **Below Pi:** UPS HAT battery compartment (or side-mounted)

**Antenna Placement:**
- LoRa: External magnetic CB antenna (included with HAT)
- HaLow: Module has onboard antenna (consider external for better range)
- WiFi: Pi's built-in antenna (internal)

---

## Hardware Compatibility Notes

### Confirmed Working
- ✅ Raspberry Pi 4 (4GB) - Tested
- ✅ Waveshare SX1262 HAT - Reticulum RNode support
- ✅ Heltec HaLow HT-HC01P - IEEE 802.11ah standard

### May Need Drivers
- ⚠️ HaLow module - Vendor driver may be required (not in mainline kernel)
- ⚠️ ESP32-S3 CAM - Arduino/ESP-IDF firmware (not Pi-based)

### Not Tested Yet
- ❓ Raspberry Pi 5 - Should work but not verified
- ❓ Pi Zero 2W - May work for lightweight deployments (lower performance)

---

## Regulatory Compliance

**⚠️ CRITICAL: Radio Frequency Regulations**

### United States (FCC)
- **915 MHz ISM Band** (LoRa + HaLow): FCC Part 15.247
  - **Max Power:** 1W EIRP (30 dBm)
  - **Antenna Gain:** Must be factored into EIRP calculation
  - **License:** Not required for Part 15 operation

**Compliance Steps:**
1. Check your LoRa TX power setting:
   ```bash
   grep "txpower" ~/.reticulum/config
   ```
2. Default in setup scripts: 17 dBm (50mW) - **compliant**
3. **DO NOT** exceed 30 dBm EIRP total (TX power + antenna gain)

### International
- **Europe:** ETSI EN 300 220 (868 MHz), max 25mW
- **Japan:** ARIB STD-T108 (920 MHz)
- **Australia:** LIPD Class License (915-928 MHz)

**Check local regulations before deployment!**

**Violation Penalties:**
- FCC fines: Up to **$10,000 per day** per violation
- Equipment seizure
- Criminal penalties for intentional interference

---

## Power Consumption Estimates

### Typical Load (3× 18650 @ 3000mAh = 33Wh)

| Mode | Power Draw | Runtime |
|------|------------|---------|
| **Idle** (Pi + radios listening) | ~3W | 11 hours |
| **Active Mesh** (data relay) | ~5W | 6.6 hours |
| **Max Load** (TX all radios + CPU) | ~8W | 4 hours |
| **Sleep Mode** (future) | ~0.5W | 66 hours |

**Battery Life Optimization:**
- Disable HDMI if no screen: `tvservice -o` (saves ~200mA)
- Lower LoRa TX power for short-range: 10-14 dBm
- Use HaLow only when needed (high power consumption)
- Implement sleep cycles (future enhancement)

---

## Purchase Checklist

**Before ordering, verify:**
- [ ] Pi 4 available (chip shortage may affect stock)
- [ ] LoRa frequency matches your region (915 MHz US, 868 MHz EU)
- [ ] HaLow module includes debug board (easier development)
- [ ] UPS HAT fits your case dimensions
- [ ] 18650 batteries are **protected** cells (safer)
- [ ] MicroSD card is **high endurance** (A1/A2 rated for Pi)

**Recommended Retailers:**
- **Pi Official:** raspberrypi.com, Adafruit, SparkFun
- **Radio Modules:** Amazon (Heltec/Waveshare official stores)
- **Batteries:** reputable brands only (Samsung, LG, Panasonic cells)

---

## Next Steps

After receiving hardware:
1. **Assemble** - Stack HATs, connect HaLow USB adapter
2. **Flash Pi OS** - Use Raspberry Pi Imager
3. **Run Setup Scripts** - `sudo ./deployment/setup-all-fixed.sh`
4. **Test Components** - Use provided test scripts
5. **Configure Reticulum** - Set callsign, TX power, frequency

**See:** `deployment/HARDWARE_SETUP_GUIDE.md` for step-by-step assembly instructions.
