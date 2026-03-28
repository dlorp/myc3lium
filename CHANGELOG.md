# Changelog

All notable changes to MYC3LIUM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- Meshtastic WebSocket broadcasts now work via PyPubSub (callbacks were silently ignored using dead instance attribute assignments)
- Callbacks registered before `SerialInterface()` constructor to capture initial nodedb (52 nodes were missed)
- `get_status()` crash: `interface.myInfo` is protobuf in Meshtastic 2.x, not a dict
- Thread-safety: `asyncio.Queue.put_nowait()` called from non-asyncio thread now uses `call_soon_threadsafe()`
- Thread-safety: `_ws_callback` captured locally before calling, `nodes_count` read inside lock
- `_on_connection` guarded against `interface=None` from PyPubSub kwargs
- `pub.unsubscribe()` separated from `interface.close()` in `stop()` to prevent error masking
- Hardcoded `"dev-key-change-in-production"` API key removed — reads from env, warns if unset

### Added
- Input validation on mesh radio packets: text capped at 237 chars, control chars stripped, timestamp/channel range validated
- `_unsubscribe_all()` helper for clean PyPubSub lifecycle management
- `_subscribed` state flag to guard unsubscribe without prior subscribe
- `pypubsub>=4.0.3` and `meshtastic>=2.0.0` added to requirements.txt
- 12-test suite for MeshtasticService PyPubSub callback lifecycle (`test_meshtastic_service.py`)

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
