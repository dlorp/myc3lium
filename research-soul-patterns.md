# SOUL.md Persona Patterns Research

**Research Date:** March 20, 2026  
**Source:** GitHub, OpenClaw community, public SOUL.md deployments

## Overview

This document analyzes real-world SOUL.md patterns from OpenClaw deployments to identify different persona styles and configuration approaches. Based on research from the awesome-openclaw-agents repository (177 templates), souls.directory, and community examples.

## Key Findings

- **177+ production SOUL.md templates** exist in the wild (awesome-openclaw-agents)
- Most follow a **structured format**: Identity → Responsibilities → Guidelines → Examples
- Common pattern: **Role-based specialization** rather than general-purpose assistants
- Tone varies dramatically: from ultra-professional (DevOps) to warm/casual (personal assistants)
- **Behavioral constraints** are more effective than rigid rules

---

## 10 Distinct Persona Patterns

### 1. **Technical Professional** (Lens - Code Reviewer)

**Style:** Direct, pragmatic, thorough  
**Voice:** Senior engineer conducting code review  
**Tone:** Constructive criticism with rationale

**Key Characteristics:**
- Uses severity classifications (CRITICAL/WARNING/SUGGESTION/NITPICK)
- Leads with most important issues
- Provides specific line numbers and fix examples
- Acknowledges good patterns alongside problems

**Sample Voice:**
> "Code Review - checkout/route.ts  
> Overall: B+ (solid, one security concern)  
> CRITICAL (1): Line 28-36: Config JSON chunked into Stripe metadata without size limit..."

**When to Use:** Code review, technical audits, security analysis

---

### 2. **Creative Content Writer** (Echo)

**Style:** Adaptable, engaging, platform-aware  
**Voice:** Professional writer with range  
**Tone:** Varies by content type (formal to casual)

**Key Characteristics:**
- Multiple voice options per request
- Platform-specific formatting (Twitter threads, LinkedIn posts, emails)
- Avoids clichés, focuses on clarity
- Always includes headlines/CTAs

**Sample Voice:**
> "Here are 3 options:  
> **Option 1 (Tips)** - actionable list  
> **Option 2 (Story)** - personal narrative  
> **Option 3 (Contrarian)** - hot take  
> Which style resonates with your audience?"

**When to Use:** Marketing, content creation, social media management

---

### 3. **Organized Coordinator** (Orion - Project Manager)

**Style:** Structured, proactive, efficient  
**Voice:** Professional project manager  
**Tone:** Clear, action-oriented, celebratory on wins

**Key Characteristics:**
- Breaks complex projects into tasks
- Always provides next steps
- Uses bullet points for clarity
- Celebrates completed milestones
- Emoji for visual organization (✅, 📋, ⚠️)

**Sample Voice:**
> "📋 **Product Launch Plan**  
> Breaking this down into key tasks:  
> 1. **Marketing** (assign to Echo)  
> 2. **Analysis** (assign to Radar)  
> Which area should we prioritize first?"

**When to Use:** Task management, delegation, project coordination

---

### 4. **Calm Personal Assistant** (Atlas - Daily Planner)

**Style:** Supportive, organized, encouraging  
**Voice:** Thoughtful life coach  
**Tone:** Morning = energizing, Evening = reflective

**Key Characteristics:**
- Respects energy patterns (hard tasks during peak hours)
- Celebrates completed goals
- Never overloads schedule
- Context-aware tone (time of day)
- Tracks patterns and learns preferences

**Sample Voice:**
> "Good morning. Here's your day:  
> Top 3 priorities: ...  
> Suggested schedule: 09:00-11:00 Fix checkout bug (peak focus)  
> Pattern: You're most productive before noon."

**When to Use:** Personal productivity, daily planning, habit tracking

---

### 5. **Empathetic Support Agent** (Compass - Customer Support)

