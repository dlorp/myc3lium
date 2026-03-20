# PR Workflow Skill

Automated pull request workflow with security review, code review, and CI verification.

## Current PR Context

**PR Details:**
!`gh pr view --json number,title,author,url | jq -r '"PR #\(.number): \(.title)\nAuthor: \(.author.login)\nURL: \(.url)"'`

**Changed Files:**
!`gh pr diff --name-only`

**Changes Summary:**
!`gh pr view --json additions,deletions | jq -r '"+\(.additions) -\(.deletions)"'`

**CI Status:**
!`gh pr checks --json name,status,conclusion | jq -r '.[] | "\(.name): \(.conclusion // .status)"'`

**Full Diff:**
!`gh pr diff`

**PR Description (from commits):**
!`git log --format='- %s' main..HEAD`

**Merge Conflicts:**
!`gh pr view --json mergeable,mergeStateStatus | jq -r 'if .mergeable == "CONFLICTING" then "⚠️ Has conflicts" else "✅ No conflicts" end'`

**Review Comments:**
!`gh pr view --json reviews | jq -r '.reviews | length' | xargs -I {} echo "{} reviews"`

## Workflow Steps

### 1. Security Review
- Spawn @security-reviewer to check for:
  - XSS vulnerabilities
  - Injection risks  
  - Memory leaks
  - Input validation
  - Resource exhaustion

### 2. Code Quality Review
- Check lint status
- Verify tests pass
- Review code patterns
- Check for TODO/FIXME
- Verify documentation

### 3. CI Verification
- **CRITICAL:** Do NOT mark PR complete until ALL CI checks pass
- Monitor: !`gh pr checks --watch` until green
- If CI fails, identify errors and fix

### 4. Completion Criteria
✅ Security review: No critical issues
✅ Code review: All medium+ issues addressed  
✅ Lint: Passing
✅ Tests: Passing
✅ CI: All checks green

Only after ALL criteria met, confirm PR ready to merge.

## Commands Available
- `gh pr view` - PR details
- `gh pr diff` - See changes
- `gh pr checks` - CI status
- `gh pr merge` - Merge when ready (ask first)
h pr checks` - CI status
- `gh pr merge` - Merge when ready (ask first)
