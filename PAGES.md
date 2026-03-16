# myc3lium - Page Layouts

**Grid:** 40 columns × 25 rows (teletext standard)  
**Colors:** 8-color palette (Black, Red, Green, Yellow, Blue, Magenta, Cyan, White)  
**Navigation:** Number keys (P100, P200, etc.) or touch zones

---

## Page Map

**100 Series: System & Menu**
- P100: Main menu
- P101: System status
- P102: Power/battery
- P103: Radio status

**200 Series: Mesh Network**
- P200: Topology graph
- P201: Node list
- P202: Link quality
- P203: Traffic stats

**300 Series: Messaging**
- P300: Inbox
- P301: Compose
- P302: Channels
- P303: History

**400 Series: Maps**
- P400: **Main map view** (full-screen)
- P401: Waypoints
- P402: Routes
- P403: Layers
- P404: Custom maps

**500 Series: Intelligence**
- P500: Satellite tracker
- P501: RF waterfall
- P502: Signal log
- P503: Cameras (future)

**600 Series: Configuration**
- P600: Radio config
- P601: Reticulum
- P602: Meshtastic
- P603: SDR
- P604: Maps
- P605: Display

---

## P100 - Main Menu

```
┌──────────────────────────────────────┐
│█MYC3LIUM█──────18:52──[GPS: LOCK]│
├──────────────────────────────────────┤
│                                      │
│  ╔════════════════════════════════╗ │
│  ║      MYC3LIUM v1.0             ║ │
│  ╚════════════════════════════════╝ │
│                                      │
│  [200] MESH NETWORK                 │
│    └─ 3 nodes online, 2 hops max    │
│                                      │
│  [300] MESSAGING                    │
│    └─ 5 unread messages             │
│                                      │
│  [400] TACTICAL MAP                 │
│    └─ GPS locked, 12 waypoints      │
│                                      │
│  [500] INTELLIGENCE                 │
│    └─ Next sat pass: 19:34 (42min)  │
│                                      │
│  [600] CONFIGURATION                │
│    └─ Battery: 68% (ECO mode)       │
│                                      │
│  STATUS:                            │
│  ▓▓▓▓▓▓▓░░░ LoRa   [ONLINE]        │
│  ▓▓▓▓▓░░░░░ HaLow  [ONLINE]        │
│  ▓▓▓▓▓▓▓▓░░ WiFi   [ONLINE]        │
│                                      │
└[ESC]EXIT──────────────────────[?]HELP┘
```

**Touch Zones:**
- Top bar: Status (tap → P101)
- Menu items: Direct navigation to pages
- Status bars: Radio details (→ P103)

---

## P200 - Mesh Topology

```
┌──────────────────────────────────────┐
│MESH NETWORK────────18:52──[3 NODES]│
├──────────────────────────────────────┤
│                                      │
│ TOPOLOGY:                            │
│                                      │
│    ┌───NODE_02 (5.2km NE)           │
│    │   LoRa -85dBm, 1 hop           │
│    │                                 │
│  ◉─┼───NODE_03 (12.8km SW)          │
│ THIS   LoRa -92dBm, 2 hops          │
│    │                                 │
│    └───RELAY_01 (0.8km N)           │
│        HaLow -78dBm, 1 hop          │
│                                      │
│ ROUTES:                              │
│  THIS → NODE_02: Direct (LoRa)      │
│  THIS → NODE_03: via NODE_02        │
│  THIS → RELAY_01: Direct (HaLow)    │
│                                      │
│ TRAFFIC (1h):                        │
│  Messages:  ▓▓▓▓▓▓░░░░  47          │
│  Data:      ▓▓▓░░░░░░░  2.3 MB      │
│  Overhead:  ▓░░░░░░░░░  142 KB      │
│                                      │
└[100]MENU─[201]NODES──────[203]STATS┘
```

**Touch Zones:**
- Node names: Details (→ P201)
- Route lines: Link quality (→ P202)
- Traffic bars: Expand details

---

## P300 - Messaging Inbox

