#!/bin/bash
# MYC3LIUM Complete Integration Test
# Tests all components of the mesh network

set -e

echo "🧪 MYC3LIUM Complete Integration Test"
echo "======================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

PASS=0
FAIL=0
WARN=0

test_result() {
    if [ $1 -eq 0 ]; then
        log_info "$2"
        ((PASS++))
    else
        log_error "$2"
        ((FAIL++))
    fi
}

# ============================================================================
# Test 1: Base System
# ============================================================================

echo "Test 1: Base System"
echo "--------------------"

# Check if running on Pi 4
if grep -q "Raspberry Pi 4" /proc/cpuinfo 2>/dev/null; then
    test_result 0 "Running on Raspberry Pi 4"
else
    log_warn "Not running on Pi 4 (OK for testing)"
    ((WARN++))
fi

# Check user exists
if id -u myc3lium &>/dev/null; then
    test_result 0 "User 'myc3lium' exists"
else
    test_result 1 "User 'myc3lium' not found"
fi

# Check directories
if [ -d "/opt/myc3lium" ]; then
    test_result 0 "MYC3LIUM directory exists"
else
    test_result 1 "MYC3LIUM directory missing"
fi

# Check Python packages
if python3 -c "import RNS" 2>/dev/null; then
    test_result 0 "Reticulum Python package installed"
else
    test_result 1 "Reticulum package not found"
fi

if python3 -c "import LXMF" 2>/dev/null; then
    test_result 0 "LXMF Python package installed"
else
    test_result 1 "LXMF package not found"
fi

if python3 -c "import fastapi" 2>/dev/null; then
    test_result 0 "FastAPI package installed"
else
    test_result 1 "FastAPI package not found"
fi

echo ""

# ============================================================================
# Test 2: LoRa Interface
# ============================================================================

echo "Test 2: LoRa Interface (SX1262)"
echo "--------------------------------"

# Check SPI device
if [ -e /dev/spidev0.0 ]; then
    test_result 0 "SPI device exists"
else
    test_result 1 "SPI device not found"
fi

# Check SPI module
if lsmod | grep -q spi_bcm2835; then
    test_result 0 "SPI kernel module loaded"
else
    test_result 1 "SPI module not loaded"
fi

# Run LoRa test if available
if [ -f /opt/myc3lium/test-lora.py ]; then
    if sudo -u myc3lium python3 /opt/myc3lium/test-lora.py &>/dev/null; then
        test_result 0 "LoRa hardware test passed"
    else
        log_warn "LoRa hardware test failed (HAT may not be connected)"
        ((WARN++))
    fi
fi

echo ""

# ============================================================================
# Test 3: WiFi HaLow
# ============================================================================

echo "Test 3: WiFi HaLow (HT-HC01P)"
echo "------------------------------"

# Check for HaLow config
if [ -f /opt/myc3lium/halow-config.conf ]; then
    test_result 0 "HaLow configuration exists"
    source /opt/myc3lium/halow-config.conf
    
    # Check interface
    if ip link show "$HALOW_IFACE" &>/dev/null; then
        test_result 0 "HaLow interface detected: $HALOW_IFACE"
    else
        log_warn "HaLow interface not detected (driver may be needed)"
        ((WARN++))
    fi
else
    test_result 1 "HaLow configuration not found"
fi

echo ""

# ============================================================================
# Test 4: BATMAN-adv Mesh
# ============================================================================

echo "Test 4: BATMAN-adv Mesh"
echo "-----------------------"

# Check batman-adv module
if lsmod | grep -q batman_adv; then
    test_result 0 "BATMAN-adv module loaded"
else
    test_result 1 "BATMAN-adv module not loaded"
fi

# Check batctl
if command -v batctl &>/dev/null; then
    test_result 0 "batctl installed"
else
    test_result 1 "batctl not found"
fi

