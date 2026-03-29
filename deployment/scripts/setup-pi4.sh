#!/bin/bash
# MYC3LIUM Pi 4 Base Setup Script
# Sets up Raspberry Pi 4 with all dependencies and network interfaces

set -e  # Exit on error

echo "🍄 MYC3LIUM Pi 4 Setup - Starting..."

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if running on Pi 4
if ! grep -q "Raspberry Pi 4" /proc/cpuinfo 2>/dev/null; then
    log_warn "Not detected as Raspberry Pi 4 - proceeding anyway"
fi

# Update system
log_info "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install essential dependencies
log_info "Installing essential packages..."
apt-get install -y \
    python3 python3-pip python3-venv \
    nodejs npm \
    git curl wget \
    build-essential cmake \
    dkms \
    linux-headers-$(uname -r) \
    raspberrypi-kernel-headers \
    network-manager \
    wireless-tools \
    rfkill \
    bluez bluez-tools \
    hostapd \
    dnsmasq \
    iptables-persistent \
    bridge-utils \
    batctl alfred \
    nginx \
    ufw \
    jq \
    screen tmux \
    i2c-tools \
    spi-tools \
    gpsd gpsd-clients \
    libgps-dev

# Enable SPI and I2C interfaces
log_info "Enabling SPI and I2C interfaces..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" >> /boot/config.txt
fi
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" >> /boot/config.txt
fi

# Load kernel modules
log_info "Configuring kernel modules..."
modprobe spi_bcm2835
modprobe i2c-dev

# Add modules to load at boot
cat > /etc/modules-load.d/myc3lium.conf <<EOF
spi_bcm2835
i2c-dev
EOF

# Install Python packages
log_info "Installing Python packages..."
pip3 install --upgrade pip
pip3 install \
    rns \
    lxmf \
    nomadnet \
    fastapi \
    uvicorn \
    websockets \
    pydantic \
    pyserial \
    gpiozero \
    smbus2 \
    adafruit-circuitpython-gps \
    meshtastic \
    protobuf \
    pypubsub

# Create MYC3LIUM user if doesn't exist
if ! id -u myc3lium &>/dev/null; then
    log_info "Creating myc3lium user..."
    useradd -m -s /bin/bash -G gpio,spi,i2c,dialout,netdev myc3lium
    echo "myc3lium:myc3lium" | chpasswd
    # Add to sudoers
    echo "myc3lium ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/myc3lium
fi

# Create directory structure
log_info "Creating MYC3LIUM directory structure..."
mkdir -p /opt/myc3lium/{backend,frontend,logs,data,config}
mkdir -p /home/myc3lium/.reticulum
mkdir -p /home/myc3lium/.nomadnet

# Set permissions
chown -R myc3lium:myc3lium /opt/myc3lium
chown -R myc3lium:myc3lium /home/myc3lium/.reticulum
chown -R myc3lium:myc3lium /home/myc3lium/.nomadnet

# Configure network interfaces
log_info "Configuring network interfaces..."
cat > /etc/network/interfaces.d/myc3lium <<EOF
# LoRa interface (managed by Reticulum)
# Interface: /dev/spidev0.0

# HaLow interface (USB)
allow-hotplug wlan1
iface wlan1 inet dhcp

# WiFi mesh interface (BATMAN-adv)
allow-hotplug wlan0
iface wlan0 inet manual
    pre-up ifconfig wlan0 mtu 1532
    pre-up iwconfig wlan0 mode ad-hoc
    pre-up iwconfig wlan0 essid myc3lium-mesh
    pre-up iwconfig wlan0 ap 02:12:34:56:78:9A
    pre-up iwconfig wlan0 channel 11
EOF

# Disable default DHCP on wlan0 (we'll use BATMAN)
cat > /etc/NetworkManager/conf.d/myc3lium-mesh.conf <<EOF
[keyfile]
unmanaged-devices=interface-name:wlan0;interface-name:bat0
EOF

# Configure firewall
log_info "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 4965/udp  # Reticulum default
ufw allow 4242/tcp  # Nomadnet

# Configure GPS (if Waveshare HAT is connected)
log_info "Configuring GPS service..."
cat > /etc/default/gpsd <<EOF
START_DAEMON="true"
USBAUTO="true"
DEVICES="/dev/ttyAMA0 /dev/ttyUSB0"
GPSD_OPTIONS="-n"
EOF

systemctl enable gpsd
systemctl restart gpsd || log_warn "GPSD not started (GPS may not be connected)"

