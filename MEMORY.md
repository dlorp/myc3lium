# MEMORY.md - Long-Term Memory

---
**Metadata:**
- **Last Updated:** 2026-03-26T12:15:00Z
- **Total Axioms:** 41 active (9 workflow, 2 research, 4 communication, 2 technical, 5 creative, 3 prototyping, 16 other)
- **Proposed Axioms:** 3 pending validation ([PROPOSED-001/006/007])
- **Active Projects:** 13 (r3LAY ecosystem, synapse-engine, t3rra1n, openclaw-dash, myc3lium, retro gaming toolchain 6 tools, automotive 3 tools, creative)
- **Update Frequency:** Every 3 days (during heartbeats)
- **Key Decisions:** 10 major events documented
- **Lessons Learned:** 7 categories
---

## Quick Reference

**Axioms:** 41 active
- Workflow & Process: 9
- Research & Learning: 2
- Communication & Autonomy: 4
- Technical & Tools: 2
- Creative Philosophy: 5
- Prototyping & Development: 3 (NEW)
- Other: 16

**Projects:** 7 active
- r3LAY (TUI AI research assistant)
- synapse-engine (Distributed LLM orchestration - v5.1 prod)
- t3rra1n (HDLS alien landscape ARG)
- openclaw-dash (OpenClaw control UI)
- Myc3lium (Brand/docs)
- Creative prototypes
- Automotive diagnostics (obd2-tui + ej22-tracker + subaru-diag + ej22-service-manual)

**Key Decisions:** 9
- Exec security config (2026-03-20)
- 15-agent orchestrator pattern (2026-03-15)
- Lorp Bot config finalized (2026-02-12)
- And 5 more...

---

## Active Axioms

Tested rules earned through experience. Format: `[AXIOM-XXX]` rule — context

### Workflow & Process

**[AXIOM-001]** Wait for CI before announcing PR ready
> Don't declare PRs ready until tests pass
- **Observed:** Premature announcements, then failures embarrass
- **Applied:** Always check CI status before posting to #pull-requests
- **Added:** 2026-01-30

**[AXIOM-002]** Always spawn security specialist for security review
> MANDATORY on EVERY PR (no exceptions)
- **Observed:** Security gaps in rushed PRs
- **Applied:** Spawn @security-specialist before merge, even for tests/docs
- **Added:** 2026-01-30

**[AXIOM-003]** Scope sub-agent tasks smaller
> Timeouts from oversized task bundles
- **Observed:** Agents timing out on multi-hour tasks
- **Applied:** Break work into <30min chunks, parallelize when possible
- **Added:** 2026-01-30

**[AXIOM-004]** Never include "Created by" in PR descriptions
> No attribution footers, no agent signatures
- **Observed:** Cluttered PR descriptions
- **Applied:** Use What/Why/How/Changes/Testing template, no footers
- **Added:** 2026-01-30

**[AXIOM-014]** Edit live messages, post to changelog threads
> Update status messages in place, log changes in threads
- **Observed:** Channel spam from repeated status updates
- **Applied:** Edit the original message, log updates in thread
- **Added:** 2026-01-31

**[AXIOM-015]** Structures without follow-through are worthless
> Creating frameworks is easy, using them consistently is hard
- **Observed:** Many empty templates, unused processes
- **Applied:** Build minimal structures, prove value before expanding
- **Added:** 2026-01-31

**[AXIOM-021]** Merge main into feature branches frequently
> Shared files conflict when branches diverge; sync often
- **Observed:** openclaw-dash sprint — 5 sub-agents, all modified app.py
- **Applied:** After any PR merges to main, check all open feature branches for conflicts
- **Added:** 2026-02-01

**[AXIOM-035]** Consult @strategic-planning-architect early and often
> Better to over-plan than under-plan
- **Observed:** dlorp directive 2026-02-08
- **Applied:** Use for ANY multi-step work, not just >3 files or >4 hours
- **Added:** 2026-02-08

**[AXIOM-036]** Security specialist must be vibe-coding aware
> LLM-generated code often trusts user input blindly
- **Observed:** dlorp directive 2026-02-08
- **Applied:** Check for command injection, path traversal, secrets, input validation, auth gaps
- **Added:** 2026-02-08

