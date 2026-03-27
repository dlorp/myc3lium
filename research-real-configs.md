# OpenClaw Exec Configuration Research: Real-World Examples

**Research Date:** 2026-03-21  
**Source:** Official OpenClaw Documentation (https://docs.openclaw.ai)

This document contains real-world configuration examples for OpenClaw's `tools.exec` security settings, extracted from official documentation. These examples demonstrate different security levels from locked-down to permissive configurations.

---

## Understanding OpenClaw Exec Security Model

OpenClaw's exec tool has multiple security layers:

1. **Host Selection** (`tools.exec.host`):
   - `sandbox` (default) - runs in isolated Docker container
   - `gateway` - runs on gateway host with approval system
   - `node` - runs on paired remote device

2. **Security Modes** (`tools.exec.security`):
   - `deny` - completely blocks execution
   - `allowlist` - requires explicit path approval
   - `full` - allows without restrictions (dangerous)

3. **Approval Prompts** (`tools.exec.ask`):
   - `off` - no prompts
   - `on-miss` - prompt only for new commands
   - `always` - prompt every time

4. **Sandboxing** (`agents.defaults.sandbox.mode`):
   - `off` - no sandboxing
   - `non-main` - sandbox non-main sessions only
   - `all` - sandbox everything

---

## Configuration Examples by Security Level

### 1. Maximum Security (Hardened Baseline)

**Use case:** Public-facing bot, untrusted users, open groups  
**Security level:** ⭐⭐⭐⭐⭐ Paranoid

```json5
{
  gateway: {
    mode: "local",
    bind: "loopback",
    auth: { mode: "token", token: "replace-with-long-random-token" },
  },
  session: {
    dmScope: "per-channel-peer",  // Isolate user contexts
  },
  tools: {
    profile: "messaging",  // Restrict to messaging-only tools
    deny: [
      "group:automation", 
      "group:runtime", 
      "group:fs", 
      "sessions_spawn", 
      "sessions_send"
    ],
    fs: { workspaceOnly: true },
    exec: { 
      security: "deny",      // Completely disable exec
      ask: "always" 
    },
    elevated: { enabled: false },
  },
  channels: {
    whatsapp: { 
      dmPolicy: "pairing",
      groups: { "*": { requireMention: true } } 
    },
  },
  agents: {
    defaults: {
      sandbox: {
        mode: "all",           // Sandbox everything
        scope: "session",      // Isolate per session
        workspaceAccess: "none",
      },
    },
  },
}
```

**Key features:**
- Exec completely disabled (`security: "deny"`)
- All sessions sandboxed
- DM isolation enabled
- Workspace-only file access
- No elevated permissions
- Minimal tool surface

---

### 2. High Security (Sandboxed Execution)

**Use case:** Shared inbox, multiple trusted users, tools needed  
**Security level:** ⭐⭐⭐⭐ High

```json5
{
  tools: {
    exec: {
      host: "sandbox",       // Force sandbox execution
      security: "allowlist", // Require explicit approval
      ask: "on-miss",        // Prompt for new commands
      safeBins: ["cat", "grep", "jq", "wc"],  // Safe stdin-only tools
      safeBinTrustedDirs: ["/bin", "/usr/bin"],
    },
  },
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",      // Sandbox non-main sessions
        scope: "session",
        workspaceAccess: "ro", // Read-only workspace
        docker: {
          image: "openclaw-sandbox:bookworm-slim",
          network: "none",     // No network access
          readOnlyRoot: true,
          tmpfs: ["/tmp", "/var/tmp", "/run"],
          user: "1000:1000",
        },
      },
    },
  },
  session: {
    dmScope: "per-channel-peer",
  },
}
```

**Key features:**
- Sandboxed execution enforced
- Allowlist-only approval
- No network access in sandbox
- Read-only workspace mount
- Safe bins for basic utilities
- Per-session isolation

---

### 3. Medium Security (Controlled Host Access)

**Use case:** Personal assistant, single trusted user, needs host access  
**Security level:** ⭐⭐⭐ Medium

```json5
{
  tools: {
    exec: {
      host: "gateway",         // Run on gateway host
      security: "allowlist",   // Require approval
      ask: "on-miss",          // Prompt for new commands
      pathPrepend: ["~/bin", "/opt/oss/bin"],
      safeBins: ["cat", "grep", "sed", "jq", "wc", "head", "tail"],
      safeBinProfiles: {
        // Custom argv policies for interpreters
        python3: {
          minPositional: 1,
          maxPositional: 1,
          allowedValueFlags: ["-c"],
          deniedFlags: [],
        },
      },
    },
  },
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",      // Sandbox untrusted sessions
        scope: "agent",
        workspaceAccess: "rw", // Read-write workspace
        docker: {
          network: "bridge",   // Limited network
        },
      },
    },
  },
}
```

**Key features:**
- Gateway host execution with approvals
- Allowlist enforcement
- Custom safe bin profiles
- Sandboxing for non-main sessions only
- Network access available in sandbox

---

### 4. Medium-Low Security (Expanded Tool Access)

**Use case:** Development agent, needs build tools and network  
**Security level:** ⭐⭐ Medium-Low

```json5
{
  tools: {
    allow: ["exec", "process", "read", "write", "edit", "apply_patch"],
    deny: ["browser", "canvas"],
    exec: {
      host: "sandbox",
      security: "allowlist",
      ask: "on-miss",
      backgroundMs: 10000,
      timeoutSec: 1800,
      cleanupMs: 1800000,
      notifyOnExit: true,
    },
  },
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        scope: "agent",
        workspaceAccess: "rw",
        docker: {
          image: "openclaw-sandbox-common:bookworm-slim",  // Includes Node, Python, Git
          network: "bridge",     // Network access enabled
          readOnlyRoot: false,   // Allow package installs
          binds: [
            "/home/user/source:/source:ro",  // Mount additional directories
            "/var/cache:/cache:rw",
          ],
        },
      },
    },
  },
}
```

**Key features:**
- Expanded tool allowlist
- Background process support
- Network access for package downloads
- Custom bind mounts
- Full-featured sandbox image

---

### 5. Low Security (Convenience Mode)

**Use case:** Local development, single user, full trust  
**Security level:** ⭐ Low

```json5
{
  tools: {
    exec: {
      host: "gateway",       // Direct host access
      security: "full",      // No restrictions
      ask: "off",            // No prompts
    },
    elevated: {
      enabled: true,         // Allow elevated execution
      allowFrom: {
        whatsapp: ["+15555550123"],
      },
    },
  },
  agents: {
    defaults: {
      sandbox: {
        mode: "off",         // No sandboxing
      },
    },
  },
}
```

**Key features:**
- Direct host execution
- No approval prompts
- Elevated mode available
- No sandboxing
- Maximum convenience, minimum security

⚠️ **Warning:** This configuration is appropriate ONLY for:
- Single-user personal assistants
- Localhost-only deployments
- Fully trusted operators

---

## Advanced Patterns

### 6. Multi-Agent Security Tiers

Different agents with different security profiles:

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        scope: "agent",
      },
    },
    list: [
      {
        id: "home",
        default: true,
        workspace: "~/.openclaw/workspace-home",
        tools: {
          exec: {
            security: "allowlist",
            ask: "on-miss",
          },
        },
      },
      {
        id: "work",
        workspace: "~/.openclaw/workspace-work",
        tools: {
          exec: {
            security: "deny",  // Work bot cannot execute commands
          },
          elevated: { enabled: false },
        },
        sandbox: {
          mode: "all",         // Always sandboxed
        },
      },
      {
        id: "build",
        workspace: "~/.openclaw/workspace-build",
        sandbox: {
          mode: "all",
          docker: {
            network: "bridge",
            binds: ["/mnt/cache:/cache:rw"],
            setupCommand: "apt-get update && apt-get install -y nodejs npm",
          },
        },
      },
    ],
  },
}
```

---

### 7. SSH Backend (Remote Execution)

Execute in a remote sandbox via SSH:

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "all",
        backend: "ssh",
        scope: "session",
        workspaceAccess: "rw",
        ssh: {
          target: "user@sandbox-host:22",
          workspaceRoot: "/tmp/openclaw-sandboxes",
          strictHostKeyChecking: true,
          updateHostKeys: true,
          identityFile: "~/.ssh/id_ed25519",
          knownHostsFile: "~/.ssh/known_hosts",
        },
      },
    },
  },
}
```

