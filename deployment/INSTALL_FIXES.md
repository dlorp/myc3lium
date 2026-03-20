# Installation Script Fixes

**Critical issues found in deployment scripts:**

## setup-pi4.sh

**Problems:**
1. Not idempotent - fails if run twice
2. Hardcoded `/boot/config.txt` - wrong path on newer Pi OS
3. No venv - pollutes system Python
4. Missing error handling

**Fixed version:** `scripts/setup-pi4-fixed.sh`

**Key improvements:**
- Idempotent - checks before creating user/dirs
- Finds boot config automatically
- Uses venv for Python packages
- Continues on package failures
- Logs everything to /tmp/myc3lium-install.log

## setup-lora.sh

**Problems:**
1. Assumes HAT is connected - no detection
2. Installs wrong libraries (Adafruit instead of Reticulum native)
3. No integration with Reticulum config
4. Hardcoded pins - doesn't detect actual HAT

**Should do instead:**
1. Detect if SX1262 HAT is actually connected (SPI probe)
2. Configure Reticulum to use the HAT (not raw libraries)
3. Verify HAT responds before declaring success

## setup-halow.sh

**Expected problems:**
1. HaLow module (HT-HC01P) needs custom driver
2. USB-to-mPCIe adapter compatibility issues
3. Firmware might need flashing
4. 902-928 MHz config might not be default

## setup-batman.sh

**Expected problems:**
1. BATMAN-adv version mismatches
2. Interface naming (wlan0 vs wlan1 vs predictable names)
3. No validation that mesh actually forms

## Recommended Approach

**Instead of running setup-all.sh blindly:**

1. **Run setup-pi4-fixed.sh first**
   ```bash
   sudo ./scripts/setup-pi4-fixed.sh
   reboot
   ```

2. **Test LoRa manually:**
   ```bash
   # Check SPI
   ls -l /dev/spidev*
   
   # Check if HAT is detected
   dmesg | grep -i spi
   
   # Test with Reticulum
   python3 -c "import RNS; RNS.vendor.platformutils.get_platform()"
   ```

3. **Configure Reticulum for LoRa:**
   - Edit `~/.reticulum/config`
   - Add SX126x interface manually
   - Test with `rnstatus` command

4. **Test HaLow separately:**
   - Plug in USB adapter
   - Check if recognized: `lsusb`, `dmesg`
   - May need kernel driver compilation

5. **BATMAN last:**
   - Ensure WiFi interface is free
   - Start small (2 nodes only)
   - Verify with `batctl o` (originators)

## Quick Fix PR

Create these improved scripts:
- ✅ setup-pi4-fixed.sh (done)
- ⏳ setup-lora-improved.sh (need to write)
- ⏳ setup-halow-improved.sh (need to write)  
- ⏳ setup-batman-improved.sh (need to write)
- ⏳ setup-all-fixed.sh (orchestrator with better error handling)

## Testing Plan

**Phase 1: Base**
```bash
sudo ./scripts/setup-pi4-fixed.sh
reboot
# Verify: user exists, dirs created, venv works
```

**Phase 2: LoRa**
```bash
# Manual Reticulum config
# Test with rnstatus
```

**Phase 3: HaLow**
```bash
# Manual driver install
# Test with iw/iwconfig
```

**Phase 4: BATMAN**
```bash
# Start mesh on working interface
# Verify with batctl
```

**Phase 5: Integration**
```bash
# Start backend bridge
# Access WebUI
```
