#!/bin/bash
# Build test script for Raspberry Pi
# Run this on the target hardware

set -e

echo "=== LoRa TAP Bridge Build Test ==="
echo

# Check dependencies
echo "Checking dependencies..."
if ! dpkg -l | grep -q libgpiod-dev; then
    echo "❌ libgpiod-dev not installed"
    echo "Install with: sudo apt install libgpiod-dev"
    exit 1
fi
echo "✓ libgpiod-dev installed"

if ! dpkg -l | grep -q build-essential; then
    echo "❌ build-essential not installed"
    echo "Install with: sudo apt install build-essential"
    exit 1
fi
echo "✓ build-essential installed"

# Check SPI device
if [ ! -e /dev/spidev0.0 ]; then
    echo "❌ /dev/spidev0.0 not found"
    echo "Enable SPI with: sudo raspi-config → Interface Options → SPI"
    exit 1
fi
echo "✓ SPI device found"

# Check TUN/TAP
if [ ! -e /dev/net/tun ]; then
    echo "❌ /dev/net/tun not found"
    echo "Load module with: sudo modprobe tun"
    exit 1
fi
echo "✓ TUN/TAP device found"

# Check GPIO chip
if [ ! -e /dev/gpiochip0 ]; then
    echo "❌ /dev/gpiochip0 not found"
    echo "GPIO subsystem not available"
    exit 1
fi
echo "✓ GPIO chip found"

echo
echo "Building..."
make clean
make

echo
echo "Testing binary..."
if [ ! -f lora-tap-bridge ]; then
    echo "❌ Build failed - binary not created"
    exit 1
fi
echo "✓ Binary created"

if ! file lora-tap-bridge | grep -q "ARM aarch64"; then
    echo "❌ Binary not built for ARM64"
    file lora-tap-bridge
    exit 1
fi
echo "✓ Built for ARM64"

if ! ldd lora-tap-bridge | grep -q "libgpiod"; then
    echo "❌ Not linked with libgpiod"
    ldd lora-tap-bridge
    exit 1
fi
echo "✓ Linked with libgpiod"

echo
echo "=== Build Test Passed ==="
echo
echo "Next steps:"
echo "  1. sudo ./lora-tap-bridge        # Test run"
echo "  2. sudo make install              # Install to /usr/local/bin"
echo "  3. sudo systemctl enable lora-bridge   # Enable service"
