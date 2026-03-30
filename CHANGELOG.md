# Changelog

All notable changes to MYC3LIUM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.7.0] - 2026-03-29

### Added
- IBSS (ad-hoc) mode mesh bringup via `mesh-up` command in myc3lium-netctl — replaces broken 802.11s mesh join commands that fail on brcmfmac (Pi's FullMAC WiFi driver has no mesh point support)
- `mesh-up <ssid> <freq> <ip/cidr>` command: modprobes batman-adv, unmanages wlan0+bat0 in NetworkManager, joins IBSS cell, creates bat0 over-the-air interface, assigns deterministic IP
- `mesh-down` command: clean teardown in reverse order (bat0 del, wlan0 down, NM restore)
- `mesh-status` command: quick state check (IBSS association, bat0 existence, IP)
- `ensure_nm_unmanaged_mesh()` helper in netctl for persistent NM unmanage of mesh interfaces
- `_derive_mesh_ip()` in `network_apply_service.py`: deterministic `10.13.<mac[4]>.<mac[5]>/16` IP from wlan0 MAC last two octets — no DHCP on mesh
- `_netctl()` helper in `network_apply_service.py` for clean privileged helper invocation via sudo
- BATMAN mesh startup before backhaul in `start_mesh_monitor()` (bat0 must exist before br0 bridge attempts to add it)
- BATMAN mesh teardown in `shutdown_services()` for clean shutdown sequencing

### Fixed
- `apply_batman()` completely rewritten: was calling `iw dev wlan0 mesh join` (802.11s, unsupported on brcmfmac) — now delegates to `netctl mesh-up` which uses IBSS mode that brcmfmac supports
- Startup order: mesh brought up before backhaul bridge so bat0 exists when br0 tries to include it
- `setup-batman.sh` stripped of embedded `setup-mesh.sh` and broken systemd `batman-adv.service` creation; now install-only (apt, module autoload, NM config)
- `batctl` commands updated to modern `batctl meshif bat0` syntax (old positional syntax deprecated)

### Removed
- Raw `sudo iw` / `sudo systemctl` calls from `network_apply_service.py` — all mesh operations now route through netctl privileged helper
- Embedded `setup-mesh.sh` and systemd unit creation from `setup-batman.sh` (mesh lifecycle managed by app, not systemd)

## [0.6.0] - 2026-03-29

### Added
- Captive portal for first-boot UX: phones connecting to myc3_m3sh AP automatically see the setup wizard via OS captive portal sheet (iOS/Android/Windows/Firefox)
- dnsmasq wildcard DNS (`address=/#/10.99.0.1`) redirects all domains to Pi when setup incomplete; removed after setup completes
- nginx probe handlers: per-OS exact-match locations return 302 to `/setup` when captive flag exists, expected responses (Success/204/etc.) when absent
- `enable_captive_portal()` / `disable_captive_portal()` lifecycle functions in `backhaul_service.py`
- `set-captive-portal`, `clear-captive-portal`, `restart-dnsmasq` commands in myc3lium-netctl
- Setup gate: blocks all non-config API endpoints (403) until first-boot setup wizard completes and AP password is changed from default
- `setup_complete` field in SystemConfig — persisted to TOML, checked by `is_setup_complete()` (also treats changed AP password as complete for existing deployments)
- Frontend 403 handler: `X-Setup-Required` header triggers automatic redirect to `/setup`
- README "First Boot / Field Deployment" section: SSID, default password, URL, setup flow, backhaul modes
- Auto band selection: `detect_uplink_band()` reads connected network frequency via nmcli IN-USE filter, `detect_optimal_ap_band()` picks opposite band to avoid co-channel interference
- USB reset recovery in `myc3lium-netctl`: unbind/rebind USB adapter on hostapd/wpa_supplicant failure, NM re-exclusion after reset
- Backhaul / AP mode: USB WiFi adapter auto-detection, client mode (join WiFi), AP mode (broadcast myc3_m3sh hotspot)
- `BackhaulConfig` Pydantic model with validators: interface (wlanN only), password (min 8 chars, no control chars/quotes), SSID, AP channel/band cross-validation
- `backhaul_service.py`: USB adapter detection via `/sys/class/net`, AP/client mode apply, NAT management, bridge setup, status reporting
- `network_apply_service.py`: wires P600 config changes to BATMAN (iw commands), Reticulum (ConfigObj format), Meshtastic (start/stop)
- `myc3lium-netctl` privileged helper script: all root-level operations (hostapd, iptables, bridge, wpa_supplicant) via sudo with interface validation
- Linux bridge (br0) connecting AP clients to BATMAN mesh: `hostapd bridge=br0` + `bat0` in bridge
- Auto-AP on first boot: detects USB WiFi adapter, starts AP with default creds (myc3_m3sh / myc3m3sh), user changes via Setup wizard
- API endpoints: `GET /backhaul/adapters`, `GET /backhaul/status` (auth), `POST /apply-backhaul` (auth), `POST /apply-network` (auth)
- P600 backhaul panel: adapter display, mode selector (disabled/client/AP), conditional fields, NAT toggle, APPLY BACKHAUL button
- "APPLY TO SYSTEM" buttons on Radio and Mesh sections in P600
- Setup wizard backhaul step (5th step before confirm): adapter detection, mode/SSID/password, pre-populated with auto-AP defaults
- dnsmasq `address=/myc3.local/10.99.0.1` for iOS DNS resolution (mDNS alone insufficient on "no internet" networks)
- `setup-backhaul.sh` deployment script: package install, hostapd/dnsmasq templates, NetworkManager exclusion, IP forwarding
- Systemd override `myc3lium-backhaul.conf`: relaxes sandbox for sudo netctl operations

### Fixed
- nginx SPA routing: `try_files $uri $uri/ /index.html` (was `=404`, broke direct navigation to `/setup`, `/p/200`, etc.)
- Setup wizard CNA close: full page load (`window.location.href`) instead of SPA navigate, so iOS/Android captive portal sheet re-probes and closes
- TOML config file now written atomically with `0o600` permissions (contains passwords)
- Password masking in GET responses for both `client_password` and `ap_password`
- iptables rules idempotent (check before add via `-C`) and targeted cleanup (no chain flush)
- `subprocess.TimeoutExpired` caught in `_run()` helpers (returns rc=1 instead of crashing)
- Sync endpoint handlers for blocking subprocess calls (FastAPI threadpool, not event loop)
- NAT masquerade through default route interface (wlan0/internet), not AP interface (wlan1)
- AP defaults changed from 5GHz ch36 to 2.4GHz ch1 (avoids co-channel interference with 5GHz home network uplink)
- `hostapd_cli` called via full path `/usr/sbin/hostapd_cli` (not in service user PATH)

### Security
- Password injection prevention: control characters and double quotes rejected in `client_password`/`ap_password`
- Interface name validation: must match `wlanN` regex (prevents argument injection)
- Config files written via privileged helper with `chmod 600` (hostapd.conf, wpa_supplicant.conf)
- WPA2 enforced: AP mode requires password, `wpa_passphrase` tool used for hashed PSK storage
- Backhaul status endpoint requires API key auth

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