---

### 8. OpenShell Backend (Managed Sandboxes)

Using OpenShell for managed remote sandboxes:

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "all",
        backend: "openshell",
        scope: "session",
        workspaceAccess: "rw",
      },
    },
  },
  plugins: {
    entries: {
      openshell: {
        enabled: true,
        config: {
          from: "openclaw",
          mode: "mirror",  // or "remote" for remote-canonical
          remoteWorkspaceDir: "/sandbox",
          remoteAgentWorkspaceDir: "/agent",
        },
      },
    },
  },
}
```

**Workspace modes:**
- `mirror`: Local workspace canonical, syncs before/after exec
- `remote`: Remote workspace canonical, seed once then remote-only

---

## Security Audit Checklist

Key `checkId` values to watch for in `openclaw security audit`:

| Check ID | Severity | What it means |
|----------|----------|---------------|
| `tools.exec.host_sandbox_no_sandbox_defaults` | warn | Sandbox mode is off but exec host=sandbox is configured |
| `security.exposure.open_groups_with_elevated` | critical | Open groups + elevated tools = high prompt injection risk |
| `security.exposure.open_groups_with_runtime_or_fs` | critical | Open groups can reach command/file tools |
| `gateway.bind_no_auth` | critical | Network binding without authentication |
| `fs.config.perms_writable` | critical | Config file world-writable |

Run regularly:
```bash
openclaw security audit
openclaw security audit --deep
openclaw security audit --fix
```

---

## Best Practices Summary

### ✅ DO:
1. Start with `security: "deny"` and selectively enable
2. Use `dmScope: "per-channel-peer"` for multi-user setups
3. Enable sandboxing for untrusted contexts (`mode: "non-main"` or `"all"`)
4. Use `workspaceOnly: true` for filesystem tools
5. Keep `requireMention: true` in groups
6. Run `openclaw security audit` regularly
7. Use `ask: "on-miss"` or `"always"` for host execution
8. Prefer strong models for tool-enabled agents
9. Isolate external content with reader agents

### ❌ DON'T:
1. Use `security: "full"` with `ask: "off"` in shared contexts
2. Run public bots with `sandbox.mode: "off"`
3. Mix personal and company identities in one runtime
4. Trust `sessionKey` as an auth boundary
5. Use weak/small models with exec tools
6. Expose Gateway on `0.0.0.0` without auth
7. Add interpreters (`python3`, `node`, `bash`) to `safeBins` without profiles
8. Enable `allowUnsafeExternalContent` in production

---

## Recommended Starting Configuration

For most users, start here and adjust:

```json5
{
  gateway: {
    mode: "local",
    bind: "loopback",
    auth: { mode: "token", token: "${OPENCLAW_GATEWAY_TOKEN}" },
  },
  session: {
    dmScope: "per-channel-peer",
  },
  tools: {
    profile: "messaging",
    exec: {
      host: "sandbox",
      security: "allowlist",
      ask: "on-miss",
      safeBins: ["cat", "grep", "jq"],
    },
    fs: { workspaceOnly: true },
  },
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        scope: "session",
        workspaceAccess: "ro",
        docker: {
          image: "openclaw-sandbox:bookworm-slim",
          network: "none",
        },
      },
    },
  },
  channels: {
    whatsapp: {
      dmPolicy: "pairing",
      groups: { "*": { requireMention: true } },
    },
  },
}
```

This provides:
- Sandboxed execution for untrusted sessions
- Approval-based allowlist
- DM isolation
- Mention-gated groups
- Read-only workspace in sandbox
- No network access from sandbox

---

## Sources & References

All examples extracted from:
- https://docs.openclaw.ai/gateway/security
- https://docs.openclaw.ai/gateway/configuration
- https://docs.openclaw.ai/gateway/configuration-examples
- https://docs.openclaw.ai/gateway/sandboxing
- https://docs.openclaw.ai/tools/exec

**Note:** OpenClaw is designed as a personal assistant, NOT a hostile multi-tenant system. These configurations assume one trusted operator boundary per gateway. For adversarial-user isolation, run separate gateways per trust boundary.

---

**Research completed:** 2026-03-21  
**Documentation version:** Latest (as of research date)
