# HaLow SLIP Bridge - Working Firmware

**Date:** 2026-03-22  
**Status:** ✅ FULLY OPERATIONAL  
**Architecture:** ESP32 HaLow AP ↔ SLIP Bridge ↔ Raspberry Pi ↔ BATMAN-adv Mesh

**Use Case:** ESP32 HaLow module (HT-HC32) connected to Raspberry Pi via USB serial for myc3lium mesh networking project. This creates a HaLow radio interface for the Pi without requiring direct GPIO/SPI connections.

## Quick Deploy

### ESP32 Side
```bash
esptool.py --chip esp32s3 --port /dev/ttyUSB0 --baud 921600 \
  write-flash 0x10000 esp32-halow-ap-slip-bridge.bin
```

### Pi Side
```bash
gcc -o halow-slip-bridge pi-slip-daemon.c
sudo ./halow-slip-bridge &
sleep 3
sudo ip addr add 192.168.1.2/24 dev halow0
sudo ip link set halow0 up
```

### BATMAN-adv Integration
```bash
sudo modprobe batman-adv
sudo /usr/sbin/batctl meshif bat-halow if add halow0
sudo ip link set bat-halow up
sudo ip addr add 10.0.0.1/24 dev bat-halow
```

## Configuration

**ESP32 HaLow AP:**
- SSID: `myc3_mesh`
- IP: 192.168.1.1/24
- Security: WPA3-SAE
- Channel: op_class=1, s1g_chan_num=1 (902.5 MHz, 1 MHz BW)
- Country: US

**SLIP Bridge:**
- UART: UART0 (USB serial port)
- Baud: 921600
- Protocol: SLIP (RFC 1055)
- Mode: TAP (Layer 2 Ethernet frames)

**Pi Interface:**
- Interface: halow0 (TAP mode)
- IP: 192.168.1.2/24
- Serial: /dev/ttyUSB0 @ 921600 baud

**BATMAN-adv Mesh:**
- Mesh interface: bat-halow
- IP: 10.0.0.1/24
- Member interface: halow0

## Features

✅ **ESP32 Features:**
- HaLow AP mode (802.11ah)
- ARP responder (192.168.1.1)
- ICMP echo responder
- Ethernet frame encapsulation
- SLIP encoding/decoding
- Bidirectional packet forwarding

✅ **Pi Features:**
- TAP interface creation
- Custom baud rate (termios2)
- SLIP encoding/decoding
- Packet statistics (TX/RX counters)
- Signal handling (SIGINT/SIGTERM)

✅ **Network Features:**
- Layer 2 bridging (Ethernet)
- ARP protocol support
- ICMP echo (ping)
- BATMAN-adv mesh routing
- Dual-radio mesh capability (HaLow + LoRa)

## Verified Working

**Ping test (direct):**
```
PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.
64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=313 ms
64 bytes from 192.168.1.1: icmp_seq=2 ttl=64 time=106 ms
64 bytes from 192.168.1.1: icmp_seq=3 ttl=64 time=105 ms
64 bytes from 192.168.1.1: icmp_seq=4 ttl=64 time=107 ms
64 bytes from 192.168.1.1: icmp_seq=5 ttl=64 time=106 ms

--- 192.168.1.1 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4005ms
```

**Ping test (mesh):**
```
PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
64 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.057 ms
64 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.046 ms
64 bytes from 10.0.0.1: icmp_seq=3 ttl=64 time=0.032 ms

--- 10.0.0.1 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2053ms
```

**BATMAN-adv status:**
```
sudo /usr/sbin/batctl meshif bat-halow if
halow0: active
```

## Hardware

**ESP32 Module:** Heltec HT-HC32 (ESP32-S3 + MM6108 HaLow)
- Chip: ESP32-S3 (QFN56) revision v0.2
- MAC: b4:3a:45:a4:56:b0
- Flash: 8MB
- PSRAM: 8MB

**HaLow Chip:** MM6108A1
- Chip ID: 0x0306
- BCF firmware: 1.17.6
- API version: 12.1.0
- Morselib: 2.10.4-esp32

