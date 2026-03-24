# Mockup vs PR #45 Implementation Analysis

## Issues Found in Mockup HTML

### 1. **Syntax Error - Missing Comma**
Line 6 in NODES array:
```javascript
{id:'RHIZOME-03',cs:'Ridge',  rx:.54,ry:.35,col:'#3B7AE4',st:'FAIR',rssi:-88,bat:68,type:'RHIZOME'}{id:'SPORE-06',cs:null,     rx:.37,ry:.67,col:RD,   st:'TOUT',rssi:null,bat:12,type:'SPORE'}
```
**Missing comma between two objects** - will cause JavaScript parse error.

### 2. **Code Quality Issues**
- Minified/obfuscated variable names (`bx`, `cv`, `n2`, `fbm`, etc.)
- No comments explaining complex shader math
- Deeply nested functions without proper organization
- Inconsistent spacing and formatting

### 3. **WebGL Shader Differences from PR**
Mockup shader uses:
- Different uniform names (`tD` vs `uTexture` in PR)
- Simplified noise function (`rr` vs more complex noise in some versions)
- Hardcoded magic numbers without explanation

PR #45 uses:
- More semantic names (`tD`, `uT`, `uR`)
- Same shader structure as mockup ✓

### 4. **Canvas Rendering Differences**

**Mockup approach:**
```javascript
const buf=document.createElement('canvas');buf.width=W;buf.height=H;
const bx=buf.getContext('2d');
const tex=new THREE.CanvasTexture(buf);
```
- Uses THREE.js CanvasTexture
- Manually updates texture with `tex.needsUpdate=true`
- Uses THREE.WebGLRenderer

**PR #45 approach:**
```javascript
const bufCanvas = document.createElement('canvas')
bufCanvas.width = w
bufCanvas.height = h
const bufCtx = bufCanvas.getContext('2d')
// ...
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, bufCanvas)
```
- Uses raw WebGL (no THREE.js dependency) ✓
- Direct texture upload ✓
- More lightweight ✓

### 5. **Animation Loop**
Mockup uses THREE.js render loop, PR uses requestAnimationFrame directly.
Both are valid, but PR approach is more lightweight.

### 6. **Missing Features PR Needs**
None identified - PR correctly extracted the core Canvas2D + CRT shader pattern.

### 7. **Performance Issues**
- Mockup redraws entire pages every frame even if static
- No dirty-region tracking
- Packet animation logic creates/destroys objects frequently

## Issues Found in PR #45 Implementation

### 1. **Content Normalization Logic**
```javascript
const normalizeContent = (content) => {
  const safeContent = Array.isArray(content) ? content : []
  return Array.from({ length: ROWS }, (_, rowIndex) => {
    const row = safeContent[rowIndex] ?? []
    const chars = Array.isArray(row) ? row : String(row).split('')
    const normalized = chars.slice(0, COLUMNS)
    while (normalized.length < COLUMNS) normalized.push(' ')
    return normalized
  })
}
```
**Issue:** If row is already array, still converts to string. Should check:
```javascript
const chars = Array.isArray(row) ? row : String(row).split('')
```

### 2. **FPS Counter Position**
Missing CSS for `.teletext-fps` class - it renders but has no styling.

### 3. **Color Cycling**
```javascript
const rowColors = [COLORS.primary, COLORS.secondary, COLORS.tertiary]
const color = rowColors[row % 3]
```
This applies color to entire rows, but mockup pages have more granular color control per text element. This is intentional simplification but differs from mockup.

### 4. **WebGL Error Handling**
No fallback error reporting when CRT init fails. Should notify parent via `onTextureError` prop (which exists but isn't used).

### 5. **Missing Resize Handler**
If container resizes, canvas doesn't adapt. Need ResizeObserver or window resize listener.

## Summary

### Critical (Blocks Deployment)
1. **Mockup syntax error** - missing comma in NODES array

### Important (Should Fix)
2. Content normalization edge case
3. Missing FPS counter styles
4. No resize handling in PR

### Nice to Have
5. Better error reporting in PR
6. Mockup code cleanup (if we want to maintain it)

## Recommendation
1. Fix mockup syntax error immediately
2. Add resize handler to PR
3. Add FPS counter styles to PR
4. Deploy after testing both work
