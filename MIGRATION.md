# TeletextGrid Migration Guide

This guide documents the API changes in the TeletextGrid component and how to migrate your code to the new version.

## Overview

The TeletextGrid component has been significantly improved with:
- **Required format validation** - Enforces strict 25×80 character grid
- **Error handling** - Graceful fallback for texture loading failures
- **Performance optimization** - Render-on-demand instead of continuous rendering
- **Comprehensive testing** - Unit tests for validation and error cases

## Key Changes

### 1. Content Format: Strict 25×80 Grid Requirement

**Before:** Content could be any shape; the component would normalize it.

```tsx
// Old code - flexible but inconsistent
const content = [
  "Hello",
  "World"
  // ... only a few rows, auto-padded with spaces
]
<TeletextGrid content={content} />
```

**After:** Content MUST be exactly 25 rows × 80 columns (string[][]).

```tsx
// New code - strict validation
const content: string[][] = Array.from({ length: 25 }, (_, row) =>
  Array.from({ length: 80 }, (_, col) =>
    row === 0 && col < 5 ? "HELLO"[col] : ' '
  )
)
<TeletextGrid content={content} />
```

### 2. Content Validation Errors

The component now validates content dimensions and throws helpful errors:

```tsx
// ❌ Error: Content is not an array
<TeletextGrid content="hello" />

// ❌ Error: Content must have exactly 25 rows
const shortContent = Array.from({ length: 20 }, () =>
  Array.from({ length: 80 }, () => ' ')
)
<TeletextGrid content={shortContent} />

// ❌ Error: Each row must have exactly 80 columns
const wrongColContent = Array.from({ length: 25 }, () =>
  Array.from({ length: 64 }, () => ' ')
)
<TeletextGrid content={wrongColContent} />

// ✅ Correct: 25 rows × 80 columns
const correctContent = Array.from({ length: 25 }, () =>
  Array.from({ length: 80 }, () => ' ')
)
<TeletextGrid content={correctContent} />
```

### 3. Error Messages

When validation fails, you'll see helpful error messages:

```
Content must have exactly 25 rows, got 20. Expected: 25 rows × 80 columns

Row 5 has 64 columns, expected 80. Each row must have exactly 80 columns

Row 10, Column 15: expected string, got number. All cells must be strings
```

## Migration Steps

### Step 1: Update Content Generation

Create a helper function to generate valid content:

```tsx
// content.ts
import { COLUMNS, ROWS } from './TeletextGrid'

export function createEmptyPage(): string[][] {
  return Array.from({ length: ROWS }, () =>
    Array.from({ length: COLUMNS }, () => ' ')
  )
}

export function writePage(text: string): string[][] {
  const page = createEmptyPage()
  let col = 0
  let row = 0
  
  for (const char of text) {
    if (char === '\n') {
      row++
      col = 0
      if (row >= ROWS) break
    } else {
      if (col < COLUMNS) {
        page[row][col] = char
        col++
      }
    }
  }
  
  return page
}
```

### Step 2: Update Component Usage

```tsx
// Before
import TeletextGrid from './TeletextGrid'

function MyPage() {
  const content = [
    "Hello, World!",
    "Line 2",
    // ... etc
  ]
  
  return <TeletextGrid content={content} />
}

// After
import TeletextGrid, { COLUMNS, ROWS } from './TeletextGrid'

function MyPage() {
  const content = Array.from({ length: ROWS }, (_, row) => {
    if (row === 0) {
      const text = "Hello, World!"
      return [
        ...text.split(''),
        ...Array.from({ length: COLUMNS - text.length }, () => ' ')
      ]
    }
    return Array.from({ length: COLUMNS }, () => ' ')
  })
  
  return <TeletextGrid content={content} />
}
```

### Step 3: Add Error Handling

```tsx
function MyPage() {
  const [error, setError] = useState<string | null>(null)
  
  const content = createPageContent()
  
  return (
    <div>
      {error && <div className="error">{error}</div>}
      <TeletextGrid content={content} />
    </div>
  )
}
```

## API Reference

### TeletextGrid Props

```tsx
interface TeletextGridProps {
  /** Content to display: exactly 25 rows × 80 columns */
  content: string[][]
  
  /** Show FPS counter (optional, default: false) */
  showFps?: boolean
  
  /** Visual effects configuration (optional) */
  effectsConfig?: {
    enableChromatic?: boolean      // RGB aberration (default: true)
    enableBloom?: boolean          // Glow effect (default: true)
    enablePhosphor?: boolean       // Persistence (default: true)
    enableNoise?: boolean          // Film grain (default: true)
    enableFlicker?: boolean        // Screen flicker (default: true)
    chromaticAmount?: number       // 0.0-0.01 (default: 0.001)
    bloomStrength?: number         // 0.0-1.0 (default: 0.45)
    phosphorDecay?: number         // 0.0-1.0 (default: 0.88)
    noiseAmount?: number           // 0.0-0.1 (default: 0.04)
    flickerAmount?: number         // 0.0-0.1 (default: 0.012)
  }
}
```

### Exported Constants