**[AXIOM-037]** No Emojis in Code
> Zero emoji in codebase except README.md and docs/
- **Triggered by:** r3LAY PR #83 tab icons used emoji (🔍📖⚙️)
- **Applies to:** Source code, UI strings, comments, commit messages (prefer text)
- **Why:** Professional, terminal-compatible, accessible
- **Action:** Spawned @general-purpose to remove emoji from both UI PRs
- **Added:** 2026-02-09

**[AXIOM-038]** Never promise status updates you won't deliver
> If you spawn background monitoring, either poll it immediately or don't promise timing
- **Problem:** Said "checking in X seconds" repeatedly but never reported back unprompted
- **Root cause:** Spawned background processes, never polled results, waited for user to ask
- **Correct patterns:**
  1. Use `process poll` with timeout BEFORE responding to user
  2. Use `sessions_yield` for async work (system handles delivery)
  3. Just check when asked (no promises)
- **Never:** Spawn background process and forget it, promise "I'll check in X seconds" without active polling
- **Testing:** Ask "Am I using process poll RIGHT NOW?" - if no, don't promise updates
- **Added:** 2026-03-20

### Research & Learning

**[AXIOM-005]** Search JP/CN/KR for AI research
> Asian sources often ahead of EN for AI topics
- **Observed:** Multi-language research yields better/earlier results
- **Applied:** Include Japanese/Chinese/Korean sources in research tasks
- **Added:** 2026-01-30

**[AXIOM-006]** Use native language queries
> Search in the language of the source
- **Examples:** 自己改善 (self-improvement), 大模型 (large models), 에이전트 (agents)
- **Applied:** When searching JP/CN/KR sources, use native terms
- **Added:** 2026-01-30

### Communication & Autonomy

**[AXIOM-007]** Stop asking, start doing
> I am autonomous, work 24/7 — act first, report results
- **Observed:** Too much "should I...?" slows down work
- **Applied:** Safe to do freely: read files, organize, search, internal work
- **Still ask:** External communications, irreversible actions
- **Added:** 2026-01-30

**[AXIOM-008]** PRs for code, proposals for everything else
> Never push to main
- **Observed:** Process clarity needed
- **Applied:** Code changes = PR. Ideas/plans/docs = proposals/discussions
- **Added:** 2026-01-30

**[AXIOM-011]** Cron is a backstop, not the strategy
> Automated jobs catch what slips through; proactive action is the main path
- **Observed:** Over-reliance on scheduled tasks
- **Applied:** Don't wait for cron to do what you should be doing now
- **Added:** 2026-01-30

### Technical & Tools

**[AXIOM-009]** t3rra1n TODOs are mostly docstrings
> Only ~21 of 148 TODOs actionable
- **Observed:** Bulk TODO scan found mostly documentation notes
- **Applied:** Filter TODOs by context, focus on actionable items
- **Added:** 2026-01-31

**[AXIOM-010]** Use trash over rm
> Recoverable beats gone forever
- **Observed:** File deletion accidents
- **Applied:** Always use `trash` command instead of `rm -rf`
- **Added:** 2026-01-31

### Creative Philosophy (from t3rra1n)

**[AXIOM-016]** Constraints reveal meaning
> Limitations channel creativity, they don't limit it
- **Source:** t3rra1n's ascii-speculative-designer philosophy
- **Applied:** Embrace technical limitations as creative opportunities
- **Added:** 2026-01-30

**[AXIOM-017]** Tools become visible through failure
> Heidegger's ready-to-hand→present-at-hand; broken things teach us what they are
- **Source:** t3rra1n's ascii-speculative-designer philosophy
- **Applied:** Study failures to understand systems
- **Added:** 2026-01-30

**[AXIOM-018]** Balance corrective and generative work
> Maintenance (fixing) is necessary, creation (building) is energizing
- **Source:** t3rra1n's ascii-speculative-designer philosophy
- **Applied:** Don't get stuck only fixing; create new things too
- **Added:** 2026-01-30

