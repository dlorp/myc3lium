# OBD2-TUI Architecture

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                         │
│  (ratatui - Terminal Rendering, Input Handling)              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION CORE                          │
│  - State Management                                           │
│  - Event Loop (user input, data updates, timer ticks)        │
│  - View Routing (dashboard, DTC, logger, settings)           │
└───────────┬─────────────────────────┬───────────────────────┘
            │                         │
            ▼                         ▼
┌─────────────────────┐   ┌─────────────────────────────────┐
│   ELM327 DRIVER     │   │      DATA LOGGER                │
│  - Serial I/O       │   │  - CSV Writer                   │
│  - AT Commands      │   │  - Session Management           │
│  - PID Parsing      │   │  - Playback Engine              │
│  - Error Handling   │   │  - Export Utilities             │
└──────────┬──────────┘   └─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERIAL PORT LAYER                          │
│  (tokio-serial - async UART communication)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
                  [ ELM327 Adapter ]
                        │
                        ▼
                  [ Vehicle ECU ]
```

## Module Breakdown

### 1. UI Layer (`src/ui/`)

**Responsibilities:**
- Render TUI components using ratatui
- Handle keyboard input and navigation
- Maintain layout state (current view, selected item)
- Format data for display (gauges, graphs, tables)

**Key Components:**
- `dashboard.rs` - Live sensor overview
- `dtc_viewer.rs` - Fault code display
- `logger.rs` - Recording interface
- `settings.rs` - Configuration menu
- `theme.rs` - PSX color scheme and styling

**Data Flow:**
- Receives immutable app state references
- Emits user actions as events
- Pure rendering (no business logic)

### 2. Application Core (`src/app.rs`)

**Responsibilities:**
- Central event loop (tokio async runtime)
- State management (current sensors, DTCs, connection status)
- Coordinate between UI, driver, and logger
- Handle view transitions and mode switches

**State Structure:**
```rust
pub struct AppState {
    pub connection: ConnectionState,
    pub sensors: HashMap<PidId, SensorReading>,
    pub dtc_list: Vec<DiagnosticCode>,
    pub logger: LoggerState,
    pub current_view: View,
    pub freeze_frame: Option<FreezeFrame>,
}
```

**Event Types:**
- `UserInput(KeyEvent)` - Keyboard press
- `DataUpdate(PidId, Value)` - New sensor reading
- `ConnectionChange(Status)` - ELM327 connect/disconnect
- `TimerTick` - Periodic refresh trigger

### 3. ELM327 Driver (`src/elm327/`)

**Responsibilities:**
- Abstract serial communication
- Implement AT command protocol
- Parse OBD-II responses
- Handle timeout and retry logic
- Auto-detect vehicle protocol

**Key Modules:**
- `connection.rs` - Serial port setup, baud rate detection
- `commands.rs` - AT command builders
- `parser.rs` - Response parsing (hex to typed values)
- `protocol.rs` - Protocol detection (ISO 9141, KWP2000, CAN)
- `pid.rs` - PID definitions and decoders

**Example API:**
```rust
pub struct Elm327Driver {
    port: SerialPort,
    protocol: Protocol,
}

