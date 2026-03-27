# OpenClaw tools.exec Configuration Guide

## Configuration Tiers

### Tier 1: Restricted (Maximum Security)
**Use case:** Production systems, shared environments, untrusted workloads

```json
{
  "tools": {
    "exec": {
      "host": "gateway",
      "security": "deny",
      "ask": "always"
    }
  }
}
```

**Behavior:**
- Blocks all exec by default
- Every command requires explicit approval
- No auto-allowed binaries

**Trade-offs:**
- ✅ Maximum security
- ❌ Requires constant manual approval
- ❌ Breaks autonomous workflows

---

### Tier 2: Balanced (Recommended for Development)
**Use case:** Personal development, trusted single-user setups, autonomous agents

```json
{
  "tools": {
    "exec": {
      "host": "gateway",
      "security": "allowlist",
      "ask": "off",
      "safeBins": [
        "jq",
        "cut",
        "uniq", 
        "head",
        "tail",
        "tr",
        "wc",
        "grep",
        "sort",
        "awk",
        "sed"
      ],
      "safeBinTrustedDirs": [
        "/bin",
        "/usr/bin"
      ],
      "safeBinProfiles": {
        "grep": {
          "minPositional": 0,
          "maxPositional": 0,
          "allowedValueFlags": ["-e", "--regexp", "-i", "-v", "-n"],
          "deniedFlags": ["-f", "--file", "-r", "-R"]
        },
        "sort": {
          "minPositional": 0,
          "maxPositional": 0,
          "allowedValueFlags": ["-n", "-r", "-u"],
          "deniedFlags": ["-o", "-T", "--compress-program"]
        },
        "awk": {
          "minPositional": 1,
          "maxPositional": 1,
          "deniedFlags": ["-f"]
        },
        "sed": {
          "minPositional": 1,
          "maxPositional": 1,
          "deniedFlags": ["-i", "-f"]
        }
      }
    }
  }
}
```

**Behavior:**
- Auto-allows safe text-processing utilities
- Requires explicit allowlist for development tools
- No approval prompts for known commands

**Trade-offs:**
- ✅ Good security baseline
- ✅ Low friction for common tasks
- ⚠️ Requires building allowlist for dev tools

---

### Tier 3: Permissive (Development Only)
**Use case:** Rapid prototyping, local-only development, debugging

```json
{
  "tools": {
    "exec": {
      "host": "gateway",
      "security": "full",
      "ask": "off"
    }
  }
}
```

**Behavior:**
- Allows all commands without restriction
- No approval prompts
- Maximum autonomy

**Trade-offs:**
- ✅ Zero friction
- ❌ No security guardrails
- ❌ Only safe for trusted single-user environments

---

## macOS Development: Common Allowlist Patterns

### Git Operations
```json
{
  "tools": {
    "exec": {
      "allowlist": [
        "/opt/homebrew/bin/git",
        "/usr/bin/git"
      ]
    }
  }
}
```

### Node/npm/pnpm Ecosystem
```json
{
  "allowlist": [
    "/opt/homebrew/bin/node",
    "/opt/homebrew/bin/npm",
    "/opt/homebrew/bin/pnpm",
    "/opt/homebrew/bin/npx"
  ]
}
```

### Modern CLI Tools
```json
{
  "allowlist": [
    "/opt/homebrew/bin/rg",
    "/opt/homebrew/bin/fd",
    "/opt/homebrew/bin/bat",
    "/opt/homebrew/bin/exa"
  ]
}
```

### System Utilities
```json
{
  "allowlist": [
    "/usr/bin/find",
    "/usr/bin/xargs",
    "/usr/bin/tar",
    "/usr/bin/gzip"
  ]
}
```

### Complete Development Setup
```json
{
  "tools": {
    "exec": {
      "allowlist": [
        "/opt/homebrew/bin/git",
        "/opt/homebrew/bin/node",
        "/opt/homebrew/bin/npm",
        "/opt/homebrew/bin/pnpm",
        "/opt/homebrew/bin/rg",
        "/opt/homebrew/bin/fd",
        "/usr/bin/find",
        "/usr/bin/tar"
      ]
    }
  }
}
```

---

## Recommended Config for Autonomous Operation

**Context:** Single-user macOS development environment, autonomous agent

```json
{
  "tools": {
    "exec": {
      "host": "gateway",
      "security": "allowlist",
      "ask": "off",
      "safeBins": [
        "jq",
        "cut",
        "uniq",
        "head",
        "tail",
        "tr",
        "wc",
        "grep",
        "sort"
      ],
      "safeBinTrustedDirs": [
        "/bin",
        "/usr/bin"
      ],
      "safeBinProfiles": {
        "grep": {
          "minPositional": 0,
          "maxPositional": 0,
          "allowedValueFlags": ["-e", "--regexp", "-i", "-v", "-n"],
          "deniedFlags": ["-f", "--file", "-r", "-R"]
        },
        "sort": {
          "minPositional": 0,
          "maxPositional": 0,
          "deniedFlags": ["-o", "-T"]
        }
      },
      "allowlist": [
        "/opt/homebrew/bin/git",
        "/opt/homebrew/bin/npm",
        "/opt/homebrew/bin/pnpm",
        "/opt/homebrew/bin/node",
        "/opt/homebrew/bin/rg",
        "/opt/homebrew/bin/fd",
        "/usr/bin/find"
      ]
    }
  }
}
```

**Why this works:**
- ✅ Safe text utilities auto-allowed (jq, grep, etc.)
- ✅ Development tools explicitly trusted
- ✅ No approval friction for routine operations
- ✅ System binaries use trusted paths only
- ✅ Homebrew tools explicitly allowlisted (not auto-trusted)

---

## Security Considerations

### ⚠️ Never Add to safeBins
- Interpreters: `python3`, `node`, `ruby`, `bash`, `zsh`
- Package managers: `npm`, `pip`, `gem`
- Network tools: `curl`, `wget`, `git`

**Why?** These can execute arbitrary code. Use explicit allowlist instead.

### ⚠️ Avoid Broad Patterns
```json
// ❌ DANGEROUS
"~/Projects/**/bin/*"

// ✅ SAFE
"/Users/lorp/Projects/my-tool/bin/specific-binary"
```

### ⚠️ User-Writable Directories
```json
// ❌ DANGEROUS (user can replace binaries)
"safeBinTrustedDirs": ["/opt/homebrew/bin"]

// ✅ SAFE (system-protected)
"safeBinTrustedDirs": ["/bin", "/usr/bin"]
```

---

## Migration Path

### Step 1: Start Restrictive
```json
{
  "tools": {
    "exec": {
      "security": "allowlist",
      "ask": "on-miss",
      "allowlist": []
    }
  }
}
```

### Step 2: Build Allowlist Through Usage
When you hit approval prompts:
```
/approve <id> allow-always
```

This automatically adds to allowlist.

### Step 3: Graduate to Autonomous
After 1 week of stable operation:
```json
{
  "tools": {
    "exec": {
      "ask": "off"
    }
  }
}
```

---

## Quick Reference

| Tier | Security | Ask | Use Case |
|------|----------|-----|----------|
| Restricted | deny | always | Production, shared |
| Balanced | allowlist | off | Development, autonomous |
| Permissive | full | off | Local prototyping only |

**Recommended:** Start with Tier 2 (Balanced) for autonomous development work.
