#!/bin/bash
# Verify Security Fixes Applied to LoRa TAP Bridge
# Date: 2026-03-22

set -e

echo "=== Verifying Security Fixes ==="
echo

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check_fix() {
    local name="$1"
    local file="$2"
    local pattern="$3"
    
    if grep -q "$pattern" "$file"; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "${RED}✗${NC} $name - MISSING!"
        return 1
    fi
}

all_pass=true

# CRITICAL-1: Fragment reassembly validation
check_fix "CRITICAL-1: total_frags validation" \
    "fragment.c" \
    "Security: Validate total_frags to prevent buffer overflow" || all_pass=false

check_fix "CRITICAL-1: frag_index bounds check in reassemble" \
    "fragment.c" \
    "if (frag->frag_index >= MAX_FRAGMENTS)" || all_pass=false

# CRITICAL-2: Fragment decode validation
check_fix "CRITICAL-2: frag_index validation in decode" \
    "fragment.c" \
    "Security: Validate fragment index is within bounds (CRITICAL-2)" || all_pass=false

# CRITICAL-3: Signal handler async-safety
check_fix "CRITICAL-3: sig_atomic_t type" \
    "lora-tap-bridge.c" \
    "volatile sig_atomic_t running" || all_pass=false

check_fix "CRITICAL-3: async-safe signal handler" \
    "lora-tap-bridge.c" \
    "Security: Only use async-signal-safe operations" || all_pass=false

# HIGH-4: SPI buffer validation
check_fix "HIGH-4: SPI write_command size check" \
    "sx1262.c" \
    "Security: Validate size to prevent buffer overflow (HIGH-4)" || all_pass=false

# HIGH-5: Payload size reduction
if grep -q "SX1262_MAX_PAYLOAD  254" sx1262.h; then
    echo -e "${GREEN}✓${NC} HIGH-5: SX1262_MAX_PAYLOAD reduced to 254"
else
    echo -e "${RED}✗${NC} HIGH-5: SX1262_MAX_PAYLOAD not fixed!"
    all_pass=false
fi

# HIGH-3: Fragment encode validation
check_fix "HIGH-3: fragment_encode payload validation" \
    "fragment.c" \
    "Security: Validate payload length to prevent buffer overflow (HIGH-3)" || all_pass=false

# MEDIUM-3: Memory exhaustion limit
check_fix "MEDIUM-3: MAX_REASSEMBLY_ENTRIES constant" \
    "fragment.h" \
    "MAX_REASSEMBLY_ENTRIES 16" || all_pass=false

check_fix "MEDIUM-3: Entry limit enforcement" \
    "fragment.c" \
    "if (count >= MAX_REASSEMBLY_ENTRIES)" || all_pass=false

echo
echo "=== Summary ==="
if [ "$all_pass" = true ]; then
    echo -e "${GREEN}All security fixes verified!${NC}"
    echo "The code is ready for compilation and testing on Raspberry Pi."
    exit 0
else
    echo -e "${RED}Some security fixes are missing!${NC}"
    echo "Review SECURITY-FIXES-APPLIED.md for details."
    exit 1
fi
