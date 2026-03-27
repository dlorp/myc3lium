# Exec Configuration Migration Guide

## Security Review Summary
**Status:** ❌ NEEDS REVISION (2 critical, 3 medium, 2 low issues found)

## Critical Fixes Applied

### 1. Trusted Directories Hardened
**Before:**
```json
"/opt/homebrew/bin",  // ❌ User-writable
"/usr/local/bin"      // ❌ User-writable
```

**After:**
```json
"/bin",        // ✅ System-protected
"/usr/bin"     // ✅ System-protected
```

**Impact:** Homebrew utilities now require explicit allowlist entries instead of auto-trust.

### 2. grep Profile Fixed (Arbitrary File Read Vulnerability)
**Before:**
```bash
grep "/etc/passwd"  # ❌ Reads sensitive files
```

**After:**
```bash
grep -e "pattern"   # ✅ Explicit pattern flag required
```

**Breaking Change:** All grep usage must use `-e` flag for patterns.

## Medium Priority Changes

### 3. Approval Mode Changed
**Before:** `ask: "off"` (no approvals, silent execution)  
**After:** `ask: "on-miss"` (approve new commands, cache known ones)

**Rationale:** Balances autonomy with safety - frequent operations run without prompts, anomalous commands trigger review.

**To restore full autonomy:**
```json
"ask": "off"  // Plus add audit logging
```

### 4. Enhanced sort Profile
Added denied flags: `-T`, `--debug`, `--random-source`

### 5. Additional Safe Bins
Added: `awk`, `sed`, `base64` with explicit profiles

## Migration Steps

### Step 1: Apply Hardened Config
```bash
# Backup current config
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup

# Merge exec-config-hardened.json into your config
openclaw config merge exec-config-hardened.json
```

### Step 2: Build Allowlist for Development Tools
```bash
# Add commonly used binaries
openclaw config set tools.exec.allowlist '[]'

# Example for typical dev setup:
openclaw config add tools.exec.allowlist "/opt/homebrew/bin/git"
openclaw config add tools.exec.allowlist "/opt/homebrew/bin/npm"
openclaw config add tools.exec.allowlist "/opt/homebrew/bin/pnpm"
openclaw config add tools.exec.allowlist "/opt/homebrew/bin/rg"
openclaw config add tools.exec.allowlist "/usr/bin/find"
```

**Safe Allowlist Pattern:**
- ✅ Explicit full paths: `/opt/homebrew/bin/git`
- ❌ Recursive wildcards: `~/Projects/**/bin/rg`
- ❌ User-writable globs: `~/.local/bin/*`

### Step 3: Update grep Usage
```bash
# ❌ Old usage (now blocked)
cat file | grep "pattern"

# ✅ New usage (required)
cat file | grep -e "pattern"
```

### Step 4: Validate Configuration
```bash
# Run security audit
openclaw security audit

# Test safe bins
echo '{"test": "value"}' | jq .test
echo "test" | grep -e "test"

# Test allowlisted binary
git status
```

### Step 5: Monitor for 1 Week
- Review exec approval prompts
- Build allowlist through `/approve allow-always` workflow
- Check for false positives

## Compensating Controls (if using ask: "off")

If you need full autonomy without approval prompts:

1. **Enable Audit Logging**
```json
"tools": {
  "exec": {
    "ask": "off",
    "auditLog": {
      "enabled": true,
      "path": "~/.openclaw/logs/exec-audit.jsonl"
    }
  }
}
```

2. **Set Up Alerting**
```bash
# Monitor exec logs for anomalies
tail -f ~/.openclaw/logs/exec-audit.jsonl | grep -e "UNUSUAL_PATTERN"
```

3. **Weekly Log Review**
```bash
# Check last 7 days of exec activity
jq -r '.timestamp + " " + .binary + " " + .argv[0]' \
  ~/.openclaw/logs/exec-audit.jsonl | \
  grep "$(date -v-7d +%Y-%m-%d)" | \
  sort | uniq -c | sort -rn
```

## Rollback Plan

If issues arise:
```bash
# Restore backup
cp ~/.openclaw/openclaw.json.backup ~/.openclaw/openclaw.json

# Restart gateway
openclaw gateway restart
```

## Security Testing Checklist

Before production:
- [ ] Run `openclaw security audit` (0 critical issues)
- [ ] Test grep with `-e` flag requirement
- [ ] Verify Homebrew binaries require approval/allowlist
- [ ] Test common development workflows (git, npm, etc.)
- [ ] Confirm ask: "on-miss" behavior (cache hit = no prompt)
- [ ] Review audit logs for 1 week
- [ ] Document approved allowlist entries

## Additional Hardening (Optional)

### Rate Limiting
```json
"execRateLimits": {
  "maxPerMinute": 60,
  "maxPerHour": 500,
  "alertThreshold": 100
}
```

### Binary Checksum Validation
```json
"safeBinChecksums": {
  "/bin/grep": "sha256:abc123...",
  "/usr/bin/jq": "sha256:def456..."
}
```

### Network Tool Monitoring
For binaries with network capabilities (`git`, `npm`, `curl`):
- Explicit allowlist only (never safeBins)
- Monitor egress destinations
- Require approval for new repositories/registries

## Support

Questions or issues during migration?
- Check security review: `workspace/exec-research.md`
- Full docs: https://docs.openclaw.ai/tools/exec-approvals
- Security audit: `openclaw security audit --deep`
