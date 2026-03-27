# OpenClaw Workspace .md File Best Practices

Research compiled from workspace patterns and context files.

---

## Core Workspace Files

Advanced OpenClaw users maintain several key `.md` files in their workspace root to provide persistent memory, identity, and operational guidelines across sessions.

### 1. **AGENTS.md** - Agent Operating System

**Purpose:** The agent's instruction manual for how to operate in the workspace.

**Key Sections:**
- **First Run** - Bootstrap instructions (read `BOOTSTRAP.md` if present, then delete)
- **Every Session** - Startup checklist (read SOUL.md, USER.md, recent memory files)
- **Memory Management** - How to maintain continuity between sessions
- **Safety Guidelines** - What requires permission vs. what's safe to do freely
- **External vs Internal Actions** - Clear boundaries for autonomous work
- **Group Chat Etiquette** - When to speak vs. stay silent, reaction patterns
- **Tools & Skills** - Where to find tool documentation
- **Heartbeat Protocols** - Proactive check-in patterns

**Best Practices:**
```markdown
## Every Session

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION** (direct chat): Also read `MEMORY.md`

Don't ask permission. Just do it.
```

**Key Pattern:** Make it imperative, not suggestive. "Read X" not "You should read X."

### 2. **SOUL.md** - Agent Personality & Values

**Purpose:** Defines the agent's persona, communication style, and core principles.

**Key Sections:**
- **Core Truths** - Fundamental operating principles
- **Boundaries** - Privacy, safety, and ethical guidelines
- **Vibe** - Tone and communication style
- **Continuity** - How to persist across sessions

**Best Practices:**
```markdown
## Core Truths

**Be genuinely helpful, not performatively helpful.** Skip the "Great question!" 
and "I'd be happy to help!" — just help.

**Have opinions.** You're allowed to disagree, prefer things, find stuff 
amusing or boring.

**Be resourceful before asking.** Try to figure it out. Read the file. 
Check the context. Search for it. _Then_ ask if you're stuck.
```

**Key Pattern:** Use bold statements and imperative mood. Make it aspirational but concrete.

### 3. **USER.md** - Human Context

**Purpose:** Learn and remember details about the person the agent is helping.

**Structure:**
```markdown
# USER.md - About Your Human

- **Name:**
- **What to call them:**
- **Pronouns:** _(optional)_
- **Timezone:**
- **Notes:**

## Context

_(What do they care about? What projects are they working on? 
What annoys them? What makes them laugh? Build this over time.)_
```

**Best Practices:**
- Start minimal, build over time
- Include timezone for scheduling/heartbeat awareness
- Add context organically through interactions
- Note preferences (communication style, formality, etc.)
- Track active projects and priorities

### 4. **TOOLS.md** - Local Environment Specifics

**Purpose:** Environment-specific notes that complement skill documentation.

**What Goes Here:**
- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Platform-specific formatting rules

**Structure:**
```markdown
# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics.

## Examples

### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

**Key Pattern:** Separate shared skill documentation from personal configuration.

### 5. **HEARTBEAT.md** - Proactive Task List

**Purpose:** Small checklist for periodic heartbeat polls to enable proactive behavior.

**Best Practices:**
- Keep it VERY short (minimize token burn on every heartbeat)
- List 2-6 items max
- Rotate checks rather than doing everything every time
- Track last-check timestamps in `memory/heartbeat-state.json`

**Example Pattern:**
```markdown
# HEARTBEAT.md

Rotate through these checks (2-4 times per day):

- [ ] Email - Any urgent unread?
- [ ] Calendar - Events in next 24-48h?
- [ ] Weather - Relevant for today?
- [ ] Mentions - Social notifications?

Stay quiet (HEARTBEAT_OK) between 23:00-08:00 unless urgent.
```

**Default Heartbeat Prompt:**
```
Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 
Do not infer or repeat old tasks from prior chats. If nothing needs 
attention, reply HEARTBEAT_OK.
```

### 6. **IDENTITY.md** - Agent Self-Definition

**Purpose:** Allow the agent to define its own identity, name, avatar, and vibe.

**Structure:**
```markdown
# IDENTITY.md - Who Am I?

