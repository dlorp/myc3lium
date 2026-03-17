# MYC3LIUM Mock Network Topology

## Network Overview

**8 Nodes** spanning the Anchorage area, connected via **9 threads** using mixed radio technologies.

## Node Distribution

```
                JBER (myc3_007)
              [SPORE, Battery: 50%]
                /           \
              WiFi         HaLow
              /               \
     Airport (myc3_004)    Eagle River (myc3_005)
    [RHIZOME, Grid Power]  [HYPHA, Battery: 65%]
           |                    |
         WiFi                HaLow
           |                    |
     Downtown (myc3_000)    Midtown (myc3_002)
      [HYPHA, Grid Power]   [FROND, Battery: 75%]
           |                    |
         LoRa                 WiFi
           |                    |
     Hillside (myc3_001)        |
    [HYPHA, Battery: 80%]       |
           |                    |
         LoRa                   |
           |                    |
     O'Malley (myc3_003)--------/
    [SPORE, Battery: 70%]
           |
         LoRa
           |
     Girdwood (myc3_006)
    [FROND, Battery: 55%]
```

## Node Details

| ID | Callsign | Type | Location | Lat/Lon | Power | Notes |
|---|---|---|---|---|---|---|
| myc3_000 | MYC3LIUM-DOWNTOWN | HYPHA | Downtown Anchorage | 61.2181, -149.9003 | Grid | Central hub |
| myc3_001 | MYC3LIUM-HILLSIDE | HYPHA | Hillside | 61.1919, -149.8478 | Battery | Relay node |
| myc3_002 | MYC3LIUM-MIDTOWN | FROND | Midtown | 61.2147, -149.8947 | Battery | Camera node |
| myc3_003 | MYC3LIUM-O'MALLEY | SPORE | O'Malley | 61.1508, -149.8606 | Battery | Sensor node |
| myc3_004 | MYC3LIUM-AIRPORT | RHIZOME | Near Airport | 61.2225, -149.8842 | Grid | Base station |
| myc3_005 | MYC3LIUM-EAGLE RIVER | HYPHA | Eagle River | 61.1944, -149.7661 | Battery | Relay node |
| myc3_006 | MYC3LIUM-GIRDWOOD | FROND | Girdwood | 61.1197, -149.9669 | Battery | Camera node |
| myc3_007 | MYC3LIUM-JBER | SPORE | JBER Base | 61.2489, -149.6856 | Battery | Sensor node |

## Thread (Connection) Details

| ID | Source | Target | Radio Type | Quality | RSSI (dBm) | Latency (ms) | Notes |
|---|---|---|---|---|---|---|---|
| thread_000 | Downtown | Hillside | LoRa | 0.85 | -95 | 150 | Long-range backbone |
| thread_001 | Downtown | Midtown | WiFi | 0.92 | -65 | 25 | High-speed local |
| thread_002 | Hillside | O'Malley | LoRa | 0.80 | -100 | 180 | Hillside coverage |
| thread_003 | Midtown | Airport | WiFi | 0.88 | -58 | 15 | Fast link |
| thread_004 | Midtown | Eagle River | HaLow | 0.75 | -92 | 120 | Extended range |
| thread_005 | O'Malley | Girdwood | LoRa | 0.70 | -105 | 200 | Mountain link |
| thread_006 | Airport | JBER | WiFi | 0.90 | -55 | 20 | Base connection |
| thread_007 | Eagle River | JBER | HaLow | 0.78 | -88 | 110 | Military link |
| thread_008 | Downtown | Airport | WiFi | 0.94 | -52 | 10 | Backbone redundancy |

## Radio Technology Breakdown

### LoRa (4 threads)
- **Range:** Long (5-15 km)
- **Bandwidth:** Low (50 kbps)
- **Latency:** High (150-200 ms)
- **Use case:** Remote sensor data, long-range relays
- **Threads:** 0, 2, 5

### HaLow (2 threads)
- **Range:** Medium (1-5 km)
- **Bandwidth:** Medium (150 kbps)
- **Latency:** Medium (110-120 ms)
- **Use case:** Extended WiFi range, penetration through obstacles
- **Threads:** 4, 7

