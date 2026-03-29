# Changelog

All notable changes to MYC3LIUM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.4.1] - 2026-03-28

### Added
- 5GHz WiFi band selection for BATMAN mesh (`batman_band` field in MeshConfig)
- Cross-field validation: `@model_validator` rejects invalid band/channel combinations (e.g., channel 165 on 2.4GHz)
- Valid 5GHz channel whitelist (36, 40, 44, ... 165) — rejects non-standard channels like 37
- P600 band selector with dynamic channel range (1-11 for 2.4GHz, 36-165 for 5GHz)
- Channel auto-reset when switching bands (prevents stale values)
- First-boot setup wizard documented in README and QUICKSTART

### Fixed
- WebUI URL: `http://<pi-ip>:8000` corrected to `http://myc3.local` across all docs
- Version references: v1.0.0/v2.0.0 updated to v0.4.x across QUICKSTART, API.md, deployment README
- Hardware references: Heltec HT-HC01P updated to ESP32 USB boards (actual hardware)
- Service name: `myc3lium-backend` corrected to `myc3lium` (actual systemd unit) across all docs
- Backend dev command: `python main.py` corrected to `uvicorn app.main:app`
- Hardcoded IPs (10.13.0.1) replaced with `myc3.local` in API.md examples
- `RESTARTABLE_SERVICES` whitelist: `"myc3lium-backend"` updated to `"myc3lium"`
- P600 `batman_band` type narrowed from `string` to `'2.4GHz' | '5GHz'` literal
- API.md health response format updated to match actual backend output
- API.md auth section now documents actual API key auth on protected endpoints

## [0.4.0] - 2026-03-28

### Added
- TOML-based configuration system (Phase 6): Pydantic models for radio, mesh, display, system settings
- Config REST API: GET/PATCH `/api/config/{section}`, first-boot detection, whitelisted service restart
- P600 configuration hub: 4-section config page with per-section save, validation feedback
- First-boot setup wizard at `/setup`: guided hostname, radio, mesh configuration
- Teletext form components: TeletextInput, TeletextSelect, TeletextToggle
- Meshtastic-to-MeshStore bridge: real radio nodes now appear in `/api/nodes` and P200 lattice map
- Zod runtime validation on all WebSocket data before Zustand store ingestion (NodeSchema, ThreadSchema, MessageSchema, RemovalSchema)
- `meshtastic_bridge.py`: maps MeshtasticNode to unified Node/Thread models with SNR-to-quality conversion
- Multiple WS callback support on MeshtasticService (list pattern replaces single callback)
- Pydantic mypy plugin enabled for proper Field default recognition

### Fixed
- ARCHITECTURE.md: full rewrite from fictional PyQt6 to actual React+FastAPI web stack
- README.md: honest project status, correct hardware (ESP32 USB not HaLow), fixed page descriptions
- `_on_node_info_updated` now sanitizes node_id, short_name, long_name (control char stripping, length truncation) and validates last_heard timestamp range
- Callsign truncated to 32 chars in Meshtastic bridge (matches Pydantic model max_length)
- Two-pass node seeding: all nodes added before synthetic threads (prevents ValueError on missing endpoints)
- Config API: auth required on mutations, API key masked in responses, extra fields rejected, device path/hostname/timezone validated
- Systemd service: `/opt/myc3lium/config` added to ReadWritePaths for config persistence
- Deployment scripts: config directory created during setup, service unit hardened
- Renamed `deployment/config/reticulum-config.py` to `reticulum.conf` (correct file format)
- Version synced to 0.4.0 across main.py, pyproject.toml, package.json

### Removed
- P600 satellite pass prediction scaffold (replaced by configuration hub)
- P600.utils.js mock radio config data (no longer needed)

## [0.3.0] - 2026-03-28

### Added
- Device metrics tracking: battery level, voltage, channel utilization, air TX utilization extracted from Meshtastic node update packets with type/range validation
- WebSocket event bridge: Meshtastic events now broadcast to both `/api/meshtastic/ws` and main `/ws` endpoint so P100 dashboard receives live updates
- Optional WebSocket token auth via `?token=` query param (skipped in dev mode when `MESHTASTIC_API_KEY` unset)
- WebSocket connection limits via `ConnectionManager` (MAX_CONNECTIONS=100, capacity rejection with code 1008)
- WebSocket message size validation (1024-byte limit, byte-level check)
- `reconnected` event type in frontend WS client, emitted on auto-reconnect for data refresh
- 13 new tests: 5 device metrics + 8 WebSocket hardening (connection limits, auth, size validation, broadcast, error sanitization)
- Protocol-level WebSocket frame size limit (`ws_max_size=4096`) on uvicorn startup
- Production safety check: CRITICAL log warning when live data mode active but `MESHTASTIC_API_KEY` unset
- 5 new security hardening tests for error detail leak prevention
- Input validation on mesh radio packets: text capped at 237 chars, control chars stripped, timestamp/channel range validated
- `_unsubscribe_all()` helper for clean PyPubSub lifecycle management
- `_subscribed` state flag to guard unsubscribe without prior subscribe
- `pypubsub>=4.0.3` and `meshtastic>=2.0.0` added to requirements.txt
- 12-test suite for MeshtasticService PyPubSub callback lifecycle (`test_meshtastic_service.py`)

