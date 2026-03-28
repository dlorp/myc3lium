# MYC3LIUM Session Notes

## 2026-03-28 [11:00] - Fix Meshtastic WebSocket Callbacks via PyPubSub

**Status:** Complete
**Commits:** 1 (squashed) + merge commit
**PR:** [#49](https://github.com/dlorp/myc3lium/pull/49) (merged), supersedes [#48](https://github.com/dlorp/myc3lium/pull/48) (closed)

### Executive Summary

Reviewed PR #48 which attempted to fix silent Meshtastic WebSocket broadcasts, found multiple issues (no tests, unsubscribe error masking, missing None guards, 525-line plan doc bloating the diff). Closed #48 and created a clean replacement PR #49 with all issues fixed, input validation added, thread-safety hardened, and 12 tests. Deployed to Pi hardware, verified 52 live mesh nodes received via PyPubSub callbacks. Also fixed pre-existing `get_status()` crash (myInfo is protobuf not dict in Meshtastic 2.x) and removed hardcoded API key default.

### Work Completed

- **PyPubSub callback registration**: Replaced dead `interface.onReceive = ...` instance attribute assignments with `pub.subscribe()` for `meshtastic.receive`, `meshtastic.connection.established`, `meshtastic.node.updated`
- **Subscribe-before-connect ordering**: Callbacks registered BEFORE `SerialInterface()` constructor, which downloads full nodedb during init (52 nodes missed otherwise)
- **Input validation on mesh packets**: Untrusted radio input now sanitized — text capped at 237 chars, control chars stripped, timestamps/channels validated
- **Thread-safety fixes**: `call_soon_threadsafe()` for async queue bridging from meshtastic's serial reader thread; `_ws_callback` captured locally before calling; `nodes_count` read inside lock
- **get_status() protobuf fix**: `interface.myInfo` is a protobuf in Meshtastic 2.x (not a dict), was crashing `/api/meshtastic/status` and killing WebSocket connections. Now reads from tracked `self._nodes` via `self._my_node_id`
- **Hardcoded API key removed**: `MESHTASTIC_API_KEY` no longer defaults to `"dev-key-change-in-production"` — logs warning if unset, skips auth in dev mode
- **Cleanup improvements**: `_unsubscribe_all()` helper deduplicates subscribe/unsubscribe logic, `_interface` nulled in `stop()` to prevent use-after-close, `_subscribed` flag guards against unsubscribe without prior subscribe
- **SSH config**: Added `myc3lium` host entry to `~/.ssh/config` for Pi access
- **12 tests**: Full callback lifecycle, input sanitization, edge cases, error paths

### Git Activity

**Commits this session:**
- `d4ba6ff` (squashed, merged as `6b7a505`) - `fix: use PyPubSub for Meshtastic callbacks`

**PRs:**
- PR #49 created, reviewed (security + code), CI green, merged to main
- PR #48 closed with superseded comment

**Uncommitted changes:** None

### Files Modified

- `backend/app/services/meshtastic_service.py` — PyPubSub subscribe/unsubscribe, kwarg signatures, None guards, input validation, `_subscribed` flag, `_unsubscribe_all()` helper, `get_status()` protobuf fix, thread-safe callback capture
- `backend/app/routers/meshtastic.py` — Thread-safe `broadcast_to_websockets()` using `call_soon_threadsafe()`, cached `_event_loop` reference
- `backend/app/auth.py` — Removed hardcoded API key default, added warning log when unset
- `backend/requirements.txt` — Added `meshtastic>=2.0.0` and `pypubsub>=4.0.3`
- `backend/tests/test_meshtastic_service.py` — New file, 12 tests

### Problems & Solutions

| Problem | Solution |
|---------|----------|
| Meshtastic uses PyPubSub, not instance callbacks — `onReceive` assignments were dead code | Switch to `pub.subscribe()` with correct topic names |
| Callbacks registered after SerialInterface init — missed all 52 initial nodes | Move `pub.subscribe()` calls before `SerialInterface()` constructor |
| `asyncio.Queue.put_nowait()` called from non-asyncio thread (meshtastic serial reader) | Use `loop.call_soon_threadsafe()` with cached event loop reference |
| `interface.myInfo` is protobuf in Meshtastic 2.x — `.get("user")` crashed `get_status()` | Store `_my_node_id` from `interface.nodes` dict, read status from tracked nodes |
| `pub.unsubscribe()` in `stop()` could mask `interface.close()` errors | Separated into `_unsubscribe_all()` helper with own try/except |
| `_on_connection` accessed `interface.myInfo` when `interface=None` | Added `interface is not None` guard |
| `len(self._nodes)` read outside lock in `_on_node_info_updated` | Capture `nodes_count` inside `self._nodes_lock` |
| mypy CI failure: `X \| Y` union syntax requires Python 3.10+ | Changed to `Optional[asyncio.AbstractEventLoop]` |
| Hardcoded `"dev-key-change-in-production"` API key | Read from env, warn if unset, skip auth in dev mode |
| SSH to Pi failed — key not in authorized_keys | Added HDLS key to Pi, configured `~/.ssh/config` host entry |

### Handoff Notes

- **PR #49 merged to main** — all CI green, hardware-verified on Pi with 52 live mesh nodes
- **Pi backend was left stopped** after testing — needs restart on `main` branch: `ssh myc3lium "cd ~/myc3lium && git checkout main && git pull"`
- **Security review deferred items** (not introduced by this PR, tracked for future):
  - WS `/api/meshtastic/ws` endpoint has no connection limit, no auth, no message size check
  - Exception details leaked in `/api/meshtastic/send` error response (`detail=f"Failed to send: {e}"`)
  - Battery/voltage/channel_utilization fields always None in status (device metrics not tracked from node updates)
- **Meshtastic is a PUBLIC radio network** — NEVER send test messages without explicit user approval. Read-only operations only.

### Next Steps

1. [ ] Restart Pi backend on `main` with merged fix: `ssh myc3lium` then pull + restart uvicorn
2. [ ] WS hardening PR: add connection limits, message size validation, optional auth to `/api/meshtastic/ws`
3. [ ] Track device metrics (battery, voltage, channel utilization) from node update events in `MeshtasticNode`
4. [ ] Frontend validation: verify P100 dashboard receives real-time WebSocket events (<1s latency)
5. [ ] Remove 5s polling fallback from frontend once WebSocket is confirmed stable
6. [ ] Phase 4+ features from roadmap: node pruning/expiry, advanced teletext pages, multi-radio support

---
