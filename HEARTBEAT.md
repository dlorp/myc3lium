# HEARTBEAT.md - Proactive Monitoring

## Adaptive Intervals (Token Optimization)

**Business Hours (4am-6pm AKST):** Every 10 minutes
- High activity period
- User likely present
- Quick response needed

**Evening (6pm-11pm AKST):** Every 30 minutes  
- Moderate activity
- Balance responsiveness with cost

**Off-Hours (11pm-4am AKST):** Every 60 minutes
- Low activity period
- Deep work mode
- Batch checks

**Override:** If agents.json shows >3 active agents, use 10min interval regardless of time.

## Current Focus: Multi-Agent System Health

### Every Heartbeat (rotate through priorities)

**Priority 1 - Agent Health (check every heartbeat):**
- Read `memory/agents.json` (if exists)
- **Heartbeat check:** Any agents with lastHeartbeat >60s old? Mark as hung.
- Any agents running >30min? Check if hung (secondary check).
- Any completed agents with results to integrate?
- Any errors or timeouts to investigate?
- Update heartbeat-state.json with findings (ISO timestamp, status, metrics)

**Priority 2 - Human Context (check 4x daily):**
- GitHub: Uncommitted work in main projects? Any open PRs needing attention?
- **PR Workflow:** Check `memory/pr-workflow-state.json` active_prs, advance states:
  - CREATED → run audit, spawn security agent
  - SECURITY_REVIEW → check agent complete, file exists
  - CODE_REVIEW → spawn code reviewer
  - FIXES_APPLIED → detect new commits
  - CI_RUNNING → poll GitHub CI status
  - Transition to READY when all gates pass
- Discord: Recent activity in project channels? Any @mentions?
- Recent conversations: Any unfinished threads or follow-ups?

**Priority 3 - System Maintenance (check 2x daily):**
- Memory files: Daily logs from >7 days ago should be archived
- MEMORY.md: Last curated >3 days ago? Time to review and update
- Discord channels for memory updates:
  - **#session-notes:** Extract key learnings, decisions, next steps from `/SN` docs
  - **#patterns:** Check for recurring observations (3+ = new axiom candidate)
  - Update MEMORY.md: Add patterns to Lessons Learned, promote validated patterns to Axioms
  - Note project progress for Active Projects section
- Workspace organization: Any stray files or incomplete work?

**Priority 4 - Proactive Research (off-hours only, 23:00-08:00):**
- Research queue: Any pending deep dives to work on?
- Documentation: Any outdated files to refresh?
- Code patterns: Improvements to suggest?
- Learning: New skills or tools worth exploring?

### State Tracking

Track checks in `memory/heartbeat-state.json`:
```json
{
  "lastChecks": {
    "agents": 1703275200,
    "github": 1703270000,
    "discord": 1703260800,
    "memory": null
  },
  "offHoursQueue": [
    "Research exec security patterns",
    "Document API improvements"
  ]
}
```

### When to Reach Out (with Evaluation Windows)

**Speak up when:**
- Important agent completed with results
- Long-running task finished (>30min duration)
- **Sustained failure:** 3+ consecutive checks show same error (evaluation window)
- Discovered something interesting during proactive work

**Stay quiet (HEARTBEAT_OK) when:**
- Late night (23:00-08:00) unless urgent
- dlorp is clearly busy/focused
- Nothing actionable since last check
- You just checked <30 minutes ago
- **Transient failures:** Single failure in check history (wait for pattern)

**Evaluation Window Logic:**
- Track last 3 check results for each priority
- Alert if: [fail, fail, fail] (3 consecutive)
- Don't alert if: [ok, fail, ok] or [fail, ok, fail] (transient)
- Update checkHistory in heartbeat-state.json after each check
- Expected impact: 70% reduction in false positives

### Off-Hours Deep Work

When dlorp is offline, work through the queue:
1. Read `memory/orchestrator-state.json` for queued tasks (if exists)
2. Pick highest-priority item from off-hours queue
3. Spawn appropriate specialist agent
4. Track progress in agents.json
5. Synthesize results and update documentation
6. Log completion for next session

**Goal:** Use quiet hours productively. Wake dlorp up to a smarter, more organized system.
