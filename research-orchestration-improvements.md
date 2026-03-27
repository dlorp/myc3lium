# Multi-Agent Orchestration: Research & Recommendations

**Generated:** 2026-03-20  
**Context:** 15 specialized agents, max 8 concurrent, 30min hung timeout

---

## 1. Coordination Patterns in Multi-Agent Systems

### Current Industry Approaches

#### **Hierarchical Coordination**
- **Pattern:** Supervisor agent delegates to worker agents
- **Pros:** Clear responsibility chain, easier debugging, natural backpressure
- **Cons:** Single point of failure, supervisor can bottleneck
- **Used by:** LangGraph, AutoGen, CrewAI

#### **Peer-to-Peer (Swarm)**
- **Pattern:** Agents communicate directly, self-organize
- **Pros:** Resilient, scales horizontally, no bottleneck
- **Cons:** Complex coordination, harder to trace, potential chaos
- **Used by:** Multi-agent RL systems, distributed planning

#### **Message Bus/Event-Driven**
- **Pattern:** Agents publish/subscribe to event streams
- **Pros:** Decoupled, asynchronous, easy to add agents
- **Cons:** Eventual consistency, harder to reason about state
- **Used by:** Production ML systems, microservices

#### **Blackboard Architecture**
- **Pattern:** Shared knowledge store, agents read/write collaboratively
- **Pros:** Knowledge persistence, agents can build on each other's work
- **Cons:** Concurrent access complexity, potential race conditions
- **Used by:** Planning systems, collaborative problem-solving

### **Recommendation for OpenClaw:**
**Hybrid: Hierarchical + Event Bus**
- Main agent coordinates (current model works well)
- Add lightweight event bus for agent-to-agent status updates
- Preserve push-based completion (already correct!)
- Agents emit lifecycle events: `spawned`, `progress`, `blocked`, `completed`, `failed`

---

## 2. Agent Lifecycle Management Best Practices

### State Machine Model

```
IDLE → PENDING → RUNNING → [COMPLETED | FAILED | TIMEOUT | KILLED]
                    ↓
                 BLOCKED (waiting on resource/agent)
```

### Key Principles

#### **1. Explicit State Tracking**
Current `agents.json` is good. Enhance with:
```json
{
  "agent_id": "subagent-abc123",
  "state": "RUNNING",
  "parent_id": "main",
  "depth": 1,
  "spawned_at": 1710975123,
  "last_heartbeat": 1710975200,
  "expected_completion": 1710976923,
  "dependencies": ["subagent-xyz789"],
  "resources": ["github-api", "file:/path/to/workspace"]
}
```

#### **2. Heartbeat Protocol**
- Agents emit heartbeats every N seconds (5-10s recommended)
- Parent expects heartbeat within 2x interval
- **Miss threshold:** 3 missed heartbeats → mark `SUSPECTED_HUNG`
- **Timeout:** 30min absolute limit (current) is good for max bound

#### **3. Graceful Shutdown Cascade**
- Parent terminated → notify children first
- Give children 10s to save state/cleanup
- Force-kill stragglers after grace period
- Bubble up partial results when possible

#### **4. Restart Policies**
```yaml
restart_policy:
  - transient_error: retry_once  # API timeout, etc.
  - rate_limit: exponential_backoff
  - invalid_input: fail_fast
  - timeout: report_partial_then_fail
```

### **Recommendations:**
1. ✅ Keep push-based completion (avoids polling, correct design)
2. ✅ 30min timeout is reasonable for long tasks
3. ➕ Add heartbeat mechanism (lighter than full polling)
4. ➕ Add `BLOCKED` state for agents waiting on dependencies
5. ➕ Track expected completion time for better timeout estimation

---

## 3. Resource Allocation Strategies

### Problems to Solve
- **Concurrency limits** (max 8 concurrent)
- **Token budget exhaustion**
- **API rate limits** (GitHub, Discord, etc.)
- **Workspace file conflicts** (multiple agents editing same files)

### Allocation Patterns

