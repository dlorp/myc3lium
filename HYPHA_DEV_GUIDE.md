# HYPHA Development Guide

**HYPHA** (Handheld Yield Processing + HaLow Adapter) — Lightweight portable mesh node for field operations.

**Hardware Platform:** Heltec ESP32-S3 HT-HC33

---

## Hardware Specification

### Core Module (Ordered)

**Heltec ESP32-S3 HT-HC33** (~$35)
- ESP32-S3 dual-core Xtensa LX7 @ 240 MHz
- 8MB PSRAM, 16MB Flash
- WiFi HaLow (built-in, 1-2km range, 32 Mbps)
- Camera (OV3660)
- BLE 5.0
- USB-C (programming + power)

### Required Add-ons

**1. Display (Choose One)**

**Option A: E-Ink (Recommended for battery life)**
- Waveshare 2.9" e-Ink display (~$20)
- SPI interface
- Ultra low power (only draws during refresh)
- Readable in full sunlight
- Perfect for tactical status display
- Resolution: 296×128 (enough for teletext-style pages)

**Option B: OLED (Best contrast)**
- 1.3" or 1.5" OLED display (~$10-15)
- I2C or SPI interface
- High contrast (perfect for low-light)
- Low power in standby
- Resolution: 128×64 or 128×128

**Option C: Character LCD (Minimal)**
- 16×2 or 20×4 character LCD (~$5-8)
- I2C interface (only 2 wires)
- Extremely simple
- Show: node status, battery %, message count
- Perfect for "always on" minimal display

**2. GPS Module (Optional but recommended)**
- u-blox NEO-6M or NEO-M8N (~$10-15)
- UART interface
- Position reporting for ATAK integration
- Battery backup for faster lock

**3. Battery System**
- 18650 or 21700 Li-ion cell (~$5-10)
- TP4056 charging module (~$2)
- Battery holder (~$2)
- Target: 5-10 hours active, 24+ hours standby

**4. Enclosure**
- 3D printed tactical case, OR
- Hammond 1591 series project box (~$10)
- Must accommodate ESP32 + display + battery

**5. External Antenna (Optional)**
- WiFi HaLow external antenna (~$15-20)
- RP-SMA pigtail cable
- Improves range significantly (1km → 2km+)

**Total Cost:** ~$80-120 depending on options

---

## Pin Assignments (ESP32-S3)

**Built-in Peripherals:**
- WiFi HaLow: Internal module
- Camera (OV3660): CSI interface (internal)
- BLE: Internal radio

**Available GPIO for Add-ons:**

**SPI (for e-Ink or OLED):**
- MOSI: GPIO11
- MISO: GPIO13
- SCK: GPIO12
- CS: GPIO10
- DC: GPIO9
- RST: GPIO8
- BUSY: GPIO7 (e-Ink only)

**I2C (for character LCD or OLED):**
- SDA: GPIO21
- SCL: GPIO22

**UART (for GPS):**
- TX: GPIO43
- RX: GPIO44

**Power:**
- 3.3V output available
- Battery monitoring via ADC (GPIO1)

---

## Software Stack

### Development Environment

**Framework:** ESP-IDF (recommended) or Arduino

**Language:** C/C++

**Libraries:**
- Reticulum-ESP32 (mesh networking)
- LXMF (encrypted messaging)
- WiFi HaLow driver (ESP-IDF native)
- Camera driver (ESP32-CAM libraries)
- GPS parser (TinyGPS++ or custom NMEA)
- Display driver (GxEPD2 for e-Ink, Adafruit_SSD1306 for OLED)

### Firmware Architecture

```
main.c
├── init_halow()       // WiFi HaLow radio setup
├── init_ble()         // BLE advertising (backup mesh)
├── init_reticulum()   // Reticulum identity + LXMF
├── init_camera()      // OV3660 camera driver
├── init_gps()         // UART GPS parser
├── init_display()     // E-Ink/OLED display
├── task_mesh()        // Reticulum message handling (FreeRTOS task)
├── task_position()    // GPS position updates (FreeRTOS task)
├── task_camera()      // Camera capture on-demand (FreeRTOS task)
├── task_display()     // UI rendering (FreeRTOS task)
└── task_power()       // Battery monitoring + sleep (FreeRTOS task)
```

### Power Management

