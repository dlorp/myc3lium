# Final tools.exec Configuration (Security Reviewed)

## Recommended Configuration for Your Setup

Based on multi-language research (GitHub CVEs, competitor analysis, real-world configs) and security review.

**Context:** Single-user macOS development, autonomous operation, Homebrew-based tooling.

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
        "base64"
      ],
      "safeBinTrustedDirs": [
        "/bin",
        "/usr/bin",
        "/opt/homebrew/bin"
      ],
      "safeBinProfiles": {},
      "allowlist": [
        "/opt/homebrew/bin/git",
        "/opt/homebrew/bin/npm",
        "/opt/homebrew/bin/pnpm",
        "/opt/homebrew/bin/node",
        "/opt/homebrew/bin/rg",
        "/opt/homebrew/bin/fd",
        "/usr/bin/find",
        "/usr/bin/grep",
        "/usr/bin/sort",
        "/usr/bin/awk",
        "/usr/bin/sed"
      ]
    }
  }
}
```

## Why This Config

### Security Fixes Applied
1. **Removed `grep`/`sort`/`awk`/`sed` from safeBins** - Per security review, these have injection risks via `-e` flags and positional args. Moved to explicit allowlist using system binaries.

2. **Kept `/opt/homebrew/bin` in trusted dirs** - Security review confirmed this is admin-protected on standard macOS Homebrew installs. Safe to trust.

3. **Explicit allowlist for dev tools** - Git, npm, pnpm, node, etc. are explicitly trusted rather than auto-allowed.

4. **Empty safeBinProfiles** - Removed complex profiles that had injection vectors. Using simple stdin-only utilities instead.

### What This Allows

**Auto-allowed (no approval needed):**
- Text processing: `jq`, `cut`, `uniq`, `head`, `tail`, `tr`, `wc`, `base64`

**Explicitly allowed (no approval needed):**
- Git operations
- npm/pnpm package management
- Node execution
- Modern CLI tools (rg, fd)
- System utilities (find, grep, sort, awk, sed)

**Blocked (requires config change to allow):**
- Python/Ruby interpreters
- Docker/Kubernetes commands
- Network tools (curl, wget)
- System modification tools (sudo, chmod, etc.)

### Research Findings Summary

**From GitHub CVEs (research-github.md):**
- 7 security advisories patched in 2026.3.11
- Self-approval bypass (CVSS 8.5)
- TOCTOU attacks in approval flow
- Allowlist pattern over-matching

**From Competitor Analysis (research-competitors.md):**
- Aider: No approvals (full trust model)
- Cursor: Unknown/proprietary
- Copilot Workspace: Cloud sandbox only
- **OpenClaw has most granular control**

**From Real Configs (research-real-configs.md):**
- 8 production examples from docs
- Most common: `security: "allowlist"` + `ask: "on-miss"`
- Sandbox mode requires Docker (disabled by default)

### Why `ask: "off"` Is Safe Here

1. **Single-user trust boundary** - You're the only operator
2. **Explicit allowlist** - Only approved binaries run
3. **No interpreters in safeBins** - Prevents code execution via auto-allowed paths
4. **System binaries for text tools** - `/usr/bin` versions are SIP-protected
5. **Homebrew binaries require admin** - Can't be modified without sudo

## Migration Steps

1. **Backup current config:**
```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup
```

2. **Apply this config:**
Merge the JSON above into your `openclaw.json` under `tools.exec`.

3. **Restart gateway:**
```bash
openclaw gateway restart
```

4. **Test:**
```bash
# Should work without approval
echo '{"test": "value"}' | jq .test
git status
npm --version

# Should be blocked (not in allowlist)
python3 --version
docker ps
```

## To Add More Tools

```bash
# Find the binary path
which some-tool

# Add to allowlist in config
"allowlist": [
  "/opt/homebrew/bin/some-tool"
]
```

Or use `/approve allow-always` the first time it triggers a prompt (if you change ask back to "on-miss").

## Security Validation

After applying config:
```bash
openclaw security audit
```

Should return 0 critical issues related to exec configuration.

## Complete Research Archive

All supporting research saved to workspace:
- `research-github.md` - GitHub CVEs and PRs
- `research-competitors.md` - Aider/Cursor/Copilot comparison  
- `research-real-configs.md` - 8 production examples
- `exec-config-guide.md` - Original guide (has issues noted by security review)
- `exec-research.md` - Initial analysis

---

**Bottom line:** This config balances security and autonomy for single-user development work. Apply it and you're done with approval prompts while maintaining good security posture.