### Fixed
- P200 lattice map: `validateNode()` and `validateLink()` now accept actual API data format (status `online`/`degraded`, nullable battery, float quality 0-1, `position.lon`) instead of only mock format
- P200 lattice map: data transformation maps API fields to internal format (`statusToDisplay`, `qualityToLabel`, `position` to `gps`)
- P200 lattice map: node positions preserved by ID across data refreshes instead of array index (prevents visual jumps)
- P200 lattice map: RSSI validation widened to -150..0 dBm to accept Meshtastic device values
- P200 lattice map: error state shows generic "MESH DATA UNAVAILABLE" instead of raw API error details
- P200 lattice map: GPS defaults to null/N/A instead of hardcoded Anchorage coordinates when no position data
- P200 lattice map: removed duplicate `validateNodeId` definition, imported from `P200.utils.js`
- P200 lattice map: `qualityToLabel` and `statusToDisplay` default to safe fallback values for unknown inputs
- Error detail leaks: 4 endpoints no longer expose `str(e)` in HTTP responses (`messages.py` send/create, `nodes.py` create, `intelligence_api.py` observation)
- API key caching: WebSocket endpoint uses module-level `API_KEY` from `auth.py` instead of per-connection `os.getenv()`
- `except HTTPException: raise` in `messages.py` send endpoint prevents 400 being swallowed as 500
- WebSocket endpoint replaced raw connection list with `ConnectionManager` for structured lifecycle management
- Timing-safe token comparison via `hmac.compare_digest()` in both `auth.py` and `meshtastic.py`
- Dict iteration race in `ConnectionManager.broadcast()` — snapshot prevents RuntimeError during concurrent connect/disconnect
- `/api/meshtastic/send` error response no longer leaks internal exception details
- `NaN` display in P100 when `channel_utilization` is null (added `?? 0` guard)
- Meshtastic WebSocket broadcasts now work via PyPubSub (callbacks were silently ignored using dead instance attribute assignments)
- Callbacks registered before `SerialInterface()` constructor to capture initial nodedb (52 nodes were missed)
- `get_status()` crash: `interface.myInfo` is protobuf in Meshtastic 2.x, not a dict
- Thread-safety: `asyncio.Queue.put_nowait()` called from non-asyncio thread now uses `call_soon_threadsafe()`
- Thread-safety: `_ws_callback` captured locally before calling, `nodes_count` read inside lock
- `_on_connection` guarded against `interface=None` from PyPubSub kwargs
- `pub.unsubscribe()` separated from `interface.close()` in `stop()` to prevent error masking
- Hardcoded `"dev-key-change-in-production"` API key removed — reads from env, warns if unset

### Removed
- 5-second polling interval from P100 dashboard (replaced by WebSocket-only live updates with reconnect refresh)

## [0.2.0] - 2026-03-28

### Added
- Meshtastic backend integration: SerialInterface wrapper, API endpoints, WebSocket support, ring buffer
- Meshtastic frontend: live node data, LoRa status, 5-minute activity window on P100 dashboard
- API key authentication and rate limiting (10 req/min on `/api/meshtastic/send`)
- Meshtastic integration roadmap documentation

## [0.1.0] - 2026-03-22

### Added
- GUI live integration with BATMAN + Reticulum overlay
- LoRa TAP bridge for dual-radio mesh networking
- ESP32 firmware scaffold with security hardening
- Phase 4.5 intelligence integration (ATAK + sensor fusion + P900)
- Complete hardware deployment package
- Teletext feature pages: P200 lattice map, P300 node detail, P400 sensor grid, P500 camera stream, P600 comms, P700 node log, P800 config
- Core API with WebSocket support
- Teletext grid renderer with CRT shaders
- Connection limits, message size limits, string length validation
- CI/CD pipeline with ruff, mypy, eslint, pytest