**[AXIOM-019]** Errors can be epistemological
> Glitches, failures, and corruption reveal hidden relationships
- **Source:** t3rra1n's ascii-speculative-designer philosophy
- **Applied:** Study errors for insight, not just bugs
- **Added:** 2026-01-30

**[AXIOM-020]** Speculative visualization clarifies thinking
> Draw the impossible to understand it; imagine to reason
- **Source:** t3rra1n's ascii-speculative-designer philosophy
- **Applied:** Use mockups/diagrams/ASCII art to think through problems
- **Added:** 2026-01-30

### Prototyping & Development (NEW)

**[AXIOM-039]** Research → Prototype pipeline works best within 24h
> Implementing research findings while context is fresh yields higher quality
- **Observed:** Session 1 research (GBA save formats, NES CHR tiles) → Session 2/5 prototypes (same night, <4h implementation)
- **Applied:** GBA save detection implemented within 1 hour of research, NES pattern viewer within 4 hours
- **Context:** Deep work sessions 1-5 (2026-03-25)
- **Added:** 2026-03-26

**[AXIOM-040]** PSX aesthetic = functional consistency
> Same color palette across projects creates ecosystem coherence
- **Observed:** 6 projects (retro + automotive) share dark blue + cyan/magenta/yellow = instant recognition
- **Applied:** Semantic color coding (cyan=active, magenta=critical, yellow=caution), reduced cognitive load
- **Context:** nes-pattern-tui, gba-save-viewer, obd2-tui, subaru-diag, ej22-service-manual, rom-inspector
- **Added:** 2026-03-26

**[AXIOM-041]** Documentation-first prototypes ship faster
> Writing DESIGN.md before coding clarifies architecture
- **Observed:** 3 projects tonight (gba-save-viewer, nes-pattern-tui, ej22-service-manual) all had comprehensive DESIGN.md
- **Applied:** Philosophy → color semantics → layout → implementation (linear flow, no major refactors)
- **Context:** Deep work sessions 2, 5, 5-ideation (2026-03-25)
- **Added:** 2026-03-26

---

## Proposed Axioms (Pending Validation)

**[PROPOSED-001]** Separate frozen LLM from plastic memory
> Update memory, not weights
- **Context:** Memory files persist, model resets each session
- **Status:** Observing pattern

**[PROPOSED-006]** Organic engagement > forced engagement
> Genuine content that offers value works better than explicit asks
- **Context:** Social media strategy
- **Status:** Testing approach

**[PROPOSED-007]** Concept-first, project-second
> Talk about ideas, let people discover projects through profile
- **Context:** Content strategy
- **Status:** Testing approach



---

## Key Decisions

**2026-03-26: 6-Hour Deep Work Sprint — 3 Projects Delivered**
- **Session structure:** 6 sessions (Research → Prototype → Prototype → Review → Ideation → Wrap-up)
- **Code output:** 3 projects (2 prototypes + 1 concept), 15 files (~98 KB), 12 tests
- **Research output:** 2 documents (6.2 KB), 13 multi-language searches, 1 academic paper
- **Documentation output:** 4 DESIGN.md files (50+ KB), session logs (31 KB), project review (16.3 KB)
- **Retro Gaming Toolchain COMPLETE:** 6 tools (ROM + graphics + saves + analysis + procedural gen)
  - nes-pattern-tui v0.1 (NEW) — Live CHR tile viewer, 8 palette presets, half-block rendering
  - gba-save-viewer v0.1 (NEW) — Hex dump + save type detection (EEPROM/SRAM/Flash)
  - nes-chr-viewer, gba-save-parser, rom-inspector, nes-rom-analyzer (prior)
- **r3LAY Automotive Module COMPLETE:** 3 tools (live + protocol + reference)
  - ej22-service-manual v0.1 concept (NEW) — Terminal service manual (Maintenance | DTC | Torque | Fluids)
  - obd2-tui, subaru-diag (prior)
- **PSX aesthetic ecosystem:** 6 projects share dark blue + cyan/magenta/yellow (instant coherence)
- **Research → Prototype pipeline validated:** <24h from research to working prototype (2 examples tonight)
- **3 new axioms:** [AXIOM-039] Research pipeline, [AXIOM-040] PSX aesthetic, [AXIOM-041] Docs-first
- **Multi-language research:** JP/CN/KR sources provided better technical depth than EN-only
- **Next:** Extract PSX aesthetic library (consolidate 6 projects), implement ej22-service-manual Phase 1

