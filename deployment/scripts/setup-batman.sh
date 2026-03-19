#!/bin/bash
# MYC3LIUM BATMAN-adv Mesh Setup
# Configures 802.11s mesh networking with BATMAN-adv on wlan0

set -e

echo "🦇 MYC3LIUM BATMAN-adv Mesh Setup"

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

# Configuration
MESH_IFACE="wlan0"
MESH_ID="myc3lium-mesh"
MESH_FREQ="2437"  # Channel 6
BAT_IFACE="bat0"
BRIDGE_IFACE="br-myc3lium"
MESH_IP="10.13.0.$(shuf -i 2-254 -n 1)"  # Random IP in mesh subnet

log_info "Installing BATMAN-adv..."
apt-get update
apt-get install -y batctl alfred

# Load batman-adv module
log_info "Loading batman-adv kernel module..."
modprobe batman-adv

# Add to modules to load at boot
if ! grep -q "batman-adv" /etc/modules; then
    echo "batman-adv" >> /etc/modules
fi

# Check if module loaded
if ! lsmod | grep -q batman_adv; then
    log_error "Failed to load batman-adv module"
    exit 1
fi

log_info "✓ batman-adv module loaded"

# Stop NetworkManager from managing wlan0
log_info "Configuring NetworkManager to ignore mesh interface..."
cat > /etc/NetworkManager/conf.d/99-myc3lium-mesh.conf <<EOF
[keyfile]
unmanaged-devices=interface-name:wlan0;interface-name:bat0;interface-name:br-myc3lium
EOF

systemctl reload NetworkManager 2>/dev/null || true

# Create mesh configuration script
cat > /opt/myc3lium/setup-mesh.sh <<'MESHEOF'
#!/bin/bash
# Mesh network initialization script

set -e

MESH_IFACE="wlan0"
MESH_ID="myc3lium-mesh"
MESH_FREQ="2437"
BAT_IFACE="bat0"
BRIDGE_IFACE="br-myc3lium"
MESH_IP="10.13.0.$(cat /proc/sys/kernel/random/uuid | md5sum | cut -d' ' -f1 | tail -c 4 | python3 -c 'import sys; print(int(sys.stdin.read().strip(), 16) % 253 + 2)')"

echo "🦇 Starting BATMAN-adv mesh on $MESH_IFACE..."

# Bring down interface
ip link set $MESH_IFACE down 2>/dev/null || true

# Set interface to mesh mode
iw dev $MESH_IFACE set type mp

# Bring up interface
ip link set $MESH_IFACE up

# Set mesh parameters
iw dev $MESH_IFACE mesh join $MESH_ID freq $MESH_FREQ HT40+ 
iw dev $MESH_IFACE set mesh_param mesh_fwding 0

# Configure batman-adv
batctl if add $MESH_IFACE

# Bring up batman interface
ip link set $BAT_IFACE up

# Set MTU
ip link set $BAT_IFACE mtu 1460

# Assign IP address
ip addr flush dev $BAT_IFACE
ip addr add $MESH_IP/16 broadcast 10.13.255.255 dev $BAT_IFACE

# Configure batman-adv parameters
batctl gw_mode client
batctl hop_penalty 15
batctl orig_interval 5000

echo "✓ Mesh interface configured"
echo "  Interface: $MESH_IFACE"
echo "  Mesh ID: $MESH_ID"
echo "  BATMAN interface: $BAT_IFACE"
echo "  IP: $MESH_IP/16"

# Show mesh status
echo ""
echo "Mesh status:"
iw dev $MESH_IFACE info
echo ""
echo "BATMAN status:"
batctl if
batctl o
MESHEOF

chmod +x /opt/myc3lium/setup-mesh.sh
chown myc3lium:myc3lium /opt/myc3lium/setup-mesh.sh

# Create systemd service
log_info "Creating BATMAN-adv systemd service..."
cat > /etc/systemd/system/batman-adv.service <<EOF
[Unit]
Description=MYC3LIUM BATMAN-adv Mesh Network
After=network-pre.target
Before=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/myc3lium/setup-mesh.sh
ExecStop=/usr/sbin/batctl if del wlan0
ExecStop=/sbin/ip link set bat0 down
ExecStop=/sbin/ip link set wlan0 down

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable batman-adv.service

# Create mesh monitoring script
cat > /opt/myc3lium/mesh-status.sh <<'STATEOF'
#!/bin/bash
# BATMAN-adv mesh status and monitoring

echo "🦇 MYC3LIUM Mesh Network Status"
echo "================================"
echo ""

if ! ip link show bat0 &>/dev/null; then
    echo "❌ bat0 interface not found - mesh not running"
    echo "Start mesh: sudo systemctl start batman-adv"
    exit 1
