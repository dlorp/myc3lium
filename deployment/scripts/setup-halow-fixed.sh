#!/bin/bash
# MYC3LIUM HaLow Setup - Improved
# Detects and configures WiFi HaLow adapter with better error handling

set -eo pipefail

LOG_FILE="/tmp/myc3lium-halow-install.log"

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

detect_halow() {
    log_step "Detecting HaLow adapter..."
    
    # Look for common HaLow USB identifiers
    # Heltec HT-HC01P uses Realtek or similar chipset
    
    if lsusb | grep -iE "(halow|802.11ah|ht-hc01)"; then
        log_info "✓ Possible HaLow device detected"
        lsusb | grep -iE "(halow|802.11ah)" | head -1
        return 0
    fi
    
    # Check for wireless interfaces in 900MHz range
    if iw dev 2>/dev/null | grep -q "902\|928"; then
        log_info "✓ Found 900MHz wireless interface"
        return 0
    fi
    
    log_warn "No obvious HaLow device found"
    log_warn "Adapter may need vendor driver installation"
    return 1
}

check_driver() {
    log_step "Checking for HaLow driver..."
    
    # Check if kernel modules are loaded
    if lsmod | grep -iE "8021[14]ah|rtw|mt76"; then
        log_info "Wireless driver loaded"
        return 0
    fi
    
    log_warn "No HaLow-compatible driver detected"
    return 1
}

configure_interface() {
    log_step "Configuring HaLow interface..."
    
    # Find wireless interfaces
    halow_if=$(iw dev 2>/dev/null | grep Interface | awk '{print $2}' | tail -1)
    
    if [ -z "$halow_if" ]; then
        log_error "No wireless interface found"
        log_error "Driver installation required"
        return 1
    fi
    
    log_info "Using interface: $halow_if"
    
    # Create NetworkManager connection for mesh mode
    # This is a placeholder - actual config depends on driver support
    cat > /etc/NetworkManager/system-connections/halow-mesh.nmconnection <<EOF
[connection]
id=halow-mesh
type=wifi
interface-name=$halow_if
autoconnect=false

[wifi]
mode=mesh
ssid=MYC3LIUM

[ipv4]
method=link-local

[ipv6]
method=link-local
EOF
    
    chmod 600 /etc/NetworkManager/system-connections/halow-mesh.nmconnection
    
    log_info "Created NetworkManager connection (will need manual activation)"
}

create_test_script() {
    cat > /opt/myc3lium/test-halow.sh <<'EOF'
#!/bin/bash
# Test HaLow adapter detection

echo "HaLow Adapter Test"
echo "=================="
echo ""

echo "USB devices:"
lsusb | grep -iE "(halow|802.11ah|realtek|mediatek)" || echo "  (none found)"
echo ""

echo "Wireless interfaces:"
iw dev 2>/dev/null || echo "  (iw command not available)"
echo ""

echo "Loaded drivers:"
lsmod | grep -iE "rtw|mt76|80211" | awk '{print $1}' | sort -u || echo "  (none found)"
echo ""

echo "If no HaLow device found:"
echo "  1. Check USB connection (lsusb should show the device)"
echo "  2. Install vendor driver from manufacturer"
echo "  3. Reboot after driver installation"
EOF
    
    chmod +x /opt/myc3lium/test-halow.sh
    log_info "Test script: /opt/myc3lium/test-halow.sh"
}

main() {
    log_info "MYC3LIUM HaLow Setup"
    
    check_root
    
    # Detection is non-fatal
    detect_halow || log_warn "Proceeding without confirmed detection"
    check_driver || log_warn "Driver may need manual installation"
    
    # Install wireless tools if missing
    if ! command -v iw &>/dev/null; then
        log_step "Installing wireless tools..."
        apt-get install -y iw wireless-tools || log_warn "Failed to install tools"
    fi
    
    configure_interface || log_warn "Interface configuration incomplete"
    create_test_script
    
    log_info ""
    log_info "✓ HaLow setup attempt complete"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Run: /opt/myc3lium/test-halow.sh"
    log_info "  2. If device not found, install vendor driver"
    log_info "  3. Activate mesh: nmcli connection up halow-mesh"
    log_info ""
    log_warn "HaLow support varies by hardware - may need manual config"
}

main "$@"
