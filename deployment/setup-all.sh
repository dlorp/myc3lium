#!/bin/bash
# MYC3LIUM Master Setup Script
# Runs all setup scripts in correct order

set -e

echo "🍄 MYC3LIUM Complete Setup"
echo "=========================="
echo ""
echo "This will set up your MYC3LIUM mesh node with:"
echo "  - Base system configuration"
echo "  - LoRa interface (SX1262 HAT)"
echo "  - WiFi HaLow interface (HT-HC01P)"
echo "  - BATMAN-adv mesh networking"
echo "  - Reticulum network stack"
echo "  - Backend API"
echo "  - WebUI"
echo ""
echo "Estimated time: 15-20 minutes"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

START_TIME=$(date +%s)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_step() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
    echo "----------------------------------------"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

# ============================================================================
# Step 1: Base Setup
# ============================================================================

log_step "Step 1/6: Base System Setup"
if bash ./scripts/setup-pi4.sh; then
    log_success "Base setup complete"
else
    log_error "Base setup failed"
    exit 1
fi

# ============================================================================
# Step 2: LoRa Setup
# ============================================================================

log_step "Step 2/6: LoRa Interface Setup"
if bash ./scripts/setup-lora.sh; then
    log_success "LoRa setup complete"
else
    log_error "LoRa setup failed (continuing anyway...)"
fi

# ============================================================================
# Step 3: HaLow Setup
# ============================================================================

log_step "Step 3/6: WiFi HaLow Setup"
if bash ./scripts/setup-halow.sh; then
    log_success "HaLow setup complete"
else
    log_error "HaLow setup failed (continuing anyway...)"
fi

# ============================================================================
# Step 4: BATMAN Mesh Setup
# ============================================================================

log_step "Step 4/6: BATMAN-adv Mesh Setup"
if bash ./scripts/setup-batman.sh; then
    log_success "BATMAN mesh setup complete"
else
    log_error "BATMAN mesh setup failed"
    exit 1
fi

# ============================================================================
# Step 5: Deploy Reticulum Config & Backend
# ============================================================================

log_step "Step 5/6: Deploying Reticulum & Backend"

# Copy Reticulum config
echo "Copying Reticulum configuration..."
mkdir -p /home/myc3lium/.reticulum
cp "$SCRIPT_DIR/config/reticulum.conf" /home/myc3lium/.reticulum/config
chown -R myc3lium:myc3lium /home/myc3lium/.reticulum
log_success "Reticulum config deployed"

# Copy backend
echo "Copying backend bridge..."
mkdir -p /opt/myc3lium/backend
cp "$SCRIPT_DIR/backend/reticulum_bridge.py" /opt/myc3lium/backend/
chmod +x /opt/myc3lium/backend/reticulum_bridge.py
chown -R myc3lium:myc3lium /opt/myc3lium/backend
log_success "Backend deployed"

# ============================================================================
# Step 6: Deploy WebUI
# ============================================================================

log_step "Step 6/6: Deploying WebUI"
if bash ./scripts/deploy-webui.sh; then
    log_success "WebUI deployed"
else
    log_error "WebUI deployment failed"
    exit 1
fi

# ============================================================================
# Start Services
# ============================================================================

log_step "Starting Services"

echo "Starting Reticulum..."
systemctl enable reticulum.service
systemctl restart reticulum.service
sleep 2

echo "Starting Backend API..."
systemctl enable myc3lium-backend.service
systemctl restart myc3lium-backend.service
sleep 2

echo "Starting BATMAN mesh..."
systemctl enable batman-adv.service
systemctl restart batman-adv.service || echo "BATMAN start failed (may need reboot)"
sleep 2

echo "Starting Nginx..."
systemctl enable nginx
systemctl restart nginx

log_success "All services started"

# ============================================================================
# Run Tests
# ============================================================================

log_step "Running Integration Tests"
cd "$SCRIPT_DIR/tests"
if bash ./test-all.sh; then
    log_success "Tests passed"
else
    log_error "Some tests failed (review output above)"
fi

# ============================================================================
# Summary
# ============================================================================

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "=========================================="
echo -e "${GREEN}🍄 MYC3LIUM Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Time elapsed: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Your mesh node is now running!"
echo ""
echo -e "${GREEN}Access WebUI:${NC}"
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "  http://$IP_ADDR"
echo "  http://$(hostname).local"
echo ""
echo -e "${GREEN}API Documentation:${NC}"
echo "  http://$IP_ADDR:8000/docs"
echo ""
echo -e "${GREEN}System Status:${NC}"
echo "  Run: myc3lium-status"
echo ""
echo -e "${GREEN}Logs:${NC}"
echo "  journalctl -fu reticulum.service"
echo "  journalctl -fu myc3lium-backend.service"
echo "  tail -f /opt/myc3lium/logs/bridge.log"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "  1. Change default password: passwd myc3lium"
echo "  2. Backup identity: /home/myc3lium/.reticulum/storage/identities/"
echo "  3. Reboot recommended: sudo reboot"
echo ""
echo "For troubleshooting, see: DEPLOYMENT.md"
echo ""
echo "🍄 Welcome to the mycelium network!"
