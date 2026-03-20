#!/bin/bash
# MYC3LIUM WiFi HaLow Setup - Heltec HT-HC01P
# Configures 902-928 MHz HaLow module via USB

set -e

echo "📶 MYC3LIUM WiFi HaLow Setup - Heltec HT-HC01P"

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

# HT-HC01P uses Morse Micro MM6108 chipset
# Driver installation may require kernel module compilation

log_info "Checking for USB WiFi HaLow device..."

# Wait for device to be detected
sleep 2

# Check if device is connected
if lsusb | grep -qE "Morse|HaLow|MM6108"; then
    log_info "✓ HaLow device detected via USB"
    lsusb | grep -E "Morse|HaLow|MM6108"
else
    log_warn "HaLow device not detected - may need USB adapter or different identifier"
    log_info "All USB devices:"
    lsusb
fi

# Install dependencies
log_info "Installing dependencies..."
apt-get update
apt-get install -y \
    build-essential \
    linux-headers-$(uname -r) \
    dkms \
    git \
    wireless-tools \
    iw \
    wpasupplicant

# Note: Driver availability depends on chipset
# For Morse Micro MM6108, check for official driver or backports

log_info "Checking for HaLow network interface..."

# Look for new wireless interfaces (usually wlan1 or similar)
HALOW_IFACE=""
for iface in $(ls /sys/class/net/ | grep -E "wlan[1-9]|halow"); do
    if [ -d "/sys/class/net/$iface/wireless" ]; then
        log_info "Found wireless interface: $iface"
        # Check if it supports HaLow frequencies (902-928 MHz)
        if iw phy$(cat /sys/class/net/$iface/phy80211/index 2>/dev/null || echo "0") info 2>/dev/null | grep -q "MHz \[9[0-2][0-9]\]"; then
            HALOW_IFACE=$iface
            log_info "✓ HaLow interface detected: $HALOW_IFACE"
            break
        fi
    fi
done

if [ -z "$HALOW_IFACE" ]; then
    log_warn "No HaLow interface found - driver may need manual installation"
    HALOW_IFACE="wlan1"  # Default assumption
    log_info "Assuming interface will be: $HALOW_IFACE"
fi

# Save configuration
cat > /opt/myc3lium/halow-config.conf <<EOF
# HaLow Interface Configuration
HALOW_IFACE=$HALOW_IFACE
HALOW_FREQ=915
HALOW_BAND=902-928MHz
HALOW_SSID=myc3lium-halow
HALOW_KEY=$(openssl rand -hex 32)
EOF

log_info "Configuration saved to /opt/myc3lium/halow-config.conf"

# Create network configuration
log_info "Creating network configuration..."

cat > /etc/network/interfaces.d/halow <<EOF
# WiFi HaLow Interface - Heltec HT-HC01P
allow-hotplug $HALOW_IFACE
iface $HALOW_IFACE inet static
    address 10.42.1.1
    netmask 255.255.255.0
    wireless-channel 11
    wireless-essid myc3lium-halow
    wireless-mode ad-hoc
EOF

# Create WPA supplicant config for managed mode (if needed)
cat > /etc/wpa_supplicant/wpa_supplicant-halow.conf <<'EOF'
ctrl_interface=/var/run/wpa_supplicant
update_config=1
country=US

network={
    ssid="myc3lium-halow"
    mode=1
    frequency=915
    key_mgmt=WPA-PSK
    psk="myc3lium-halow-mesh"
    scan_ssid=1
}
EOF

chmod 600 /etc/wpa_supplicant/wpa_supplicant-halow.conf

# Create systemd service for HaLow interface
cat > /etc/systemd/system/halow-interface.service <<EOF
[Unit]
Description=MYC3LIUM WiFi HaLow Interface
After=network-pre.target
Before=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/ifup $HALOW_IFACE
ExecStop=/sbin/ifdown $HALOW_IFACE

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable halow-interface.service

# Create test script
cat > /opt/myc3lium/test-halow.sh <<'TESTEOF'
#!/bin/bash
# HaLow interface test script

source /opt/myc3lium/halow-config.conf

echo "📶 Testing HaLow Interface: $HALOW_IFACE"
echo "========================================="
echo ""

# Check if interface exists
if ! ip link show "$HALOW_IFACE" &>/dev/null; then
    echo "❌ Interface $HALOW_IFACE not found"
    echo "Available interfaces:"
    ip link show | grep -E "^[0-9]+:" | cut -d: -f2
    exit 1
fi

echo "✓ Interface exists: $HALOW_IFACE"

# Check interface status
if ip link show "$HALOW_IFACE" | grep -q "state UP"; then
    echo "✓ Interface is UP"
else
    echo "⚠ Interface is DOWN - attempting to bring up..."
    sudo ifup "$HALOW_IFACE" || sudo ip link set "$HALOW_IFACE" up
fi

# Show interface details
echo ""
echo "Interface details:"
ip addr show "$HALOW_IFACE"

echo ""
echo "Wireless info:"
iw dev "$HALOW_IFACE" info 2>/dev/null || echo "iw info not available"

echo ""
echo "Scanning for HaLow networks..."
iw dev "$HALOW_IFACE" scan 2>/dev/null | grep -E "SSID|freq|signal" || echo "No networks found or scan not supported"

echo ""
echo "========================================="
echo "✅ HaLow interface test complete"
TESTEOF

chmod +x /opt/myc3lium/test-halow.sh
chown myc3lium:myc3lium /opt/myc3lium/test-halow.sh

# Create driver installation helper (for manual setup if needed)
cat > /opt/myc3lium/install-halow-driver.sh <<'DRVEOF'
#!/bin/bash
# Helper script to install HaLow driver if not automatically detected

echo "🔧 HaLow Driver Installation Helper"
echo "====================================="
echo ""
echo "This script helps install the Morse Micro MM6108 driver"
echo "for Heltec HT-HC01P HaLow module."
echo ""
echo "⚠️  Driver source needed from vendor or community"
echo ""
echo "Common sources:"
echo "  - Morse Micro SDK (requires registration)"
echo "  - OpenWrt backports"
echo "  - Vendor-provided binary modules"
echo ""
echo "Manual steps:"
echo "  1. Download driver source/binary"
echo "  2. Extract to /usr/src/"
echo "  3. Use DKMS to build and install"
echo "  4. Load module with modprobe"
echo ""
echo "Example DKMS installation:"
echo "  cd /usr/src/mm6108-1.0.0/"
echo "  dkms add -m mm6108 -v 1.0.0"
echo "  dkms build -m mm6108 -v 1.0.0"
echo "  dkms install -m mm6108 -v 1.0.0"
echo "  modprobe mm6108"
echo ""
echo "For community support, check:"
echo "  - Heltec forums"
echo "  - OpenWrt HaLow discussions"
echo "  - Morse Micro developer portal"
DRVEOF

chmod +x /opt/myc3lium/install-halow-driver.sh

# Run test
log_info "Running HaLow interface test..."
bash /opt/myc3lium/test-halow.sh || log_warn "Interface test completed with warnings"

log_info "✅ HaLow setup complete!"
log_info ""
log_info "Configuration: /opt/myc3lium/halow-config.conf"
log_info "Test script: /opt/myc3lium/test-halow.sh"
log_info "Driver helper: /opt/myc3lium/install-halow-driver.sh"
log_info ""
log_info "⚠️  Note: HaLow driver may require vendor-specific installation"
log_info "   If interface not detected, check with vendor for driver support"
log_info ""
log_info "To test manually:"
log_info "  bash /opt/myc3lium/test-halow.sh"