**Active Mode:** All radios on, camera ready
- Current draw: ~200-300mA
- Runtime: 5-10 hours (3000mAh battery)

**Eco Mode:** WiFi HaLow periodic check-in, camera off
- Current draw: ~50-100mA
- Runtime: 15-20 hours

**Deep Sleep:** All radios off, wake on timer or button
- Current draw: <1mA
- Runtime: >1 week

---

## ATAK Integration

### How HYPHA Feeds into Tactical Picture

```
HYPHA (handheld)
  ↓ WiFi HaLow/BLE/LoRa
SPORE (base station)
  ↓ FreeTAKServer
ATAK (Android device)
```

### Position Reporting

**HYPHA → SPORE:**
```c
// HYPHA firmware: Send GPS position via LXMF
lxmf_message_t msg;
msg.destination = SPOR3_IDENTITY;
msg.content = cbor_encode({
  "type": "position",
  "lat": gps.latitude,
  "lon": gps.longitude,
  "alt": gps.altitude,
  "timestamp": time(NULL)
});
lxmf_send(&msg);
```

**SPORE → ATAK:**
```python
# SPORE Python: Convert LXMF to CoT
cot_xml = f"""
<event version="2.0" uid="HYPHA-03" type="a-f-G-E-S" how="h-g-i-g-o">
  <point lat="{lat}" lon="{lon}" hae="{alt}" ce="10" le="10"/>
  <detail>
    <contact callsign="HYPHA-03 // Ranger"/>
    <status battery="{battery}"/>
  </detail>
</event>
"""
fretak_server.broadcast(cot_xml)
```

**ATAK Display:**
- Blue friendly icon appears at HYPHA position
- Callsign: "HYPHA-03 // Ranger"
- Battery status visible in details

### Messaging

**HYPHA → ATAK Chat:**
```c
// HYPHA: Send text message
lxmf_message_t msg;
msg.destination = BROADCAST;
msg.content = "Reached checkpoint Alpha";
lxmf_send(&msg);
```

**SPORE → ATAK:**
```python
# SPORE: Translate to TAK chat
cot_xml = f"""
<event version="2.0" uid="{msg_id}" type="b-t-f" how="h-e">
  <detail>
    <__chat id="All Chat Rooms" chatroom="All Chat Rooms">
      <chatgrp uid0="{sender_uid}" id="All Chat Rooms"/>
    </__chat>
    <link uid="{sender_uid}" relation="p-p" type="a-f-G-E-S"/>
    <remarks source="HYPHA-03" time="{timestamp}">{message_text}</remarks>
  </detail>
</event>
"""
```

### Waypoint Marking

**HYPHA → ATAK Marker:**
```c
// HYPHA: Mark position of interest
lxmf_message_t msg;
msg.destination = SPOR3_IDENTITY;
msg.content = cbor_encode({
  "type": "waypoint",
  "lat": gps.latitude,
  "lon": gps.longitude,
  "name": "Cache Location",
  "description": "Supplies stashed here"
});
lxmf_send(&msg);
```

**SPORE → ATAK:**
```python
# SPORE: Create CoT marker
cot_xml = f"""
<event version="2.0" uid="waypoint-{id}" type="b-m-p-s-p-loc" how="h-e">
  <point lat="{lat}" lon="{lon}" hae="0" ce="10" le="10"/>
  <detail>
    <contact callsign="{name}"/>
    <remarks>{description}</remarks>
  </detail>
</event>
"""
```

### Camera Attachment

**HYPHA → ATAK with Image:**
```c
// HYPHA: Capture and send image
uint8_t* jpeg_buf = camera_capture_jpeg();
lxmf_message_t msg;
msg.destination = SPOR3_IDENTITY;
msg.content = cbor_encode({
  "type": "image",
  "lat": gps.latitude,
  "lon": gps.longitude,
  "image": base64_encode(jpeg_buf)
});
lxmf_send(&msg);
```

**SPORE → ATAK:**
```python
# SPORE: Attach image to CoT
image_uid = f"image-{uuid.uuid4()}"
save_image(f"/atak/images/{image_uid}.jpg", image_data)

cot_xml = f"""
<event version="2.0" uid="{image_uid}" type="b-i-x-i" how="h-e">
  <point lat="{lat}" lon="{lon}" hae="0" ce="10" le="10"/>
  <detail>
    <image>
      <file>{image_uid}.jpg</file>
    </image>
  </detail>
</event>
"""
```