#### **Semaphore/Slot-Based (Current Model)**
✅ Already using: max 8 concurrent slots  
**Enhancement:** Priority queue for slot allocation
```python
priority_order = [
  "user-interactive",  # User waiting for response
  "deadline-driven",   # Has external deadline
  "background",        # Heartbeat tasks, research
  "batch"              # Mass operations
]
```

#### **Token Budget Allocation**
**Problem:** One greedy agent can starve others  
**Solution:** Per-agent token budgets with borrowing
```
Total: 200k tokens/session
- Main agent: 50k (reserve)
- Subagents: 150k pool
  - Each gets min 10k guaranteed
  - Can borrow from pool if available
  - Hard cutoff at 40k/agent
```

#### **Resource Locking (File/API)**
Prevent conflicts when multiple agents touch same resources:
```json
{
  "locks": {
    "file:/workspace/AGENTS.md": {
      "held_by": "subagent-abc",
      "mode": "write",
      "acquired_at": 1710975123
    },
    "api:github": {
      "held_by": "subagent-xyz",
      "quota_remaining": 4500,
      "resets_at": 1710978723
    }
  }
}
```

**Lock Modes:**
- `read`: Many agents can hold simultaneously
- `write`: Exclusive, blocks other readers/writers
- `quota`: Shared pool, decrement on use

### **Recommendations:**
1. ➕ Add priority queue for agent scheduling
2. ➕ Implement per-agent token budgets (prevents starvation)
3. ➕ Add file lock coordinator (prevents edit conflicts)
4. ➕ Track API quota per-resource (prevents rate limit cascade)

---

## 4. Deadlock & Hung Agent Detection

### Deadlock Scenarios

#### **Circular Dependency**
```
Agent A waits for Agent B
Agent B waits for Agent C
Agent C waits for Agent A
```

