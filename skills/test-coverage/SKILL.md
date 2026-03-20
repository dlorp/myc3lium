# Test Coverage & Lint Skill

Multi-language test coverage and linting with live status.

## Live Coverage Context

**JavaScript/TypeScript (Vitest/Jest):**
!`npm test -- --coverage --reporter=json 2>/dev/null | jq -r '.coverageMap | "Coverage: \(.total.lines.pct)% lines | \(.total.statements.pct)% statements"' || npm test 2>&1 | grep -E "Coverage|All files" | head -5`

**JavaScript Lint (ESLint):**
!`npm run lint 2>&1 | grep -E "problems|errors|warnings" | head -3`

**Python Coverage (pytest):**
!`pytest --cov --cov-report=term-missing 2>/dev/null | grep "TOTAL" || echo "Python tests not configured"`

**Python Lint (ruff/flake8):**
!`ruff check . 2>/dev/null | tail -5 || flake8 . 2>/dev/null | tail -5 || echo "Python linting not configured"`

**Go Coverage:**
!`go test -cover ./... 2>/dev/null | grep coverage || echo "Go tests not configured"`

**Go Lint (golangci-lint):**
!`golangci-lint run 2>/dev/null | tail -10 || echo "Go linting not configured"`

**Rust Coverage (tarpaulin):**
!`cargo tarpaulin --skip-clean 2>/dev/null | grep "Coverage" || echo "Rust coverage not configured"`

**Rust Lint (clippy):**
!`cargo clippy 2>&1 | grep -E "warning|error" | head -5`

## JavaScript/TypeScript

### Testing (Vitest)
```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch

# Run specific test
npm test -- src/component.test.ts
```

### Linting (ESLint)
```bash
# Lint all files
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Lint specific files
npx eslint src/**/*.ts

# Check specific rules
npx eslint . --rule 'no-console: error'
```

### Type Checking (TypeScript)
```bash
# Check types
npx tsc --noEmit

# Watch mode
npx tsc --noEmit --watch

# Strict mode check
npx tsc --noEmit --strict
```

## Python

### Testing (pytest)
```bash
# Run tests with coverage
pytest --cov --cov-report=html

# Run specific test
pytest tests/test_feature.py

# Verbose output
pytest -v

# Show coverage gaps
pytest --cov --cov-report=term-missing
```

### Linting (ruff)
```bash
# Check all files
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Format code
ruff format .

# Check specific rules
ruff check --select E,F .
```

### Type Checking (mypy)
```bash
# Type check all files
mypy .

# Strict mode
mypy --strict .

# Show error codes
mypy --show-error-codes .
```

## Go

### Testing
```bash
# Run tests with coverage
go test -cover ./...

# Detailed coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Run specific test
go test -run TestFeature ./...

# Verbose
go test -v ./...
```

### Linting (golangci-lint)
```bash
# Lint all files
golangci-lint run

# Fast mode
golangci-lint run --fast

# Enable all linters
golangci-lint run --enable-all

# Fix issues
golangci-lint run --fix
```

## Rust

### Testing
```bash
# Run tests
cargo test

# With coverage (tarpaulin)
cargo tarpaulin --out Html

# Run specific test
cargo test test_name

# Show output
cargo test -- --nocapture
```

### Linting (clippy)
```bash
# Lint all code
cargo clippy

# Deny warnings
cargo clippy -- -D warnings

# All lints
cargo clippy -- -W clippy::all

# Fix issues
cargo clippy --fix
```

### Formatting (rustfmt)
```bash
# Format code
cargo fmt

# Check formatting
cargo fmt -- --check
```

## Coverage Thresholds

**Minimum Coverage Goals:**
- **Statements:** 80%
- **Branches:** 70%
- **Functions:** 80%
- **Lines:** 80%

**Configure in package.json:**
```json
{
  "vitest": {
    "coverage": {
      "lines": 80,
      "functions": 80,
      "branches": 70,
      "statements": 80
    }
  }
}
```

## Health Checks

**Coverage trending:**
!`git log --oneline --since="7 days ago" -- "*coverage*" | wc -l` coverage commits this week

**Lint status:**
!`npm run lint 2>&1 | grep -E "0 errors|✨" && echo "✅ Clean" || echo "⚠️ Has issues"`

**Test status:**
!`npm test 2>&1 | grep -E "passed|failed" | head -1`

## Troubleshooting

**Tests failing:**
- Run in watch mode: `npm test -- --watch`
- Check specific test: `npm test -- path/to/test.ts`
- Clear cache: `rm -rf node_modules/.vitest`

**Coverage too low:**
- Find untested files: `npm test -- --coverage --reporter=text`
- Add missing tests
- Remove dead code

**Lint errors:**
- Auto-fix: `npm run lint -- --fix`
- Disable specific rule: `// eslint-disable-next-line rule-name`
- Update config: `.eslintrc.js`
