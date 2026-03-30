#!/bin/bash
# MYC3LIUM BATMAN-adv Deployment Setup
#
# One-time script to install packages and configure module autoloading.
# Runtime mesh bringup is handled by the myc3lium app via myc3lium-netctl.
#
# Usage: sudo bash setup-batman.sh

set -e

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

log_info "MYC3LIUM BATMAN-adv deployment setup"

# Install batctl (userspace control tool)
log_info "Installing batctl..."
apt-get update -qq
apt-get install -y batctl

# Load batman-adv kernel module
log_info "Loading batman-adv kernel module..."
modprobe batman-adv

if ! lsmod | grep -q batman_adv; then
    log_error "Failed to load batman-adv module"
    exit 1
fi
log_info "batman-adv module loaded"

# Persist module load across reboots
if ! grep -q "batman-adv" /etc/modules; then
    echo "batman-adv" >> /etc/modules
    log_info "Added batman-adv to /etc/modules"
fi

# Exclude wlan0 and bat0 from NetworkManager
log_info "Configuring NetworkManager to ignore mesh interfaces..."
mkdir -p /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/99-myc3lium-mesh.conf <<EOF
[keyfile]
unmanaged-devices=interface-name:wlan0;interface-name:bat0
EOF
systemctl reload NetworkManager 2>/dev/null || true

# Create diagnostic scripts
mkdir -p /opt/myc3lium
cat > /opt/myc3lium/mesh-status.sh <<'STATEOF'
#!/bin/bash
# BATMAN-adv mesh status

echo "MYC3LIUM Mesh Network Status"
echo "============================="
echo ""

if ! ip link show bat0 &>/dev/null; then
    echo "bat0 interface not found - mesh not running"
    echo "The myc3lium service starts the mesh automatically."
    exit 1
fi

echo "BATMAN Interface:"
ip addr show bat0
echo ""

echo "Mesh Interface (wlan0):"
iw dev wlan0 info 2>/dev/null || echo "wlan0 not in IBSS mode"
echo ""

echo "BATMAN Neighbors (direct):"
batctl meshif bat0 neighbors 2>/dev/null || echo "No neighbors"
echo ""

echo "BATMAN Originators (all reachable nodes):"
batctl meshif bat0 originators 2>/dev/null || echo "No originators"
echo ""

echo "BATMAN Statistics:"
batctl meshif bat0 statistics 2>/dev/null || echo "Stats unavailable"
STATEOF

cat > /opt/myc3lium/test-mesh.sh <<'TESTEOF'
#!/bin/bash
# Test mesh connectivity

echo "MYC3LIUM Mesh Connectivity Test"
echo "================================"
echo ""

if ! ip link show bat0 &>/dev/null; then
    echo "bat0 interface not found - mesh not running"
    exit 1
fi
echo "bat0 interface exists"

BAT_IP=$(ip -4 addr show bat0 2>/dev/null | grep -oP 'inet \K[0-9.]+')
echo "Mesh IP: ${BAT_IP:-none}"

WLAN_TYPE=$(iw dev wlan0 info 2>/dev/null | grep -i "type" | awk '{print $2}')
echo "wlan0 type: ${WLAN_TYPE:-unknown}"

NEIGHBOR_COUNT=$(batctl meshif bat0 neighbors 2>/dev/null | grep -c "wlan0" || echo "0")
echo "Direct neighbors: $NEIGHBOR_COUNT"

if [ "$NEIGHBOR_COUNT" -gt 0 ]; then
    echo ""
    echo "Neighbors:"
    batctl meshif bat0 neighbors 2>/dev/null
else
    echo ""
    echo "No neighbors found - this node is alone in the mesh."
    echo "Ensure another node is running with the same mesh SSID and channel."
fi

echo ""
echo "================================"
echo "Test complete"
TESTEOF

chmod +x /opt/myc3lium/mesh-status.sh /opt/myc3lium/test-mesh.sh
chown myc3:myc3 /opt/myc3lium/mesh-status.sh /opt/myc3lium/test-mesh.sh 2>/dev/null || true

log_info "BATMAN-adv deployment setup complete"
log_info ""
log_info "Packages installed: batctl"
log_info "Module: batman-adv (loaded and persistent)"
log_info "NetworkManager: wlan0 and bat0 unmanaged"
log_info ""
log_info "Diagnostics:"
log_info "  bash /opt/myc3lium/mesh-status.sh"
log_info "  bash /opt/myc3lium/test-mesh.sh"
log_info ""
log_info "The myc3lium service handles mesh startup/shutdown automatically."
log_info "Manual control: sudo myc3lium-netctl mesh-up|mesh-down|mesh-status"
