#!/bin/bash
# HaLow SLIP Bridge Auto-Start Script for Raspberry Pi
# Deployed by: halow-bridge.service (systemd)
#
# Creates halow0 TAP interface via SLIP bridge daemon,
# then adds it to bat0 as a second BATMAN-adv transport.
#
# Retrieved from Pi deployment 2026-03-30, then fixed:
# - FIXED: Was creating separate bat-halow instance (wrong)
# - NOW: Adds halow0 to existing bat0 (correct single mesh)
# - FIXED: MTU set to 1560 for BATMAN-adv overhead headroom

set -e

LOG="/var/log/halow-bridge.log"
DAEMON="/usr/local/bin/halow-slip-bridge"
INTERFACE="halow0"
PI_IP="192.168.1.2/24"
TAP_MTU=1560

echo "=== HaLow Bridge Startup $(date) ===" | tee -a "$LOG"

# Kill existing daemon
pkill -f halow-slip-bridge 2>/dev/null || true
sleep 1

# Remove old interface
ip link delete "$INTERFACE" 2>/dev/null || true
sleep 1

# Start SLIP daemon
echo "Starting SLIP bridge daemon..." | tee -a "$LOG"
$DAEMON &
DAEMON_PID=$!
echo "Daemon PID: $DAEMON_PID" | tee -a "$LOG"

# Wait for interface (M7: also verify daemon is still alive)
for i in {1..10}; do
    if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
        echo "FAILED: Daemon exited early (PID $DAEMON_PID)" | tee -a "$LOG"
        exit 1
    fi
    if ip link show "$INTERFACE" >/dev/null 2>&1; then
        echo "Interface $INTERFACE created" | tee -a "$LOG"
        break
    fi
    sleep 1
done

if ! ip link show "$INTERFACE" >/dev/null 2>&1; then
    echo "FAILED: Interface not created" | tee -a "$LOG"
    exit 1
fi

# Configure interface
echo "Configuring $INTERFACE..." | tee -a "$LOG"
ip link set "$INTERFACE" mtu "$TAP_MTU"
ip addr add "$PI_IP" dev "$INTERFACE" 2>/dev/null || echo "IP already set"
ip link set "$INTERFACE" up

# Verify point-to-point connectivity
ip addr show "$INTERFACE" | tee -a "$LOG"

echo "Testing connectivity to ESP32..." | tee -a "$LOG"
if ping -c 3 -W 2 192.168.1.1 >/dev/null 2>&1; then
    echo "ESP32 reachable via HaLow" | tee -a "$LOG"
else
    echo "WARNING: Cannot ping ESP32" | tee -a "$LOG"
fi

# Add to bat0 (the SINGLE mesh instance — NOT a separate bat-halow)
echo "Adding $INTERFACE to bat0 mesh..." | tee -a "$LOG"
modprobe batman-adv 2>/dev/null || true

# Wait for bat0 to exist (created by mesh-up from myc3lium-netctl)
for i in {1..10}; do
    if ip link show bat0 >/dev/null 2>&1; then
        break
    fi
    echo "Waiting for bat0..." | tee -a "$LOG"
    sleep 2
done

if ip link show bat0 >/dev/null 2>&1; then
    /usr/sbin/batctl meshif bat0 interface add "$INTERFACE" 2>/dev/null || \
        echo "WARNING: Failed to add $INTERFACE to bat0 (may already be added)" | tee -a "$LOG"
    echo "Added $INTERFACE to bat0" | tee -a "$LOG"
else
    echo "WARNING: bat0 not found, $INTERFACE running standalone" | tee -a "$LOG"
fi

# Verify
/usr/sbin/batctl meshif bat0 interface 2>/dev/null | tee -a "$LOG"
ip addr show "$INTERFACE" | tee -a "$LOG"

echo "=== Startup complete $(date) ===" | tee -a "$LOG"
echo ""
echo "HaLow interface: $INTERFACE ($PI_IP) MTU=$TAP_MTU"
echo "Mesh interface: bat0 (shared with wlan0)"
echo "Daemon PID: $DAEMON_PID"
echo "Log: $LOG"
