#!/bin/bash
# Install HaLow SLIP Bridge on Raspberry Pi
# Run as: sudo ./install.sh

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./install.sh)"
    exit 1
fi

echo "Installing HaLow SLIP Bridge..."

# Compile daemon
echo "Compiling daemon..."
gcc -o halow-slip-bridge pi-slip-daemon.c
chmod +x halow-slip-bridge

# Install binaries
echo "Installing to /usr/local/bin..."
cp halow-slip-bridge /usr/local/bin/
cp pi-startup.sh /usr/local/bin/halow-start.sh
chmod +x /usr/local/bin/halow-start.sh

# Install systemd service
echo "Installing systemd service..."
cp halow-bridge.service /etc/systemd/system/
systemctl daemon-reload

# Enable service
echo "Enabling auto-start..."
systemctl enable halow-bridge.service

echo ""
echo "✓ Installation complete!"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start halow-bridge"
echo "  Stop:    sudo systemctl stop halow-bridge"
echo "  Status:  sudo systemctl status halow-bridge"
echo "  Logs:    sudo journalctl -u halow-bridge -f"
echo "           tail -f /var/log/halow-bridge.log"
echo ""
echo "Manual start: sudo /usr/local/bin/halow-start.sh"
echo ""
echo "Next: Flash ESP32 with esp32-halow-ap-slip-bridge.bin"
echo "  esptool.py --chip esp32s3 --port /dev/ttyUSB0 --baud 921600 \\"
echo "    write-flash 0x10000 esp32-halow-ap-slip-bridge.bin"