```
┌──────────────────────────────────────┐
│INBOX───────────────18:52──[5 UNREAD]│
├──────────────────────────────────────┤
│                                      │
│ ┌─[NEW]─18:45─NODE_02─via LoRa─────┐│
│ │"At waypoint Alpha. All clear.    ││
│ │ Proceeding to Bravo. -K"         ││
│ └─────────────────────[R]REPLY─────┘│
│                                      │
│ ┌─[NEW]─18:32─NODE_03─via LoRa/2hop┐│
│ │"Lost GPS lock near grid B4.      ││
│ │ Using dead reckoning. -J"        ││
│ └─────────────────────[R]REPLY─────┘│
│                                      │
│ ┌──18:15─RELAY_01─via HaLow────────┐│
│ │"Satellite pass 19:34. Recording  ││
│ │ METEOR-M. Will relay image. -A"  ││
│ └─────────────────────[R]REPLY─────┘│
│                                      │
│ ┌──17:58─NODE_02─via LoRa──────────┐│
│ │"Heading back. ETA 20 min. -K"    ││
│ └─────────────────────[R]REPLY─────┘│
│                                      │
└[301]COMPOSE────[302]CHANNELS────[▼]┘
```

**Touch Zones:**
- Message box: Expand (full screen)
- [R]REPLY: Quick reply (→ P301 with recipient)
- Sender name: Node details
- Transport (LoRa/HaLow): Link info

---

## P301 - Compose Message

```
┌──────────────────────────────────────┐
│COMPOSE MESSAGE─────18:52─────────────│
├──────────────────────────────────────┤
│                                      │
│ TO: [NODE_02_____________]  [ALL]   │
│                                      │
│ TRANSPORT:                           │
│  (•) Auto (best route)               │
│  ( ) LoRa only                       │
│  ( ) HaLow only                      │
│  ( ) WiFi mesh only                  │
│                                      │
│ MESSAGE:                             │
│ ┌────────────────────────────────────┤
│ │Received. Confirming waypoint     ││
│ │Alpha clear. Continue to Bravo.   ││
│ │Check in at 1930. -L              ││
│ │                                  ││
│ │                                  ││
│ │                                  ││
│ │                                  ││
│ │                                  ││
│ │                                  ││
│ └──────────────────────────────────┘│
│ [120/280 chars]  [ENCRYPTED: YES]   │
│                                      │
└[SEND]──────[ATTACH]──────[ESC]CANCEL┘
```

**Touch Zones:**
- TO field: Select recipient (contacts list)
- [ALL]: Broadcast to all nodes
- Transport radio buttons: Force specific radio
- Message area: On-screen keyboard
- [SEND]: Transmit
- [ATTACH]: Add waypoint/position

---

## P400 - Tactical Map (PRIMARY INTERFACE)

```
┌──────────────────────────────────────┐
│MAP────────────────18:52───[Z:14]────│
├──────────────────────────────────────┤
│                                      │
│  ┌──────────────────────────────┐   │
│  │░░░░▓▓▓▓████████▓▓░░          │   │
│  │░░▓▓▓▓██◉███████▓▓░           │   │
│  │░▓▓████★██●██████▓░           │   │
│  │▓▓██████████●████▓            │   │
│  │▓███●█████W██████▓            │   │
│  │░▓▓███████████▓▓░             │   │
│  │  ░░▓▓▓▓▓▓▓░░                 │   │
│  └──────────────────────────────┘   │
│                                      │
│ ◉ YOUR POS    61.2181°N 149.9003°W  │
│ ● MESH NODE   ★ WAYPOINT  W WEATHER │
│                                      │
│ LAYERS: [√]OSM [√]Nodes [ ]Sat      │
│ ZOOM: [+][-]  PAN: Touch/Arrow      │
│                                      │
└[401]WPT──[402]ROUTE──[403]LAYER─[<>]┘
```

**Full-screen mode:** Tap map → hides all chrome, map fills screen

**Gestures:**
- **Pinch:** Zoom in/out
- **Drag:** Pan
- **Long press:** Create waypoint
- **Double tap:** Center on position
- **Two-finger rotate:** Rotate map (optional)

