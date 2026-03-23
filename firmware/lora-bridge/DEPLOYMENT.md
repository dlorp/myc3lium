# Deployment Checklist for LoRa TAP Bridge

## Pre-Deployment (Development)

- [x] Code written to specification
- [x] All source files created (8 files)
- [x] Makefile with -Wall -Wextra -Werror
- [x] Error handling on all syscalls
- [x] Signal handlers for clean shutdown
- [x] Logging to stdout with timestamps
- [x] No deprecated APIs (using libgpiod, not sysfs)
- [x] README with build/usage instructions
- [x] TESTING.md with comprehensive test plan
- [x] Systemd service file
- [ ] Code review completed
- [ ] Security audit completed

## Hardware Setup (Raspberry Pi)

- [ ] Waveshare SX1262 HAT installed on GPIO header
- [ ] Antenna connected to SX1262 (915 MHz)
- [ ] SPI interface enabled (`sudo raspi-config`)
- [ ] GPIO pins available:
  - GPIO 18: RESET
  - GPIO 23: BUSY
  - GPIO 24: DIO1
- [ ] Power supply adequate (2.5A minimum for Pi 4)

## Software Prerequisites

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install dependencies
sudo apt install -y build-essential libgpiod-dev

# Enable SPI
sudo raspi-config
# → Interface Options → SPI → Enable

# Load TUN module (if not auto-loaded)
sudo modprobe tun
echo "tun" | sudo tee -a /etc/modules

# Reboot
sudo reboot
```

## Build & Install

```bash
# Transfer source code to Pi
cd ~/repos/myc3lium/firmware/lora-bridge

# Run automated build test
./test-build.sh

# If successful, install
sudo make install

# Verify installation
which lora-tap-bridge
ls -l /etc/systemd/system/lora-bridge.service
```

## Configuration

### 1. Edit systemd service (if needed)

```bash
sudo nano /etc/systemd/system/lora-bridge.service
```

Update IP configuration in `ExecStartPost`:

```ini
ExecStartPost=/bin/sh -c 'sleep 2; ip addr add 10.0.0.X/24 dev lora0; ip link set lora0 up'
```

Replace `X` with node number (1, 2, 3, etc.)

### 2. Enable service

```bash
sudo systemctl daemon-reload
sudo systemctl enable lora-bridge
```

### 3. Configure routing (optional)

For batman-adv integration:

```bash
sudo apt install batctl
```

Create `/etc/network/interfaces.d/lora0`:

```
auto lora0
iface lora0 inet manual
    pre-up batctl if add lora0
```

## Testing

### 1. Manual Test Run

```bash
# Stop service if running
sudo systemctl stop lora-bridge

# Run manually
sudo /usr/local/bin/lora-tap-bridge
```

Expected output:

```
=== myc3lium LoRa TAP Bridge ===
Waveshare SX1262 HAT on Raspberry Pi 4

Initializing SX1262...
Resetting SX1262...
Configuring SX1262 for LoRa operation...
SX1262 configured successfully

Creating TAP interface: lora0
Created TAP interface: lora0
Interface lora0 is UP

Starting continuous RX mode...

[YYYY-MM-DD HH:MM:SS] Bridge active: lora0 <-> SX1262 LoRa
```

✓ No errors  
✓ TAP interface created  
✓ SX1262 initialized

Press Ctrl+C to test clean shutdown.

### 2. Two-Node Connectivity Test

**Node 1:**

```bash
sudo systemctl start lora-bridge
ping 10.0.0.2
```

**Node 2:**

```bash
sudo systemctl start lora-bridge
ping 10.0.0.1
```

Expected: Ping replies with 200-400ms latency

### 3. Check Logs

```bash
sudo journalctl -u lora-bridge -f
```

Look for:
- No error messages
- TX/RX fragment logs
- Reassembly completions

## Production Deployment

### 1. Start service

```bash
sudo systemctl start lora-bridge
sudo systemctl status lora-bridge
```

### 2. Verify operation

```bash
# Check interface
ip addr show lora0
ip route show dev lora0

# Check logs
sudo journalctl -u lora-bridge --since "5 minutes ago"

# Check process
ps aux | grep lora-tap-bridge
```

### 3. Test connectivity

```bash
# Ping another node
ping -c 10 10.0.0.X

# Check statistics (Ctrl+C the manual process to see stats)
```

### 4. Monitor for 24 hours

```bash
# Check memory stability
watch -n 60 'ps aux | grep lora-tap-bridge | grep -v grep'

