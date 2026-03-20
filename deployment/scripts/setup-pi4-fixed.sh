#!/bin/bash
# MYC3LIUM Pi 4 Base Setup Script - Improved
# Idempotent, safer, with better error handling

set -eo pipefail

# ============================================================================
# Configuration
# ============================================================================

INSTALL_DIR="/opt/myc3lium"
USER="myc3lium"
LOG_FILE="/tmp/myc3lium-install.log"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }
log_step() { echo -e "${BLUE}▶${NC} $1" | tee -a "$LOG_FILE"; }

# ============================================================================
# Checks
# ============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_platform() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_warn "Not running on Raspberry Pi - some features may not work"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]] || exit 1
    fi
}

find_boot_config() {
    # Handle different Pi boot config locations
    if [ -f /boot/firmware/config.txt ]; then
        echo "/boot/firmware/config.txt"
    elif [ -f /boot/config.txt ]; then
        echo "/boot/config.txt"
    else
        log_error "Could not find boot config file"
        return 1
    fi
}

# ============================================================================
# Package Installation (with retries)
# ============================================================================

install_packages() {
    local packages=("$@")
    local failed=()
    
    log_step "Installing packages..."
    
    # Update first
    apt-get update || log_warn "apt-get update failed, continuing..."
    
    for pkg in "${packages[@]}"; do
        if dpkg -l | grep -q "^ii  $pkg "; then
            log_info "$pkg already installed"
        else
            if apt-get install -y "$pkg" 2>>"$LOG_FILE"; then
                log_info "Installed $pkg"
            else
                log_warn "Failed to install $pkg (might not exist on this system)"
                failed+=("$pkg")
            fi
        fi
    done
    
    if [ ${#failed[@]} -gt 0 ]; then
        log_warn "Failed packages: ${failed[*]}"
        log_warn "Continuing anyway - some features may not work"
    fi
}

# ============================================================================
# Main Installation
# ============================================================================

main() {
    log_info "MYC3LIUM Pi 4 Setup Starting..."
    log_info "Log file: $LOG_FILE"
    
    check_root
    check_platform
    
    # Essential packages only
    install_packages \
        python3 python3-pip python3-venv \
        git curl wget \
        build-essential cmake \
        network-manager \
        wireless-tools \
        nginx \
        jq \
        screen \
        i2c-tools
    
    # Optional packages (won't fail if missing)
    install_packages \
        spi-tools \
        gpsd gpsd-clients \
        batctl alfred \
        raspberrypi-kernel-headers \
        linux-headers-$(uname -r) || true
    
    # Enable SPI/I2C
    log_step "Enabling hardware interfaces..."
    BOOT_CONFIG=$(find_boot_config)
    if [ -n "$BOOT_CONFIG" ]; then
        if ! grep -q "^dtparam=spi=on" "$BOOT_CONFIG"; then
            echo "dtparam=spi=on" >> "$BOOT_CONFIG"
            log_info "Enabled SPI in $BOOT_CONFIG"
        fi
        if ! grep -q "^dtparam=i2c_arm=on" "$BOOT_CONFIG"; then
            echo "dtparam=i2c_arm=on" >> "$BOOT_CONFIG"
            log_info "Enabled I2C in $BOOT_CONFIG"
        fi
    fi
    
    # Load modules (skip if already loaded)
    log_step "Loading kernel modules..."
    modprobe spi_bcm2835 2>/dev/null || log_warn "spi_bcm2835 module not available"
    modprobe i2c-dev 2>/dev/null || log_warn "i2c-dev module not available"
    
    # Create modules config (idempotent)
    if [ ! -f /etc/modules-load.d/myc3lium.conf ]; then
        cat > /etc/modules-load.d/myc3lium.conf <<EOF
spi_bcm2835
i2c-dev
EOF
        log_info "Created module load config"
    fi
    
    # Python packages (use venv to avoid system conflicts)
    log_step "Installing Python packages in venv..."
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        python3 -m venv "$INSTALL_DIR/venv"
    fi
    
    source "$INSTALL_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install \
        rns \
        lxmf \
        fastapi \
        uvicorn \
        websockets \
        pydantic \
        pyserial \
        gpiozero || log_warn "Some Python packages failed"
    deactivate
    
    # Create user (idempotent)
    if ! id -u "$USER" &>/dev/null; then
        log_step "Creating $USER user..."
        useradd -m -s /bin/bash -G dialout,netdev "$USER" || true
        # Try to add to gpio/spi/i2c groups if they exist
        for group in gpio spi i2c; do
            if getent group "$group" >/dev/null; then
                usermod -a -G "$group" "$USER"
            fi
        done
        echo "$USER:$USER" | chpasswd
    else
        log_info "User $USER already exists"
    fi
    
    # Create directory structure (idempotent)
    log_step "Creating directory structure..."
    mkdir -p "$INSTALL_DIR"/{backend,frontend,logs,data}
    mkdir -p "/home/$USER/.reticulum"
    
    chown -R "$USER:$USER" "$INSTALL_DIR"
    chown -R "$USER:$USER" "/home/$USER/.reticulum"
    
    # Verification
    log_step "Verification..."
    if [ -d "$INSTALL_DIR" ]; then
        log_info "✓ Install directory created"
    fi
    if id "$USER" &>/dev/null; then
        log_info "✓ User created"
    fi
    if [ -d "$INSTALL_DIR/venv" ]; then
        log_info "✓ Python venv created"
    fi
    
    log_info "Base setup complete!"
    log_warn "Reboot required for hardware changes to take effect"
}

main "$@"
