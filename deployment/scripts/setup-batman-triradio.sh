#!/bin/bash
# MYC3LIUM Tri-Radio BATMAN-adv Setup
# Configures LoRa + HaLow + WiFi mesh with intelligent routing

set -eo pipefail

LOG_FILE="/tmp/myc3lium-triradio-install.log"

# Interface names (adjust based on your hardware)
LORA_IF="lora0"      # LoRa interface (created by driver)
HALOW_IF="wlan1"     # HaLow 802.11ah interface
WIFI_IF="wlan0"      # Standard WiFi interface
BAT_IF="bat0"        # BATMAN master interface

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }
log_step() { echo -e "${BLUE}▶${NC} $1" | tee -a "$LOG_FILE"; }

DRY_RUN=0
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=1
    log_info "DRY RUN MODE - no changes will be made"
fi

execute() {
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[DRY RUN] Would execute: $*"
    else
        "$@"
    fi
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

detect_interfaces() {
    log_step "Detecting available interfaces..."
    
    AVAILABLE_IFS=()
    
    # Check LoRa (might be serial-based, not a netdev)
    if ip link show "$LORA_IF" &>/dev/null; then
        log_info "✓ LoRa interface detected: $LORA_IF"
        AVAILABLE_IFS+=("$LORA_IF")
    else
        log_warn "✗ LoRa interface not found: $LORA_IF"
        log_info "  LoRa might use serial/SPI transport - check driver"
    fi
    
    # Check HaLow
    if ip link show "$HALOW_IF" &>/dev/null; then
        log_info "✓ HaLow interface detected: $HALOW_IF"
        AVAILABLE_IFS+=("$HALOW_IF")
    else
        log_warn "✗ HaLow interface not found: $HALOW_IF"
    fi
    
    # Check WiFi
    if ip link show "$WIFI_IF" &>/dev/null; then
        log_info "✓ WiFi interface detected: $WIFI_IF"
        AVAILABLE_IFS+=("$WIFI_IF")
    else
        log_warn "✗ WiFi interface not found: $WIFI_IF"
    fi
    
    if [[ ${#AVAILABLE_IFS[@]} -eq 0 ]]; then
        log_error "No mesh interfaces detected!"
        log_error "Cannot configure tri-radio mesh without hardware"
        exit 1
    fi
    
    log_info "Found ${#AVAILABLE_IFS[@]} interface(s): ${AVAILABLE_IFS[*]}"
}

install_batman() {
    log_step "Installing BATMAN-adv..."
    
    if command -v batctl &>/dev/null; then
        log_info "batctl already installed"
    else
        execute apt-get update
        execute apt-get install -y batctl alfred
    fi
    
    # Load kernel module
    if ! lsmod | grep -q batman_adv; then
        log_info "Loading batman-adv module..."
        execute modprobe batman_adv
    else
        log_info "batman-adv module already loaded"
    fi
    
    # Make module persistent
    if ! grep -q "batman_adv" /etc/modules; then
        execute sh -c 'echo "batman_adv" >> /etc/modules'
        log_info "Added batman-adv to /etc/modules"
    fi
}

configure_lora_interface() {
    log_step "Configuring LoRa interface for BATMAN..."
    
    # LoRa is typically NOT a standard netdev
    # It might be exposed via:
    # 1. Virtual network interface (tun/tap)
    # 2. Serial port with SLIP/PPP
    # 3. Custom driver
    
    # For now, assume virtual interface exists
    if ip link show "$LORA_IF" &>/dev/null; then
        execute ip link set "$LORA_IF" mtu 1532
        execute ip link set "$LORA_IF" up
        execute batctl if add "$LORA_IF"
        log_info "LoRa interface added to BATMAN mesh"
    else
        log_warn "LoRa interface setup skipped (not a netdev)"
        log_info "  Reticulum may handle LoRa transport separately"
    fi
}

configure_halow_interface() {
    log_step "Configuring HaLow (802.11ah) interface for BATMAN..."
    
    if ! ip link show "$HALOW_IF" &>/dev/null; then
        log_warn "HaLow interface not detected, skipping"
        return
    fi
    
    # Set 802.11ah mesh mode
    execute ip link set "$HALOW_IF" down
    execute iw dev "$HALOW_IF" set type mp  # Mesh point mode
    
    # Join mesh with SSID
    execute iw dev "$HALOW_IF" mesh join "MYC3LIUM_HALOW" freq 902 HT20
    
    # Increase MTU for BATMAN overhead
    execute ip link set "$HALOW_IF" mtu 1532
    execute ip link set "$HALOW_IF" up
    
    # Add to BATMAN
    execute batctl if add "$HALOW_IF"
    
    log_info "HaLow interface configured and added to mesh"
}

configure_wifi_interface() {
    log_step "Configuring WiFi (2.4 GHz) interface for BATMAN..."
    
    if ! ip link show "$WIFI_IF" &>/dev/null; then
        log_warn "WiFi interface not detected, skipping"
        return
    fi
    
    # Set mesh mode
    execute ip link set "$WIFI_IF" down
    execute iw dev "$WIFI_IF" set type mp
    
    # Join mesh (channel 6, 2.4 GHz)
    execute iw dev "$WIFI_IF" mesh join "MYC3LIUM_WIFI" freq 2437 HT40+
    
    # MTU
    execute ip link set "$WIFI_IF" mtu 1532
    execute ip link set "$WIFI_IF" up
    
    # Add to BATMAN
    execute batctl if add "$WIFI_IF"
    
    log_info "WiFi interface configured and added to mesh"
}

configure_batman_master() {
    log_step "Configuring BATMAN master interface (bat0)..."
    
    # Bring up bat0
    execute ip link set "$BAT_IF" up
    
    # Assign IP address (192.168.42.X subnet for mesh)
    # Use last octet from MAC address for uniqueness
    MAC=$(cat /sys/class/net/"$BAT_IF"/address)
    LAST_OCTET=$((0x${MAC##*:}))
    MESH_IP="192.168.42.$LAST_OCTET/24"
    
    execute ip addr add "$MESH_IP" dev "$BAT_IF" || {
        log_warn "IP address already assigned or failed"
    }
    
    log_info "BATMAN master interface configured: $MESH_IP"
}

tune_batman_settings() {
    log_step "Tuning BATMAN-adv for tri-radio mesh..."
    
    # Enable gateway mode (allows internet sharing)
    execute batctl gw_mode server
    
    # Set hop penalty (default 15, lower = prefer fewer hops)
    # For tri-radio, increase slightly to allow adaptive routing
    execute batctl hop_penalty 20
    
    # Enable multicast optimization
    execute batctl multicast_mode 1
    
    # Increase originator interval (default 1000ms)
    # Longer interval reduces overhead on LoRa
    execute batctl orig_interval 5000
    
    # Enable network coding (improves throughput)
    execute batctl network_coding 1
    
    # Enable bridge loop avoidance
    execute batctl bridge_loop_avoidance 1
    
    log_info "BATMAN settings optimized for tri-radio operation"
}

create_systemd_service() {
    log_step "Creating systemd service for tri-radio mesh..."
    
    SERVICE_FILE="/etc/systemd/system/myc3lium-triradio.service"
    
    execute tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=MYC3LIUM Tri-Radio Mesh Network
After=network.target
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/myc3lium-triradio-start.sh
ExecStop=/usr/local/bin/myc3lium-triradio-stop.sh

[Install]
WantedBy=multi-user.target
EOF

    # Create start script
    execute tee "/usr/local/bin/myc3lium-triradio-start.sh" > /dev/null <<'EOF'
#!/bin/bash
# Bring up tri-radio mesh on boot

modprobe batman_adv

# Configure interfaces
for iface in lora0 wlan1 wlan0; do
    if ip link show "$iface" &>/dev/null; then
        ip link set "$iface" up
        batctl if add "$iface" 2>/dev/null || true
    fi
done

ip link set bat0 up
EOF

    execute chmod +x "/usr/local/bin/myc3lium-triradio-start.sh"
    
    # Create stop script
    execute tee "/usr/local/bin/myc3lium-triradio-stop.sh" > /dev/null <<'EOF'
#!/bin/bash
# Tear down tri-radio mesh

for iface in lora0 wlan1 wlan0; do
    if ip link show "$iface" &>/dev/null; then
        batctl if del "$iface" 2>/dev/null || true
        ip link set "$iface" down
    fi
done

ip link set bat0 down
EOF

    execute chmod +x "/usr/local/bin/myc3lium-triradio-stop.sh"
    
    # Enable service
    execute systemctl daemon-reload
    execute systemctl enable myc3lium-triradio.service
    
    log_info "Systemd service created and enabled"
}

print_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  MYC3LIUM Tri-Radio Mesh Configuration Complete"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Configured Interfaces:"
    for iface in "${AVAILABLE_IFS[@]}"; do
        echo "  ✓ $iface"
    done
    echo ""
    echo "BATMAN master: $BAT_IF"
    echo "Mesh IP: $MESH_IP"
    echo ""
    echo "Useful commands:"
    echo "  batctl n        - Show mesh neighbors"
    echo "  batctl o        - Show mesh originators"
    echo "  batctl if       - Show BATMAN interfaces"
    echo "  batctl statistics - Show mesh statistics"
    echo ""
    echo "Test connectivity:"
    echo "  ping 192.168.42.1  (example mesh node)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

main() {
    log_info "MYC3LIUM Tri-Radio BATMAN-adv Setup Starting..."
    echo "Log file: $LOG_FILE"
    echo ""
    
    check_root
    detect_interfaces
    install_batman
    
    # Configure each available interface
    for iface in "${AVAILABLE_IFS[@]}"; do
        case "$iface" in
            "$LORA_IF")
                configure_lora_interface
                ;;
            "$HALOW_IF")
                configure_halow_interface
                ;;
            "$WIFI_IF")
                configure_wifi_interface
                ;;
        esac
    done
    
    configure_batman_master
    tune_batman_settings
    create_systemd_service
    
    print_summary
    
    log_info "Setup complete! Mesh network is operational."
}

main
