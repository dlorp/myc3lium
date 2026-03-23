# Testing Guide for LoRa TAP Bridge

## Pre-Build Testing (on Development Machine)

The code is designed for Raspberry Pi and requires kernel headers not available on macOS/other dev machines.

### Syntax Check

```bash
gcc -fsyntax-only -Wall -Wextra -std=gnu11 -I. lora-tap-bridge.c
gcc -fsyntax-only -Wall -Wextra -std=gnu11 -I. tap.c
gcc -fsyntax-only -Wall -Wextra -std=gnu11 -I. fragment.c
```

Expected: No errors (kernel header includes will fail, but syntax should be valid)

## Build Testing (on Raspberry Pi)

### Automated Build Test

Transfer files to Raspberry Pi and run:

```bash
./test-build.sh
```

This checks:
- Dependencies (libgpiod-dev, build-essential)
- SPI device availability
- TUN/TAP device
- GPIO chip
- Compilation
- Binary architecture (ARM64)
- Library linkage (libgpiod)

### Manual Build

```bash
make clean
make
```

Expected output (no warnings):

```
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c lora-tap-bridge.c -o lora-tap-bridge.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c sx1262.c -o sx1262.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c tap.c -o tap.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c fragment.c -o fragment.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -o lora-tap-bridge lora-tap-bridge.o sx1262.o tap.o fragment.o -lgpiod
Built lora-tap-bridge successfully
```

## Runtime Testing

### 1. Hardware Test (Single Node)

Start the bridge:

```bash
sudo ./lora-tap-bridge
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

[2026-03-22 17:30:00] Bridge active: lora0 <-> SX1262 LoRa
```

✓ No errors during initialization  
✓ TAP interface created  
✓ SX1262 in RX mode

### 2. TAP Interface Test

In another terminal:

```bash
# Check interface exists
ip link show lora0

# Assign IP
sudo ip addr add 10.0.0.1/24 dev lora0

# Verify
ip addr show lora0
```

Expected output:

```
5: lora0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc fq_codel state DOWN group default qlen 1000
    link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.1/24 scope global lora0
```

### 3. Fragmentation Test (Loopback)

Test fragment/reassembly with netcat:

```bash
# Terminal 1: Start listener
nc -l -u -p 5000

# Terminal 2: Send large packet (will fragment)
echo "Testing LoRa fragmentation with a long message that will definitely exceed 252 bytes and require multiple fragments to transmit over the radio link. This should trigger the fragmentation engine and test reassembly on the receiving side." | nc -u 10.0.0.1 5000
```

In bridge output, look for:

```
[2026-03-22 17:31:00] TAP RX: 180 bytes
[2026-03-22 17:31:00] Fragmenting into 1 packets
[2026-03-22 17:31:00] TX fragment 1/1: 183 bytes
```

### 4. Two-Node Test

**Setup:**

- Node 1: 10.0.0.1
- Node 2: 10.0.0.2
- Distance: Start with radios side-by-side, then increase

**Node 1:**

```bash
sudo ./lora-tap-bridge
# In another terminal:
sudo ip addr add 10.0.0.1/24 dev lora0
ping 10.0.0.2
```

**Node 2:**

```bash
sudo ./lora-tap-bridge
# In another terminal:
sudo ip addr add 10.0.0.2/24 dev lora0
ping 10.0.0.1
```

**Expected ping output:**

```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=312 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=298 ms
```

Note: Latency will be 200-400ms due to LoRa air time.

**Bridge output on Node 1:**

```
[2026-03-22 17:32:00] TAP RX: 98 bytes
[2026-03-22 17:32:00] Fragmenting into 1 packets
[2026-03-22 17:32:00] TX fragment 1/1: 101 bytes
[2026-03-22 17:32:01] RX fragment: 101 bytes
[2026-03-22 17:32:01] Frame reassembled: 98 bytes
[2026-03-22 17:32:01] TAP TX: 98 bytes
```

### 5. Large Frame Test

Test fragmentation with larger packets:

```bash
# Terminal 1 (Node 2)
nc -l -u -p 5000 > /tmp/received.txt

# Terminal 2 (Node 1)
dd if=/dev/urandom bs=1400 count=1 | nc -u 10.0.0.2 5000
```

**Bridge output on Node 1:**

```
[2026-03-22 17:33:00] TAP RX: 1442 bytes
[2026-03-22 17:33:00] Fragmenting into 6 packets
[2026-03-22 17:33:00] TX fragment 1/6: 255 bytes
[2026-03-22 17:33:01] TX fragment 2/6: 255 bytes
[2026-03-22 17:33:02] TX fragment 3/6: 255 bytes
[2026-03-22 17:33:03] TX fragment 4/6: 255 bytes
[2026-03-22 17:33:04] TX fragment 5/6: 255 bytes
[2026-03-22 17:33:05] TX fragment 6/6: 167 bytes
```

**Bridge output on Node 2:**

