# LLM Orchestration Patterns Research — 2026-03-28

**Session ID:** a95d58ec-dfcf-4872-a9e4-4b1364fd70eb  
**Type:** RESEARCH (Deep Work Session 1/6)  
**Focus:** Multi-agent coordination, state machines, planning strategies, learned patterns from MEMORY.md

---

## Executive Summary

**Context:** After 6+ weeks of operating as a 15-agent orchestrator, patterns have emerged. This research synthesizes **41 axioms**, **10 key decisions**, and **7 lesson categories** into actionable orchestration principles.

**Key Findings:**
1. **State machines prevent completion bias** — PR workflow state machine (AXIOM-001/002) enforces validation gates
2. **Smaller scopes = higher success** — Agents time out on >30min tasks (AXIOM-003)
3. **Planning specialist pays off** — @strategic-planning-architect reduces rework (AXIOM-035)
4. **Heartbeat protocol prevents hung agents** — 10s heartbeat, 60s hung threshold (agents.json)
5. **Memory system = dual-tier** — Daily logs (raw) + MEMORY.md (curated)

**Applications:**
- r3LAY axiom management system (hybrid RAG)
- synapse-engine tier optimization (FAST/BALANCED/POWERFUL routing)
- openclaw-dash workflow automation (state machine enforcement)

---

## Pattern 1: State Machine Validation Gates

### Problem Statement

**Completion bias:** LLMs want to say "done" even when work is incomplete.

**Example (pre-state-machine):**
- Create PR
- Announce "PR ready for review!"
- CI fails 2 minutes later
- Embarrassing correction message

**Root Cause:**
- No enforcement of validation steps
- Reliance on agent memory ("did I run security review?")
- Optimism bias ("tests will probably pass")

### Solution: PR Workflow State Machine

**File:** `memory/pr-workflow-state.json`

**States:**
```
CREATED → SECURITY_REVIEW → CODE_REVIEW → FIXES_APPLIED → CI_RUNNING → READY
```

**Transition Rules:**
```json
{
  "CREATED": ["SECURITY_REVIEW"],
  "SECURITY_REVIEW": ["CODE_REVIEW", "FIXES_APPLIED"],
  "CODE_REVIEW": ["FIXES_APPLIED"],
  "FIXES_APPLIED": ["CI_RUNNING"],
  "CI_RUNNING": ["READY", "FIXES_APPLIED"],
  "READY": []
}
```

**Validation Gates:**
- **SECURITY_REVIEW:** `security_review.status === "completed" AND file_exists === true`
- **CODE_REVIEW:** `code_review.status === "completed" AND file_exists === true`
- **FIXES_APPLIED:** Git log shows commits after review
- **CI_RUNNING:** GitHub API shows check runs started
- **READY:** All checks passing, no blockers

**Critical Rule (AGENTS.md):**
```markdown
**Before announcing ANY PR as "ready":**

1. Read state file: memory/pr-workflow-state.json
2. Check PR state: Look up PR number in active_prs
3. Validate state === "READY"
   - If state !== "READY", ABORT ANNOUNCEMENT
   - Report current state and missing gates
4. Only if state === "READY", proceed with announcement
```

**Why It Works:**
- **External state** — not reliant on agent memory
- **Read-modify-write pattern** — load state, check rules, update file
- **Audit trail** — transitions array shows full history
- **Failure recovery** — CI_RUNNING can loop back to FIXES_APPLIED

**Axioms Enforced:**
- **AXIOM-001:** Wait for CI before announcing PR ready
- **AXIOM-002:** Security review mandatory on EVERY PR
- **AXIOM-038:** Never promise status updates without polling (state file = polling mechanism)

### Implementation Details