# Check for restarts
sudo journalctl -u lora-bridge | grep -i restart
```

## Integration with myc3lium

### Add LoRa to batman-adv

```bash
# Stop service
sudo systemctl stop lora-bridge

# Edit service to add batman-adv support
sudo nano /etc/systemd/system/lora-bridge.service
```

Update `ExecStartPost`:

```ini
ExecStartPost=/bin/sh -c 'sleep 2; ip link set lora0 up; batctl if add lora0'
```

```bash
# Restart service
sudo systemctl daemon-reload
sudo systemctl start lora-bridge

# Verify batman-adv interface
batctl if
```

Expected output:

```
lora0: active
```

### Configure mesh routing

```bash
# Check batman-adv neighbors
batctl n

# Check routing table
batctl rt

# Test mesh connectivity
batctl ping <neighbor-mac>
```

## Monitoring

### Health Checks

Create `/usr/local/bin/lora-health-check.sh`:

```bash
#!/bin/bash
# Check if lora0 interface exists
if ! ip link show lora0 &>/dev/null; then
    echo "ERROR: lora0 interface not found"
    exit 1
fi

# Check if process is running
if ! pgrep -x lora-tap-bridge &>/dev/null; then
    echo "ERROR: lora-tap-bridge not running"
    exit 1
fi

# Check for errors in recent logs
if sudo journalctl -u lora-bridge --since "5 minutes ago" | grep -i error; then
    echo "WARNING: Errors in recent logs"
    exit 2
fi

echo "OK: LoRa bridge healthy"
exit 0
```

```bash
chmod +x /usr/local/bin/lora-health-check.sh
```

Add to cron (every 5 minutes):

```bash
sudo crontab -e
```

```
*/5 * * * * /usr/local/bin/lora-health-check.sh >> /var/log/lora-health.log 2>&1
```

### Grafana/Prometheus (Optional)

Export metrics via node_exporter or custom script:

```bash
# Count TX/RX packets from logs
sudo journalctl -u lora-bridge --since "1 hour ago" | \
  grep -E "(TAP TX|TAP RX)" | wc -l
```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u lora-bridge -xe

# Check SPI device
ls -l /dev/spidev0.0

# Check TUN device
ls -l /dev/net/tun

# Check GPIO
sudo gpioinfo gpiochip0 | grep -E "line (18|23|24)"
```

### No packets received

```bash
# Check antenna connection
# Check frequency configuration (915 MHz for US)
# Check other node is transmitting

# Monitor IRQ line
sudo gpioinfo gpiochip0 | grep "line  24"
```

### Reassembly timeouts

```bash
# Check signal strength (requires modification to log RSSI)
# Reduce distance between nodes
# Check for interference (other LoRa devices)
```

### High packet loss

```bash
# Increase spreading factor (edit sx1262.c, change SF7 to SF9)
# Reduce bandwidth (better sensitivity)
# Check antenna placement (line of sight)
```

## Maintenance

### Log Rotation

Create `/etc/logrotate.d/lora-bridge`:

```
/var/log/lora-bridge.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload lora-bridge >/dev/null 2>&1 || true
    endscript
}
```

### Updates

```bash
# Pull latest code
cd ~/repos/myc3lium
git pull origin feature/lora-batman-integration

# Rebuild
cd firmware/lora-bridge
make clean
make

# Stop service
sudo systemctl stop lora-bridge

# Install
sudo make install

# Restart service
sudo systemctl start lora-bridge

# Verify
sudo systemctl status lora-bridge
```

## Rollback Plan

If deployment fails:

```bash
# Stop service
sudo systemctl stop lora-bridge
sudo systemctl disable lora-bridge

# Remove binaries
sudo make uninstall

# Or manually:
sudo rm /usr/local/bin/lora-tap-bridge
sudo rm /etc/systemd/system/lora-bridge.service
sudo systemctl daemon-reload
```

## Sign-Off

Before marking deployment complete:

- [ ] Hardware verified working
- [ ] Software builds without warnings
- [ ] Service starts successfully
- [ ] TAP interface created
- [ ] Ping test passes between 2+ nodes
- [ ] No errors in logs after 24 hours
- [ ] Memory usage stable
- [ ] Integration with batman-adv verified (if applicable)
- [ ] Health check script installed
- [ ] Documentation reviewed by team
- [ ] Security audit findings addressed

**Deployment Date:** ________________

**Deployed By:** ________________

**Verified By:** ________________

**Notes:**

_____________________________________________

_____________________________________________

_____________________________________________
