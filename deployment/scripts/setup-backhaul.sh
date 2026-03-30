#!/usr/bin/env bash
# setup-backhaul.sh - Configure USB WiFi adapter for backhaul/AP mode
#
# This script:
# 1. Auto-detects USB WiFi adapters (excludes wlan0 mesh interface)
# 2. Installs dnsmasq, iptables-persistent, hostapd
# 3. Creates hostapd config template
# 4. Excludes backhaul interface from NetworkManager
# 5. Enables IP forwarding
#
# Run on Pi as root: sudo bash setup-backhaul.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[BACKHAUL]${NC} $*"; }
warn() { echo -e "${YELLOW}[BACKHAUL]${NC} $*"; }
err() { echo -e "${RED}[BACKHAUL]${NC} $*" >&2; }

if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root (sudo)"
    exit 1
fi

# ============================================================================
# 1. Detect USB WiFi adapters
# ============================================================================
log "Scanning for USB WiFi adapters..."

BACKHAUL_IFACE=""
for iface in /sys/class/net/*/wireless; do
    [ -d "$iface" ] || continue
    iface_name=$(basename "$(dirname "$iface")")

    # Skip mesh interface
    [ "$iface_name" = "wlan0" ] && continue

    # Check if USB-backed
    device_path=$(readlink -f "/sys/class/net/$iface_name/device" 2>/dev/null || true)
    if echo "$device_path" | grep -q "usb"; then
        BACKHAUL_IFACE="$iface_name"
        driver=$(basename "$(readlink -f "/sys/class/net/$iface_name/device/driver" 2>/dev/null)" 2>/dev/null || echo "unknown")
        mac=$(cat "/sys/class/net/$iface_name/address" 2>/dev/null || echo "unknown")
        log "Found USB WiFi: $BACKHAUL_IFACE (driver: $driver, MAC: $mac)"
        break
    fi
done

if [ -z "$BACKHAUL_IFACE" ]; then
    warn "No USB WiFi adapter detected. Script will install packages but skip interface config."
    warn "Plug in a USB WiFi adapter and re-run, or configure via P600 web UI."
fi

# ============================================================================
# 2. Install required packages
# ============================================================================
log "Installing backhaul packages..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    hostapd \
    dnsmasq \
    iptables-persistent \
    bridge-utils \
    isc-dhcp-client

# Stop services until configured
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true

log "Packages installed"

# ============================================================================
# 3. Enable IP forwarding
# ============================================================================
log "Enabling IP forwarding..."
if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi
sysctl -w net.ipv4.ip_forward=1 > /dev/null

# ============================================================================
# 4. Exclude backhaul interface from NetworkManager
# ============================================================================
if [ -n "$BACKHAUL_IFACE" ]; then
    log "Excluding $BACKHAUL_IFACE from NetworkManager..."

    NM_CONF="/etc/NetworkManager/conf.d/99-myc3lium-backhaul.conf"
    mkdir -p "$(dirname "$NM_CONF")"
    cat > "$NM_CONF" <<EOF
# MYC3LIUM: Exclude USB WiFi backhaul interface from NetworkManager
# This interface is managed by myc3lium backhaul service (hostapd/wpa_supplicant)
[keyfile]
unmanaged-devices=interface-name:${BACKHAUL_IFACE}
EOF

    # Reload NetworkManager if running
    systemctl reload NetworkManager 2>/dev/null || true
    log "NetworkManager configured to ignore $BACKHAUL_IFACE"
fi

# ============================================================================
# 5. Create hostapd config template
# ============================================================================
log "Creating hostapd config template..."
HOSTAPD_CONF="/etc/hostapd/hostapd.conf"
mkdir -p "$(dirname "$HOSTAPD_CONF")"

if [ ! -f "$HOSTAPD_CONF" ]; then
    cat > "$HOSTAPD_CONF" <<EOF
# MYC3LIUM AP Mode - Template
# This file is overwritten by the backhaul service when AP mode is activated.
# Configure via P600 web UI or API.
# DO NOT start hostapd manually - passphrase is set by backhaul service.

interface=${BACKHAUL_IFACE:-wlan1}
bridge=br0
ssid=myc3_m3sh
hw_mode=g
channel=1
wpa=2
# wpa_passphrase is set by backhaul service — do not start hostapd manually
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
ieee80211n=1
wmm_enabled=0
country_code=US
EOF
    chmod 600 "$HOSTAPD_CONF"
    log "Created $HOSTAPD_CONF (template)"
else
    warn "$HOSTAPD_CONF already exists, not overwriting"
fi

# Point hostapd daemon to our config
if [ -f /etc/default/hostapd ]; then
    sed -i 's|^#\?DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
fi

# ============================================================================
# 6. Create dnsmasq config template
# ============================================================================
log "Creating dnsmasq config template..."
DNSMASQ_CONF="/etc/dnsmasq.d/myc3lium-ap.conf"
mkdir -p "$(dirname "$DNSMASQ_CONF")"

if [ ! -f "$DNSMASQ_CONF" ]; then
    cat > "$DNSMASQ_CONF" <<EOF
# MYC3LIUM AP Mode DHCP - Template
# This file is overwritten by the backhaul service when AP mode is activated.

interface=br0
bind-dynamic
dhcp-range=10.99.0.10,10.99.0.200,255.255.255.0,24h
dhcp-option=3,10.99.0.1
dhcp-option=6,10.99.0.1
server=8.8.8.8
server=1.1.1.1
address=/$(hostname).local/10.99.0.1
EOF
    log "Created $DNSMASQ_CONF (template)"
else
    warn "$DNSMASQ_CONF already exists, not overwriting"
fi

# ============================================================================
# 7. Install myc3lium-netctl privileged helper
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETCTL_SRC="${SCRIPT_DIR}/myc3lium-netctl"

if [ -f "$NETCTL_SRC" ]; then
    log "Installing myc3lium-netctl helper..."
    cp "$NETCTL_SRC" /usr/local/bin/myc3lium-netctl
    chmod 755 /usr/local/bin/myc3lium-netctl
    chown root:root /usr/local/bin/myc3lium-netctl
    log "Installed /usr/local/bin/myc3lium-netctl"
else
    warn "myc3lium-netctl not found at $NETCTL_SRC — copy it manually to /usr/local/bin/"
fi

# Sudoers entry: allow myc3 user to run netctl without password
SUDOERS_FILE="/etc/sudoers.d/myc3lium"
if [ ! -f "$SUDOERS_FILE" ] || ! grep -q myc3lium-netctl "$SUDOERS_FILE" 2>/dev/null; then
    echo 'myc3 ALL=(ALL) NOPASSWD: /usr/local/bin/myc3lium-netctl' > "$SUDOERS_FILE"
    chmod 440 "$SUDOERS_FILE"
    log "Created sudoers entry for myc3lium-netctl"
else
    log "Sudoers entry already exists"
fi

# ============================================================================
# 8. Install systemd override for backhaul operations
# ============================================================================
OVERRIDE_DIR="/etc/systemd/system/myc3lium.service.d"
OVERRIDE_SRC="${SCRIPT_DIR}/../systemd/myc3lium-backhaul.conf"

if [ -f "$OVERRIDE_SRC" ]; then
    log "Installing systemd backhaul override..."
    mkdir -p "$OVERRIDE_DIR"
    cp "$OVERRIDE_SRC" "${OVERRIDE_DIR}/backhaul.conf"
    systemctl daemon-reload
    log "Installed ${OVERRIDE_DIR}/backhaul.conf"
else
    warn "myc3lium-backhaul.conf not found at $OVERRIDE_SRC — copy it manually"
fi

# Create state directory
mkdir -p /opt/myc3lium/run
chown myc3:myc3 /opt/myc3lium/run
log "State directory /opt/myc3lium/run ready"

# ============================================================================
# 9. Summary
# ============================================================================
echo ""
log "===== Backhaul setup complete ====="
log "Packages: hostapd, dnsmasq, iptables-persistent, bridge-utils"
log "IP forwarding: enabled"
log "myc3lium-netctl: $(which myc3lium-netctl 2>/dev/null || echo 'NOT INSTALLED')"
log "Sudoers: $(test -f /etc/sudoers.d/myc3lium && echo 'configured' || echo 'NOT CONFIGURED')"
log "Systemd override: $(test -f /etc/systemd/system/myc3lium.service.d/backhaul.conf && echo 'installed' || echo 'NOT INSTALLED')"
if [ -n "$BACKHAUL_IFACE" ]; then
    log "USB WiFi adapter: $BACKHAUL_IFACE"
    log "NetworkManager: $BACKHAUL_IFACE excluded"
else
    warn "No USB WiFi adapter found - plug one in and configure via P600"
fi
log "Services hostapd/dnsmasq are stopped until activated via P600 or API"
log ""
log "Next: Restart myc3lium service, then configure via P600 or API"
log "  sudo systemctl restart myc3lium"