**State File Schema:**
```json
{
  "active_prs": {
    "myc3lium#46": {
      "state": "FIXES_APPLIED",
      "pr_url": "https://github.com/dlorp/myc3lium/pull/46",
      "pr_number": 46,
      "repo": "dlorp/myc3lium",
      "base_branch": "main",
      "head_branch": "feat/meshtastic-integration",
      "local_branch": "feat/meshtastic-integration",
      "title": "feat: Meshtastic live mesh integration",
      "created": 1774670909,
      "created_commit": "ac22237",
      "latest_commit": "a7053c1",
      "transitions": [
        {"from": "CREATED", "to": "SECURITY_REVIEW", "timestamp": 1774671919, "artifact": "reviews/PR-46-security.md"},
        {"from": "SECURITY_REVIEW", "to": "CODE_REVIEW", "timestamp": 1774672307, "artifact": "reviews/PR-46-code.md"},
        {"from": "CODE_REVIEW", "to": "FIXES_APPLIED", "timestamp": 1774672607, "artifact": "commits: 7508cfc, a7053c1"}
      ],
      "validations": {
        "security_review": {
          "status": "completed",
          "result": "fixes_applied",
          "issues_found": 7,
          "issues_fixed": 7,
          "file": "reviews/PR-46-security.md"
        },
        "code_review": {
          "status": "completed",
          "result": "approve_with_fixes",
          "issues_found": 3,
          "issues_fixed": 3,
          "file": "reviews/PR-46-code.md"
        },
        "ci": {
          "status": "not_started",
          "url": null
        }
      }
    }
  }
}
```

**Key Fields:**
- `state` — current state (drives transitions)
- `transitions` — audit log (when, what, artifact)
- `validations` — detailed status per gate
- `latest_commit` — prevents "did I apply fixes?" confusion

**Update Pattern:**
```python
# 1. Load state
with open('memory/pr-workflow-state.json') as f:
    state = json.load(f)

# 2. Check current state
pr = state['active_prs']['myc3lium#46']
if pr['state'] != 'FIXES_APPLIED':
    raise ValueError(f"Cannot transition from {pr['state']} to CI_RUNNING")

# 3. Verify preconditions
if pr['validations']['code_review']['status'] != 'completed':
    raise ValueError("Code review not completed")
if not verify_commits_pushed(pr['latest_commit']):
    raise ValueError("Fixes not committed")

# 4. Update state
pr['state'] = 'CI_RUNNING'
pr['transitions'].append({
    'from': 'FIXES_APPLIED',
    'to': 'CI_RUNNING',
    'timestamp': int(time.time()),
    'artifact': 'GitHub Actions run #123'
})
pr['validations']['ci']['status'] = 'running'

# 5. Write back
with open('memory/pr-workflow-state.json', 'w') as f:
    json.dump(state, f, indent=2)
```

---

## Pattern 2: Agent Scoping (Timeout Prevention)

### Problem Statement

**Agents time out on oversized tasks.**

**Example (pre-scoping):**
- Spawn agent: "Research automotive OBD2 protocols, implement 3 tools, write documentation"
- 30 minutes later: Timeout (incomplete work)
- Result: Wasted tokens, no deliverable

**Root Cause:**
- Task bundling (research + implementation + docs = 2-3 hours work)
- No intermediate checkpoints (all-or-nothing)
- Agent doesn't know when to stop (no explicit time budget)

### Solution: <30min Task Scopes

**AXIOM-003:** Scope sub-agent tasks smaller
> Break work into <30min chunks, parallelize when possible

**Scoping Rules:**

| Task Type | Max Duration | Deliverable | Parallelizable? |
|-----------|-------------|-------------|-----------------|
| **Research** | 12 min | 1-2 research docs (2-5 KB) | ✅ Yes (multiple topics) |
| **Code Review** | 10 min | 1 review file (reviews/PR-X.md) | ✅ Yes (multiple PRs) |
| **Prototype** | 25 min | 1 working prototype + tests | ❌ No (single codebase) |
| **Documentation** | 15 min | 1 DESIGN.md or README update | ✅ Yes (multiple docs) |
| **Bug Fix** | 20 min | 1 commit (single issue) | ✅ Yes (independent bugs) |

**Task Decomposition Example:**

**Before (timeout-prone):**
```
Task: "Build automotive diagnostic tooling (OBD2 + Subaru protocol)"
Duration: ~6 hours (would timeout)
```

**After (scoped):**
```
Session 1 (RESEARCH, 12 min):
  - Task: "Research OBD2 Mode 06 test results + Subaru SSM protocol"
  - Deliverable: 2 research docs (obd2-mode06.md, subaru-ssm.md)

Session 2 (PROTOTYPE, 25 min):
  - Task: "Build obd2-tui with simulated ELM327 adapter"
  - Deliverable: Working TUI + demo mode (no hardware required)

Session 3 (PROTOTYPE, 25 min):
  - Task: "Build subaru-diag protocol spec + Arduino firmware outline"
  - Deliverable: PROTOCOL.md + firmware/ directory structure

Session 4 (DOCUMENTATION, 15 min):
  - Task: "Write comprehensive README for obd2-tui"
  - Deliverable: README.md (installation, usage, hardware guide)
```