# Create systemd service for Reticulum
log_info "Creating Reticulum systemd service..."
cat > /etc/systemd/system/reticulum.service <<EOF
[Unit]
Description=Reticulum Network Stack
After=network.target

[Service]
Type=simple
User=myc3lium
WorkingDirectory=/home/myc3lium
ExecStart=/usr/local/bin/rnsd --config /home/myc3lium/.reticulum/config
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for MYC3LIUM backend
log_info "Creating MYC3LIUM backend service..."
cat > /etc/systemd/system/myc3lium-backend.service <<EOF
[Unit]
Description=MYC3LIUM Backend API
After=network.target reticulum.service
Requires=reticulum.service

[Service]
Type=simple
User=myc3lium
WorkingDirectory=/opt/myc3lium/backend
ExecStart=/usr/bin/python3 /opt/myc3lium/backend/reticulum_bridge.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Filesystem access
ReadWritePaths=/opt/myc3lium/backend /opt/myc3lium/config /opt/myc3lium/logs

# Device access for serial radios
DeviceAllow=char-ttyUSB rw

# Resource limits
LimitNOFILE=4096
MemoryMax=512M

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Configure automatic updates (optional - can be disabled)
log_info "Configuring automatic security updates..."
apt-get install -y unattended-upgrades
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
};
Unattended-Upgrade::Automatic-Reboot "false";
EOF

# Set timezone
log_info "Setting timezone to UTC..."
timedatectl set-timezone UTC

# Configure hostname
log_info "Setting hostname..."
SERIAL=$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2 | tail -c 9)
HOSTNAME="myc3lium-${SERIAL}"
hostnamectl set-hostname "$HOSTNAME"

# Add to /etc/hosts
if ! grep -q "$HOSTNAME" /etc/hosts; then
    echo "127.0.1.1    $HOSTNAME" >> /etc/hosts
fi

# Performance optimizations
log_info "Applying performance optimizations..."
cat >> /boot/config.txt <<EOF

# MYC3LIUM Performance Settings
# Increase GPU memory for touchscreen
gpu_mem=128

# Disable unused features
dtoverlay=disable-bt
dtoverlay=disable-wifi-power-management

# Enable hardware watchdog
dtparam=watchdog=on
EOF

# Install watchdog
apt-get install -y watchdog
systemctl enable watchdog

# Create status check script
log_info "Creating system status script..."
cat > /usr/local/bin/myc3lium-status <<'EOF'
#!/bin/bash
echo "🍄 MYC3LIUM System Status"
echo "========================"
echo ""
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo "Temperature: $(vcgencmd measure_temp)"
echo ""
echo "Network Interfaces:"
ip -br addr | grep -E "wlan|bat|eth"
echo ""
echo "Services:"
systemctl is-active reticulum.service && echo "✓ Reticulum: Running" || echo "✗ Reticulum: Stopped"
systemctl is-active myc3lium-backend.service && echo "✓ Backend: Running" || echo "✗ Backend: Stopped"
systemctl is-active nginx.service && echo "✓ Nginx: Running" || echo "✗ Nginx: Stopped"
systemctl is-active batman-adv.service && echo "✓ BATMAN: Running" || echo "✗ BATMAN: Stopped"
echo ""
echo "Storage:"
df -h / | tail -n 1
echo ""
echo "Memory:"
free -h | grep Mem
EOF

chmod +x /usr/local/bin/myc3lium-status

# Create quick commands in myc3lium user profile
cat >> /home/myc3lium/.bashrc <<'EOF'

# MYC3LIUM Quick Commands
alias myc-status='myc3lium-status'
alias myc-logs='journalctl -fu myc3lium-backend.service'
alias myc-restart='sudo systemctl restart reticulum.service myc3lium-backend.service'
alias myc-backend='cd /opt/myc3lium/backend'
alias myc-config='cd /home/myc3lium/.reticulum'

echo "🍄 MYC3LIUM Node Ready"
echo "Type 'myc-status' for system status"
EOF

chown myc3lium:myc3lium /home/myc3lium/.bashrc

log_info "✅ Base setup complete!"
log_info ""
log_info "Next steps:"
log_info "  1. Run setup-lora.sh to configure LoRa HAT"
log_info "  2. Run setup-halow.sh to configure WiFi HaLow"
log_info "  3. Run setup-batman.sh to configure mesh networking"
log_info "  4. Copy Reticulum config to /home/myc3lium/.reticulum/config"
log_info "  5. Run deploy-webui.sh to set up the web interface"
log_info ""
log_info "⚠️  Reboot required to apply all changes!"
log_info "    Run: sudo reboot"
