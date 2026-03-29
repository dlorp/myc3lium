#!/bin/bash
# MYC3LIUM LoRa Setup - Waveshare SX1262 HAT
# Configures SX1262 LoRa module on Raspberry Pi 4

set -e

echo "📡 MYC3LIUM LoRa Setup - Waveshare SX1262"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# Pin configuration for Waveshare SX1262 HAT
# Based on standard Waveshare pinout:
# RESET: GPIO 18 (Pin 12)
# BUSY: GPIO 23 (Pin 16)
# DIO1: GPIO 24 (Pin 18)
# NSS: CE0 (Pin 24, SPI0)
# MOSI: GPIO 10 (Pin 19, SPI0_MOSI)
# MISO: GPIO 9 (Pin 21, SPI0_MISO)
# SCK: GPIO 11 (Pin 23, SPI0_SCLK)

log_info "Configuring SPI interface..."

# Ensure SPI is enabled
if ! lsmod | grep -q spi_bcm2835; then
    log_warn "SPI module not loaded, attempting to load..."
    modprobe spi_bcm2835
fi

# Check if SPI device exists
if [ ! -e /dev/spidev0.0 ]; then
    log_error "SPI device /dev/spidev0.0 not found!"
    log_error "Make sure SPI is enabled in /boot/config.txt and reboot"
    exit 1
fi

log_info "SPI device found: /dev/spidev0.0"

# Set SPI permissions
chmod 666 /dev/spidev0.0
chown myc3lium:spi /dev/spidev0.0

# Add udev rule for persistent permissions
cat > /etc/udev/rules.d/99-spi.rules <<EOF
# SPI devices for MYC3LIUM
SUBSYSTEM=="spidev", KERNEL=="spidev0.0", MODE="0666", GROUP="spi"
EOF

udevadm control --reload-rules
udevadm trigger

# Install SX126x Python library
log_info "Installing SX126x Python library..."
pip3 install --upgrade setuptools wheel

# Clone and install sx126x library (if not using Reticulum's built-in support)
cd /tmp
if [ -d "sx126x-python" ]; then
    rm -rf sx126x-python
fi

# Note: Reticulum has native SX126x support via RNode firmware
# For raw access, we can use CircuitPython libraries
pip3 install adafruit-circuitpython-rfm9x adafruit-circuitpython-busdevice

# Configure GPIO pins
log_info "Configuring GPIO pins..."

# Export GPIO pins if needed (usually handled by gpiozero/RPi.GPIO)
cat > /opt/myc3lium/lora-pins.conf <<EOF
# Waveshare SX1262 HAT Pin Configuration
SPI_BUS=0
SPI_DEVICE=0
RESET_PIN=18
BUSY_PIN=23
DIO1_PIN=24
NSS_PIN=8
FREQUENCY=915000000
BANDWIDTH=125000
SPREADING_FACTOR=7
TX_POWER=22
EOF

# Create Python test script
log_info "Creating LoRa test script..."
cat > /opt/myc3lium/test-lora.py <<'PYEOF'
#!/usr/bin/env python3
"""
MYC3LIUM LoRa Test Script
Tests Waveshare SX1262 HAT connectivity
"""

import time
import spidev
from gpiozero import LED, Button

# Pin configuration
RESET_PIN = 18
BUSY_PIN = 23
DIO1_PIN = 24

# SPI configuration
SPI_BUS = 0
SPI_DEVICE = 0

def test_spi():
    """Test SPI connection"""
    print("🔌 Testing SPI connection...")
    try:
        spi = spidev.SpiDev()
        spi.open(SPI_BUS, SPI_DEVICE)
        spi.max_speed_hz = 500000
        spi.mode = 0
        
        # Try to read a register (GetStatus command: 0xC0)
        response = spi.xfer2([0xC0, 0x00])
        print(f"✓ SPI response: {[hex(b) for b in response]}")
        
        spi.close()
        return True
    except Exception as e:
        print(f"✗ SPI test failed: {e}")
        return False

def test_gpio():
    """Test GPIO pins"""
    print("🔌 Testing GPIO pins...")
    try:
        # Test RESET pin (output)
        reset = LED(RESET_PIN)
        reset.on()
        time.sleep(0.1)
        reset.off()
        print(f"✓ RESET pin (GPIO {RESET_PIN}) working")
        
        # Test BUSY pin (input)
        busy = Button(BUSY_PIN)
        print(f"✓ BUSY pin (GPIO {BUSY_PIN}) readable: {busy.is_pressed}")
        
        # Test DIO1 pin (input)
        dio1 = Button(DIO1_PIN)
        print(f"✓ DIO1 pin (GPIO {DIO1_PIN}) readable: {dio1.is_pressed}")
        
        return True
    except Exception as e:
        print(f"✗ GPIO test failed: {e}")
        return False

def main():
    print("📡 MYC3LIUM LoRa Hardware Test")
    print("=" * 40)
    print()
    
    spi_ok = test_spi()
    gpio_ok = test_gpio()
    
    print()
    print("=" * 40)
    if spi_ok and gpio_ok:
        print("✅ LoRa HAT hardware test PASSED")
        print()
        print("Next steps:")
        print("  1. Configure Reticulum with LoRa interface")
        print("  2. Start Reticulum daemon: sudo systemctl start reticulum")
        return 0
    else:
        print("❌ LoRa HAT hardware test FAILED")
        print()
        print("Troubleshooting:")
        print("  - Check HAT is properly seated on GPIO pins")
        print("  - Verify SPI is enabled: ls /dev/spidev*")
        print("  - Check /boot/config.txt has: dtparam=spi=on")
        print("  - Reboot and try again")
        return 1

if __name__ == "__main__":
    exit(main())
PYEOF

chmod +x /opt/myc3lium/test-lora.py
chown myc3lium:myc3lium /opt/myc3lium/test-lora.py

# Configure Reticulum to use LoRa (will be done in reticulum.conf)
log_info "LoRa configuration template ready for Reticulum"

# Create systemd service monitor for LoRa
cat > /opt/myc3lium/lora-monitor.sh <<'EOF'
#!/bin/bash
# Monitor LoRa interface health
while true; do
    if ! pgrep -f "rnsd" > /dev/null; then
        echo "$(date): Reticulum not running, restarting..."
        systemctl restart reticulum.service
    fi
    sleep 60
done
EOF

chmod +x /opt/myc3lium/lora-monitor.sh

# Run hardware test
log_info "Running LoRa hardware test..."
sudo -u myc3lium python3 /opt/myc3lium/test-lora.py || log_warn "Hardware test failed - check connections"

log_info "✅ LoRa setup complete!"
log_info ""
log_info "Configuration saved to: /opt/myc3lium/lora-pins.conf"
log_info "Test script: /opt/myc3lium/test-lora.py"
log_info ""
log_info "To test LoRa manually:"
log_info "  sudo -u myc3lium python3 /opt/myc3lium/test-lora.py"