```
[2026-03-22 17:33:00] RX fragment: 255 bytes
[2026-03-22 17:33:01] RX fragment: 255 bytes
[2026-03-22 17:33:02] RX fragment: 255 bytes
[2026-03-22 17:33:03] RX fragment: 255 bytes
[2026-03-22 17:33:04] RX fragment: 255 bytes
[2026-03-22 17:33:05] RX fragment: 167 bytes
[2026-03-22 17:33:05] Frame reassembled: 1442 bytes
[2026-03-22 17:33:05] TAP TX: 1442 bytes
```

Verify:

```bash
# On Node 2
ls -l /tmp/received.txt
# Should be 1400 bytes
```

### 6. Stress Test

Continuous ping flood:

```bash
# From Node 1
ping -f -s 1400 10.0.0.2
```

Let run for 1 minute, then Ctrl+C.

Check statistics:

```
=== Statistics ===
TX: 60 packets, 84000 bytes, 360 fragments
RX: 58 packets, 81200 bytes, 348 fragments
Reassembly: 0 active, 58 complete, 2 timeout, 0 corrupted
```

Acceptable packet loss: <5%

### 7. Reassembly Timeout Test

Simulate fragment loss:

```bash
# On Node 1, modify code to drop fragment 2/6
# Or physically block radio during transmission

# Send large packet
dd if=/dev/urandom bs=1400 count=1 | nc -u 10.0.0.2 5000
```

After 5 seconds, check Node 2 logs:

```
Cleaned up 1 expired reassembly entries
```

✓ Timeout mechanism working

### 8. Systemd Service Test

```bash
sudo make install
sudo systemctl start lora-bridge
sudo systemctl status lora-bridge
```

Expected:

```
● lora-bridge.service - myc3lium LoRa TAP Bridge
     Loaded: loaded (/etc/systemd/system/lora-bridge.service; disabled)
     Active: active (running) since ...
```

Check logs:

```bash
sudo journalctl -u lora-bridge -f
```

Test auto-restart:

```bash
# Kill process
sudo killall lora-tap-bridge

# Service should restart within 10 seconds
sudo systemctl status lora-bridge
```

### 9. Memory Leak Test

Run for extended period with continuous traffic:

```bash
# Start bridge
sudo ./lora-tap-bridge &
PID=$!

# Monitor memory
while true; do
    ps aux | grep lora-tap-bridge | grep -v grep
    sleep 60
done

# After 1 hour, RSS memory should be stable (~2-3 MB)
```

### 10. Clean Shutdown Test

```bash
sudo ./lora-tap-bridge
# Press Ctrl+C
```

Expected output:

```
^C
Shutdown signal received...

=== Statistics ===
TX: 10 packets, 980 bytes, 10 fragments
RX: 8 packets, 784 bytes, 8 fragments
Reassembly: 0 active, 8 complete, 0 timeout, 0 corrupted

Cleaning up...
Shutdown complete
```

✓ No segfaults  
✓ Statistics printed  
✓ Resources released

## Troubleshooting Tests

### Debug GPIO

```bash
sudo gpioinfo gpiochip0 | grep -E "line (18|23|24)"
```

Expected:

```
line  18:      unnamed       output  active-high [used]
line  23:      unnamed       input  active-high [used]
line  24:      unnamed       input  active-high [used]
```

### Debug SPI

```bash
# Install spi-tools
sudo apt install spi-tools

# Test SPI communication
sudo spi-test -D /dev/spidev0.0 -v
```

### Debug TAP

```bash
# Check TUN module
lsmod | grep tun

# Check TAP device
cat /sys/class/net/lora0/type
# Should return: 1 (Ethernet)
```

## Performance Benchmarks

### Expected Performance

- **Ping latency**: 200-400ms (depends on fragment count)
- **Throughput**: 1-2 kbps (SF7, BW125, effective after overhead)
- **Fragment transmission time**: ~50ms per 255-byte fragment
- **Reassembly CPU usage**: <1%
- **Memory footprint**: 2-3 MB RSS

### Benchmark Commands

```bash
# Latency test
ping -c 100 10.0.0.2 | tail -n 4

# Throughput test
iperf3 -c 10.0.0.2 -u -b 2k -t 60

# CPU usage
top -p $(pidof lora-tap-bridge)
```

## Pass/Fail Criteria

### Build Phase

- ✓ Compiles without warnings (-Werror)
- ✓ Links with libgpiod
- ✓ Binary is ARM64

### Runtime Phase

- ✓ SX1262 initializes successfully
- ✓ TAP interface created
- ✓ Ping works between nodes
- ✓ Large frames fragment correctly (6 fragments max)
- ✓ Reassembly completes within 5 seconds
- ✓ Timeout cleanup works
- ✓ No memory leaks after 1 hour
- ✓ Clean shutdown on SIGINT/SIGTERM
- ✓ Packet loss <5% under normal conditions

## Security Testing

Before production deployment:

1. **Fuzzing**: Send malformed LoRa packets
2. **Buffer overflow**: Test with oversized fragments
3. **Fragment ID collision**: Test ID wraparound
4. **Reassembly exhaustion**: Send incomplete fragments rapidly

Run these tests in isolated environment before field deployment.