fi

echo "BATMAN Interface:"
ip addr show bat0
echo ""

echo "Mesh Interface:"
iw dev wlan0 info 2>/dev/null || echo "wlan0 not in mesh mode"
echo ""

echo "Mesh Station List:"
iw dev wlan0 station dump 2>/dev/null || echo "No stations"
echo ""

echo "BATMAN Originators (Mesh Neighbors):"
batctl o
echo ""

echo "BATMAN Gateway Status:"
batctl gw
echo ""

echo "BATMAN Routing Table:"
batctl n
echo ""

echo "BATMAN Multicast Flags:"
batctl mcast_flags 2>/dev/null || echo "Multicast info unavailable"
echo ""

echo "Recent Mesh Activity:"
batctl log 2>/dev/null | tail -n 10 || echo "Logging not enabled"
STATEOF

chmod +x /opt/myc3lium/mesh-status.sh
chown myc3lium:myc3lium /opt/myc3lium/mesh-status.sh

# Create mesh test script
cat > /opt/myc3lium/test-mesh.sh <<'TESTEOF'
#!/bin/bash
# Test mesh connectivity

source /opt/myc3lium/halow-config.conf 2>/dev/null || true

echo "🦇 Testing Mesh Connectivity"
echo "============================="
echo ""

# Check if mesh is running
if ! systemctl is-active --quiet batman-adv.service; then
    echo "❌ BATMAN-adv service not running"
    echo "Start with: sudo systemctl start batman-adv"
    exit 1
fi

echo "✓ BATMAN-adv service is running"

# Check bat0 interface
if ! ip link show bat0 &>/dev/null; then
    echo "❌ bat0 interface not found"
    exit 1
fi

echo "✓ bat0 interface exists"

# Get mesh IP
MESH_IP=$(ip addr show bat0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
echo "✓ Mesh IP: $MESH_IP"

# Check for mesh neighbors
NEIGHBOR_COUNT=$(batctl o | grep -v "No" | grep -c "wlan0" || echo "0")
echo "✓ Mesh neighbors: $NEIGHBOR_COUNT"

if [ "$NEIGHBOR_COUNT" -gt 0 ]; then
    echo ""
    echo "Mesh neighbors:"
    batctl o
    
    echo ""
    echo "Testing connectivity to neighbors..."
    batctl n | grep -oE "10\.13\.[0-9]+\.[0-9]+" | while read neighbor_ip; do
        if [ "$neighbor_ip" != "$MESH_IP" ]; then
            echo -n "  Pinging $neighbor_ip... "
            if ping -c 1 -W 2 "$neighbor_ip" &>/dev/null; then
                echo "✓ OK"
            else
                echo "✗ Failed"
            fi
        fi
    done
else
    echo "⚠️  No mesh neighbors found - this node is alone"
    echo "   Wait for other nodes to join, or check:"
    echo "   - wlan0 is in mesh mode: iw dev wlan0 info"
    echo "   - Mesh ID matches: myc3lium-mesh"
    echo "   - Nodes are within range"
fi

echo ""
echo "============================="
echo "✅ Mesh test complete"
TESTEOF

chmod +x /opt/myc3lium/test-mesh.sh
chown myc3lium:myc3lium /opt/myc3lium/test-mesh.sh

# Alfred configuration (optional mesh visualization)
log_info "Configuring Alfred (mesh visualization helper)..."
cat > /etc/default/alfred <<EOF
# Alfred configuration for MYC3LIUM
ALFRED_ARGS="-i bat0 -b batman-adv"
EOF

systemctl enable alfred 2>/dev/null || true

# Start mesh
log_info "Starting BATMAN-adv mesh network..."
systemctl start batman-adv.service || log_warn "Failed to start mesh - check logs"

sleep 3

# Run status check
bash /opt/myc3lium/mesh-status.sh || log_warn "Mesh status check completed with warnings"

log_info "✅ BATMAN-adv setup complete!"
log_info ""
log_info "Scripts created:"
log_info "  Setup: /opt/myc3lium/setup-mesh.sh"
log_info "  Status: /opt/myc3lium/mesh-status.sh"
log_info "  Test: /opt/myc3lium/test-mesh.sh"
log_info ""
log_info "Systemd service: batman-adv.service"
log_info "  Start: sudo systemctl start batman-adv"
log_info "  Status: sudo systemctl status batman-adv"
log_info ""
log_info "To check mesh status:"
log_info "  bash /opt/myc3lium/mesh-status.sh"
log_info ""
log_info "To test connectivity:"
log_info "  bash /opt/myc3lium/test-mesh.sh"