**Overlay Icons:**
- ◉ Your position (GPS, live update)
- ● Mesh nodes (color = signal strength)
- ★ Waypoints (tap for details)
- W Weather overlay (sat imagery)

**Shader Pipeline:**
1. Load OSM tiles from MBTiles
2. Quantize to 8-color teletext palette
3. Overlay GPS track, mesh nodes, waypoints
4. Apply CRT scanlines/vignette
5. Render to screen

---

## P401 - Waypoint Manager

```
┌──────────────────────────────────────┐
│WAYPOINTS───────────18:52──[12 TOTAL]│
├──────────────────────────────────────┤
│                                      │
│ ┌─ALPHA──────────────────[ACTIVE]──┐│
│ │ 61.2245°N 149.8876°W             ││
│ │ Elev: 125m  Dist: 2.3km (NE)     ││
│ │ Notes: "Rally point primary"     ││
│ │ [NAVIGATE] [SHARE] [DELETE]      ││
│ └──────────────────────────────────┘│
│                                      │
│ ┌─BRAVO──────────────────────────────│
│ │ 61.2198°N 149.9156°W             ││
│ │ Elev: 98m   Dist: 1.1km (W)      ││
│ │ Notes: "Backup location"         ││
│ │ [NAVIGATE] [SHARE] [DELETE]      ││
│ └──────────────────────────────────┘│
│                                      │
│ ┌─HOME BASE────────────[DEFAULT]────│
│ │ 61.2181°N 149.9003°W (CURRENT)   ││
│ │ Elev: 105m  Dist: 0.0km          ││
│ │ Notes: "Main terminal location"  ││
│ │ [NAVIGATE] [SHARE] [DELETE]      ││
│ └──────────────────────────────────┘│
│                                      │
└[CREATE]──────[IMPORT]──────[400]MAP─┘
```

**Touch Zones:**
- Waypoint box: Expand details
- [NAVIGATE]: Set as destination (→ P402 route)
- [SHARE]: Send via mesh to other nodes
- [DELETE]: Remove waypoint
- [CREATE]: Manual entry or long-press on map
- [IMPORT]: Load from .gpx file

---

## P500 - Satellite Tracker

```
┌──────────────────────────────────────┐
│SATELLITE INTEL─────18:52─[NEXT:42m]│
├──────────────────────────────────────┤
│                                      │
│ NEXT PASS: METEOR-M N2-3            │
│  AOS: 19:34:22  MAX EL: 67°  TCA    │
│  LOS: 19:48:11  Duration: 13m 49s   │
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░  42 min    │
│                                      │
│ AUTO-CAPTURE: [√] Enabled           │
│  Pre-warm SDR: 2 min before AOS     │
│  Record: LRPT 137.9 MHz             │
│  Decode: Auto (SatDump)             │
│  Save: /data/sat/YYYYMMDD_HHMM.png  │
│                                      │
│ VISIBLE NOW: (none)                 │
│                                      │
│ LAST CAPTURE:                        │
│  NOAA 19  18:15 UTC  Quality: 87%   │
│  ┌──────────────────────────────┐   │
│  │░░▓▓▓▓████████████▓▓░░        │   │
│  │░▓▓████████████████▓░         │   │
│  │▓▓██████████████████▓         │   │
│  └──────────────────────────────┘   │
│  [VIEW FULL] [ADD TO MAP] [DELETE]  │
│                                      │
└[501]WATERFALL────────────[SCHEDULE]─┘
```

**Auto-capture workflow:**
1. Satellite pass prediction (pyorbital)
2. SDR warms up 2 min before AOS
3. Recording starts at AOS
4. SatDump decodes in real-time
5. Image saved + georeferenced
6. Option to add as map overlay

---

## P501 - RF Waterfall

