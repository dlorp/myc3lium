# NPM/Package Management Skill

Manage Node.js dependencies, security, and package health.

## Live Package Context

**Package Info:**
!`cat package.json | jq -r '"\(.name)@\(.version)\nDeps: \(.dependencies | length // 0) | DevDeps: \(.devDependencies | length // 0)"' 2>/dev/null || echo "Not a Node.js project"`

**Outdated Packages:**
!`npm outdated --json 2>/dev/null | jq -r 'to_entries | .[] | "\(.key): \(.value.current) → \(.value.latest)"' | head -10`

**Security Vulnerabilities:**
!`npm audit --json 2>/dev/null | jq -r '.metadata | "Total: \(.vulnerabilities.total) | Critical: \(.vulnerabilities.critical) | High: \(.vulnerabilities.high)"'`

**Package Size:**
!`du -sh node_modules 2>/dev/null || echo "node_modules not found"`

**Lock File Status:**
!`ls -lh package-lock.json pnpm-lock.yaml yarn.lock 2>/dev/null | awk '{print $9, "("$5")"}' || echo "No lock file"`

**Scripts Available:**
!`cat package.json | jq -r '.scripts | keys | .[]' 2>/dev/null | head -10`

## Common Operations

### Dependency Management
```bash
# Install dependencies
npm install

# Add dependency
npm install <package>

# Add dev dependency
npm install -D <package>

# Remove dependency
npm uninstall <package>

# Update all packages
npm update

# Update specific package
npm update <package>
```

### Security
```bash
# Audit dependencies
npm audit

# Fix vulnerabilities automatically
npm audit fix

# Force fix (may break things)
npm audit fix --force

# Check for known vulnerabilities
npm audit --json | jq '.vulnerabilities'
```

### Package Info
```bash
# View package info
npm info <package>

# List installed packages
npm list --depth=0

# Check for outdated packages
npm outdated

# View dependency tree
npm list <package>
```

### Workspace Management
```bash
# Clean install
rm -rf node_modules package-lock.json && npm install

# Verify integrity
npm ci

# Dedupe dependencies
npm dedupe

# Check for duplicate packages
npm list --depth=0 | grep -i deduped
```

## Health Checks

**Dependency freshness:**
!`npm outdated --json 2>/dev/null | jq 'length' || echo "0"` packages outdated

**Security score:**
!`npm audit --json 2>/dev/null | jq -r '.metadata.vulnerabilities | if .total == 0 then "✅ No vulnerabilities" else "⚠️ \(.total) vulnerabilities (\(.critical) critical)" end'`

**Install health:**
!`test -d node_modules && echo "✅ Installed" || echo "❌ Missing node_modules"`

## Troubleshooting

**Install fails:**
- Clear cache: `npm cache clean --force`
- Delete lock: `rm package-lock.json`
- Fresh install: `rm -rf node_modules && npm install`

**Version conflicts:**
- Check peer deps: `npm list --depth=0 2>&1 | grep UNMET`
- Use npm overrides in package.json

**Slow installs:**
- Use pnpm: `pnpm install` (faster, smaller)
- Use offline mode: `npm install --offline`
- Check registry: `npm config get registry`

## Alternative Package Managers

**pnpm (faster, disk-efficient):**
```bash
pnpm install
pnpm add <package>
pnpm update
```

**yarn (parallel installs):**
```bash
yarn install
yarn add <package>
yarn upgrade
```