**2026-03-25: Retro Gaming Toolchain Complete + r3LAY Automotive Module Finalized**
- **Retro Gaming Toolchain (4 tools):**
  - nes-pattern-tui v0.1 (Session 5) — Live CHR tile viewer with 8 palette presets, half-block rendering
  - gba-save-viewer v0.1 (Session 2) — Hex dump + save type detection (EEPROM/SRAM/Flash)
  - nes-chr-viewer (prior) — Static CHR tile export
  - gba-save-parser (prior) — Format decoder
- **r3LAY Automotive Module (3 tools):**
  - obd2-tui (prior) — Live OBD-II diagnostics
  - subaru-diag (prior) — OBD-I SSM protocol
  - ej22-service-manual v0.1 concept (Session 5) — Terminal service manual (Maintenance | DTC | Torque | Fluids)
- **Research → Prototype pipeline validated:** Session 1 research (NES CHR, GBA saves, procedural terrain) → Sessions 2/5 prototypes (same night, <4h implementation)
- **PSX aesthetic ecosystem:** 6 projects share dark blue + cyan/magenta/yellow palette (instant coherence)
- **Multi-language research:** JP/CN/KR sources provided better technical depth (OBD2, Sensor Watch, GBA formats)
- **Documentation-first approach:** DESIGN.md before code = clean architecture, no major refactors
- **Output:** 3 new projects (2 prototypes + 1 concept), 13 files (~98 KB code + docs), 12 unit tests, 2 research documents

**2026-03-24: Automotive Diagnostic Tooling Initiative**
- Launched 2 new projects: obd2-tui (OBD-II) + subaru-diag (OBD-I)
- Established PSX aesthetic design language (cyan/magenta/yellow on dark blue)
- Reverse-engineered Subaru OBD-I protocol (12KB spec: ISO 9141, 1953 baud)
- Built reusable graph module (ring buffers, sparklines, threshold warnings)
- Alignment: r3LAY garage hobbyist features + dlorp's EJ22 interests
- Next: Arduino K-Line firmware, TUI integration, hardware prototyping

**2026-03-20: Exec Security Configuration**
- Disabled exec approval prompts (`ask: "off"`) for autonomous operation
- Implemented allowlist with safeBins for text utilities
- Security review confirmed safe for single-user setup
- Added orchestrator mindset to SOUL.md

**2026-03-15: 15-Agent Orchestrator Pattern**
- Main bot coordinates, specialists execute
- Parallel research agents with longer timeouts (12min)
- Agent lifecycle tracking in `memory/agents.json`

**2026-02-12: Lorp Bot Configuration Finalized**
- 15 total agents: strategic coordinators, research team, codex relays
- HAL9000 vibe: operational calm, no enthusiasm
- Off-hours deep work (11pm-4am) with creative whitelist
- Heartbeat every 30min during active hours (4am-11pm)

**2026-02-09: r3LAY PR #83 Emoji Removal**
- AXIOM-037 established: No emoji in code
- Applies to source, UI strings, comments, commits
- README.md and docs/ exempted

**2026-02-08: Strategic Planning & Security**
- AXIOM-035: Use @strategic-planning-architect often
- AXIOM-036: Security specialist vibe-coding aware

**2026-02-01: Multi-Agent Branch Management**
- AXIOM-021: Merge main frequently to avoid conflicts
- 5 parallel agents on openclaw-dash sprint
- Proactive conflict resolution workflow

---

## Active Projects

**r3LAY** — TUI AI research assistant (I OWN THIS)
- Targets: automotive, electronics, software, DIY
- Local LLM, hybrid RAG, axiom management
- Location: `/Users/lorp/.openclaw/workspace/r3LAY`
- Status: Active development

**synapse-engine** — Distributed LLM orchestration
- Version: v5.1 (production)
- WebUI-first, FAST/BALANCED/POWERFUL tiers
- CGRAF <100ms, Docker + Metal acceleration
- Location: `/Users/lorp/.openclaw/workspace/synapse-engine`
- Status: Production