**Detection:** Dependency graph cycle detection (Tarjan's algorithm)  
**Prevention:** 
- Limit dependency depth (current: 1 level, good!)
- Timeout on inter-agent waits (5-10min)
- Fail-fast on detected cycles

#### **Resource Deadlock**
```
Agent A holds Lock X, wants Lock Y
Agent B holds Lock Y, wants Lock X
```

**Detection:** Wait-for graph analysis  
**Prevention:**
- Lock ordering (always acquire in consistent order)
- Lock timeout (auto-release after 5min)
- Banker's algorithm for quota allocation

#### **Hung Detection (Non-Deadlock)**

**Symptoms:**
- No heartbeat for >30s
- No tool calls for >5min on active agent
- CPU/memory flatlined
- Process exists but unresponsive

**Detection Strategy:**
```python
def is_hung(agent):
    # Multi-signal approach
    signals = [
        time.now() - agent.last_heartbeat > 30,
        time.now() - agent.last_tool_call > 300,
        agent.state == "RUNNING" and not agent.process.is_active(),
        agent.output_buffer_unchanged_for > 120
    ]
    return sum(signals) >= 2  # 2+ signals = likely hung
```

**Recovery Actions:**
1. Send interrupt signal (SIGINT)
2. Wait 10s for graceful shutdown
3. Force kill (SIGKILL)
4. Mark as `TIMEOUT`
5. Return partial results if available

### **Recommendations:**
1. ✅ Keep depth limit (prevents deep cycles)
2. ➕ Implement dependency graph cycle detection
3. ➕ Multi-signal hung detection (more robust than timeout alone)
4. ➕ Add resource lock coordinator with timeouts
5. ➕ Graceful degradation: return partial results before killing

---

## 5. Result Aggregation Patterns

### Aggregation Strategies

#### **Sequential Composition**
```
Agent A output → Agent B input → Agent C input → Final result
```
**Use when:** Each step depends on previous  
**Current model:** ✅ Implicit via parent-child relationships

#### **Parallel Fan-Out/Fan-In**
```
        ┌─ Agent A ─┐
Input ──┼─ Agent B ─┼── Aggregate → Output
        └─ Agent C ─┘
```
**Use when:** Independent sub-tasks, combine results  
**Example:** Multi-source research, parallel API calls

#### **Map-Reduce**
```
Map:    [Item1, Item2, Item3] → [Agent1(Item1), Agent2(Item2), Agent3(Item3)]
Reduce: [Result1, Result2, Result3] → Aggregate(Results)
```
**Use when:** Same operation on many items  
**Example:** Analyzing 50 repos, processing 100 files

#### **Streaming Aggregation**
Agents emit results incrementally, parent processes as they arrive  
**Use when:** Large results, want partial updates  
**Example:** Long research reports, video transcription

### Aggregation Techniques

#### **Conflict Resolution**
When multiple agents provide different answers:
```python
strategies = {
    "majority_vote": lambda results: most_common(results),
    "confidence_weighted": lambda results: max(results, key=lambda r: r.confidence),
    "timestamp_latest": lambda results: max(results, key=lambda r: r.timestamp),
    "human_review": lambda results: prompt_user_to_choose(results)
}
```

#### **Partial Results**
When agents timeout/fail, preserve what was completed:
```json
{
  "status": "partial",
  "completed": ["taskA", "taskB"],
  "failed": ["taskC"],
  "results": {
    "taskA": {...},
    "taskB": {...}
  },
  "error": "Agent timeout after 30min"
}
```

### **Recommendations:**
1. ✅ Current push-based model handles sequential well
2. ➕ Add parallel fan-out support (spawn multiple, wait for all)
3. ➕ Implement map-reduce helper for batch operations
4. ➕ Always preserve partial results on failure/timeout
5. ➕ Add conflict resolution strategies for multi-agent consensus

---

## 6. Comparative Analysis: Your Current Setup

### Strengths ✅

1. **Push-based completion** — Correct design, avoids polling overhead
2. **Depth limiting** — Prevents runaway recursion
3. **30min timeout** — Reasonable max bound for long tasks
4. **Specialized agents** — Clear separation of concerns
5. **agents.json tracking** — Central state visibility

### Gaps & Opportunities ➕

| Gap | Impact | Fix Complexity |
|-----|--------|----------------|
| No heartbeat mechanism | Can't distinguish hung vs slow | Low |
| No resource locking | File conflicts, API quota races | Medium |
| No priority queue | User-interactive blocked by batch | Low |
| No token budgets | Agent starvation possible | Medium |
| No dependency tracking | Can't detect circular waits | Medium |
| No partial result recovery | All-or-nothing on timeout | Low |
| No graceful shutdown | Orphaned resources on parent kill | Medium |

---

## 7. Specific Improvements for AGENTS.md

### Additions to AGENTS.md

#### **Section: Agent Coordination Rules**

```markdown
## Agent Coordination Rules

### Heartbeats
- Subagents emit heartbeat every 10s (via `HEARTBEAT_PING` message)
- Parent expects heartbeat within 25s (2.5x interval)
- 3 missed heartbeats → marked `SUSPECTED_HUNG`
- Hung detection uses multi-signal approach (see orchestration docs)

### Resource Locking
Before accessing shared resources:
1. Check if lock available: `lock:request:<resource>`
2. Acquire lock: `lock:acquire:<resource>:<mode>`
3. Use resource
4. Release lock: `lock:release:<resource>`

Locks auto-expire after 5min to prevent deadlock.

**Lock Modes:**
- `read` - Shared (multiple agents ok)
- `write` - Exclusive (blocks all others)

**Lockable Resources:**
- Files: `file:/absolute/path/to/file.md`
- APIs: `api:github`, `api:discord`, etc.

### Partial Results
When timeout/failure is imminent:
1. Serialize current state to workspace
2. Emit `PARTIAL_RESULT` with path to saved state
3. Parent can resume or use partial data

### Dependencies
- Declare dependencies at spawn: `depends_on: [agent_id1, agent_id2]`
- System detects circular dependencies (fails fast)
- Max dependency wait: 10min (then fail)
```

#### **Section: Priority Levels**

```markdown
## Agent Priority Levels

When max concurrency (8) is reached, queue by priority:

1. **URGENT** - User waiting for response
2. **HIGH** - Deadline-driven tasks
3. **NORMAL** - Standard operations (default)
4. **LOW** - Background research, batch jobs

Set priority at spawn:
`sessions_spawn priority=high task="..."`
```

#### **Section: Token Budget Guidelines**

```markdown
## Token Budget Management

**Total pool:** 200k tokens/session  
**Allocation:**
- Main agent: 50k (reserved)
- Subagent pool: 150k (shared)

**Per-subagent limits:**
- Guaranteed minimum: 10k
- Borrowable maximum: 40k
- Hard cutoff at 40k (prevents starvation)

**When approaching limit:**
1. Summarize findings to main agent
2. Request continuation in fresh session
3. Or compress context (drop old tool outputs)
```

#### **Section: Anti-Patterns to Avoid**

```markdown
## Multi-Agent Anti-Patterns

**DON'T:**
- ❌ Poll for subagent status (use push-based completion)
- ❌ Spawn >3 subagents for simple tasks (overhead > benefit)
- ❌ Create circular dependencies (A waits for B waits for A)
- ❌ Edit same file from multiple agents (acquire lock first)
- ❌ Ignore partial results (always save progress)
- ❌ Spawn depth >2 (rarely needed, hard to debug)

**DO:**
- ✅ Let subagents auto-announce completion
- ✅ Use map-reduce for parallel batch work
- ✅ Emit heartbeats from long-running agents
- ✅ Request locks before file writes
- ✅ Preserve partial results on timeout
- ✅ Keep agent tasks focused and bounded
```

---

## 8. Implementation Roadmap

### Phase 1: Low-Hanging Fruit (1-2 days)
- [ ] Add heartbeat protocol to subagent template
- [ ] Implement partial result saving on timeout
- [ ] Add priority field to spawn command
- [ ] Document lock conventions in AGENTS.md

### Phase 2: Core Infrastructure (1 week)
- [ ] Build resource lock coordinator
- [ ] Implement per-agent token budgets
- [ ] Add dependency graph tracking
- [ ] Multi-signal hung detection

### Phase 3: Advanced Features (2 weeks)
- [ ] Parallel fan-out/fan-in helpers
- [ ] Map-reduce batch processor
- [ ] Conflict resolution strategies
- [ ] Graceful shutdown cascade

---

## 9. Key Takeaways

### What You're Doing Right ✅
1. **Push-based completion** (industry best practice)
2. **Depth limiting** (prevents chaos)
3. **Specialized agents** (clear contracts)
4. **Max concurrency cap** (prevents resource exhaustion)

### Quick Wins ➕
1. **Heartbeats** → Distinguish hung from slow (10 lines of code)
2. **Partial results** → Recover value from timeouts (save-on-exit)
3. **Priority queue** → User responsiveness (simple sort)
4. **Lock docs** → Prevent file conflicts (documentation only)

### Bigger Investments 🏗️
1. **Resource lock coordinator** → Prevents deadlock (new service)
2. **Token budgets** → Fairness guarantees (accounting layer)
3. **Map-reduce** → Batch operations (framework)

---

## 10. References & Further Reading

### Academic Foundations
- **Multi-Agent Systems (Wooldridge, 2009)** - Coordination theory
- **Contract Net Protocol (Smith, 1980)** - Task allocation classic
- **Deadlock detection in distributed systems (Chandy et al, 1983)**

### Industry Implementations
- **LangGraph** - Hierarchical + state machines
- **AutoGen** - Group chat + agent protocols
- **Ray** - Distributed scheduling + resource management
- **Kubernetes** - Pod lifecycle, health checks, graceful shutdown

### Patterns
- **Circuit Breaker** (Nygard, Release It!) - Prevent cascade failures
- **Saga Pattern** (Garcia-Molina, 1987) - Distributed transactions
- **Bulkhead** (Microsoft) - Isolate resource pools

---

**End of Report**

*This research was conducted 2026-03-20 as part of improving OpenClaw's multi-agent orchestration capabilities. Priority: implement heartbeats + partial results first (highest ROI).*
