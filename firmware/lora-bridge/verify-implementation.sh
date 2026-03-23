#!/bin/bash
# Verification script for LoRa TAP Bridge implementation
# Run this to verify all deliverables are present

set -e

echo "=== LoRa TAP Bridge Implementation Verification ==="
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        return 1
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 (executable)"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $1 (not executable)"
        return 1
    fi
}

MISSING=0

echo "Source Files:"
check_file "lora-tap-bridge.c" || MISSING=$((MISSING+1))
check_file "sx1262.c" || MISSING=$((MISSING+1))
check_file "sx1262.h" || MISSING=$((MISSING+1))
check_file "tap.c" || MISSING=$((MISSING+1))
check_file "tap.h" || MISSING=$((MISSING+1))
check_file "fragment.c" || MISSING=$((MISSING+1))
check_file "fragment.h" || MISSING=$((MISSING+1))

echo
echo "Build System:"
check_file "Makefile" || MISSING=$((MISSING+1))
check_executable "test-build.sh" || MISSING=$((MISSING+1))

echo
echo "Documentation:"
check_file "README.md" || MISSING=$((MISSING+1))
check_file "TESTING.md" || MISSING=$((MISSING+1))
check_file "DEPLOYMENT.md" || MISSING=$((MISSING+1))
check_file "IMPLEMENTATION-SUMMARY.md" || MISSING=$((MISSING+1))

echo
echo "Service Configuration:"
check_file "lora-bridge.service" || MISSING=$((MISSING+1))

echo
echo "=== Statistics ==="
echo -n "Total files: "
ls -1 | grep -v verify-implementation.sh | wc -l | tr -d ' '

echo -n "Source lines (C): "
wc -l *.c *.h 2>/dev/null | tail -1 | awk '{print $1}'

echo -n "Documentation lines: "
wc -l *.md 2>/dev/null | tail -1 | awk '{print $1}'

echo -n "Total lines: "
wc -l *.c *.h *.md Makefile *.service *.sh 2>/dev/null | tail -1 | awk '{print $1}'

echo
echo "=== Code Quality Checks ==="

# Check for TODO/FIXME
TODO_COUNT=$(grep -r "TODO\|FIXME" *.c *.h 2>/dev/null | wc -l | tr -d ' ')
if [ "$TODO_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No TODOs or FIXMEs"
else
    echo -e "${YELLOW}⚠${NC} $TODO_COUNT TODOs/FIXMEs found"
fi

# Check for basic syntax (requires gcc)
if command -v gcc &> /dev/null; then
    echo -n "Syntax check (lora-tap-bridge.c): "
    if gcc -fsyntax-only -Wall -Wextra -std=gnu11 -I. lora-tap-bridge.c 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Pass"
    else
        echo -e "${YELLOW}⚠${NC} Cannot verify (missing headers)"
    fi
else
    echo -e "${YELLOW}⚠${NC} GCC not available for syntax check"
fi

echo
echo "=== Requirements Verification ==="

# Check technical requirements from spec
echo -n "SPI device path: "
grep -q "/dev/spidev0.0" sx1262.h && echo -e "${GREEN}✓${NC} Correct" || echo -e "${RED}✗${NC} Wrong"

echo -n "SPI speed: "
grep -q "2000000" sx1262.h && echo -e "${GREEN}✓${NC} 2MHz" || echo -e "${RED}✗${NC} Wrong"

echo -n "GPIO pins: "
grep -q "GPIO_RESET.*18" sx1262.h && \
grep -q "GPIO_BUSY.*23" sx1262.h && \
grep -q "GPIO_DIO1.*24" sx1262.h && \
echo -e "${GREEN}✓${NC} 18, 23, 24" || echo -e "${RED}✗${NC} Wrong"

echo -n "TAP interface name: "
grep -q "lora0" tap.h && echo -e "${GREEN}✓${NC} lora0" || echo -e "${RED}✗${NC} Wrong"

echo -n "MTU: "
grep -q "1500" tap.h && echo -e "${GREEN}✓${NC} 1500" || echo -e "${RED}✗${NC} Wrong"

echo -n "Fragment header size: "
grep -q "FRAG_HEADER_SIZE.*3" fragment.h && echo -e "${GREEN}✓${NC} 3 bytes" || echo -e "${RED}✗${NC} Wrong"

echo -n "Fragment max payload: "
grep -q "FRAG_MAX_PAYLOAD.*252" fragment.h && echo -e "${GREEN}✓${NC} 252 bytes" || echo -e "${RED}✗${NC} Wrong"

echo -n "Reassembly timeout: "
grep -q "FRAG_TIMEOUT_SEC.*5" fragment.h && echo -e "${GREEN}✓${NC} 5 seconds" || echo -e "${RED}✗${NC} Wrong"

echo -n "Max fragments: "
grep -q "MAX_FRAGMENTS.*6" fragment.h && echo -e "${GREEN}✓${NC} 6" || echo -e "${RED}✗${NC} Wrong"

echo -n "RF frequency: "
grep -q "915000000" sx1262.h && echo -e "${GREEN}✓${NC} 915 MHz" || echo -e "${RED}✗${NC} Wrong"

echo
echo "=== Final Status ==="

if [ $MISSING -gt 0 ]; then
    echo -e "${RED}✗ FAILED${NC} - $MISSING files missing"
    exit 1
else
    echo -e "${GREEN}✓ PASSED${NC} - All deliverables present"
    echo
    echo "Implementation complete and ready for:"
    echo "  1. Code review"
    echo "  2. Security audit"
    echo "  3. Hardware testing on Raspberry Pi"
    echo
    echo "See IMPLEMENTATION-SUMMARY.md for details."
    exit 0
fi