---

## Display UI Design

### E-Ink Page System (Simplified Teletext)

**296×128 resolution = ~37 chars × 16 lines**

**Page Navigation:**
- Button A: Previous page
- Button B: Next page
- Button C: Action (send message, mark waypoint, etc.)

**P100: Status Page**
```
┌─────────────────────────────────┐
│HYPHA-03 // "Ranger"      21:05 │
├─────────────────────────────────┤
│ SPORE-01: CONNECTED (GOOD)      │
│ Lattice: 5 nodes, 8 threads     │
│                                 │
│ GPS: 61.2181, -149.9003         │
│ Alt: 125m  Sats: 9  HDOP: 1.2  │
│                                 │
│ Battery: 68% (5.2h remaining)   │
│ Mode: ACTIVE                    │
│                                 │
│ Messages: 3 unread              │
│                                 │
│ [A] Menu  [B] Messages  [C] >  │
└─────────────────────────────────┘
```

**P200: Mesh Status**
```
┌─────────────────────────────────┐
│MESH STATUS               21:05  │
├─────────────────────────────────┤
│                                 │
│ SPORE-01 (THIS → 0m)            │
│  Thread: WiFi HaLow, -72dBm     │
│  Status: GOOD                   │
│                                 │
│ HYPHA-05 (via SPORE, 3.2km)     │
│  Thread: LoRa relay             │
│  Status: FAIR                   │
│                                 │
│ RHIZOME-12 (via SPORE, 1.8km)     │
│  Thread: LoRa                   │
│  Status: GOOD                   │
│                                 │
│ [A] < [B] Refresh [C] Details  │
└─────────────────────────────────┘
```

**P300: Messages**
```
┌─────────────────────────────────┐
│INBOX (3 unread)          21:05  │
├─────────────────────────────────┤
│                                 │
│ [NEW] SPORE-01 (20:48)          │
│ "Satellite pass NOAA-19 in 15m" │
│                                 │
│ [NEW] HYPHA-05 (20:32)          │
│ "Reached waypoint Bravo"        │
│                                 │
│ SPORE-01 (19:15)                │
│ "Weather alert: storm approach" │
│                                 │
│ [A] < [B] Read [C] Compose     │
└─────────────────────────────────┘
```

**P400: Waypoints**
```
┌─────────────────────────────────┐
│WAYPOINTS                 21:05  │
├─────────────────────────────────┤
│                                 │
│ 1. Camp Alpha (2.1km N)         │
│    61.2203, -149.8995           │
│                                 │
│ 2. Cache Bravo (5.8km NE)       │
│    61.2389, -149.8721           │
│                                 │
│ 3. Rally Point (1.2km W)        │
│    61.2175, -149.9156           │
│                                 │
│ [A] < [B] Mark Here [C] Nav >  │
└─────────────────────────────────┘
```

**P500: Camera**
```
┌─────────────────────────────────┐
│CAMERA                    21:05  │
├─────────────────────────────────┤
│                                 │
│ [Preview disabled on e-Ink]     │
│                                 │
│ Last capture: 20:42             │
│ Resolution: 640×480             │
│ Size: 42 KB                     │
│ Status: Sent to SPORE           │
│                                 │
│ GPS: 61.2181, -149.9003         │
│ Tagged: Yes                     │
│                                 │
│ [A] < [B] Capture [C] Settings │
└─────────────────────────────────┘
```

---

## Character LCD Option (Minimal)

**16×2 Display:**
```
HYPHA-03 68% 5N
MSG:3  GPS:LOCK
```

**20×4 Display:**
```
HYPHA-03 // Ranger
Mesh: 5N  Bat: 68%
GPS: LOCK  MSG: 3
[A]Menu [B]Msg [C]>
```

---

## Development Roadmap