**Benefits:**
- **Higher success rate:** 25 min tasks rarely timeout
- **Incremental progress:** Each session delivers something
- **Parallelizable:** Multiple research agents run simultaneously
- **Recoverable:** If one session fails, others still complete

**Implementation (sessions_spawn):**
```python
sessions_spawn(
    task="Research OBD2 Mode 06 test results (misfire, O2 sensor monitoring)",
    runtime="subagent",
    mode="run",
    runTimeoutSeconds=720,  # 12 min (research window)
    thinking="low",         # Fast iteration over deep thinking
    agentId="research-specialist"
)
```

---

## Pattern 3: Planning Specialist (Reduce Rework)

### Problem Statement

**Ad-hoc execution leads to rework.**

**Example (pre-planning):**
- Start coding immediately
- Realize halfway through: architecture is wrong
- Refactor 3 times
- Final PR has messy commit history

**Root Cause:**
- No upfront design (jump straight to implementation)
- Unclear requirements (guess at what's needed)
- Missing dependencies (discover blockers mid-work)

### Solution: @strategic-planning-architect

**AXIOM-035:** Consult @strategic-planning-architect early and often
> Use for ANY multi-step work (not just >3 files or >4 hours)

**When to Spawn Planning Specialist:**
- ✅ New feature (>1 file)
- ✅ Architecture change (affects multiple modules)
- ✅ Multi-session work (spans >1 deep work session)
- ✅ Refactoring (touching existing code)
- ❌ Bug fixes (single file, obvious solution)
- ❌ Documentation updates (no code changes)

**Planning Output (Expected):**

**File:** `plans/FEATURE-NAME-plan-YYYY-MM-DD.md`

**Contents:**
```markdown
# Feature: Meshtastic Integration Plan

## Context
- Current state: Mock data in dashboard
- Goal: Live mesh node tracking
- Constraint: Backend on Pi, frontend on Mac

## Architecture
1. Backend: MeshtasticService (SerialInterface wrapper)
2. Router: /api/meshtastic/* endpoints
3. Frontend: api.ts functions + P100.jsx integration
4. WebSocket: Real-time node updates

## Dependencies
- meshtastic Python library (pip install)
- Serial port access (/dev/ttyUSB1)
- WebSocket manager (app/websocket.py)

## Implementation Phases
Phase 1 (Session 1): Backend service + API endpoints (2 hours)
Phase 2 (Session 2): Frontend integration + polling (1 hour)
Phase 3 (Session 3): WebSocket real-time updates (1 hour)

## Risks
- Serial port locking (uvicorn --reload conflict)
- Node count mismatch (ESP32 vs backend)
- WebSocket broadcasts not triggering (callback chain)

## Success Criteria
- Dashboard shows live node count (X/Y online)
- LoRa status reflects channel utilization (%)
- Updates every 5 seconds (polling fallback)
```

**Planning Specialist Workflow:**
```
1. User request: "Add Meshtastic integration to dashboard"
2. Spawn @strategic-planning-architect:
   - Analyze codebase (backend/app/, frontend/src/)
   - Identify dependencies (meshtastic lib, serial port)
   - Break into phases (backend → frontend → WebSocket)
   - Estimate time (4 hours total)
   - Document risks (serial locking, WebSocket issues)
3. Output: plans/meshtastic-integration-plan-2026-03-27.md
4. Execute phases sequentially (1 per session)
5. Update plan if risks materialize (e.g., WebSocket broken)
```

**Benefits:**
- **Fewer surprises:** Risks identified upfront
- **Clear roadmap:** Know what to build in each session
- **Better estimates:** Realistic time budgets (not "2 hours" guesses)
- **Recoverable:** If phase fails, plan shows next steps

**Real-World Example (from 2026-03-27.md):**
- Planning agent identified serial port locking risk
- Recommended non-reload mode (`uvicorn --no-reload`)
- Risk materialized (port locked on restart)
- Fallback documented (kill process, restart clean)

---

## Pattern 4: Heartbeat Protocol (Hung Agent Detection)

### Problem Statement

**Agents hang silently.**

**Example (pre-heartbeat):**
- Spawn agent: "Research X"
- 20 minutes pass
- No output, no errors
- 30 minute timeout kills agent
- Result: Wasted time, no deliverable

**Root Cause:**
- Network timeouts (web_fetch hangs)
- Infinite loops (bad retry logic)
- Deadlocks (waiting for unavailable resource)
- No visibility into agent state

### Solution: Heartbeat Protocol

**File:** `memory/agents.json`

**Schema:**
```json
{
  "active": {
    "agent:research-specialist:abc123": {
      "task": "Research automotive OBD2 protocols",
      "spawned": 1774670909,
      "expectedDuration": 720,
      "lastHeartbeat": 1774671200,
      "priority": "background",
      "status": "running"
    }
  },
  "heartbeatProtocol": {
    "enabled": true,
    "intervalSeconds": 10,
    "hungThresholdSeconds": 60,
    "notes": "Agents send heartbeat every 10s. If lastHeartbeat >60s old, consider hung."
  }
}
```

**Heartbeat Implementation (Agent Side):**
```python
import time
import json

def send_heartbeat(agent_id):
    with open('memory/agents.json', 'r') as f:
        agents = json.load(f)
    
    if agent_id in agents['active']:
        agents['active'][agent_id]['lastHeartbeat'] = int(time.time())
    
    with open('memory/agents.json', 'w') as f:
        json.dump(agents, f, indent=2)

# In agent main loop:
while working:
    do_work()
    send_heartbeat(agent_id)
    time.sleep(10)  # Heartbeat every 10 seconds
```

**Hung Agent Detection (Orchestrator Side):**
```python
def check_hung_agents():
    with open('memory/agents.json', 'r') as f:
        agents = json.load(f)
    
    now = int(time.time())
    hung_threshold = agents['heartbeatProtocol']['hungThresholdSeconds']
    
    for agent_id, agent in agents['active'].items():
        last_heartbeat = agent.get('lastHeartbeat', 0)
        if now - last_heartbeat > hung_threshold:
            print(f"⚠️ Agent {agent_id} hung (no heartbeat for {now - last_heartbeat}s)")
            # Option 1: Kill and restart
            kill_agent(agent_id)
            # Option 2: Steer agent with new context
            steer_agent(agent_id, "Status check: Are you stuck?")
```

**Benefits:**
- **Early detection:** Know agent is hung after 60s (not 30 min)
- **Intervention:** Steer or kill hung agents
- **Debugging:** `lastHeartbeat` timestamp shows where agent got stuck
- **Resource management:** Don't waste slots on hung agents

**Real-World Example:**
- Security review agent hung on web_fetch (network timeout)
- After 60s (no heartbeat), orchestrator killed agent
- Respawned with fallback (local static analysis only)
- Result: Review completed in 2 min (vs 30 min timeout)

---

## Pattern 5: Dual-Tier Memory System

### Problem Statement

**LLMs have no persistent memory across sessions.**

**Example (pre-memory-system):**
- Session 1: Learn that EJ22 timing belt is critical
- Session 2 (next day): Forget lesson, suggest "check timing belt when convenient"
- User: "I told you yesterday this is urgent!"

**Root Cause:**
- Model weights frozen (no learning)
- Context window resets each session
- No external memory (all knowledge is ephemeral)

### Solution: Dual-Tier Memory

**Tier 1: Daily Logs (Raw Notes)**
- **File:** `memory/YYYY-MM-DD.md`
- **Purpose:** Capture everything that happened today
- **Format:** Chronological, append-only
- **Retention:** Keep last 7 days (prune older)

**Tier 2: Long-Term Memory (Curated)**
- **File:** `MEMORY.md`
- **Purpose:** Distilled insights, axioms, key decisions
- **Format:** Structured (axioms, projects, lessons)
- **Retention:** Forever (or until invalidated)

**Update Workflow:**

**During session (write to daily log):**
```markdown
# 2026-03-28 — Session Log

## Deep Work Session 1/6 (23:00-00:00 AKST)

**Research:**
- EJ22 timing belt research (12.8 KB doc)
- Interference engine mechanics
- Timing belt failure modes (4 types)
- Replacement procedure (step-by-step)

**Key Finding:**
- EJ22 is interference engine (valves hit pistons if belt breaks)
- 60k mile interval is NON-NEGOTIABLE
- Failure cost: $2,500-4,500 (vs $165-295 prevention)

**Tool Integration:**
- ej22-tracker must enforce timing belt warnings
- Red badge + startup acknowledgment if overdue
- Educational help screen (explain interference mechanics)
```

**During heartbeats (update MEMORY.md):**
```markdown
## Active Axioms

**[AXIOM-042]** Timing belt maintenance is non-negotiable on interference engines
> EJ22 belt failure = catastrophic damage ($3k+ repair)
- **Observed:** Research revealed interference design (valves hit pistons)
- **Applied:** ej22-tracker enforces 60k mile interval with startup warnings
- **Added:** 2026-03-28
```

**Benefits:**
- **Session continuity:** Load yesterday's log, know what happened
- **Long-term learning:** Axioms persist across weeks/months
- **Pattern detection:** Review daily logs → extract recurring themes → promote to axiom
- **Audit trail:** Full history available (when did we decide X?)

**Real-World Example (from MEMORY.md):**
- AXIOM-039 (Research → Prototype pipeline <24h) — extracted from 2026-03-27 session notes
- Pattern: Session 1 research → Session 2/5 prototypes (same night)
- Promoted to axiom after 3+ occurrences

---

## Pattern 6: Priority Queue (User Tasks Jump Queue)

### Problem Statement

**User requests wait while background work runs.**

**Example (pre-priority-queue):**
- 8 agents running (maxConcurrent = 8)
- All doing background research
- User asks: "Check PR status"
- Response: "All slots full, queued..."
- User waits 10 minutes

**Root Cause:**
- No prioritization (first-come, first-served)
- Background work consumes all slots
- User-interactive tasks treated same as batch jobs

### Solution: Priority Queue + Reserved Slots

**File:** `memory/agents.json`

**Schema:**
```json
{
  "priorityQueue": {
    "enabled": true,
    "rules": "User-interactive tasks jump queue when at maxConcurrent. Background work waits.",
    "maxConcurrent": 8,
    "reservedSlotsForUser": 2
  }
}
```

**Agent Priority Levels:**

| Priority | Examples | Slot Reservation |
|----------|----------|------------------|
| **user** | sessions_send responses, direct requests | 2 slots reserved |
| **background** | Research, cleanup, maintenance | Remaining 6 slots |

**Queue Implementation:**
```python
def spawn_agent(task, priority="background"):
    with open('memory/agents.json', 'r') as f:
        agents = json.load(f)
    
    active_count = len(agents['active'])
    max_concurrent = agents['priorityQueue']['maxConcurrent']
    reserved_slots = agents['priorityQueue']['reservedSlotsForUser']
    
    if priority == "user":
        # User tasks always get a slot (kill background if needed)
        if active_count >= max_concurrent:
            kill_lowest_priority_agent()
    else:
        # Background tasks wait if user slots reserved
        available_slots = max_concurrent - reserved_slots
        if active_count >= available_slots:
            return "QUEUED (waiting for slot)"
    
    # Spawn agent
    agent_id = f"agent:{task_id}"
    agents['active'][agent_id] = {
        'task': task,
        'priority': priority,
        'spawned': int(time.time())
    }
    
    with open('memory/agents.json', 'w') as f:
        json.dump(agents, f, indent=2)
```

**Benefits:**
- **Responsive:** User requests complete quickly
- **Fair:** Background work still runs (when slots available)
- **Recoverable:** Killed background agents can restart later

---

## Application to Active Projects

### r3LAY: Axiom Management System

**Current State:**
- Hybrid RAG (local files + axiom database)
- Axioms stored in MEMORY.md (41 active)
- No automated extraction from patterns

**Improvements:**
1. **Axiom Promotion Pipeline:**
   - Pattern detection (scan #patterns channel for 3+ occurrences)
   - Auto-suggest axiom candidates (PROPOSED-XXX)
   - Validation workflow (test in 3 sessions, then promote)

2. **Axiom Application Tracking:**
   - Log when axiom is applied (timestamp, context)
   - Measure effectiveness (did it prevent error?)
   - Deprecate unused axioms (no applications in 30 days)

3. **Cross-Project Axiom Sharing:**
   - Export axioms to r3LAY (automotive, retro gaming, LLM orchestration)
   - Import external axioms (from GitHub, forums, research papers)
   - Conflict resolution (when axioms contradict)

### synapse-engine: Tier Optimization

**Current State:**
- 3 tiers (FAST/BALANCED/POWERFUL)
- Manual tier selection (user picks)
- No auto-routing based on task type

**Improvements:**
1. **Task Classification:**
   - Simple queries → FAST (GPT-4o-mini)
   - Multi-step work → BALANCED (Claude Sonnet)
   - Deep research → POWERFUL (Claude Opus)

2. **Tier Routing Rules:**
   - File count <3 → FAST
   - File count 3-10 → BALANCED
   - File count >10 → POWERFUL

3. **Cost Optimization:**
   - FAST tier for 80% of queries (cheap, fast)
   - POWERFUL tier for 5% of queries (expensive, rare)
   - Track cost per session (prevent runaway spending)

### openclaw-dash: Workflow Automation

**Current State:**
- PR workflow state machine (manual transitions)
- No auto-spawning of review agents
- No CI status polling

**Improvements:**
1. **Auto-Spawn Workflow:**
   - On PR creation → spawn @security-specialist (immediate)
   - After security pass → spawn @code-reviewer (automatic)
   - After fixes applied → poll GitHub API for CI status

2. **State Machine Enforcement:**
   - Prevent merge unless state === "READY"
   - Block manual state changes (only valid transitions)
   - Audit log (who changed what, when)

3. **Integration with GitHub Actions:**
   - GitHub webhook → update pr-workflow-state.json
   - CI pass → transition to READY (automatic)
   - CI fail → add comment to PR (link to logs)

---

## Lessons Learned (Meta-Patterns)

### 1. External State > Agent Memory

**Problem:** Agents forget between sessions.  
**Solution:** Write state to files (`memory/agents.json`, `pr-workflow-state.json`).  
**Benefit:** Reliable, auditable, recoverable.

### 2. Smaller Scopes = Higher Success

**Problem:** Agents timeout on large tasks.  
**Solution:** Break work into <30min chunks.  
**Benefit:** Incremental progress, parallelizable, recoverable.

### 3. Planning Reduces Rework

**Problem:** Ad-hoc execution leads to refactors.  
**Solution:** Spawn @strategic-planning-architect upfront.  
**Benefit:** Clear roadmap, realistic estimates, fewer surprises.

### 4. Heartbeats Enable Intervention

**Problem:** Hung agents waste time.  
**Solution:** 10s heartbeat, 60s hung threshold.  
**Benefit:** Early detection, intervention, debugging.

### 5. Dual-Tier Memory = Continuity

**Problem:** LLMs have no persistent memory.  
**Solution:** Daily logs (raw) + MEMORY.md (curated).  
**Benefit:** Session continuity, long-term learning, pattern detection.

### 6. Priority Queues = Responsiveness

**Problem:** Background work blocks user requests.  
**Solution:** Reserved slots for user-interactive tasks.  
**Benefit:** Fast responses, fair scheduling, recoverable.

---

## Future Research Directions

1. **Axiom Conflict Resolution:**
   - What happens when 2 axioms contradict?
   - Example: AXIOM-003 (scope small) vs AXIOM-035 (plan early) — planning adds overhead
   - Resolution: Context-dependent (simple tasks skip planning)

2. **Agent Cost Tracking:**
   - Track token usage per agent (input + output)
   - Identify expensive patterns (e.g., research agents use 10x more tokens)
   - Optimize prompts (reduce input bloat)

3. **Multi-Agent Code Review:**
   - Spawn 3 reviewers in parallel (security, performance, style)
   - Merge reviews into single report
   - Faster than sequential (1/3 time)

4. **Automated Testing Integration:**
   - PR creation → auto-spawn test agent
   - Run unit tests, report coverage
   - Block merge if coverage <80%

5. **Agent Specialization Metrics:**
   - Which agents succeed most often?
   - Which tasks cause timeouts?
   - Refine agent prompts based on success rate

---

## Conclusion

**Key Takeaways:**

1. **State machines prevent completion bias** — external validation gates
2. **Smaller scopes = higher success** — <30min tasks rarely timeout
3. **Planning reduces rework** — @strategic-planning-architect pays off
4. **Heartbeats enable intervention** — detect hung agents early
5. **Dual-tier memory = continuity** — daily logs + curated axioms
6. **Priority queues = responsiveness** — user tasks jump queue

**Applications:**
- r3LAY: Axiom management (auto-promotion pipeline)
- synapse-engine: Tier optimization (task-based routing)
- openclaw-dash: Workflow automation (auto-spawn, CI polling)

**Next Steps:**
- Extract patterns into reusable libraries (psx-aesthetic, pr-workflow-lib)
- Implement axiom promotion pipeline (scan #patterns → PROPOSED-XXX)
- Build orchestrator dashboard (visualize agent activity, state machines)

**Time Investment:** 25 min research + documentation  
**Output:** 4,892 words, 6 actionable patterns  
**Total Session Time:** 60 min (RESEARCH window complete)

---

_Session complete. Moving to DOCUMENTATION phase (35-60 min)._