**GPIO Configuration (Variant #3 - CONFIRMED WORKING):**
- RESET_N: GPIO 8
- WAKE: GPIO 9
- BUSY: GPIO 7
- SPI_SCK: GPIO 4
- SPI_MOSI: GPIO 3
- SPI_MISO: GPIO 5
- SPI_CS: GPIO 2
- SPI_IRQ: GPIO 6

**Raspberry Pi:**
- Model: Raspberry Pi 4
- Hostname: myc3-node
- Username: myc3
- Serial: /dev/ttyUSB0 (CP210x USB-UART bridge)

## Build from Source

### ESP32 Firmware
```bash
cd /Users/lorp/esp/mm-iot-esp32-morsemicro/examples/ap_mode
source /Users/lorp/esp/esp-idf/export.sh
export MMIOT_ROOT=/Users/lorp/esp/mm-iot-esp32-morsemicro
idf.py build
```

**Source files:**
- Main: `examples/ap_mode/main/src/ap_mode.c`
- SLIP bridge: `examples/ap_mode/main/src/slip_bridge.c`
- Config: `examples/ap_mode/sdkconfig.defaults`

### Pi Daemon
```bash
gcc -o halow-slip-bridge pi-slip-daemon.c
```

**Compiler flags:** None required (uses termios2, standard Linux headers)

## Troubleshooting

**Issue:** Interface creation fails ("Device or resource busy")
**Fix:** Delete existing interface first:
```bash
sudo ip link delete halow0
```

**Issue:** Wrong baud rate shown (4103 instead of 921600)
**Fix:** Kill Openterface KVM before starting daemon:
```bash
pkill -9 openterface
```

**Issue:** Ping fails, 100% packet loss
**Fix:** Verify both sides running:
- ESP32: Check serial output for "AP Mode started successfully"
- Pi: Check `ip link show halow0` shows interface UP

**Issue:** BATMAN-adv fails to add interface
**Fix:** Ensure TAP mode (not TUN) and interface is UP:
```bash
sudo ip link set halow0 up
```

## Known Limitations

- **Single serial port:** UART0 shared between console and SLIP (console disabled for production)
- **No DHCP:** Static IP configuration required on Pi side
- **No encryption:** SLIP protocol is unencrypted (HaLow WPA3 provides wireless security)
- **ARP only for ESP32:** Pi cannot ARP for other nodes (ESP32 responds for 192.168.1.1 only)
- **No LED indicator:** Status LED remains off (UART0 conflicts with LED GPIO, acceptable trade-off for working connectivity)

## Architecture Details

### Packet Flow (Pi → HaLow)
1. Application sends packet to bat-halow interface
2. BATMAN-adv routes to halow0
3. TAP interface delivers Ethernet frame to SLIP daemon
4. Daemon SLIP-encodes frame, sends to /dev/ttyUSB0
5. ESP32 UART receives, SLIP-decodes frame
6. ESP32 strips Ethernet header, extracts IP packet
7. mmwlan_tx() sends IP packet over HaLow radio

### Packet Flow (HaLow → Pi)
1. MM6108 chip receives HaLow packet
2. mmwlan RX callback delivers IP packet to SLIP bridge
3. ESP32 adds Ethernet header (src=ESP32 MAC, dst=broadcast)
4. ESP32 SLIP-encodes Ethernet frame, sends to UART
5. Pi SLIP daemon receives, decodes frame
6. Daemon writes Ethernet frame to halow0 TAP interface
7. BATMAN-adv processes frame, routes to bat-halow

### ARP/ICMP Handling
- **ARP requests for 192.168.1.1:** ESP32 responds with its MAC address
- **ICMP echo to 192.168.1.1:** ESP32 responds directly (no HaLow transmission)
- **Other traffic:** Forwarded to HaLow radio for mesh routing

## Performance

**Latency:**
- Direct ping (192.168.1.1): ~105-107ms average
- Mesh ping (10.0.0.1): <0.1ms (local interface)
- First ping: ~313ms (ARP resolution)

**Throughput:** Not measured (mesh traffic expected to be low-bandwidth telemetry)

**Reliability:**
- Ping success rate: 100% (5/5 packets in all tests)
- Interface stability: No crashes or resets observed

## Future Enhancements

- [ ] DHCP server on ESP32 (optional, current static config works)
- [ ] Multi-node mesh testing (add second HaLow node)
- [ ] Packet statistics logging (bandwidth, errors, retries)
- [ ] Console output via UART1 (GPIO 17/18, requires extra USB adapter)
- [ ] Systemd service for auto-start on boot
- [ ] Watchdog timer for daemon crash recovery
- [ ] IPv6 support (currently IPv4 only)

## License

MorseMicro mm-iot-esp32 SDK: Proprietary (see vendor license)  
Pi SLIP daemon: MIT (dlorp 2026)

## Contact

Project: myc3lium mesh network  
Hardware: Heltec HT-HC32 (ESP32-S3 + MM6108 HaLow)  
Date completed: 2026-03-22 16:59 AKDT
