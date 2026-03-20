# Skills Library

Shared utilities for OpenClaw skills.

## inline-exec.js

Execute inline commands in SKILL.md files.

**Pattern:**
```markdown
Current time: !`date`
Git status: !`git status --short`
```

**Becomes:**
```markdown
Current time: Wed Mar 18 15:30:00 AKDT 2026
Git status: ?? myfile.txt
```

**Usage in skills:**

When reading a SKILL.md that contains `!`command`` patterns, extract and execute them before processing the skill.

**Example:**
```javascript
const { expandInlineCommands } = require('./lib/inline-exec')

// Read skill
const skillContent = fs.readFileSync('SKILL.md', 'utf8')

// Expand commands
const expanded = await expandInlineCommands(skillContent, async (cmd) => {
  // Execute using OpenClaw exec tool
  const result = await exec({ command: cmd })
  return result.stdout || ''
})

// Now use expanded content
```

**Security:**
- Commands run with same approval policy as regular exec
- Failed commands show `[ERROR: ...]` instead of breaking
- All commands execute in parallel for speed
