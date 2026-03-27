# Exec Tool Research & Configuration

## Documentation Summary

### Core Security Model
- **Three-tier security**: deny (block all) | allowlist (explicit trust) | full (allow all)
- **Three-tier prompting**: off (no prompts) | on-miss (prompt for new) | always (prompt every time)
- **Host execution targets**: sandbox | gateway | node
- **Default behavior**: sandbox mode (but sandboxing OFF by default - fails closed if requested)

### Safe Bins (stdin-only utilities)
- **Purpose**: Auto-allow narrow stream filters without explicit allowlist
- **Default safe bins**: `jq`, `cut`, `uniq`, `head`, `tail`, `tr`, `wc`
- **NOT included by default**: `grep`, `sort` (require opt-in)
- **Restrictions**:
  - Must resolve from trusted directories only
  - Default trusted: `/bin`, `/usr/bin`
  - PATH entries never auto-trusted
  - Rejects positional file args
  - Forces literal argv (no globbing/expansion)
  - Validates flags fail-closed

**CRITICAL: Never add interpreters (python3, node, ruby, bash) to safeBins**

### Denied Flags (fail-closed validation)
- `grep`: `-f`, `--file`, `-r`, `-R`, `--recursive`, etc.
- `jq`: `-f`, `--from-file`, `-L`, `--library-path`, etc.
- `sort`: `-o`, `--output`, `--compress-program`, etc.
- `wc`: `--files0-from`

### Trust Model
- Gateway-authenticated = trusted operator
- Approvals reduce **accidental** execution, not a per-user auth boundary
- Single-user deployment: one trust boundary per gateway
- Approval binds: canonical cwd, exact argv, env, executable path
- Best-effort file binding for scripts

### Allowlist Patterns
- Per-agent allowlists
- Case-insensitive glob matching
- Must resolve to binary paths
- Examples:
  - `~/Projects/**/bin/rg`
  - `~/.local/bin/*`
  - `/opt/homebrew/bin/*`

### Security Guardrails
1. Rejects `env.PATH` overrides for host execution
2. Rejects loader overrides (`LD_*`, `DYLD_*`)
3. Shell chaining (`&&`, `||`, `;`) only when all segments satisfy allowlist
4. Command substitution (`$()`, backticks) rejected in allowlist mode
5. Redirections unsupported in allowlist mode

## Threat Analysis

### Primary Risks
1. **Command injection** via unvalidated user input in exec calls
2. **Path traversal** if allowlist patterns too broad
3. **Privilege escalation** via interpreter abuse (if added to safeBins)
4. **Data exfiltration** via unrestricted network/file access
5. **Supply chain** attacks via compromised binaries in trusted paths

### Mitigations
- Strict safeBins policy (no interpreters)
- Explicit allowlist for development tools
- Trusted directory enforcement for safeBins
- Fail-closed validation for flags
- Canonical path binding for approvals

## Recommended Configuration

### For Autonomous Operation (ask: "off")
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
        "/usr/bin",
        "/opt/homebrew/bin",
        "/usr/local/bin"
      ],
      "safeBinProfiles": {
        "grep": {
          "minPositional": 1,
          "maxPositional": 1,
          "allowedValueFlags": ["-e", "--regexp", "-i", "--ignore-case", "-v", "--invert-match", "-n", "--line-number"],
          "deniedFlags": ["-f", "--file", "-r", "-R", "--recursive"]
        },
        "sort": {
          "minPositional": 0,
          "maxPositional": 0,
          "allowedValueFlags": ["-n", "--numeric-sort", "-r", "--reverse", "-u", "--unique"],
          "deniedFlags": ["-o", "--output", "--compress-program", "--files0-from"]
        }
      }
    }
  }
}
```

### Rationale
- **host: gateway**: Runs on actual macOS host (sandboxing disabled by default)
- **security: allowlist**: Strict - only approved binaries run
- **ask: off**: Autonomous operation (single-user trust boundary)
- **safeBins**: Common dev utilities + grep/sort with explicit profiles
- **safeBinTrustedDirs**: macOS standard + Homebrew paths
- **safeBinProfiles**: Explicit argv policy for grep/sort to prevent file-based attacks

### What This Allows (without approval/allowlist)
- Text processing pipelines: `cat file | grep pattern | sort | uniq`
- JSON manipulation: `cat data.json | jq '.key'`
- File inspection: `head -n 10 file.txt`

### What This Blocks (requires allowlist)
- Git operations (`git` not in safeBins)
- Package managers (`npm`, `pnpm` not in safeBins)
- Interpreters (`node`, `python3` explicitly forbidden)
- Custom binaries (must be allowlisted)

### Adding Development Tools to Allowlist
```json
{
  "allowlist": [
    "/opt/homebrew/bin/git",
    "/opt/homebrew/bin/npm",
    "/opt/homebrew/bin/pnpm",
    "/opt/homebrew/bin/rg",
    "/usr/bin/find"
  ]
}
```

## Security Validation Checklist

✅ No interpreters in safeBins
✅ Explicit safeBinProfiles for custom bins
✅ Trusted directories exclude user-writable paths
✅ ask: off acceptable for single-user boundary
✅ security: allowlist (not full)
✅ No broad glob patterns like `/**/*`
✅ safeBins restricted to stdin-only utilities
✅ Fail-closed flag validation

## Injection Risk Assessment

### Low Risk
- safeBins with explicit profiles
- Literal argv enforcement
- Trusted directory resolution

### Medium Risk
- Allowlist patterns (review glob scope)
- ask: off (no human-in-loop)

### High Risk (AVOIDED)
- security: full
- Interpreters in safeBins
- PATH trusted automatically
- Broad allowlist globs

## Post-Configuration Actions
1. Run `openclaw security audit` to validate
2. Test safeBins with: `/exec echo "test" | jq -r .`
3. Monitor for approval-required commands
4. Add development tools to allowlist as needed
5. Review allowlist monthly for stale entries
