# LoRa TAP Bridge for myc3lium

Production-quality bridge daemon for integrating Waveshare SX1262 LoRa HAT with myc3lium mesh networking via TAP interface.

## Hardware Requirements

- **Raspberry Pi 4** (or compatible)
- **Waveshare SX1262 LoRa HAT** (915 MHz ISM band)
- GPIO connections:
  - GPIO 18: RESET
  - GPIO 23: BUSY
  - GPIO 24: DIO1 (IRQ)
- SPI interface: `/dev/spidev0.0` @ 2 MHz

## Features

- **TAP interface** (`lora0`) for seamless Linux networking integration
- **Automatic fragmentation** of Ethernet frames (up to 1500 bytes) into LoRa packets (≤255 bytes)
- **Reassembly engine** with timeout handling (5 seconds)
- **Production-grade error handling** on all syscalls
- **Clean shutdown** on SIGINT/SIGTERM
- **Statistics tracking** (TX/RX packets, bytes, fragments)
- **libgpiod** for modern GPIO handling (no deprecated sysfs)

## Architecture

```
┌─────────────────────────────────────────────────┐
│            lora-tap-bridge daemon                │
│                                                  │
│  ┌──────────┐     ┌──────────┐    ┌──────────┐ │
│  │  TAP fd  │◄───►│ Fragment │◄──►│ SPI I/O  │ │
│  │ (lora0)  │     │  Engine  │    │(spidev0) │ │
│  └──────────┘     └──────────┘    └──────────┘ │
│       ↑                                  ↑      │
│   Ethernet                          SX1262      │
│   frames                           commands     │
│  (≤1500B)                          (≤255B)      │
└─────────────────────────────────────────────────┘
```

## Build Instructions

### Prerequisites

Install required dependencies on Raspberry Pi OS (Debian Bookworm):

```bash
sudo apt update
sudo apt install -y build-essential libgpiod-dev
```

### Compile

```bash
cd ~/repos/myc3lium/firmware/lora-bridge
make
```

The build should complete without warnings. Expected output:

```
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c lora-tap-bridge.c -o lora-tap-bridge.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c sx1262.c -o sx1262.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c tap.c -o tap.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -c fragment.c -o fragment.o
gcc -Wall -Wextra -Werror -O2 -std=gnu11 -o lora-tap-bridge lora-tap-bridge.o sx1262.o tap.o fragment.o -lgpiod
Built lora-tap-bridge successfully
```

### Test Build

```bash
make test
```

Verify:
- ✓ Built for ARM64
- ✓ Linked with libgpiod

## Usage

### Manual Execution

```bash
# Run as root (required for TAP interface and GPIO access)
sudo ./lora-tap-bridge
```

Expected startup output:

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
Configure with:
  sudo ip addr add 10.0.0.1/24 dev lora0
  sudo ip route add 10.0.0.0/8 dev lora0
```

### Network Configuration

Assign IP address and routes:

```bash
# On node 1
sudo ip addr add 10.0.0.1/24 dev lora0
sudo ip route add 10.0.0.0/8 dev lora0

# On node 2
sudo ip addr add 10.0.0.2/24 dev lora0
sudo ip route add 10.0.0.0/8 dev lora0
```

### Testing

Ping between nodes:

```bash
# From node 1
ping 10.0.0.2

# Check stats
# Press Ctrl+C to see statistics summary
```

Monitor traffic:

```bash
sudo tcpdump -i lora0 -n
```

## Systemd Service

Create `/etc/systemd/system/lora-bridge.service`:

```ini
[Unit]
Description=myc3lium LoRa TAP Bridge
Documentation=https://github.com/yourusername/myc3lium
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/lora-tap-bridge
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/dev

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo make install  # Installs binary to /usr/local/bin
sudo systemctl daemon-reload
sudo systemctl enable lora-bridge
sudo systemctl start lora-bridge
```

View logs:

```bash
sudo journalctl -u lora-bridge -f
```

Check status:

```bash
sudo systemctl status lora-bridge
```

## Fragment Protocol

**Header Format (3 bytes):**

```
Byte 0: [FRAG_ID (4 bits)] [TOTAL_FRAGS (4 bits)]
Byte 1: [FRAG_INDEX (8 bits)]
Byte 2: [PAYLOAD_LEN (8 bits)]
```

- **FRAG_ID**: Fragment ID (0-15, wraps around)
- **TOTAL_FRAGS**: Total fragments in this frame (1-6)
- **FRAG_INDEX**: Index of this fragment (0-based)
- **PAYLOAD_LEN**: Length of payload in this fragment (≤252 bytes)

**Constraints:**

- Max payload per fragment: 252 bytes (255 - 3 header)
- Max fragments per frame: 6 (ceil(1500 / 252))
- Reassembly timeout: 5 seconds

## LoRa Configuration

- **Frequency**: 915 MHz (US ISM band)
- **Spreading Factor**: SF7 (fast, shorter range)
- **Bandwidth**: 125 kHz
- **Coding Rate**: 4/5
- **Preamble**: 8 symbols
- **CRC**: Enabled
- **TX Power**: 14 dBm

## Troubleshooting

### SPI Device Not Found

```bash
# Enable SPI interface
sudo raspi-config
# Interface Options → SPI → Enable

# Verify SPI device
ls -l /dev/spidev0.0
```

### GPIO Permission Denied

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Or run as root
sudo ./lora-tap-bridge
```

### TAP Interface Creation Failed

```bash
# Load TUN/TAP kernel module
sudo modprobe tun

# Verify device
ls -l /dev/net/tun
```

### No Packets Received

1. Check antenna connection
2. Verify both nodes on same frequency (915 MHz)
3. Check IRQ line (GPIO 24) with `gpioinfo`:
   ```bash
   sudo gpioinfo | grep -A2 "line  24"
   ```
4. Monitor SX1262 IRQ register:
   ```bash
   # In source, enable debug logging in sx1262.c
   ```

## File Structure

```
firmware/lora-bridge/
├── lora-tap-bridge.c      # Main daemon (select loop)
├── sx1262.h               # SX1262 register definitions
├── sx1262.c               # SPI driver & LoRa config
├── tap.h                  # TAP interface API
├── tap.c                  # TAP creation & I/O
├── fragment.h             # Fragmentation protocol
├── fragment.c             # Fragment/reassemble logic
├── Makefile               # Build system
└── README.md              # This file
```

## Performance Characteristics

- **Latency**: ~200-400ms per packet (depends on fragment count)
- **Throughput**: ~1-2 kbps (SF7, BW125)
- **Range**: 500m-2km line-of-sight (depends on environment)
- **Packet Loss**: Handled by reassembly timeout (5s)

## Integration with myc3lium

Once running, the `lora0` TAP interface appears as a standard network device:

```bash
# Bring up batman-adv on lora0
sudo batctl if add lora0
sudo ip link set bat0 up
```

See `plans/integration-roadmap-2026-03-22.md` for full mesh integration.

## License

MIT License - See project root for details

## Security Notes

⚠️ **Production Deployment:**

- No encryption implemented (handled by upper layers)
- No authentication on LoRa packets
- Assumes trusted physical layer
- Run security audit before production use

For encrypted mesh networking, integrate with batman-adv + wireguard.

## Support

- Issues: https://github.com/yourusername/myc3lium/issues
- Docs: `plans/integration-roadmap-2026-03-22.md`
- Hardware: Waveshare SX1262 HAT documentation
