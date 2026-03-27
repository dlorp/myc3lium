# MorseMicro Driver Kernel 6.6 Fix Script

Run this on your Raspberry Pi to fix compilation issues.

## Commands to Run

```bash
cd ~/morse_driver

# Create the fix script
cat > kernel-6.6-fix-complete.sh << 'ENDSCRIPT'
#!/bin/bash
set -e

echo "=== Complete Kernel 6.6 Fix ==="

# Backup compat.h
cp compat.h compat.h.backup

# Add ALL missing defines to compat.h
cat >> compat.h << 'ENDCOMPAT'

/* Kernel 6.6 compatibility - missing constants */
#ifndef IEEE80211_CHAN_IGNORE
#define IEEE80211_CHAN_IGNORE (1 << 20)
#endif

#ifndef IEEE80211_CHAN_NO_HE
#define IEEE80211_CHAN_NO_HE 0
#endif

/* Power save modes - map to generic values */
#ifndef POWERSAVE_MODE_FULLY_ENABLED
#define POWERSAVE_MODE_FULLY_ENABLED 1
#endif

#ifndef POWERSAVE_MODE_DISABLED
#define POWERSAVE_MODE_DISABLED 0
#endif

#ifndef MCS10_MODE_DISABLED
#define MCS10_MODE_DISABLED 0
#endif
ENDCOMPAT

echo "Patched compat.h with all missing defines"
echo ""
echo "Building driver..."
make clean
make MORSE_TRACE_PATH=$(pwd) KERNEL_SRC=/lib/modules/$(uname -r)/build CONFIG_WLAN_VENDOR_MORSE=m CONFIG_MORSE_SPI=y CONFIG_MORSE_USER_ACCESS=y

if [ $? -eq 0 ]; then
    echo ""
    echo "=== BUILD SUCCESS ==="
    echo ""
    echo "Install with:"
    echo "  sudo make install"
    echo "  sudo depmod -a"
    echo "  sudo modprobe morse"
    echo "  lsmod | grep morse"
else
    echo ""
    echo "=== BUILD FAILED ==="
    echo ""
    echo "Restore backup with:"
    echo "  mv compat.h.backup compat.h"
    exit 1
fi
ENDSCRIPT

# Make executable and run
chmod +x kernel-6.6-fix-complete.sh
./kernel-6.6-fix-complete.sh
```

## What This Does

1. Backs up `compat.h`
2. Adds compatibility defines for deprecated kernel 6.6 constants:
   - `IEEE80211_CHAN_IGNORE`
   - `IEEE80211_CHAN_NO_HE`
   - `POWERSAVE_MODE_FULLY_ENABLED`
   - `POWERSAVE_MODE_DISABLED`
   - `MCS10_MODE_DISABLED`
3. Rebuilds the driver
4. Shows install commands if successful

## If More Errors Appear

The build might reveal additional missing constants. If it fails again, send me the error screenshot and I'll add more defines to the script.