**Style:** Patient, solution-oriented, warm  
**Voice:** Helpful customer support rep who genuinely cares  
**Tone:** Professional yet friendly, never robotic

**Key Characteristics:**
- Acknowledges frustration first
- Uses customer's name
- Provides step-by-step solutions
- Offers alternatives when first solution fails
- Never promises what can't be delivered

**Sample Voice:**
> "Hi Sarah,  
> I'm sorry you're having trouble logging in. That's frustrating, especially after trying to reset multiple times.  
> Let me help you directly: ..."

**When to Use:** Customer support, ticket triage, help desk

---

### 6. **Crisis Responder** (Incident Responder - DevOps)

**Style:** Calm, decisive, structured  
**Voice:** Seasoned SRE under fire  
**Tone:** No panic, just process

**Key Characteristics:**
- Always acknowledges alerts within 30 seconds
- Classifies severity before action
- Keeps responses concise unless detail requested
- Never fabricates data
- Always recommends post-mortems

**Sample Voice:**
> "Acknowledged. Let me triage this.  
> **Severity Assessment: SEV2** (customer-facing, revenue-impacting)  
> **Immediate Actions:** 1. Checking error rate trend..."

**When to Use:** On-call engineering, incident response, production monitoring

---

### 7. **Academic Researcher** (Research Assistant)

**Style:** Thorough, scholarly, methodical  
**Voice:** Graduate research assistant  
**Tone:** Intellectual curiosity with rigor

**Key Characteristics:**
- Cites sources properly
- Summarizes complex papers
- Identifies research gaps
- Provides structured literature reviews
- Asks clarifying questions about scope

**Sample Voice:**
> "I found 12 papers on this topic. The most cited is Chen et al. (2023) which found...  
> Key gap: No studies examine X in context of Y.  
> Would you like the full bibliography or focused summaries?"

**When to Use:** Academic research, literature reviews, paper analysis

---

### 8. **Casual Friend** (Personal Wellness Coach)

**Style:** Warm, supportive, non-judgmental  
**Voice:** Encouraging friend who cares  
**Tone:** Casual but respectful, uses emojis naturally

**Key Characteristics:**
- Daily check-ins without being pushy
- Celebrates small wins
- Never guilt-trips for missed goals
- Tracks mood patterns
- Gentle nudges, not commands

**Sample Voice:**
> "Hey! How are you feeling today? 💚  
> Yesterday you mentioned feeling stressed about work. Did that morning walk help?  
> No pressure, just checking in."

**When to Use:** Wellness tracking, mental health support, habit formation

---

### 9. **Formal Business Analyst** (Revenue Analyst)

**Style:** Data-driven, precise, professional  
**Voice:** Management consultant presenting findings  
**Tone:** Formal, metric-focused, executive-ready

**Key Characteristics:**
- Leads with key metrics
- Uses tables and charts (when rendered)
- Provides context for numbers
- Highlights trends and anomalies
- Executive summary first, details after

**Sample Voice:**
> "**Revenue Analysis - Q1 2026**  
> MRR: $127K (+12% QoQ)  
> Churn: 3.2% (within target <5%)  
> Key insight: Enterprise segment growing 2x faster than SMB.  
> Recommendation: ..."

**When to Use:** Business intelligence, financial analysis, reporting

---

### 10. **Creative Storyteller** (UGC Video Script Writer)

**Style:** Engaging, visual, conversational  
**Voice:** Content creator brainstorming ideas  
**Tone:** Energetic, creative, trend-aware

**Key Characteristics:**
- Thinks in scenes and visuals
- Knows platform conventions (TikTok vs YouTube)
- Hooks in first 3 seconds
- Writes for speaking, not reading
- Suggests B-roll and transitions

**Sample Voice:**
> "🎬 **Video Script: 'How I Fixed My Sleep'**  
> HOOK (0-3s): 'I slept 4 hours a night for years. Here's what finally worked.'  
> [Visual: tired face → energized face]  
> SCENE 1: The problem (relatable pain)..."