# Check bat0 interface
if ip link show bat0 &>/dev/null; then
    test_result 0 "bat0 interface exists"
    
    # Check if mesh is active
    if batctl o 2>/dev/null | grep -q "wlan0"; then
        test_result 0 "BATMAN mesh is active"
    else
        log_warn "BATMAN mesh active but no neighbors"
        ((WARN++))
    fi
else
    log_warn "bat0 interface not found (mesh not started)"
    ((WARN++))
fi

echo ""

# ============================================================================
# Test 5: Reticulum Services
# ============================================================================

echo "Test 5: Reticulum Services"
echo "--------------------------"

# Check Reticulum config
if [ -f /home/myc3lium/.reticulum/config ]; then
    test_result 0 "Reticulum config exists"
else
    test_result 1 "Reticulum config not found"
fi

# Check Reticulum service
if systemctl is-active --quiet reticulum.service 2>/dev/null; then
    test_result 0 "Reticulum service running"
else
    log_warn "Reticulum service not running"
    ((WARN++))
fi

# Check if rnsd is running
if pgrep -f "rnsd" >/dev/null; then
    test_result 0 "rnsd process active"
else
    log_warn "rnsd not running"
    ((WARN++))
fi

echo ""

# ============================================================================
# Test 6: Backend API
# ============================================================================

echo "Test 6: Backend API"
echo "-------------------"

# Check backend service
if systemctl is-active --quiet myc3lium-backend.service 2>/dev/null; then
    test_result 0 "Backend service running"
else
    log_warn "Backend service not running"
    ((WARN++))
fi

# Check if API is responding
if curl -s http://localhost:8000/health &>/dev/null; then
    test_result 0 "Backend API responding"
    
    # Get API health
    HEALTH=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH" | grep -q '"status":"healthy"'; then
        test_result 0 "Backend API healthy"
    else
        test_result 1 "Backend API unhealthy"
    fi
else
    test_result 1 "Backend API not responding"
fi

echo ""

# ============================================================================
# Test 7: WebUI
# ============================================================================

echo "Test 7: WebUI (Nginx)"
echo "---------------------"

# Check nginx service
if systemctl is-active --quiet nginx.service; then
    test_result 0 "Nginx service running"
else
    test_result 1 "Nginx not running"
fi

# Check if WebUI is accessible
if curl -s http://localhost/ | grep -q "MYC3LIUM"; then
    test_result 0 "WebUI accessible"
else
    test_result 1 "WebUI not accessible"
fi

# Check nginx config
if nginx -t &>/dev/null; then
    test_result 0 "Nginx configuration valid"
else
    test_result 1 "Nginx configuration invalid"
fi

echo ""

# ============================================================================
# Test 8: Network Connectivity
# ============================================================================

echo "Test 8: Network Connectivity"
echo "----------------------------"

# Check if we can reach the internet (for time sync, etc)
if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
    test_result 0 "Internet connectivity"
else
    log_warn "No internet connectivity (OK for isolated mesh)"
    ((WARN++))
fi

# Check local network
if ip route | grep -q default; then
    test_result 0 "Default route exists"
else
    log_warn "No default route"
    ((WARN++))
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "${GREEN}Passed:${NC}  $PASS"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo -e "${RED}Failed:${NC}  $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    if [ $WARN -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
        echo "🍄 MYC3LIUM is fully operational"
        echo ""
        echo "Access WebUI: http://$(hostname -I | awk '{print $1}')"
        echo "System status: myc3lium-status"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Tests passed with warnings${NC}"
        echo ""
        echo "Some components may need configuration or hardware may not be connected."
        echo "Review warnings above."
        exit 0
    fi
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please review failed tests and fix issues before deployment."
    echo ""
    echo "Common fixes:"
    echo "  - Run setup scripts: setup-*.sh"
    echo "  - Check hardware connections"
    echo "  - Review logs: journalctl -u reticulum.service"
    echo "  - Restart services: systemctl restart myc3lium-backend reticulum"
    exit 1
fi