### Week 1: Hardware Assembly
- [x] Order ESP32-S3 HT-HC33
- [ ] Order e-Ink display (Waveshare 2.9")
- [ ] Order GPS module (NEO-6M)
- [ ] Order battery + charging module
- [ ] 3D print enclosure or acquire project box
- [ ] Solder pin headers
- [ ] Wire display + GPS + battery
- [ ] Test power system (charging, monitoring)

### Week 2: Firmware Foundation
- [ ] Set up ESP-IDF toolchain
- [ ] Flash "Hello World" to ESP32-S3
- [ ] Test WiFi HaLow connectivity
- [ ] Test BLE advertising
- [ ] Test camera capture (save JPEG to flash)
- [ ] Test GPS UART (parse NMEA sentences)
- [ ] Test display (render text)

### Week 3: Reticulum Integration
- [ ] Port Reticulum core to ESP32 (or use existing port)
- [ ] Generate HYPHA cryptographic identity
- [ ] Establish WiFi HaLow link to SPORE
- [ ] Send/receive LXMF messages
- [ ] Verify end-to-end encryption
- [ ] Test store-and-forward (disconnect/reconnect)

### Week 4: Basic UI
- [ ] Implement page navigation (3 buttons)
- [ ] P100: Status page (mesh, GPS, battery)
- [ ] P200: Mesh nodes list
- [ ] P300: Message inbox
- [ ] P400: Waypoint list
- [ ] P500: Camera control
- [ ] Menu system (button inputs)

### Week 5: ATAK Integration
- [ ] Implement position reporting (GPS → LXMF → SPORE)
- [ ] Verify HYPHA appears in ATAK
- [ ] Implement messaging (text → LXMF → ATAK chat)
- [ ] Implement waypoint marking
- [ ] Test camera attachment (JPEG → SPORE → ATAK)
- [ ] Field test (range, battery life, usability)

### Week 6+: Polish & Expansion
- [ ] Power optimization (deep sleep modes)
- [ ] Battery calibration (accurate % estimation)
- [ ] Error handling (lost GPS, mesh disconnect)
- [ ] Firmware OTA updates (via SPORE)
- [ ] Add LoRa module (optional, SPI breakout)
- [ ] Ruggedization (waterproof enclosure)

---

## Power Budget

**Active Mode (all radios on):**
- ESP32-S3 core: ~80mA
- WiFi HaLow TX: ~120mA (peak)
- BLE: ~20mA
- GPS: ~30mA
- Camera (standby): ~10mA
- E-Ink (refresh): ~20mA (brief)
- **Total: ~200-300mA**

**3000mAh battery:**
- Active: 10-15 hours
- Eco (periodic check-in): 20-30 hours
- Deep sleep: >1 week

**Optimization Strategies:**
- Disable camera when not in use
- GPS duty cycle (sample every 30s, sleep between)
- WiFi HaLow low-power mode (beacon interval tuning)
- E-Ink partial refresh (faster, lower power)
- Deep sleep when stationary (wake on button or timer)

---

## Field Deployment Scenarios

### 1. **Hiking Scout (Primary Use Case)**
- HYPHA in backpack side pocket
- SPORE stays at camp (vehicle or tent)
- HYPHA reports position every 5 minutes
- Send text messages to SPORE/ATAK
- Mark waypoints (cache, hazard, rally point)
- Camera: Capture thumbnail on-demand

### 2. **Vehicle Convoy**
- HYPHA in each vehicle
- SPORE in lead vehicle (mesh hub)
- Real-time position tracking
- Inter-vehicle messaging
- Camera: Document obstacles/threats

### 3. **Stationary Observation Post**
- HYPHA deployed at overlook
- Deep sleep mode (wake on motion sensor)
- Periodic position check-in
- Camera: Capture on motion detect
- Ultra long battery life (>1 week)

### 4. **Emergency Relay**
- HYPHA deployed at high point (ridge, tower)
- WiFi HaLow + LoRa relay mode
- Store-and-forward for distant nodes
- Solar charging for indefinite runtime

---

## Enclosure Design

### Option A: 3D Printed Tactical Case

**Features:**
- Belt clip or MOLLE webbing mount
- Waterproof gasket (O-ring seal)
- Transparent window for e-Ink display
- Button access (mechanical switches or capacitive)
- Antenna port (RP-SMA bulkhead)
- USB-C charging port (waterproof plug)

**STL Files:** TBD (design in Blender or OpenSCAD)

### Option B: Hammond 1591 Project Box

**Model:** 1591XXSSBK (125 × 80 × 57 mm)
- Off-the-shelf enclosure (~$10)
- Drill holes for display, buttons, antenna
- Add gasket for water resistance
- Paint/hydrodip for tactical aesthetic

---

## Testing & Validation

### Bench Tests (Before Field Deploy)

**1. Range Test:**
- HYPHA at known distance from SPORE
- Measure RSSI at 100m, 500m, 1km, 2km
- Verify message delivery at max range

**2. Battery Life Test:**
- Full charge → run until shutdown
- Log power draw at each mode
- Validate runtime estimates

**3. GPS Accuracy:**
- Compare HYPHA GPS to known coordinates
- Test cold start, warm start, hot start times
- Verify position accuracy (<10m CEP)

**4. Camera Quality:**
- Capture test images at various lighting
- Verify JPEG compression
- Test transmission to SPORE (file size vs quality)

### Field Tests (Real-World Validation)

**1. Hike Test (8+ hours):**
- Carry HYPHA while hiking
- Report position every 5 minutes
- Send messages at waypoints
- Capture photos at landmarks
- Verify battery lasts full hike

**2. Vehicle Test:**
- Mount HYPHA in vehicle
- Drive convoy with multiple HYPHAs
- Verify real-time tracking in ATAK
- Test messaging while moving

**3. Static Relay Test:**
- Deploy HYPHA at remote location
- Leave for 24+ hours
- Verify store-and-forward works
- Check battery after retrieval

---

## Troubleshooting

### WiFi HaLow Not Connecting to SPORE
- Check antenna connection (RP-SMA tight?)
- Verify SPORE HaLow is broadcasting SSID
- Check frequency band match (902-928 MHz)
- Increase TX power if allowed by regulations

### GPS Not Locking
- Ensure clear view of sky (no metal enclosure blocking)
- Wait 5-10 minutes for cold start
- Check UART wiring (TX ↔ RX swapped?)
- Verify baud rate (9600 for NEO-6M)

### E-Ink Display Ghosting
- Full refresh every 10 partial refreshes
- Clear display before deep sleep
- Check power supply voltage (e-Ink needs stable 3.3V)

### Battery Draining Fast
- Check for WiFi HaLow staying in active TX mode
- Disable camera if not needed
- Reduce GPS sample rate (60s instead of 10s)
- Enter deep sleep when stationary

---

## Future Enhancements

### Phase 2: LoRa Expansion
- Add SX1262 LoRa breakout module (SPI)
- Ultra long-range backup (5-50km)
- Slower data rate, perfect for position updates

### Phase 3: Environmental Sensors
- Add BME280 (temp, humidity, pressure)
- Report local weather to SPORE
- Appears in ATAK as weather overlay

### Phase 4: Motion Detection
- Add PIR sensor or accelerometer
- Wake from deep sleep on movement
- Auto-capture camera on motion

### Phase 5: Solar Charging
- Add small solar panel (5V, 1-2W)
- Trickle charge during day
- Indefinite runtime for static deployments

---

## Appendix: CBOR Message Schemas

### Position Report
```cbor
{
  "type": "position",
  "node": "HYPHA-03",
  "ts": 1710532800,
  "lat": 61.2181,
  "lon": -149.9003,
  "alt": 125,
  "speed": 1.2,
  "heading": 270,
  "battery": 68,
  "sig": "ed25519:abc123..."
}
```

### Text Message
```cbor
{
  "type": "message",
  "node": "HYPHA-03",
  "ts": 1710532800,
  "text": "Reached checkpoint Alpha",
  "sig": "ed25519:def456..."
}
```

### Waypoint
```cbor
{
  "type": "waypoint",
  "node": "HYPHA-03",
  "ts": 1710532800,
  "lat": 61.2181,
  "lon": -149.9003,
  "name": "Cache Location",
  "description": "Supplies stashed here",
  "sig": "ed25519:ghi789..."
}
```

### Camera Capture
```cbor
{
  "type": "image",
  "node": "HYPHA-03",
  "ts": 1710532800,
  "lat": 61.2181,
  "lon": -149.9003,
  "image": "<base64 JPEG data>",
  "resolution": "640x480",
  "size": 42000,
  "sig": "ed25519:jkl012..."
}
```

---

**END HYPHA DEV GUIDE**

*Last updated: 2026-03-15*  
*Status: Hardware ordered, ready for assembly*
