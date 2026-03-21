#!/bin/bash
# MYC3LIUM BATMAN-adv Setup - Improved
# Configures mesh networking with interface detection and validation

set -eo pipefail

LOG_FILE="/tmp/myc3lium-batman-install.log"
MESH_SSID="MYC3LIUM"
MESH_FREQ="2437"  # Channel 6
MESH_IF="mesh0"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }
log_step() { echo -e "${BLUE}▶${NC} $1" | tee -a "$LOG_FILE"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

install_batman() {
    log_step "Installing BATMAN-adv..."
    
    # Check if already installed
    if command -v batctl &>/dev/null; then
        log_info "batctl already installed"
    else
        apt-get install -y batctl alfred || {
            log_warn "Failed to install batctl - may need kernel module"
        }
    fi
    
    # Load kernel module
    if ! lsmod | grep -q batman_adv; then
        log_info "Loading batman-adv module..."
        modprobe batman_adv || {
            log_error "Failed to load batman-adv kernel module"
            log_error "Your kernel may not support it"
            return 1
        }
    else
        log_info "batman-adv module already loaded"
    fi
    
    # Add to modules load
    if ! grep -q "batman_adv" /etc/modules-load.d/myc3lium.conf 2>/dev/null; then
        echo "batman_adv" >> /etc/modules-load.d/myc3lium.conf
    fi
}

find_wifi_interface() {
    log_step "Finding available WiFi interface..."
    
    # Look for wireless interfaces (prefer wlan0, but handle predictable names)
    local interfaces=($(iw dev 2>/dev/null | grep Interface | awk '{print $2}'))
    
    if [ ${#interfaces[@]} -eq 0 ]; then
        log_error "No wireless interfaces found"
        return 1
    fi
    
    # Check if any are free (not already used)
    for iface in "${interfaces[@]}"; do
        if ! ip link show "$iface" 2>/dev/null | grep -q "UP"; then
            echo "$iface"
            return 0
        fi
    done
    
    # All are up - use first one with warning
    log_warn "All interfaces in use, using ${interfaces[0]} (may conflict)"
    echo "${interfaces[0]}"
}

configure_mesh() {
    log_step "Configuring mesh network..."
    
    local phy_if
    phy_if=$(find_wifi_interface) || {
        log_error "No suitable WiFi interface found"
        return 1
    }
    
    log_info "Using interface: $phy_if"
    
    # Bring down interface
    ip link set "$phy_if" down 2>/dev/null || true
    
    # Create mesh interface
    if ! iw dev | grep -q "$MESH_IF"; then
        iw dev "$phy_if" interface add "$MESH_IF" type mp || {
            log_error "Failed to create mesh interface"
            return 1
        }
        log_info "Created mesh interface: $MESH_IF"
    else
        log_info "Mesh interface $MESH_IF already exists"
    fi
    
    # Configure mesh
    iw dev "$MESH_IF" set channel $(( ($MESH_FREQ - 2407) / 5 )) || log_warn "Failed to set channel"
    ip link set "$MESH_IF" up || {
        log_error "Failed to bring up mesh interface"
        return 1
    }
    
    # Join mesh
    iw dev "$MESH_IF" mesh join "$MESH_SSID" freq "$MESH_FREQ" || {
        log_error "Failed to join mesh"
        return 1
    }
    
    log_info "✓ Joined mesh SSID: $MESH_SSID"
    
    # Add to BATMAN
    batctl if add "$MESH_IF" || {
        log_error "Failed to add interface to BATMAN"
        return 1
    }
    
    # Bring up bat0
    ip link set bat0 up || {
        log_error "Failed to bring up bat0"
        return 1
    }
    
    # Assign link-local address
    ip addr add 169.254.$(shuf -i 1-254 -n 1).$(shuf -i 1-254 -n 1)/16 dev bat0 2>/dev/null || log_warn "Address already assigned"
    
    log_info "✓ BATMAN interface bat0 is up"
}

create_test_script() {
    cat > /opt/myc3lium/test-batman.sh <<'EOF'
#!/bin/bash
# Test BATMAN-adv mesh

echo "BATMAN-adv Mesh Status"
echo "======================"
echo ""

if ! command -v batctl &>/dev/null; then
    echo "ERROR: batctl not installed"
    exit 1
fi

echo "Mesh interfaces:"
batctl if
echo ""

echo "Mesh neighbors (originators):"
batctl o
echo ""

echo "Routing table:"
batctl n
echo ""

if [ $(batctl o | wc -l) -gt 1 ]; then
    echo "✓ Mesh has neighbors - network is forming!"
else
    echo "⚠ No neighbors detected"
    echo "  Ensure other nodes are running and in range"
fi
EOF
    
    chmod +x /opt/myc3lium/test-batman.sh
    log_info "Test script: /opt/myc3lium/test-batman.sh"
}

create_systemd_service() {
    log_step "Creating systemd service..."
    
    cat > /etc/systemd/system/myc3lium-mesh.service <<EOF
[Unit]
Description=MYC3LIUM Mesh Network
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/myc3lium/start-mesh.sh
ExecStop=/opt/myc3lium/stop-mesh.sh

[Install]
WantedBy=multi-user.target
EOF
    
    # Create start/stop scripts
    cat > /opt/myc3lium/start-mesh.sh <<'EOF'
#!/bin/bash
# Start mesh (placeholder - customize for your interface)
batctl if add mesh0 2>/dev/null || true
ip link set bat0 up 2>/dev/null || true
EOF
    
    cat > /opt/myc3lium/stop-mesh.sh <<'EOF'
#!/bin/bash
# Stop mesh
ip link set bat0 down 2>/dev/null || true
batctl if del mesh0 2>/dev/null || true
EOF
    
    chmod +x /opt/myc3lium/{start,stop}-mesh.sh
    
    systemctl daemon-reload
    log_info "Created systemd service (not enabled by default)"
}

main() {
    log_info "MYC3LIUM BATMAN-adv Mesh Setup"
    
    check_root
    install_batman || exit 1
    configure_mesh || {
        log_error "Mesh configuration failed"
        log_error "Check logs: $LOG_FILE"
        exit 1
    }
    
    create_test_script
    create_systemd_service
    
    log_info ""
    log_info "✓ BATMAN-adv setup complete!"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Run: /opt/myc3lium/test-batman.sh"
    log_info "  2. Check for neighbors with: batctl o"
    log_info "  3. Enable on boot: systemctl enable myc3lium-mesh"
    log_info ""
    log_warn "Mesh won't show neighbors until other nodes join"
}

main "$@"