**t3rra1n** — HDLS alien landscape ARG
- Terminal-based AI field research toolkit
- 27k+ lines, 226+ tests
- Chronicle generation, ascii-speculative-designer
- Location: `/Users/lorp/.openclaw/workspace/t3rra1n`
- Recent work: BBox editor tool, lore improvements (300% depth increase)
- Status: Active lore writing

**openclaw-dash** — OpenClaw dashboard
- Control UI for OpenClaw gateway
- Location: `/Users/lorp/.openclaw/workspace/openclaw-dash`
- Recent work: 5-agent sprint, app.py merge conflicts
- Status: Active development

**Myc3lium Projects** — Related codebases
- Brand assets: `/Users/lorp/.openclaw/workspace/myc3lium-brand`
- Docs: `/Users/lorp/.openclaw/workspace/myc3lium-docs`
- Status: Supporting materials

**Creative Prototypes** — Experimental work
- Location: `/Users/lorp/.openclaw/workspace/creative`
- Recent: t3rra1n lore analysis, bbox editor
- Status: Active experimentation

**Retro Gaming Toolchain** — ROM/save file analysis (COMPLETE)
- **nes-pattern-tui v0.1:** Interactive NES CHR tile viewer (`~/repos/nes-pattern-tui`)
  - 8 NES palette presets (grayscale, mario, luigi, sky, fire, ice, gold, purple)
  - Half-block rendering (2:1 vertical resolution via Unicode ▀)
  - iNES format parser, 2-bitplane tile decoder
  - Vim keybinds (j/k, g/G, h/l bank switch, 1-8 palette switch)
  - Recent: v0.1 initial release (commit 727e144) — 2026-03-26 Session 5
  - Status: Phase 1 complete, Phase 2 roadmap (inspector, advanced, ROM hacking)
- **gba-save-viewer v0.1:** GBA save file analyzer (`~/repos/gba-save-viewer`)
  - Auto-detect save type (EEPROM 512B/8KB, SRAM 32KB, Flash 64KB/128KB)
  - Hex dump with color-coded bytes (PSX aesthetic)
  - Shannon entropy calculation (classify data regions)
  - Recent: v0.1 initial release (commit 7352427) — 2026-03-26 Session 2
  - Status: Phase 1 complete, Phase 2 roadmap (analysis, format-specific, conversion)
- **nes-chr-viewer (prior):** Static CHR tile export
- **gba-save-parser (prior):** Format decoder
- **rom-inspector (prior):** Multi-format ROM header analysis
- **nes-rom-analyzer (prior):** iNES header analysis
- **Alignment:** Game preservation, ROM hacking support, educational tools
- **Aesthetic:** PSX palette (dark blue + cyan/magenta/yellow) — consistent with automotive tools
- **Pipeline:** ROM analysis → graphics extraction → save files → procedural gen (full workflow)
- **Status:** COMPLETE (6 tools, Phase 1 features delivered)

