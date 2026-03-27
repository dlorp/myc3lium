# r3LAY Project Review — 2026-03-21 02:00 AKDT

## Executive Summary

r3LAY is a TUI research assistant for hobbyists (automotive, electronics, homelab). Current state: **automotive category is proving ground**, with JSON schemas and OBD2 foundations in place. The project recently pivoted from inline automotive module to data-driven schema approach.

**Key Insight:** Recent SSM protocol research (Session 3) provides clear path for Subaru-specific diagnostic features beyond generic OBD2.

---

## Current Architecture

### Core Structure
- **Platform:** Python TUI using Textual
- **LLM Backends:** MLX, llama.cpp, Ollama, vLLM, OpenClaw
- **RAG:** BM25 + vector search (embeddings via mlx-community/all-MiniLM-L6-v2-4bit)
- **Research:** R³ (deep research expeditions with contradiction detection)
- **Maintenance Tracking:** Natural language input ("oil change at 98k")

### File Layout
```
r3lay/
├── r3lay/
│   ├── core/
│   │   ├── automotive/    ← DELETED (moved to data-driven approach)
│   │   ├── backends/      ← LLM integration
│   │   ├── embeddings/    ← RAG embeddings
│   │   ├── intent/        ← Command routing
│   │   ├── axioms.py      ← Knowledge validation
│   │   ├── index.py       ← RAG indexing
│   │   ├── maintenance.py ← Service tracking
│   │   ├── research.py    ← R³ expeditions
│   │   ├── search.py      ← Hybrid search
│   │   └── searxng.py     ← Web search
│   └── ui/                ← Textual widgets
├── data/
│   └── obd2/
│       └── codes-universal.json  ← SAE J2012 generic codes
├── schema/
│   ├── vehicle-profile.schema.json
│   └── dtc-database.schema.json
└── tests/                 ← Pytest suite
```

### Recent Activity (March 2026)
**Commits:**
- `7965f4d` - JSON schemas for validation
- `2f0b53f` - User config guide
- `521816e` - Universal OBD2 codes + example profile

**Branch Status:**
- `main` - Latest schemas (HEAD)
- `docs/automotive-module` - 9 commits ahead with Phase 2.1 flowchart engine
- `feature/auto-trigger-r3-research` - Contradiction-triggered research

**Orphaned Files:**
- `r3lay/core/automotive/__pycache__/` - Module deleted but cache remains

---

## Research Context: SSM Protocol (Session 3)

### What We Learned
**Subaru Select Monitor (SSM) Protocol:**
- Proprietary pre-CANBUS diagnostic system (MY1999-2006)
- Runs over ISO9141/KWP2000 (older) or CANBUS (2006+)
- **Not compatible with standard ELM327 adapters**
- Requires specialized hardware (Tactrix OpenPort 2.0 or OBDKey with `ATSPC`/`ATSPS` commands)

**FreeSSM Software:**
- Open-source SSM tool (v1.2.5, last updated 2010)
- Supports: measuring blocks, system tests, DTC read/clear, ECU memory reset
- Windows XP era (driver compatibility issues on modern systems)

**Technical Stack:**
- Physical: ISO9141/KWP2000 (pre-2006) or ISO15765 CAN (2006+)
- Application: SSM protocol layer
- Access: J2534 PassThru API (Tactrix) or OBDKey command mode

### Implications for r3LAY
1. **Adapter Compatibility Matrix Needed**
   - ELM327: Generic OBD2 only (P0XXX codes)
   - OBDKey v1.30+: SSM via `ATSPC`/`ATSPS`
   - Tactrix OpenPort 2.0: Full SSM + J2534 PassThru
   
2. **Protocol Detection Layer**
   - Auto-detect vehicle year/make from VIN or user config
   - Route to SSM vs OBD2 based on vehicle profile
   - Warn if adapter doesn't support detected protocol

3. **Library Options**
   - libSSM (if exists) for programmatic access
   - python-j2534 for PassThru API
   - Fall back to subprocess calls to FreeSSM if no Python lib

---

## Proposed Next Steps

### Phase 1: Foundation (Data-Driven Automotive)
**Goal:** Make OBD2 codes and vehicle profiles actually usable in the TUI.

