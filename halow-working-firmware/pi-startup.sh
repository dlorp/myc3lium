#!/bin/bash
# HaLow SLIP Bridge Auto-Start Script for Raspberry Pi
# Save to /usr/local/bin/halow-start.sh and run at boot

set -e

LOG="/var/log/halow-bridge.log"
DAEMON="/usr/local/bin/halow-slip-bridge"
INTERFACE="halow0"
PI_IP="192.168.1.2/24"
MESH_IP="10.0.0.1/24"
MESH_IFACE="bat-halow"

echo "=== HaLow Bridge Startup $(date) ===" | tee -a "$LOG"

# Kill existing daemon
pkill -f halow-slip-bridge 2>/dev/null || true
sleep 1

# Remove old interface
ip link delete $INTERFACE 2>/dev/null || true
sleep 1

# Start SLIP daemon
echo "Starting SLIP bridge daemon..." | tee -a "$LOG"
$DAEMON &
DAEMON_PID=$!
echo "Daemon PID: $DAEMON_PID" | tee -a "$LOG"

# Wait for interface
for i in {1..10}; do
    if ip link show $INTERFACE >/dev/null 2>&1; then
        echo "✓ Interface $INTERFACE created" | tee -a "$LOG"
        break
    fi
    sleep 1
done

if ! ip link show $INTERFACE >/dev/null 2>&1; then
    echo "✗ FAILED: Interface not created" | tee -a "$LOG"
    exit 1
fi

# Configure interface
echo "Configuring $INTERFACE..." | tee -a "$LOG"
ip addr add $PI_IP dev $INTERFACE 2>/dev/null || echo "IP already set"
ip link set $INTERFACE up

# Verify
ip addr show $INTERFACE | tee -a "$LOG"

# Test connectivity
echo "Testing connectivity to ESP32..." | tee -a "$LOG"
if ping -c 3 -W 2 192.168.1.1 >/dev/null 2>&1; then
    echo "✓ ESP32 reachable via HaLow" | tee -a "$LOG"
else
    echo "✗ WARNING: Cannot ping ESP32" | tee -a "$LOG"
fi

# Load BATMAN-adv module
echo "Loading BATMAN-adv..." | tee -a "$LOG"
modprobe batman-adv

# Add to mesh
echo "Adding $INTERFACE to BATMAN-adv mesh..." | tee -a "$LOG"
/usr/sbin/batctl meshif $MESH_IFACE if add $INTERFACE
ip link set $MESH_IFACE up
ip addr add $MESH_IP dev $MESH_IFACE 2>/dev/null || echo "Mesh IP already set"

# Verify mesh
/usr/sbin/batctl meshif $MESH_IFACE if | tee -a "$LOG"
ip addr show $MESH_IFACE | tee -a "$LOG"

echo "=== Startup complete $(date) ===" | tee -a "$LOG"
echo ""
echo "HaLow interface: $INTERFACE ($PI_IP)"
echo "Mesh interface: $MESH_IFACE ($MESH_IP)"
echo "Daemon PID: $DAEMON_PID"
echo "Log: $LOG"