impl Elm327Driver {
    pub async fn connect(port_name: &str) -> Result<Self>;
    pub async fn read_pid(&mut self, pid: PidId) -> Result<PidValue>;
    pub async fn read_dtcs(&mut self) -> Result<Vec<DtcCode>>;
    pub async fn clear_dtcs(&mut self) -> Result<()>;
    pub async fn get_vin(&mut self) -> Result<String>;
}
```

**Communication Pattern:**
- Send: `01 0C\r` (read RPM)
- Recv: `41 0C 1A F8\r` (response: 4 bytes)
- Parse: `(0x1A << 8 | 0xF8) / 4 = 1726 RPM`

### 4. Data Logger (`src/logger/`)

**Responsibilities:**
- Record sensor data to CSV
- Manage log sessions (start/stop/pause)
- Playback historical data
- Generate summary statistics
- Export reports

**CSV Format:**
```csv
timestamp,session_id,pid,name,value,unit
2026-03-23T03:15:42Z,abc123,0C,RPM,2450,rpm
2026-03-23T03:15:42Z,abc123,05,COOLANT_TEMP,90,celsius
```

**Features:**
- Configurable sample rate (1-10 Hz)
- Buffer management (avoid blocking UI on write)
- Automatic file rotation (by session or size)
- Compression support (gzip for archived logs)

### 5. DTC Database (`src/dtc/`)

**Responsibilities:**
- Decode fault codes to human-readable descriptions
- Provide severity levels and troubleshooting hints
- Support standard OBD-II codes (P0xxx, P2xxx)
- Allow custom code definitions (manufacturer-specific)

**Data Structure:**
```rust
pub struct DtcDefinition {
    pub code: String,        // "P0171"
    pub description: String, // "System Too Lean (Bank 1)"
    pub severity: Severity,  // Critical, Warning, Info
    pub causes: Vec<String>, // Possible fault causes
    pub fixes: Vec<String>,  // Suggested actions
}
```

**Storage:**
- Embedded JSON database (`assets/dtc-codes.json`)
- Runtime lookup via HashMap
- Fallback to generic descriptions for unknown codes

## Threading Model

**Main Thread:**
- TUI rendering (ratatui draw loop)
- User input handling
- State updates from channels

**Async Runtime (Tokio):**
- Serial I/O (non-blocking UART reads/writes)
- Data logging (async file writes)
- Periodic PID polling (interval timer)

**Communication:**
- `tokio::sync::mpsc` channels for event passing
- `tokio::sync::Mutex` for shared state (minimize locks)
- `crossterm` event stream for keyboard input

## Polling Strategy

**Challenge:** Balance UI responsiveness with ECU load.

**Approach:**
- **Priority tiers:**
  - High: RPM, speed, coolant temp (10 Hz)
  - Medium: MAF, O2 sensors, fuel pressure (5 Hz)
  - Low: VIN, calibration ID (once on connect)
- **Round-robin within tier** to avoid starvation
- **Adaptive rate** based on vehicle protocol speed
- **Batch requests** for CAN-based protocols (faster than ISO)

**Example Schedule (100ms tick):**
```
Tick 0: RPM
Tick 1: Speed
Tick 2: RPM + MAF
Tick 3: Coolant
Tick 4: RPM + O2 (B1S1)
Tick 5: Speed
Tick 6: RPM + Fuel Pressure
Tick 7: Coolant
Tick 8: RPM + O2 (B1S2)
Tick 9: Speed
```

## Error Handling

**Connection Errors:**
- Auto-retry with exponential backoff
- Display connection status in UI
- Allow manual reconnect via hotkey

**Protocol Errors:**
- Log malformed responses
- Skip bad readings (don't crash)
- Display error count in status bar

**ECU Not Responding:**
- Timeout after 500ms per request
- Fall back to slower poll rate
- Alert user if persistent

## Configuration System

**File:** `~/.config/obd2-tui/config.toml`

```toml
[connection]
port = "/dev/ttyUSB0"
baud_rate = 38400
protocol = "auto"

[display]
theme = "psx"
refresh_rate = 10
units = "imperial"  # or "metric"

[logging]
auto_start = false
log_dir = "~/.local/share/obd2-tui/logs"
sample_rate = 5

[pids]
enabled = [
    "0C", # RPM
    "0D", # Speed
    "05", # Coolant
    "10", # MAF
    "14", # O2 B1S1
]
```

**Runtime Override:**
- Command-line flags for port/baud
- Hot-reload config on SIGHUP
- Save session settings on clean exit

## Testing Strategy

**Unit Tests:**
- PID parser correctness (known inputs → expected values)
- DTC decoder accuracy
- Logger CSV format validation

**Integration Tests:**
- Mock serial port for driver testing
- Simulated ELM327 responses
- Playback recorded sessions

**Hardware Tests:**
- Test with real ELM327 + vehicle
- Verify protocol detection (ISO, KWP, CAN)
- Stress test polling rates
- Battery safety (don't drain vehicle battery)

## Performance Targets

- **UI Latency:** < 16ms frame time (60 FPS)
- **Serial Throughput:** 10-20 PIDs/sec (standard), 50+ (CAN)
- **Memory Usage:** < 50 MB RSS
- **CPU Usage:** < 5% idle, < 20% active polling

## Security Considerations

- **No network access** (local-only tool)
- **Read-only by default** (require confirmation for clear DTCs)
- **No ECU writes** (prevent accidental reprogramming)
- **Validate all serial input** (prevent injection attacks)

## Future Extensions

- **Plugin system:** Custom PID definitions via TOML
- **Alerts:** Threshold-based notifications (e.g., coolant > 220°F)
- **Multi-vehicle profiles:** Save per-VIN configurations
- **GPS integration:** Correlate sensor data with location
- **Remote monitoring:** Optional WebSocket server for phone display

---

**Next Step:** Prototype `src/elm327/connection.rs` with basic serial I/O.

