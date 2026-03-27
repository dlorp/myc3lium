# obd2view Architecture

## System Design

```
┌─────────────────────────────────────────────────────────┐
│                     obd2view TUI                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │Dashboard │  │   DTC    │  │  Logger  │  │ Config │ │
│  │  View    │  │  View    │  │   View   │  │  View  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │             │              │            │      │
│       └─────────────┴──────────────┴────────────┘      │
│                         │                              │
│                    ┌────▼────┐                         │
│                    │  Event  │                         │
│                    │  Loop   │                         │
│                    └────┬────┘                         │
└─────────────────────────┼──────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │   OBD2    │
                    │  Manager  │
                    └─────┬─────┘
                          │
        ┏━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┓
        ▼                 ▼                  ▼
   ┌─────────┐      ┌──────────┐      ┌──────────┐
   │  ELM327 │      │   PID    │      │   DTC    │
   │ Protocol│      │  Parser  │      │  Parser  │
   └────┬────┘      └──────────┘      └──────────┘
        │
   ┌────▼────┐
   │ Serial  │
   │  Port   │
   └────┬────┘
        │
   ┌────▼────┐
   │ Vehicle │
   │  ECU    │
   └─────────┘
```

## Core Components

### 1. TUI Layer (`src/ui/`)
- **Dashboard:** Real-time gauge rendering
- **DTC View:** Trouble code list + details
- **Logger View:** Session history browser
- **Config View:** Settings editor
- Built with `ratatui`, event-driven updates

### 2. OBD2 Manager (`src/obd2/`)
- **Connection:** Serial port management
- **Protocol:** ELM327 command wrapper
- **Polling:** Async PID request loop
- **State:** Vehicle connection status

### 3. Protocol Layer (`src/protocol/`)
- **ELM327:** AT command implementation
- **PID Parser:** Mode 01/02/09 response decoding
- **DTC Parser:** Mode 03 code extraction
- **Checksum:** CAN frame validation

### 4. Data Layer (`src/data/`)
- **Database:** SQLite session storage
- **Models:** Sensor reading structs
- **Export:** CSV/JSON serialization

### 5. Definitions (`src/defs/`)
- **PIDs:** Mode 01 parameter definitions
- **DTCs:** Trouble code lookup tables
- **Units:** Conversion helpers (°F/°C, mph/km/h)

## Data Flow

### Live Data Loop
```
1. UI requests update (60Hz render loop)
   ↓
2. OBD2 Manager checks cache age (<200ms = use cached)
   ↓
3. If stale, send Mode 01 multi-PID request:
   "01 0C 0D 05 0F 11 04" (RPM, speed, temps, throttle, load)
   ↓
4. ELM327 returns: "41 0C 26 1A 0D 42 05 E1 ..."
   ↓
5. PID Parser extracts values:
   - RPM = (0x26 * 256 + 0x1A) / 4 = 2438 rpm
   - Speed = 0x42 = 66 km/h
   - Coolant = 0xE1 - 40 = 185°C
   ↓
6. Update cache, notify UI
   ↓
7. UI renders gauges with new values
```

### DTC Reading
```
1. User presses [3] for DTC view
   ↓
2. Send "03" (request stored DTCs)
   ↓
3. ECU responds: "43 02 01 33 02 71 00 00"
   - 02 codes
   - P0133 (0x0133)
   - P0271 (0x0271)
   ↓
4. Lookup definitions:
   - P0133: O2 Sensor Circuit Slow Response (Bank 1)
   - P0271: Injector 3 Circuit Low
   ↓
5. For each code, request freeze frame (Mode 02)
   ↓
6. Display in DTC view with timestamps
```

## Performance Targets

- **UI Framerate:** 60 FPS (smooth gauges)
- **Poll Rate:** 5 Hz (live data refresh)
- **Latency:** <50ms PID response time
- **Memory:** <10MB resident (efficient!)
- **CPU:** <5% idle, <15% active polling

## Error Handling

### Connection Failures
- Auto-retry with exponential backoff
- Graceful degradation (show last known values)
- User notification in status bar

### Protocol Errors
- Invalid checksums → discard frame
- Timeout (>1s) → mark stale, retry
- Unsupported PID → gray out in UI

### Serial Issues
- Device unplugged → reconnect loop
- Permission denied → helpful error message
- Baud rate mismatch → try common rates

## Configuration

### ~/.obd2viewrc (TOML)
```toml
[connection]
device = "/dev/ttyUSB0"
baud_rate = 38400
protocol = "auto"  # or specific: "6" for ISO 15765-4 CAN

[ui]
theme = "psx"  # psx, gameboy, metro, terminal
units = "imperial"  # imperial, metric
refresh_rate = 60

[logging]
enabled = true
path = "~/.local/share/obd2view/sessions/"
auto_export = false

[vehicle]
name = "2000 Subaru Impreza"
vin = "JF1GC8K64YG123456"
notes = "EJ22, 5MT, 180k miles"
```

## Database Schema

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    vehicle_name TEXT,
    protocol TEXT
);

CREATE TABLE readings (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    pid TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE dtcs (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    freeze_frame BLOB,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_readings_session ON readings(session_id);
CREATE INDEX idx_readings_time ON readings(timestamp);
CREATE INDEX idx_dtcs_session ON dtcs(session_id);
```

## Security Considerations

- **Read-only by default:** No ECU writes without explicit flag
- **No telemetry:** Zero network activity
- **Local storage:** All data stays on device
- **Open source:** Auditable, no black boxes

## Future Extensions

- **CAN bus sniffing:** Raw frame inspection
- **Custom PIDs:** Manufacturer-specific codes
- **Multi-vehicle:** Profile switching
- **Performance logging:** Track lap times, g-forces
- **Plugin system:** User scripts for custom metrics

---

**Design Philosophy:**
- **Simplicity:** Do one thing well (diagnostics)
- **Performance:** Fast enough for real-time use
- **Reliability:** Graceful degradation on errors
- **Transparency:** User understands what's happening
