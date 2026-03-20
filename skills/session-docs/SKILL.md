# Session Documentation Skill

Generate comprehensive session handoff documentation with live git/workspace state.

## Live Session Context

**Current Time:**
!`date "+%Y-%m-%d %H:%M %Z"`

**Git Status:**
!`git status --short`

**Current Branch:**
!`git branch --show-current`

**Recent Commits (last 24h):**
!`git log --oneline --since="24 hours ago" --all`

**Uncommitted Changes:**
!`git diff --stat`

**Untracked Files:**
!`git ls-files --others --exclude-standard | head -20`

**Recent File Changes:**
!`find . -name "*.md" -o -name "*.txt" -mtime -1 -type f 2>/dev/null | grep -v node_modules | head -20`

**Active Branches:**
!`git branch --sort=-committerdate | head -10`

**Stashes:**
!`git stash list`

## Documentation Template

Create a session handoff document covering:

### 1. Session Overview
- Date/time
- Main objectives
- Work completed
- Blockers/issues encountered

### 2. Git State
- Current branch
- Commits made
- Pending changes
- Merge conflicts (if any)

### 3. Open Tasks
- In-progress work
- Next steps
- Decisions needed
- Outstanding questions

### 4. Files Modified
- New files created
- Files edited
- Files deleted
- Important changes to note

### 5. Context for Next Session
- Where to pick up
- Important commands/state
- Things to remember
- Gotchas/traps

### 6. External State
- PRs opened/merged
- Issues created/closed
- Slack/Discord conversations
- Calendar events

## Output Format

Save to: `memory/session-handoff-YYYY-MM-DD-HHMM.md`

Use clear headings, bullet points, and code blocks. Be concise but thorough.

## Usage

Invoke this skill at the end of a work session or when handing off to another agent/human.

**Example:**
```
Create a session handoff document for the work I just did on PR #33
```

The skill will use the live context above to generate a comprehensive summary.

## Post-Generation Actions

After creating the handoff document:

1. **Save to memory:**
   ```bash
   # File is already at memory/session-handoff-YYYY-MM-DD-HHMM.md
   ```

2. **Commit it (optional):**
   ```bash
   git add memory/session-handoff-*.md
   git commit -m "docs: session handoff $(date +%Y-%m-%d)"
   ```

3. **Link to previous handoff:**
   Add reference to last handoff at top of new doc

4. **Update MEMORY.md:**
   Add significant learnings to long-term memory