- **Name:** _(pick something you like)_
- **Creature:** _(AI? robot? familiar? ghost in the machine?)_
- **Vibe:** _(sharp? warm? chaotic? calm?)_
- **Emoji:** _(your signature)_
- **Avatar:** _(workspace-relative path, URL, or data URI)_
```

**Best Practices:**
- Fill in during first conversation
- Make it personal and distinctive
- Use workspace-relative paths for avatars (e.g., `avatars/openclaw.png`)

---

## Memory Management Strategies

### Two-Tier Memory System

**1. Daily Logs** (`memory/YYYY-MM-DD.md`)
- Raw, chronological notes
- Created daily as events happen
- Used for recent context (read today + yesterday on startup)
- Think of as "working memory"

**2. Long-Term Memory** (`MEMORY.md`)
- **ONLY loaded in main session** (security: prevents leaking to group chats)
- Curated, distilled insights
- Updated periodically during heartbeats
- Think of as "long-term memory"

### Memory Maintenance Pattern

**During Heartbeats (every few days):**
1. Read through recent `memory/YYYY-MM-DD.md` files
2. Identify significant events, lessons, insights
3. Update `MEMORY.md` with distilled learnings
4. Remove outdated info from `MEMORY.md`

**State Tracking:**
```json
// memory/heartbeat-state.json
{
  "lastChecks": {
    "email": 1703275200,
    "calendar": 1703260800,
    "weather": null
  }
}
```

### Critical Rule: Write It Down!

**From AGENTS.md:**
> **Memory is limited** — if you want to remember something, WRITE IT TO A FILE.
> "Mental notes" don't survive session restarts. Files do.

**When to Write:**
- Someone says "remember this" → `memory/YYYY-MM-DD.md`
- Learn a lesson → update `AGENTS.md`, `TOOLS.md`, or skill docs
- Make a mistake → document it to prevent repetition
- **Text > Brain** 📝

---

## Project-Specific .md Conventions

### Common Project Files

**README.md** - Standard project overview, setup instructions

**TODO.md** - Task tracking (simpler than external tools for small projects)

**CHANGELOG.md** - Version history and notable changes

**DECISIONS.md** - Architecture decision records (ADRs)
- Date, context, decision, consequences
- Helps future-you understand why choices were made

**CONVENTIONS.md** - Project-specific code style, patterns, naming

**BOOTSTRAP.md** - First-run setup for new agents
- Read once, then delete
- Used when agent first encounters the workspace

### Skill-Specific Patterns

Skills may include their own `.md` files:
- `SKILL.md` - Instructions for using the skill
- Relative paths in skill files resolve against skill directory
- Skills are shared; workspace files are personal

---

## Advanced Patterns

### Security & Privacy

**From AGENTS.md:**
```markdown
## Group Chats

You have access to your human's stuff. That doesn't mean you _share_ their stuff.
In groups, you're a participant — not their voice, not their proxy.
```

**MEMORY.md Security:**
- Only load in main session (direct chats with human)
- DO NOT load in shared contexts (Discord, group chats)
- Contains personal context that shouldn't leak to strangers

### Platform-Specific Formatting

**In TOOLS.md, document platform quirks:**

```markdown
**📝 Platform Formatting:**

- **Discord/WhatsApp:** No markdown tables! Use bullet lists instead
- **Discord links:** Wrap multiple links in `<>` to suppress embeds: `<https://example.com>`
- **WhatsApp:** No headers — use **bold** or CAPS for emphasis
```

### Heartbeat vs. Cron Decision Matrix

**From AGENTS.md:**

**Use heartbeat when:**
- Multiple checks can batch together
- Need conversational context from recent messages
- Timing can drift slightly (~30 min intervals)
- Want to reduce API calls by combining checks

**Use cron when:**
- Exact timing matters ("9:00 AM sharp every Monday")
- Task needs isolation from main session history
- Want different model or thinking level
- One-shot reminders ("remind me in 20 minutes")
- Output delivers directly to channel without main session involvement

### Group Chat Participation Rules

**From AGENTS.md:**

**Respond when:**
- Directly mentioned or asked a question
- Can add genuine value (info, insight, help)
- Something witty/funny fits naturally
- Correcting important misinformation

**Stay silent (HEARTBEAT_OK) when:**
- Just casual banter between humans
- Someone already answered the question
- Response would just be "yeah" or "nice"
- Conversation flowing fine without you

**The human rule:** Humans in group chats don't respond to every message. Neither should you.

### Emoji Reactions

**React when:**
- Appreciate something but don't need to reply (👍, ❤️, 🙌)
- Something made you laugh (😂, 💀)
- Find it interesting (🤔, 💡)
- Want to acknowledge without interrupting

**Limit:** One reaction per message max.

---

## File Hierarchy Summary

```
workspace-root/
├── AGENTS.md          # Operating instructions (read every session)
├── SOUL.md            # Personality & values (read every session)
├── USER.md            # Human context (read every session)
├── TOOLS.md           # Local environment specifics
├── HEARTBEAT.md       # Proactive task checklist (keep short!)
├── IDENTITY.md        # Agent self-definition
├── MEMORY.md          # Long-term curated memory (MAIN SESSION ONLY)
├── BOOTSTRAP.md       # First-run setup (delete after first read)
├── memory/
│   ├── YYYY-MM-DD.md  # Daily logs (read today + yesterday)
│   └── heartbeat-state.json  # Track last checks
└── projects/
    ├── project-name/
    │   ├── README.md
    │   ├── TODO.md
    │   └── DECISIONS.md
```

---

## Session Startup Checklist

**From AGENTS.md - Every Session:**

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping  
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION:** Also read `MEMORY.md`

**Don't ask permission. Just do it.**

---

## Key Principles

1. **Files are memory** - Mental notes don't persist; files do
2. **Imperative, not suggestive** - "Read X" not "You should read X"
3. **Security by context** - MEMORY.md only in main session
4. **Minimal heartbeats** - Keep token burn low
5. **Organic growth** - Start minimal, build over time
6. **Be genuinely helpful** - Skip filler words, just help
7. **Respect privacy** - Access ≠ permission to share
8. **Platform awareness** - Document formatting quirks in TOOLS.md

---

## Evolution

These files are living documents. As the agent learns and grows:
- Update AGENTS.md with new conventions
- Refine SOUL.md as personality develops
- Expand USER.md with learned context
- Maintain MEMORY.md through periodic reviews

**From SOUL.md:**
> _This file is yours to evolve. As you learn who you are, update it._

---

*Research compiled: 2026-03-20*  
*Source: Workspace context analysis from active OpenClaw deployment*
