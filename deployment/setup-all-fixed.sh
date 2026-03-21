#!/bin/bash
# MYC3LIUM Master Setup Script - Improved
# Safer, with better error handling and rollback

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/myc3lium-install-master.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }
log_step() { echo -e "${BLUE}▶${NC} $1" | tee -a "$LOG_FILE"; }
log_success() { echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"; }

run_step() {
    local name="$1"
    local script="$2"
    local required="$3"  # "required" or "optional"
    
    log_step "$name"
    
    if [ ! -f "$script" ]; then
        if [ "$required" = "required" ]; then
            log_error "Script not found: $script"
            return 1
        else
            log_warn "Optional script not found: $script (skipping)"
            return 0
        fi
    fi
    
    if bash "$script"; then
        log_success "$name complete"
        return 0
    else
        if [ "$required" = "required" ]; then
            log_error "$name FAILED (required)"
            return 1
        else
            log_warn "$name failed (optional, continuing...)"
            return 0
        fi
    fi
}

main() {
    echo "🍄 MYC3LIUM Complete Setup (Improved)"
    echo "======================================"
    echo ""
    echo "This will set up your MYC3LIUM mesh node with:"
    echo "  - Base system configuration"
    echo "  - LoRa interface (if HAT detected)"
    echo "  - WiFi HaLow interface (if adapter detected)"
    echo "  - BATMAN-adv mesh networking"
    echo ""
    echo "All output logged to: $LOG_FILE"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
    
    if [[ $EUID -ne 0 ]]; then
       log_error "This script must be run as root (use sudo)"
       exit 1
    fi
    
    cd "$SCRIPT_DIR"
    START_TIME=$(date +%s)
    
    # Track which steps succeeded
    declare -A completed
    
    # Step 1: Base (REQUIRED)
    if run_step "Base System Setup" "scripts/setup-pi4-fixed.sh" "required"; then
        completed[base]=1
    else
        log_error "Base setup failed - cannot continue"
        exit 1
    fi
    
    # Step 2: LoRa (OPTIONAL - hardware may not be present)
    if run_step "LoRa Interface" "scripts/setup-lora-fixed.sh" "optional"; then
        completed[lora]=1
    fi
    
    # Step 3: HaLow (OPTIONAL - hardware may not be present)
    if run_step "HaLow Interface" "scripts/setup-halow-fixed.sh" "optional"; then
        completed[halow]=1
    fi
    
    # Step 4: BATMAN (OPTIONAL - may fail without WiFi)
    if run_step "BATMAN-adv Mesh" "scripts/setup-batman-fixed.sh" "optional"; then
        completed[batman]=1
    fi
    
    # Summary
    END_TIME=$(date +%s)
    ELAPSED=$(( END_TIME - START_TIME ))
    
    echo ""
    echo "=========================================="
    log_info "Setup completed in ${ELAPSED}s"
    echo ""
    
    echo "Completed steps:"
    for step in base lora halow batman; do
        if [ "${completed[$step]}" = "1" ]; then
            log_success "$step"
        else
            log_warn "$step (skipped or failed)"
        fi
    done
    
    echo ""
    log_info "Next steps:"
    log_info "  1. Review logs: cat $LOG_FILE"
    log_info "  2. Reboot to apply changes: sudo reboot"
    log_info "  3. After reboot, test components:"
    log_info "     - LoRa: /opt/myc3lium/test-lora.sh"
    log_info "     - HaLow: /opt/myc3lium/test-halow.sh"
    log_info "     - BATMAN: /opt/myc3lium/test-batman.sh"
    echo ""
    
    if [ "${completed[base]}" = "1" ]; then
        log_success "Base setup successful - system ready for testing"
    fi
}

main "$@"