```tsx
import { COLUMNS, ROWS } from './TeletextGrid'

console.log(COLUMNS) // 80
console.log(ROWS)    // 25
```

## Example: Complete Migration

### Before (Old Code)

```tsx
import TeletextGrid from './components/TeletextGrid'

export function StatusPage() {
  const pageData = [
    "STATUS REPORT",
    "CPU: 45%",
    "MEM: 2.1GB",
    "DISK: 156GB free"
  ]
  
  return (
    <div className="status-page">
      <TeletextGrid content={pageData} />
    </div>
  )
}
```

### After (New Code)

```tsx
import TeletextGrid, { COLUMNS, ROWS } from './components/TeletextGrid'

function writeText(page: string[][], row: number, col: number, text: string) {
  for (let i = 0; i < text.length && col + i < COLUMNS; i++) {
    page[row][col + i] = text[i]
  }
}

export function StatusPage() {
  // Create empty 25×80 grid
  const page = Array.from({ length: ROWS }, () =>
    Array.from({ length: COLUMNS }, () => ' ')
  )
  
  // Write content at specific positions
  writeText(page, 0, 0, 'STATUS REPORT')
  writeText(page, 2, 0, 'CPU: 45%')
  writeText(page, 3, 0, 'MEM: 2.1GB')
  writeText(page, 4, 0, 'DISK: 156GB free')
  
  return (
    <div className="status-page">
      <TeletextGrid content={page} />
    </div>
  )
}
```

## Common Issues & Solutions

### Issue: "Content must have exactly 25 rows"

**Cause:** Your content array doesn't have 25 rows.

**Solution:**
```tsx
// ❌ Wrong
const page = Array.from({ length: 10 }, () => /* ... */)

// ✅ Correct
const page = Array.from({ length: 25 }, () => /* ... */)
```

### Issue: "Row X has Y columns, expected 80"

**Cause:** One or more rows don't have exactly 80 columns.

**Solution:**
```tsx
// ❌ Wrong
const row = "Hello".split('')  // Only 5 columns

// ✅ Correct
const row = [
  ...text.split(''),
  ...Array.from({ length: COLUMNS - text.length }, () => ' ')
]
```

### Issue: Texture loading error

**Cause:** Font atlas image not found at `/fonts/vga-8x16-atlas.png`.

**Solution:**
1. Ensure the font atlas file exists
2. Check the path in public assets
3. The component will display an error message if loading fails

### Issue: Component not rendering

**Cause:** Content validation failed due to incorrect format.

**Solution:**
1. Check the browser console for detailed error messages
2. Verify content is exactly 25×80
3. Verify all cells contain strings
4. Use the migration examples as a template

## Performance Notes

### Rendering Optimization

The new version automatically optimizes rendering:

- **Static content:** Renders once on load, then on-demand only
- **Animated effects:** Continuous rendering when phosphor/flicker/noise/chromatic/bloom are enabled
- **Effect disabling:** Turn off unused effects to reduce GPU usage

```tsx
// Static display - minimal CPU/GPU usage
<TeletextGrid
  content={page}
  effectsConfig={{
    enableChromatic: false,
    enableBloom: false,
    enablePhosphor: false,
    enableNoise: false,
    enableFlicker: false,
  }}
/>

// Animated display - normal CPU/GPU usage
<TeletextGrid
  content={page}
  effectsConfig={{
    enablePhosphor: true,    // Persistence trail effect
    enableFlicker: true,     // Screen flicker
    enableNoise: true,       // Film grain animation
  }}
/>
```

## Troubleshooting

### Validation errors not helpful enough?

Add your own validation layer:

```tsx
function validatePageContent(content: any): content is string[][] {
  if (!Array.isArray(content)) {
    console.error('Content must be an array')
    return false
  }
  
  if (content.length !== ROWS) {
    console.error(`Expected ${ROWS} rows, got ${content.length}`)
    return false
  }
  
  for (let i = 0; i < content.length; i++) {
    if (!Array.isArray(content[i])) {
      console.error(`Row ${i} is not an array`)
      return false
    }
    
    if (content[i].length !== COLUMNS) {
      console.error(`Row ${i} has ${content[i].length} columns, expected ${COLUMNS}`)
      return false
    }
    
    for (let j = 0; j < content[i].length; j++) {
      if (typeof content[i][j] !== 'string') {
        console.error(`Row ${i}, Column ${j} is not a string`)
        return false
      }
    }
  }
  
  return true
}

export function SafePage({ content }: { content: any }) {
  if (!validatePageContent(content)) {
    return <div>Invalid page content</div>
  }
  
  return <TeletextGrid content={content} />
}
```

## Need Help?

- Check the unit tests in `TeletextGrid.test.tsx` for usage examples
- Review example implementations in the codebase
- Check browser console for detailed validation error messages

## Changelog

### Version 2.0 (Current)

- ✅ Added strict 25×80 content validation
- ✅ Added texture loading error handler
- ✅ Fixed wasteful animation loop
- ✅ Added comprehensive unit tests
- ✅ Created migration guide
- ✅ Improved error messages

### Version 1.0

- Initial release with flexible content normalization