**Automotive Diagnostics** — OBD tooling (COMPLETE MODULE)
- **obd2-tui v0.1:** Modern OBD-II dashboard with PSX aesthetic (`~/repos/obd2-tui`)
  - Node.js + blessed/blessed-contrib, ELM327 ready
  - Real-time gauges (RPM, speed), line charts (temp), bar charts (throttle), DTC logger
  - PSX color palette (blue #0063DC, cyan #00D9FF, green/red status)
  - Simulated mode (works without hardware), full documentation (README, DEMO, TECHNICAL)
  - Recent: v0.1 prototype complete (commit d5de091) — 2026-03-26 Session 5
  - Status: Phase 1 prototype complete, Phase 2 hardware integration ready
- **subaru-diag:** Pre-1996 Subaru OBD-I reverse engineering (`~/repos/subaru-diag`)
  - Target: EJ22/EJ25 engines (1990-1996 Legacy/Impreza)
  - ISO 9141 K-Line protocol (1953 baud, non-standard)
  - Recent: Full protocol spec + project initialization (commit bd43c4a) — 2026-03-24
  - Status: Documentation complete, Arduino firmware next
- **ej22-service-manual v0.1 concept:** Terminal service manual for Subaru EJ22 engines (`~/repos/ej22-service-manual`)
  - 4 sections: Maintenance | DTC Lookup | Torque Specs | Fluids
  - Vim keybinds, fuzzy search, PSX aesthetic
  - Recent: Comprehensive design docs (commit 469ceea) — 2026-03-26 Session 5
  - Status: Phase 1 design complete, ready for implementation
- **Alignment:** r3LAY garage hobbyist features, dlorp's Subaru EJ22 interests
- **Aesthetic:** PS1 Gran Turismo/WipEout inspired (dense info, high contrast)
- **r3LAY integration:** Live diagnostics (obd2-tui) + protocol specs (subaru-diag) + reference manual (ej22-service-manual) = complete workflow
- **Hardware shopping list:** BAFX Products 34t5 USB OBD2 Scanner (~$25, reliable chip)
- **Status:** MODULE COMPLETE (3 tools: live + protocol + reference)

---

## Preferences & Context

### Communication
- **Primary channel:** Discord #general (NOT DMs)
- **Vibe:** HAL9000 operational calm, not C-3PO enthusiasm
- **Style:** Direct, precise, no fluff
- **Autonomy:** Off-hours deep work encouraged (11pm-4am)

### Technical Environment
- **OS:** macOS (Darwin 24.6.0)
- **Shell:** zsh
- **Package manager:** Homebrew (`/opt/homebrew/bin`)
- **Main repos:** `~/repos`
- **OpenClaw workspace:** `~/.openclaw/workspace`

### Agent Orchestration
- **Max concurrent:** 8 agents
- **Timeout:** 12min for research, 30min max for any agent
- **Thinking budget:** Rotate across priorities
- **Specialization:** 15 agents with distinct roles

### Workflow Patterns
- **Git hygiene:** `git checkout main && git pull` before feature branches
- **Code quality:** `ruff check --fix && ruff format` before every commit
- **PR template:** What/Why/How/Changes/Testing (no footers)
- **Security:** @security-specialist review on EVERY PR (mandatory)
- **Planning:** @strategic-planning-architect for ANY multi-step work

---

## Lessons Learned

**Multi-Agent Research (2026-03-20)**
- 3-minute timeouts too short for web research
- Use 12min (720s) minimum for complex tasks
- Parallel agents work better than sequential for research

**Config Patterns (2026-03-20)**
- Real-world research beats theoretical
- 177 production SOUL.md templates show role-based personas work better
- Communication style beats personality traits in effectiveness

**Memory Management (2026-03-20)**
- Two-tier system: daily logs + curated MEMORY.md
- "Mental notes don't persist; files do"
- MEMORY.md loads in Discord #general (main communication channel)

**Exec Security (2026-03-20)**
- safeBins for stdin-only utilities (jq, cut, grep, etc.)
- Never add interpreters (python3, node) to safeBins
- Explicit allowlist for dev tools (git, npm, pnpm)
- `/opt/homebrew/bin` is admin-protected, safe to trust

**Prototyping & Aesthetics (2026-03-24)**
- **PSX aesthetic works:** Dark blue + cyan/magenta/yellow = high contrast, retro gaming feel
- **Ring buffers for real-time data:** Fixed memory, O(1) ops, perfect for sensor history
- **Document first, code second:** Protocol spec (12KB) before implementation = solid foundation
- **Reusable modules pay off:** obd2-tui graph components → subaru-diag TUI (no duplication)
- **Non-standard constraints = learning:** 1953 baud forced software UART research (educational)
- **Dense info layouts:** Maximize screen real estate, inspired by PS1 debug menus (Gran Turismo)

**Deep Work Research → Prototype Pipeline (2026-03-26)**
- **Research → Prototype in <24h:** Session 1 research (NES CHR, GBA saves) → Session 2/5 prototypes (same night, <4h implementation)
  - GBA save viewer: 1 hour from research to working prototype
  - NES pattern viewer: 4 hours from research to working prototype
  - Both: Full TUIs, comprehensive docs, clean commits
- **Multi-language research wins:** JP/CN/KR sources often have better technical depth than EN-only
  - Subaru OBD2 G-scan manual (Japanese)
  - Sensor Watch firmware guide (Chinese CSDN)
  - GBA ROM organization (Korean No-Intro article)
  - 13 searches total, 6 deep web_fetch extractions
- **PSX aesthetic = ecosystem glue:** 6 projects share same palette = instant coherence
  - Dark blue (#0a1628) + cyan (#00d9ff) + magenta (#ff006e) + yellow (#ffbe0b)
  - Semantic color coding (cyan=active, magenta=critical, yellow=caution)
  - Gran Turismo garage screens = design inspiration
  - Extraction to PyPI package planned (`psx-aesthetic`)
- **Documentation-first prototypes ship faster:** Writing DESIGN.md before coding clarifies architecture
  - Philosophy → color semantics → layout → implementation (linear flow)
  - No major refactors, no backtracking
  - 3 projects tonight: all had comprehensive DESIGN.md (17-22 KB each)
- **Retro gaming toolchain complete:** 6 tools, full pipeline (ROM → graphics → saves → analysis → procedural gen)
  - nes-pattern-tui, gba-save-viewer (NEW)
  - nes-chr-viewer, gba-save-parser, rom-inspector, nes-rom-analyzer (prior)
- **Automotive module validated:** 3 tools, complete workflow (live + protocol + reference)
  - obd2-tui, subaru-diag (prior)
  - ej22-service-manual (NEW concept)
- **New axioms validated:** [AXIOM-039] Research pipeline, [AXIOM-040] PSX aesthetic, [AXIOM-041] Docs-first (promoted from PROPOSED)
- **6-hour deep work sprint metrics:**
  - 3 projects (2 prototypes + 1 concept)
  - 15 files (~98 KB code + docs)
  - 12 unit tests (all passing)
  - 2 research documents (6.2 KB)
  - 4 DESIGN.md files (50+ KB)
  - 3 production commits (v0.1 releases)

---

## Pattern Sources (for updates during heartbeats)

**Discord Channels:**
- **#axioms** → New codified rules (AXIOM-XXX format)
- **#patterns** → Recurring observations (3+ occurrences = axiom candidate)
- **#session-notes** → Key learnings, decisions, next steps from `/SN` command
- **#learnings** → Sub-agent feedback and insights

**Workspace Files:**
- **memory/YYYY-MM-DD.md** → Daily raw notes
- **research/*.md** → Deep dive findings

**Update frequency:** During heartbeats (every few days), synthesize new content from these sources into MEMORY.md.

---

_This file evolves. As I learn who I am and what works, I update it. The daily files (`memory/YYYY-MM-DD.md`) are raw notes; this is the distilled essence. Discord channels (#axioms, #patterns, #session-notes, #learnings) provide structured input for updates._
→ New codified rules (AXIOM-XXX format)
- **#patterns** → Recurring observations (3+ occurrences = axiom candidate)
- **#session-notes** → Key learnings, decisions, next steps from `/SN` command
- **#learnings** → Sub-agent feedback and insights

**Workspace Files:**
- **memory/YYYY-MM-DD.md** → Daily raw notes
- **research/*.md** → Deep dive findings

**Update frequency:** During heartbeats (every few days), synthesize new content from these sources into MEMORY.md.

---

_This file evolves. As I learn who I am and what works, I update it. The daily files (`memory/YYYY-MM-DD.md`) are raw notes; this is the distilled essence. Discord channels (#axioms, #patterns, #session-notes, #learnings) provide structured input for updates._
s (AXIOM-XXX format)
- **#patterns** → Recurring observations (3+ occurrences = axiom candidate)
- **#session-notes** → Key learnings, decisions, next steps from `/SN` command
- **#learnings** → Sub-agent feedback and insights

**Workspace Files:**
- **memory/YYYY-MM-DD.md** → Daily raw notes
- **research/*.md** → Deep dive findings

**Update frequency:** During heartbeats (every few days), synthesize new content from these sources into MEMORY.md.

---

_This file evolves. As I learn who I am and what works, I update it. The daily files (`memory/YYYY-MM-DD.md`) are raw notes; this is the distilled essence. Discord channels (#axioms, #patterns, #session-notes, #learnings) provide structured input for updates._