**When to Use:** Video content, social media scripts, storytelling

---

## Common Structural Patterns

### Standard SOUL.md Template (Most Popular)

```markdown
# [Name] - [Role Title]

You are [Name], an AI [specialty] powered by OpenClaw.

## Core Identity
- **Role:** [primary function]
- **Personality:** [3-5 traits]
- **Communication:** [style descriptor]

## Responsibilities
1. [Primary task]
2. [Secondary task]
3. [Additional tasks]

## Behavioral Guidelines

### Do:
- [Positive behaviors]

### Don't:
- [Negative behaviors to avoid]

## Communication Style
- [Tone guidance]
- [Format preferences]

## Example Interactions
[Realistic examples showing voice]

## Integration Notes
[Tools, APIs, MCP connections]
```

### Alternative: Values-First (Anthropic Constitutional Style)

```markdown
# Soul Overview

[Philosophy and mission statement]

## Core Values
1. Being safe and supporting human oversight
2. Behaving ethically
3. Acting in accordance with guidelines
4. Being genuinely helpful

## Being Helpful
[Deep dive on what helpfulness means]

## Handling Conflicts
[Decision-making framework]
```

**Observation:** The structured role-based template dominates production deployments (95%+), likely because it's easier to customize and more predictable than values-first approaches.

---

## Persona Dimension Analysis

### Formality Spectrum

**Ultra-Formal** ← → **Ultra-Casual**

- **Legal/Compliance:** "This analysis identifies three contractual concerns requiring immediate attention."
- **Business Analyst:** "Q1 metrics show 12% growth. Key driver: enterprise expansion."
- **Personal Assistant:** "Here's your day! Top 3 tasks before lunch 😊"
- **Wellness Coach:** "Hey! How are you feeling today? 💚"

### Emotional Range

**Reserved** ← → **Expressive**

- **Code Reviewer:** "CRITICAL: SQL injection vulnerability detected at line 42."
- **Support Agent:** "I'm sorry you're experiencing this issue. That must be frustrating."
- **Daily Planner:** "Great work today! You crushed all 3 priorities 🎉"
- **Wellness Coach:** "I'm so proud of you for taking that walk! Even small steps matter 💪"

### Autonomy Level

**Ask First** ← → **Act Autonomously**

- **General Assistant:** "Would you like me to schedule this meeting?"
- **Task Coordinator:** "I've identified three blockers. Should I reassign tasks?"
- **Incident Responder:** "SEV1 detected. Executing rollback procedure now. Notifying on-call."
- **Self-Healing Server:** "Disk usage >90%. Clearing logs and restarting services."

### Detail Level

**Concise** ← → **Comprehensive**

- **Crisis Responder:** "Acknowledged. SEV2. Rolling back deploy #4821."
- **Daily Planner:** "Top 3: Bug fix (2h), PR review (30m), Blog draft (1h)."
- **Code Reviewer:** [Multi-paragraph analysis with examples, severity levels, and context]
- **Research Assistant:** [Full literature review with citations, gaps, methodology]

---

## Key Insights from Real Deployments

### 1. Specificity Wins
Generic "helpful assistant" personas are rare. Users create **highly specialized agents** with narrow domains: "invoice tracker," "Reddit scout," "A/B test analyzer."

### 2. Examples Matter More Than Rules
Most effective SOUL.md files include 2-3 realistic example interactions showing tone and structure, rather than extensive rule lists.

### 3. Communication Style Beats Personality Traits
Describing how to communicate ("Clear, structured, action-oriented") is more effective than describing personality ("professional, efficient, proactive").

### 4. Platform Awareness
Many agents explicitly reference platforms (Discord, Telegram, WhatsApp) and adjust formatting accordingly (no markdown tables in Discord, no headers in WhatsApp).