```
┌──────────────────────────────────────┐
│RF MONITOR──────────18:52─[SCANNING]│
├──────────────────────────────────────┤
│                                      │
│ FREQ: 915.0 MHz   BW: 2.0 MHz       │
│ GAIN: 30 dB       MODE: Waterfall   │
│                                      │
│ WATERFALL:                           │
│  ░░░░▓▓▓████████▓▓▓░░░              │
│  ░░░▓▓▓▓██████████▓▓░░              │
│  ░░▓▓▓████████████▓▓░               │
│  ░▓▓▓▓████████████▓▓░               │
│  ▓▓████████████████▓▓               │
│  ▓▓████████████████▓▓               │
│  ░▓▓████████████████▓               │
│  ░░▓▓██████████████▓░               │
│  ░░░▓▓▓██████████▓▓░                │
│  ░░░░▓▓▓████████▓▓░                 │
│                                      │
│ DETECTED SIGNALS:                    │
│  915.2 MHz  LoRa  -82dBm  [MESH]    │
│  915.8 MHz  LoRa  -95dBm  [MESH]    │
│  433.5 MHz  FSK   -70dBm  [UNKNOWN] │
│                                      │
└[◄][►]FREQ──[+][-]GAIN──[502]LOG────┘
```

**Real-time shader rendering:**
- FFT computed every frame
- Waterfall scrolls down
- Color = signal strength
- Teletext palette quantization

**Touch Zones:**
- [◄][►]: Tune frequency (±1 MHz)
- [+][-]: Adjust gain
- Signal line: Details → P502

---

## P600 - Radio Configuration

```
┌──────────────────────────────────────┐
│RADIO CONFIG────────18:52─────────────│
├──────────────────────────────────────┤
│                                      │
│ LoRa (SX1262):                       │
│  Frequency:  [915.0___] MHz         │
│  Bandwidth:  [125_____] kHz         │
│  Spreading:  [8_______] (7-12)      │
│  TX Power:   [17______] dBm         │
│  Status:     [ONLINE] ▓▓▓▓▓▓▓░░░    │
│                                      │
│ WiFi HaLow (HT-HC01):                │
│  Frequency:  [915.0___] MHz         │
│  Channel:    [AUTO____]             │
│  TX Power:   [20______] dBm         │
│  Status:     [ONLINE] ▓▓▓▓▓▓░░░░    │
│                                      │
│ WiFi Mesh (BCM43455):                │
│  Band:       [2.4GHz__] / 5GHz      │
│  Channel:    [11______] (1-13)      │
│  Mode:       [802.11s_] (BATMAN-adv)│
│  Status:     [ONLINE] ▓▓▓▓▓▓▓▓░░    │
│                                      │
│ [APPLY] [RESET] [TEST CONNECTION]   │
│                                      │
└[100]MENU────[601]RETIC───[602]MESH──┘
```

**Configuration stored in:** `data/config/user.toml`

**Changes require:**
- Daemon restart (Reticulum, Meshtastic bridge)
- [TEST CONNECTION] validates before applying

---

## Navigation Flow

```
        P100 (Main Menu)
         │
    ┌────┼────┬────┬────┐
    │    │    │    │    │
  P200 P300 P400 P500 P600
  Mesh  Msg  Map  Intel Config
    │    │    │    │    │
  ┌─┼─┐  │  ┌─┼─┐  │  ┌─┼─┐
 201 202 │ 401 402 │ 601 602
      203 │ 403 404 │ 603 604
      │   │    │    │    605
    P303  │  P404  │
          │        │
        P300     P501
        Inbox    Waterfall
                   │
                 P502
                  Log
```

**Quick Keys:**
- **0**: P100 (main menu)
- **2**: P200 (mesh)
- **3**: P300 (inbox)
- **4**: P400 (map) ← primary interface
- **5**: P500 (sat)
- **6**: P600 (config)
- **ESC**: Back / previous page
- **?**: Help overlay

---

## Common UI Elements

**All pages have:**
- **Top bar:** Title, time, status icon
- **Bottom bar:** Navigation buttons
- **Touch zones:** Clearly defined tap areas
- **Keyboard shortcuts:** For every action

**Color scheme (teletext palette):**
- **Background:** Black
- **Text:** White / Cyan
- **Highlights:** Yellow
- **Warnings:** Red / Magenta
- **Success:** Green
- **Inactive:** Blue / Dark gray

**Character grid:** 40×25 (teletext standard)

**Fonts:** Monospace, bitmap-rendered via shader

---

**Next:** See **SHADERS.md** for rendering pipeline details.