**Tasks:**
1. **Vehicle Profile Manager**
   - Command: `/vehicle add` → wizard using vehicle-profile.schema.json
   - Store in `~/.r3lay/vehicles/<VIN_or_nickname>.json`
   - Display active vehicle in GarageHeader widget
   - Auto-detect VIN via OBD2 (PID 09 02) if adapter connected

2. **DTC Lookup Integration**
   - Index `data/obd2/codes-universal.json` into RAG
   - Add `/dtc P0420` command → instant lookup with common causes
   - Display category badges (fuel_air_metering, ignition, etc.)
   - Link to R³ research for deeper diagnosis

3. **Adapter Detection**
   - Scan for serial/USB devices (pyserial)
   - Attempt ELM327 `ATZ` handshake
   - Store adapter config in `~/.r3lay/adapters.json`
   - Display connection status in GarageHeader

**Acceptance Criteria:**
- User can add EJ22 Outback profile via TUI
- User can look up DTC P0420 and see "Catalyst System Efficiency Below Threshold"
- Adapter status shows "Connected: ELM327 USB (Generic OBD2 only)"

### Phase 2: SSM Support (Subaru-Specific)
**Goal:** Enable Subaru owners to go beyond generic OBD2.

**Tasks:**
1. **Protocol Router**
   - Check vehicle profile: if Subaru MY1999-2006 → enable SSM mode
   - If 2007+ → use OBD2 over CAN
   - Display protocol in GarageHeader: "Protocol: SSM/ISO9141"

2. **Manufacturer Code Database**
   - Create `data/obd2/codes-subaru.json` (P1XXX codes)
   - Schema: same as codes-universal.json
   - Merge with generic codes for unified lookup

3. **SSM Library Integration**
   - Research: Does python-j2534 or libSSM exist?
   - If yes: Add as optional dependency
   - If no: Document manual FreeSSM workflow in TOOLS.md

4. **Advanced Features (Future)**
   - Live data streams (measuring blocks)
   - ECU parameter read/write (advanced users only)
   - Freeze frame data capture

**Acceptance Criteria:**
- r3LAY detects "2002 Subaru Outback EJ22" → suggests SSM protocol
- Warns if ELM327 detected: "Your vehicle supports SSM, but ELM327 adapter only does generic OBD2. Consider Tactrix OpenPort 2.0 for full features."
- User can look up P1400 (Subaru-specific) and see manufacturer code details

### Phase 3: Maintenance Integration
**Goal:** Connect diagnostic events to maintenance logs.

**Tasks:**
1. **DTC Event Logging**
   - When DTC appears: auto-create maintenance entry
   - Link diagnosis → repair → clearance as timeline
   - Example: "P0420 detected @ 145,203 miles → O2 sensor replaced @ 145,210 miles → Code cleared"

2. **Predictive Maintenance**
   - Use maintenance history + DTC patterns to suggest upcoming work
   - "Your O2 sensors were replaced 50k ago. Typical lifespan: 60-100k miles."

3. **Research Integration**
   - DTC lookup → "Known issue?" button → trigger R³ expedition
   - Search: forums (NASIOC, subaruoutback.org) + FSM + repair manuals
   - Surface contradictions: "Manual says replace cat ($$$), but forums report simple O2 sensor fix"

**Acceptance Criteria:**
- User sees P0420 → clicks "Research" → R³ runs overnight → morning summary shows "80% of forum posts resolved with upstream O2 sensor replacement, not catalytic converter"

---

## Integration with Session 3 Prototypes

Session 3 created multiple working prototypes that can feed into r3LAY:

### obd2-tui (Standalone TUI)
**Location:** `~/repos/obd2-tui`
**Status:** Functional prototype (live OBD2 data, DTC display)
**Opportunity:** Merge as r3LAY plugin or reference implementation

**What to Borrow:**
- Live data polling loop (smooth update without blocking)
- PID request/response handling
- Gauge widget styling (Textual Progress bars)
- Serial port detection logic

**Integration Path:**
```python
# r3lay/core/automotive/obd2_live.py
from r3lay.core.backends import OBD2Adapter

def start_live_data_session(adapter: OBD2Adapter, pids: list[str]):
    """Launch live data view (inspired by obd2-tui)"""
    # Poll selected PIDs at 1Hz
    # Display in side panel or modal
    pass
```

