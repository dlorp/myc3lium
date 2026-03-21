#!/bin/bash
# MYC3LIUM LoRa Setup - Improved
# Configures Reticulum to use SX1262 LoRa HAT with proper detection

set -eo pipefail

LOG_FILE="/tmp/myc3lium-lora-install.log"
RETICULUM_CONFIG="$HOME/.reticulum/config"

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

check_spi() {
    log_step "Checking SPI interface..."
    
    # Check if SPI module is loaded
    if ! lsmod | grep -q spi_bcm2835; then
        log_warn "SPI module not loaded, attempting to load..."
        modprobe spi_bcm2835 || {
            log_error "Failed to load SPI module"
            return 1
        }
    fi
    
    # Check if SPI device exists
    if [ ! -e /dev/spidev0.0 ]; then
        log_error "SPI device /dev/spidev0.0 not found!"
        log_error "Enable SPI in boot config and reboot"
        return 1
    fi
    
    log_info "✓ SPI device found: /dev/spidev0.0"
    return 0
}

detect_lora_hat() {
    log_step "Detecting LoRa HAT..."
    
    # Try to detect SX126x via SPI
    # This is a basic check - proper detection requires querying the chip
    if [ -e /dev/spidev0.0 ]; then
        log_info "SPI device present (HAT may be connected)"
        log_warn "Cannot verify SX1262 without running Reticulum test"
        return 0
    else
        log_error "No SPI device found - is the HAT connected?"
        return 1
    fi
}

configure_reticulum() {
    log_step "Configuring Reticulum for LoRa..."
    
    # Create Reticulum config directory
    mkdir -p "$(dirname "$RETICULUM_CONFIG")"
    
    # Check if config exists
    if [ -f "$RETICULUM_CONFIG" ]; then
        log_info "Reticulum config exists, will append LoRa interface"
        backup="$RETICULUM_CONFIG.backup.$(date +%s)"
        cp "$RETICULUM_CONFIG" "$backup"
        log_info "Backed up to: $backup"
    else
        log_info "Creating new Reticulum config"
        cat > "$RETICULUM_CONFIG" <<'EOF'
# MYC3LIUM Reticulum Configuration

[reticulum]
  enable_transport = yes
  share_instance = yes
  shared_instance_port = 37428
  instance_control_port = 37429

[logging]
  loglevel = 4

EOF
    fi
    
    # Add LoRa interface (if not already present)
    if grep -q "\[LoRa Interface\]" "$RETICULUM_CONFIG"; then
        log_info "LoRa interface already configured"
    else
        cat >> "$RETICULUM_CONFIG" <<'EOF'

[[LoRa Interface]]
  type = RNodeInterface
  interface_enabled = yes
  outgoing = yes
  
  # SX1262 HAT on Raspberry Pi
  port = /dev/spidev0.0
  frequency = 915000000
  bandwidth = 125000
  txpower = 17
  spreadingfactor = 7
  codingrate = 5
  
  # Callsign (change this!)
  id_callsign = SPORE-01
  id_interval = 600

EOF
        log_info "✓ Added LoRa interface to Reticulum config"
    fi
}

set_permissions() {
    log_step "Setting SPI permissions..."
    
    chmod 666 /dev/spidev0.0 || log_warn "Failed to set SPI permissions"
    
    # Add udev rule for persistent permissions
    cat > /etc/udev/rules.d/99-spi.rules <<EOF
# SPI devices for MYC3LIUM
SUBSYSTEM=="spidev", KERNEL=="spidev0.0", MODE="0666"
EOF
    
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
}

create_test_script() {
    log_step "Creating LoRa test script..."
    
    cat > /opt/myc3lium/test-lora.sh <<'EOF'
#!/bin/bash
# Test LoRa interface via Reticulum

echo "Testing LoRa interface..."
echo ""

# Check if Reticulum is installed
if ! python3 -c "import RNS" 2>/dev/null; then
    echo "ERROR: Reticulum not installed"
    echo "Install with: pip3 install rns"
    exit 1
fi

# Show Reticulum status
echo "Reticulum status:"
rnstatus

echo ""
echo "If you see 'LoRa Interface' listed above, the HAT is working!"
echo "If not, check:"
echo "  1. SPI enabled in boot config"
echo "  2. HAT properly seated on GPIO header"
echo "  3. Power to HAT (check LED if present)"
EOF
    
    chmod +x /opt/myc3lium/test-lora.sh
    log_info "Test script: /opt/myc3lium/test-lora.sh"
}

main() {
    log_info "MYC3LIUM LoRa Setup (SX1262)"
    
    check_root
    
    if ! check_spi; then
        log_error "SPI not available - fix and retry"
        exit 1
    fi
    
    detect_lora_hat || log_warn "HAT detection inconclusive"
    
    set_permissions
    configure_reticulum
    create_test_script
    
    log_info ""
    log_info "✓ LoRa setup complete!"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Edit ~/.reticulum/config and set your callsign"
    log_info "  2. Run: /opt/myc3lium/test-lora.sh"
    log_info "  3. Check output for 'LoRa Interface'"
    log_info ""
    log_warn "If interface doesn't appear, you may need RNode firmware"
    log_warn "See: https://reticulum.network/manual/interfaces.html#rnode"
}

main "$@"
