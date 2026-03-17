# Network Topology

## Overview
MYC3LIUM uses a hybrid mesh topology combining multiple radio technologies for redundancy and range optimization.

## Radio Technologies

### LoRa (Long Range)
- **Frequency:** 915 MHz (US/Alaska)
- **Range:** 2-10 km (urban/rural)
- **Data Rate:** 0.3-50 kbps
- **Use Case:** Long-range telemetry, position beacons, emergency messages
- **Power:** Low (~20 mA TX, ~10 mA RX)

### HaLow (802.11ah)
- **Frequency:** 902-928 MHz
- **Range:** 1-2 km
- **Data Rate:** 150 kbps - 78 Mbps
- **Use Case:** Medium-range data, camera streams, bulk transfers
- **Power:** Medium (~150 mA TX, ~50 mA RX)

### WiFi (802.11n/ac)
- **Frequency:** 2.4/5 GHz
- **Range:** 50-200 m
- **Data Rate:** 50-500 Mbps
- **Use Case:** High-bandwidth local transfers, real-time video
- **Power:** High (~200-400 mA TX, ~100 mA RX)

## Node Types

### Gateway Node
- **Role:** Internet uplink, network coordinator
- **Radios:** LoRa + HaLow + WiFi
- **Power:** AC/Solar + battery backup
- **Location:** Fixed (rooftop, building)

### Mobile Node
- **Role:** Vehicle-mounted mesh participant
- **Radios:** LoRa + WiFi (HaLow optional)
- **Power:** Vehicle DC + battery
- **Location:** Moving

### Sensor Node
- **Role:** Environmental monitoring, position beacon
- **Radios:** LoRa only
- **Power:** Battery + solar
- **Location:** Fixed or mobile

### Relay Node
- **Role:** Range extension, dead zone coverage
- **Radios:** LoRa + HaLow
- **Power:** Battery + solar
- **Location:** Fixed (elevated)

## Mesh Routing

### Reticulum Protocol
MYC3LIUM uses [Reticulum](https://reticulum.network/) for mesh networking:

- **Addressing:** 128-bit cryptographic identity
- **Routing:** Shortest-path with RSSI weighting
- **Encryption:** End-to-end (Curve25519 + AES)
- **Retransmission:** Automatic with exponential backoff
- **Discovery:** Announce broadcasts, periodic refresh

### Thread Model
A **thread** is a bidirectional radio link between two nodes:

```python
Thread(
    source_id="node-001",
    target_id="node-002",
    radio_type="LoRa",
    rssi=-85,           # Signal strength (dBm)
    quality=0.72,       # Link quality (0-1)
    latency=250,        # Round-trip time (ms)
)
```

Threads are discovered automatically and updated in real-time.

## Data Flow

### Message Priority
1. **Emergency:** Distress signals, alerts (LoRa broadcast)
2. **Command:** Node control, config changes (LoRa unicast)
3. **Telemetry:** Position, sensors, battery (LoRa/HaLow)
4. **Bulk:** Logs, media, database sync (HaLow/WiFi)

### Routing Strategy
- **LoRa:** All critical messages, fallback for others
- **HaLow:** Preferred for telemetry when available
- **WiFi:** Local high-bandwidth only

### Example: GPS Position Update
1. Sensor node collects GPS fix
2. Encodes as Reticulum packet (~64 bytes)
3. Transmits via LoRa (50 bps → 10 sec airtime)
4. Relayed by intermediate nodes
5. Reaches gateway, forwarded to API
6. WebUI updates tactical map

## Network Map

```
                  ┌─────────────┐
                  │   Internet  │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Gateway-01 │ (AC powered)
                  │ LoRa/HaLow  │
                  └──┬───────┬──┘
                     │       │
          ┌──────────┘       └──────────┐
          │                              │
    ┌─────▼─────┐                  ┌────▼────┐
    │  Mobile-01│                  │ Relay-03│ (solar)
    │ LoRa/WiFi │                  │  LoRa   │
    └─────┬─────┘                  └────┬────┘
          │                              │
    ┌─────▼─────┐                  ┌────▼────┐
    │ Sensor-05 │                  │ Sensor-07│
    │   LoRa    │                  │   LoRa   │
    └───────────┘                  └──────────┘
```

## Mock Network Topology

Current simulation includes 8 nodes spread across ~50 km:

| Node       | Type    | Radios         |
|------------|---------|----------------|
| Gateway-01 | Gateway | LoRa/HaLow/WiFi|
| Mobile-01 | Mobile | LoRa/WiFi      |
| Mobile-02 | Mobile | LoRa/WiFi      |
| Relay-03 | Relay | LoRa/HaLow     |
| Sensor-04 | Sensor | LoRa           |
| Sensor-05 | Sensor | LoRa           |
| Sensor-06 | Sensor | LoRa           |
| Sensor-07 | Sensor | LoRa           |

Geographic spread represents realistic LoRa range in mixed terrain.

## Future: Satellite Integration

Planned satellite backhaul via Iridium or LoRaWAN uplink for:
- Remote nodes beyond mesh range
- Emergency fallback when terrestrial network down
- Position tracking in wilderness

See `SATELLITE_INTEGRATION.md` for details.

## References
- [Reticulum Network Stack](https://reticulum.network/)
- [LoRa Specification](https://lora-alliance.org/)
- [IEEE 802.11ah (HaLow)](https://standards.ieee.org/)
- [Meshtastic](https://meshtastic.org/) (inspiration)