### WiFi (3 threads)
- **Range:** Short (100-500 m)
- **Bandwidth:** High (1+ Mbps)
- **Latency:** Low (10-25 ms)
- **Use case:** High-bandwidth local connections, backbones
- **Threads:** 1, 3, 6, 8

## Network Characteristics

### Redundancy
- **Multi-path routing:** Downtown ↔ Airport has 2 paths (direct WiFi + via Midtown)
- **Hub nodes:** Downtown and Airport serve as primary hubs
- **Backup routes:** If Downtown fails, Eagle River → JBER → Airport path exists

### Coverage Area
- **Urban:** Downtown, Midtown, Airport (high-speed WiFi mesh)
- **Suburban:** Hillside, O'Malley, Eagle River (LoRa/HaLow)
- **Remote:** Girdwood (LoRa fallback), JBER (military base)
- **Total span:** ~50 km north-south (Girdwood to JBER)

### Power Profile
- **Grid-powered (always-on):** Downtown (HYPHA), Airport (RHIZOME)
- **Battery-powered (periodic):** All others
- **Battery life (estimated at current drain):**
  - SPORE (2%/hr): ~42 hours (O'Malley, JBER)
  - FROND (3.5%/hr): ~24 hours (Midtown, Girdwood)
  - HYPHA (1%/hr): ~100 hours (Hillside, Eagle River)

### Data Flow
1. **Sensor nodes (SPORE)** collect environmental data
2. **Camera nodes (FROND)** capture imagery
3. **Relay nodes (HYPHA)** forward traffic
4. **Base stations (RHIZOME)** provide internet uplink
5. Messages route through optimal path based on radio type and quality

## Sensor Data (Per Node)

Each node generates realistic sensor data:

### Temperature (24-hour cycle)
- **Base temp:** -1°C (March Anchorage average)
- **Diurnal swing:** ±3°C
- **Coldest:** 6:00 AM (~-4°C)
- **Warmest:** 3:00 PM (~+2°C)
- **Random variance:** ±0.5°C

### Humidity
- **Range:** 65-85%
- **Typical:** 75% (Anchorage coastal climate)

### Pressure
- **Range:** 1010-1020 hPa
- **Typical:** 1015 hPa (sea level, corrected)

## Example Message Routing

**Scenario:** Girdwood sensor sends data to Airport base station

```
Girdwood (myc3_006)
    ↓ [LoRa, thread_005, 200ms]
O'Malley (myc3_003)
    ↓ [LoRa, thread_002, 180ms]
Hillside (myc3_001)
    ↓ [LoRa, thread_000, 150ms]
Downtown (myc3_000)
    ↓ [WiFi, thread_008, 10ms]
Airport (myc3_004)
```

**Total latency:** ~540ms  
**Total hops:** 4  
**Mixed radio:** LoRa → WiFi transition at Downtown

## Network Health Simulation

### Healthy State (100%)
- All 8 nodes online
- 9 threads active
- Average quality: 0.85
- Message delivery: >95%

### Degraded State (75%)
- 1-2 nodes offline (battery depletion)
- 7-8 threads active
- Average quality: 0.70
- Message delivery: 80-90%
- **Recovery:** Battery nodes recharge via solar

### Critical State (<50%)
- 3+ nodes offline
- <6 threads active
- Network partitioning risk
- Message delivery: <70%
- **Mitigation:** Grid-powered nodes (Downtown, Airport) maintain core network

## Realistic Failure Modes

1. **Battery depletion:** FROND nodes (cameras) drain fastest → go offline after ~24h
2. **Weather interference:** LoRa quality degrades during storms
3. **Line-of-sight:** HaLow threads fail if obstacles (buildings, terrain) block path
4. **Node reboot:** Sensor nodes (SPORE) cycle on/off to conserve battery
5. **Congestion:** WiFi threads saturate during high-bandwidth camera streams

## Growth Path

Future network expansion could add:
- **Satellite uplink** at JBER or Airport
- **Mobile nodes** (vehicles, drones) with temporary connections
- **More sensors** in remote areas (Hatcher Pass, Turnagain Arm)
- **Redundant backbones** between hubs
- **Solar-powered repeaters** in wilderness areas

---

**Note:** All coordinates, radio parameters, and sensor data are realistic for Anchorage, Alaska deployment. The network topology balances coverage, redundancy, and power efficiency for a real-world mesh network scenario.