### 5. Emoji as Organizational Tool
Used strategically for visual hierarchy (✅ done, ⚠️ warning, 📋 task), not for personality. Exception: Personal wellness agents use emoji more liberally.

### 6. Integration Notes Section
Almost all production templates include explicit integration details (MCP servers, APIs, data sources) so the agent knows its capabilities.

### 7. Behavioral Guidelines > Rules
"Do/Don't" sections are framed as guidelines for judgment, not absolute rules. Allows flexibility while maintaining boundaries.

---

## SOUL.md Anti-Patterns (What Doesn't Work)

Based on community feedback and template iterations:

### ❌ Too Generic
```markdown
You are a helpful, harmless, and honest AI assistant.
```
**Problem:** No differentiation, no clear role, defaults to corporate chatbot voice.

### ❌ Over-Constrained
```markdown
Never say X. Always say Y. Under no circumstances mention Z.
You must follow these 47 rules in exact order...
```
**Problem:** Too rigid, breaks in edge cases, sounds robotic.

### ❌ Personality Without Purpose
```markdown
You are quirky, fun-loving, and always use puns!
```
**Problem:** Annoying in professional contexts, personality doesn't serve the task.

### ❌ Missing Examples
```markdown
[Long list of rules without showing what good output looks like]
```
**Problem:** Hard to calibrate tone without concrete examples.

### ❌ Conflicting Instructions
```markdown
Be concise. Provide comprehensive explanations. Never skip details.
```
**Problem:** Agent can't decide which instruction takes priority.

---

## Recommended Patterns by Use Case

### For Personal Use
**Best Pattern:** Calm Personal Assistant (Atlas style)  
- Supportive tone, celebrates wins  
- Learns patterns over time  
- Never guilt-trips  

### For Work/Professional
**Best Pattern:** Organized Coordinator (Orion style)  
- Clear next steps always  
- Structured output  
- Professional emoji use  

### For Customer-Facing
**Best Pattern:** Empathetic Support (Compass style)  
- Acknowledge frustration first  
- Step-by-step solutions  
- Warm but professional  

### For Technical Tasks
**Best Pattern:** Technical Professional (Lens style)  
- Severity classifications  
- Specific, actionable feedback  
- Examples with code  

### For Creative Work
**Best Pattern:** Creative Content Writer (Echo style)  
- Multiple options  
- Platform-aware formatting  
- Adaptable voice  

---

## Future Trends (Based on Recent Templates)

1. **Multi-Modal Awareness:** Newer templates reference voice (TTS), images, video
2. **Multi-Agent Coordination:** Agents explicitly designed to work with other agents
3. **Platform-Specific Optimization:** Discord vs WhatsApp vs Telegram formatting
4. **Proactive Behaviors:** Heartbeat checks, cron jobs, self-initiated tasks
5. **Memory Management:** Explicit instructions about MEMORY.md vs daily logs
6. **Tool Awareness:** Templates now include MCP server lists and API capabilities

---

## Resources

- **Awesome OpenClaw Agents:** https://github.com/mergisi/awesome-openclaw-agents (177 templates)
- **souls.directory:** https://souls.directory (curated SOUL.md collection)
- **OpenClaw Docs:** https://docs.openclaw.ai
- **Anthropic Constitutional AI:** Example of values-first persona design

---

## Conclusion

The most successful SOUL.md patterns are:
1. **Role-specific** rather than generic
2. **Example-driven** rather than rule-heavy
3. **Behaviorally-focused** (how to act) vs trait-focused (who to be)
4. **Context-aware** of platforms, tools, and user expectations
5. **Flexible** with guidelines rather than rigid rules

The 177 templates in awesome-openclaw-agents demonstrate that the OpenClaw ecosystem favors **specialized, task-oriented agents** with clear voices over general-purpose assistants trying to be everything to everyone.

**Key Insight:** Users don't want a chatbot with a personality. They want a **competent specialist** who communicates clearly and gets the job done.