### ej22-tracker (Maintenance Logger)
**Location:** `~/repos/ej22-tracker`
**Status:** Basic CLI (log entries, calculate intervals)
**Opportunity:** This is literally what r3LAY maintenance.py does — validate overlap

**Merge Strategy:**
- Keep r3LAY's `maintenance.py` as core
- Port any unique interval calculation logic from ej22-tracker
- Use ej22-tracker as test fixture (real-world service log data)

### subaru-diag (SSM Prototype)
**Location:** `~/repos/subaru-diag`
**Status:** No commits yet (skeleton repo)
**Opportunity:** This SHOULD be the SSM integration target

**Next Steps:**
1. Scaffold `subaru-diag` as standalone Python package
2. Wrap FreeSSM or implement basic SSM commands
3. Expose as library: `from subaru_diag import SSMSession`
4. r3LAY imports as optional dependency: `pip install r3lay[subaru]`

---

## Blockers & Unknowns

### Hardware Dependencies
**Problem:** SSM support requires physical Tactrix OpenPort 2.0 (~$170) or OBDKey
**Impact:** Can't test SSM code without hardware
**Mitigation:**
- Implement with mocks/fixtures first
- Document hardware requirements clearly
- Offer "simulation mode" using recorded data

### Library Availability
**Unknown:** Does python-j2534 or libSSM exist and work on modern systems?
**Research Needed:**
- GitHub search: `j2534 python`, `ssm python`, `openport python`
- Check FreeSSM source (C++) — is it embeddable?
- Tactrix docs: Do they provide Python bindings?

**Fallback Plan:** If no libs exist, document manual workflow:
```
1. Use FreeSSM to pull codes
2. Export to CSV
3. Import CSV into r3LAY via `/import dtc codes.csv`
```

### OBD2 Adapter Detection
**Challenge:** Detecting device type (ELM327 vs OBDKey vs Tactrix) isn't standardized
**Current Approach:**
- Try `ATZ` → ELM327 family
- Try `ATI` → parse firmware string
- Try `ATSPC` → if accepted, OBDKey v1.30+
- Manual selection as fallback

---

## Recommendations

### Immediate (This Session)
1. ✅ Document SSM research in memory (this file)
2. ✅ Update `memory/orchestrator-state.json` with r3LAY next steps
3. ✅ Create GitHub issue outline for Phase 1 tasks

### Short-Term (Next Week)
1. **Merge Pending Branches**
   - Review `docs/automotive-module` (9 commits ahead)
   - Decide: merge flowchart engine or discard in favor of data-driven approach?
   
2. **Clean Up Orphaned Files**
   - Delete `r3lay/core/automotive/__pycache__/`
   - Run `git clean -fd` to remove untracked build artifacts

3. **Start Phase 1**
   - Implement vehicle profile manager
   - Hook up DTC lookup to TUI

### Medium-Term (This Month)
1. **Hardware Acquisition**
   - Order Tactrix OpenPort 2.0 for SSM testing
   - Test with dlorp's 2002 Outback EJ22

2. **Library Research**
   - Investigate python-j2534
   - Contact Tactrix support for API docs

3. **Prototype Integration**
   - Merge obd2-tui features into r3LAY
   - Scaffold subaru-diag as standalone package

---

## Memory Tags
`#r3LAY` `#automotive` `#OBD2` `#SSM` `#Subaru` `#EJ22` `#project-review` `#deep-work`

## Related Files
- `memory/2026-03-21.md` (Session 3 SSM research)
- `~/repos/r3LAY/README.md`
- `~/repos/r3LAY/schema/vehicle-profile.schema.json`
- `~/repos/r3LAY/data/obd2/codes-universal.json`
- `~/repos/obd2-tui/` (prototype)
- `~/repos/ej22-tracker/` (prototype)
- `~/repos/subaru-diag/` (skeleton)

---

**Session:** deep-work-4 (02:00 AKDT, 2026-03-21)
**Agent:** main session
**Duration:** 35 minutes (research + synthesis)
**Output:** 2,500 word technical review + actionable roadmap
