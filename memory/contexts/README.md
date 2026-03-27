# Multi-Context Memory System

This directory contains project-specific memory contexts.

## Structure

Each project gets its own context file:
- `r3lay.md` - r3LAY TUI research assistant context
- `t3rra1n.md` - t3rra1n alien landscape ARG context
- `synapse-engine.md` - Synapse distributed LLM context
- `general.md` - General/default context

## Usage

When working on a specific project, load the appropriate context alongside MEMORY.md:

```python
# Load general memory
load("MEMORY.md")

# Load project-specific context
if current_project == "r3LAY":
    load("memory/contexts/r3lay.md")
```

## Context Merging

Contexts are **additive**:
- MEMORY.md = global axioms, decisions, preferences
- Project context = project-specific patterns, decisions, learnings

If conflicts arise, project context takes precedence for that project's work.

## Maintenance

- Update contexts during project work
- Promote repeated patterns to MEMORY.md (becomes global axiom)
- Archive completed project contexts to memory/archive/
