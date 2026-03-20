# MYC3LIUM LOGO IMPLEMENTATION GUIDE
**Technical Reference for Developers**  
Version 1.0 | 2026-03-17

---

## I. LOGO VARIANT SELECTION

### Scale Breakpoints (Auto-select based on display size)

| Display Size | File | Contents | Use Case |
|--------------|------|----------|----------|
| **≥256px** | `myc3lium-logo-512px.svg` | M + 3 + branching pattern (60% opacity) | Hero sections, landing pages, print materials |
| **≥128px <256px** | `myc3lium-logo-256px.svg` | M + 3 + branching pattern | Standard web headers, about pages |
| **≥64px <128px** | `myc3lium-logo-128px.svg` | M + 3 solid (no branching) | Navigation bars, mobile headers |
| **≥32px <64px** | `myc3lium-logo-64px.svg` | M + simplified 3 (thicker stroke) | Favicons (large), app icons, social media avatars |
| **≥16px <32px** | `myc3lium-logo-32px.svg` | M only (micro-mark, no 3) | Favicons (standard), browser tabs |
| **<16px** | `myc3lium-logo-16px.svg` | M only (extreme micro-mark) | Favicons (small), taskbar icons |

### Decision Tree

```
Display width ≥ 256px?
├─ YES → Use 512px or 256px variant (full macro with branching)
└─ NO
   └─ Display width ≥ 128px?
      ├─ YES → Use 128px variant (M + 3 solid)
      └─ NO
         └─ Display width ≥ 64px?
            ├─ YES → Use 64px variant (simplified 3)
            └─ NO → Use 32px or 16px variant (M only)
```

---

## II. CSS INTEGRATION

### Responsive Logo Implementation

```css
/* CSS Variables (include in :root or theme file) */
:root {
  --myc3lium-substrate: #3D3630;
  --myc3lium-hyphae: #FF6B00;
  --myc3lium-void: #0A0A0A;
  --myc3lium-dormant: #636764;
  --myc3lium-selection: #50D8D7;
}

/* Logo container with automatic variant switching */
.myc3lium-logo {
  display: inline-block;
  width: 100%;
  max-width: 512px;
  height: auto;
  background-image: url('myc3lium-logo-512px.svg');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

/* Responsive breakpoints */
@media (max-width: 255px) {
  .myc3lium-logo {
    background-image: url('myc3lium-logo-128px.svg');
  }
}

@media (max-width: 127px) {
  .myc3lium-logo {
    background-image: url('myc3lium-logo-64px.svg');
  }
}

@media (max-width: 63px) {
  .myc3lium-logo {
    background-image: url('myc3lium-logo-32px.svg');
  }
}

/* Alternative: img tag with srcset (recommended) */
.myc3lium-logo-img {
  display: block;
  width: 100%;
  height: auto;
}
```

### HTML Implementation (Recommended)

```html
<!-- Responsive logo with automatic variant selection -->
<img 
  src="myc3lium-logo-512px.svg" 
  alt="MYC3LIUM"
  class="myc3lium-logo-img"
  width="512"
  height="512"
/>

<!-- Fixed-size logo (e.g., nav bar at 128px) -->
<img 
  src="myc3lium-logo-128px.svg" 
  alt="MYC3LIUM"
  width="128"
  height="128"
/>

<!-- Favicon links (see Section IV) -->
```

### Inline SVG (for maximum control)

```html
<!-- Embed SVG directly for CSS/JS manipulation -->
<div class="logo-container">
  <?xml version="1.0" encoding="UTF-8"?>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
    <!-- Paste contents of myc3lium-logo-512px.svg here -->
  </svg>
</div>

<style>
  .logo-container svg {
    width: 100%;
    height: auto;
    max-width: 512px;
  }
  
  /* Hover effect: glow on "3" */
  .logo-container:hover path[stroke="#FF6B00"] {
    filter: drop-shadow(0 0 8px rgba(255, 107, 0, 0.8));
    transition: filter 150ms ease-out;
  }
</style>
```

---

## III. USAGE RULES

### Minimum Sizes

| Context | Minimum Size | Recommended Variant |
|---------|--------------|---------------------|
| **Print** | 25mm (≈94px) | 128px or 256px |
| **Web (desktop)** | 64px | 128px |
| **Web (mobile)** | 48px | 64px |
| **App icon** | 32px | 32px (M only) |
| **Favicon** | 16px | 16px (M only) |

**Rule:** Never display logo below 16×16px. At extreme micro sizes, use text "MYC3LIUM" instead.

### Safe Zone / Clearance

**Clearance = 10% of logo canvas size**

| Logo Size | Clearance (all sides) |
|-----------|----------------------|
| 512px | 51.2px (≈51px) |
| 256px | 25.6px (≈26px) |
| 128px | 12.8px (≈13px) |
| 64px | 6.4px (≈6px) |
| 32px | 3.2px (≈3px) |
| 16px | 1.6px (≈2px) |

**Rule:** Maintain minimum clearance around logo. No text, graphics, or UI elements within safe zone.

**Example CSS:**

```css
.logo-wrapper {
  padding: 51px; /* 10% clearance for 512px logo */
}
```

### Background Requirements

**Primary:** Logo designed for **The Void (#0A0A0A)** background.

**Acceptable alternatives:**
- Pure black `#000000` (minimal difference)
- Dark gray `#1A1A1A` to `#0F0F0F` (contrast retained)

**NEVER use on:**
- White or light backgrounds (invisible Substrate Brown)
- Saturated color backgrounds (color clash with Hyphae Orange)
- Patterned backgrounds (visual noise)

**Light background exception:**  
If logo MUST appear on light background, use inverted variant (create manually):
- M-frame: `#C9C3CC` (inverted Substrate Brown)
- "3": `#FF6B00` (Hyphae Orange unchanged - pops on light)
- Background: `#F5F5F5` (near-white)

### Prohibited Modifications

**DO NOT:**
- ❌ Change colors (except approved light-background inversion)
- ❌ Rotate logo (distorts 90° CW rotation geometry)
- ❌ Add effects (gradients, shadows, outlines) except approved glow
- ❌ Stretch or skew (breaks grid alignment)
- ❌ Crop into partial logo
- ❌ Rearrange M and "3" elements
- ❌ Use branching pattern outside logo context

**ALLOWED:**
- ✅ Scale proportionally (maintain aspect ratio)
- ✅ Subtle glow on hover (Hyphae Orange: `0 0 8px rgba(255,107,0,0.6)`)
- ✅ Opacity adjustments for loading states (fade-in)
- ✅ CSS filters: grayscale (for disabled state)

---

## IV. EXPORT FORMATS & GENERATION

### Favicon Package (Multi-Resolution)

**Generate from SVG sources:**

```bash
# Using ImageMagick (install via: brew install imagemagick)

# favicon.ico (multi-size ICO file)
convert \
  myc3lium-logo-16px.svg \
  myc3lium-logo-32px.svg \
  myc3lium-logo-64px.svg \
  -colors 256 favicon.ico

# PNG exports for various devices
convert myc3lium-logo-16px.svg -resize 16x16 favicon-16x16.png
convert myc3lium-logo-32px.svg -resize 32x32 favicon-32x32.png
convert myc3lium-logo-64px.svg -resize 64x64 favicon-64x64.png
convert myc3lium-logo-128px.svg -resize 128x128 apple-touch-icon.png
convert myc3lium-logo-256px.svg -resize 192x192 android-chrome-192x192.png
convert myc3lium-logo-512px.svg -resize 512x512 android-chrome-512x512.png
```

### HTML Favicon Links

```html
<!-- Favicon declarations (place in <head>) -->
<link rel="icon" type="image/svg+xml" href="/myc3lium-logo-32px.svg">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="128x128" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">

<!-- Open Graph / Social Media -->
<meta property="og:image" content="/android-chrome-512x512.png">
<meta property="og:image:width" content="512">
<meta property="og:image:height" content="512">
```

### site.webmanifest (PWA Support)

```json
{
  "name": "MYC3LIUM",
  "short_name": "MYC3LIUM",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "theme_color": "#0A0A0A",
  "background_color": "#0A0A0A",
  "display": "standalone"
}
```

### Print Export (High-Resolution)

```bash
# 300 DPI print export (A4 size: 210mm × 297mm = 2480px × 3508px)
# Logo at 100mm width = 1181px at 300 DPI

convert myc3lium-logo-512px.svg -resize 1181x1181 -density 300 myc3lium-logo-print.png

# PDF export (vector, scalable)
# macOS: use built-in SVG→PDF converter
/System/Library/Printers/Libraries/convert -f myc3lium-logo-512px.svg -o myc3lium-logo.pdf

# Linux: use Inkscape or rsvg-convert
rsvg-convert -f pdf -o myc3lium-logo.pdf myc3lium-logo-512px.svg
```

---

## V. APPLICATION EXAMPLES

### Example 1: Website Header (Desktop)

```html
<header class="site-header">
  <div class="logo-container">
    <a href="/">
      <img 
        src="/myc3lium-logo-128px.svg" 
        alt="MYC3LIUM - Return to homepage"
        width="128"
        height="128"
      />
    </a>
  </div>
  <nav><!-- navigation items --></nav>
</header>

<style>
  .site-header {
    background: var(--myc3lium-void);
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 40px;
  }
  
  .logo-container {
    padding: 13px; /* 10% of 128px */
  }
  
  .logo-container img {
    display: block;
    width: 128px;
    height: 128px;
  }
  
  .logo-container a:hover img {
    filter: drop-shadow(0 0 8px rgba(255, 107, 0, 0.6));
    transition: filter 150ms ease-out;
  }
</style>
```

### Example 2: Hero Section (Full-Width)

```html
<section class="hero">
  <div class="hero-logo">
    <img 
      src="/myc3lium-logo-512px.svg" 
      alt="MYC3LIUM"
      width="512"
      height="512"
    />
  </div>
  <h1>Decentralized Mesh Network</h1>
</section>

<style>
  .hero {
    background: var(--myc3lium-void);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 51px; /* 10% clearance */
  }
  
  .hero-logo {
    max-width: 512px;
    width: 100%;
    margin-bottom: 40px;
  }
  
  .hero-logo img {
    width: 100%;
    height: auto;
  }
  
  @media (max-width: 768px) {
    .hero-logo {
      max-width: 256px;
    }
    
    .hero-logo img {
      content: url('/myc3lium-logo-256px.svg');
    }
  }
</style>
```

### Example 3: Loading Spinner (Animated)

```html
<div class="loading-spinner">
  <img 
    src="/myc3lium-logo-128px.svg" 
    alt="Loading..."
    class="spinner-logo"
  />
</div>

<style>
  .loading-spinner {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
  }
  
  .spinner-logo {
    width: 128px;
    height: 128px;
    animation: pulse-glow 1200ms ease-in-out infinite;
  }
  
  @keyframes pulse-glow {
    0%, 100% {
      filter: drop-shadow(0 0 4px rgba(255, 107, 0, 0.3));
      opacity: 0.7;
    }
    50% {
      filter: drop-shadow(0 0 12px rgba(255, 107, 0, 0.8));
      opacity: 1;
    }
  }
</style>
```

### Example 4: React Component (TypeScript)

```tsx
import React from 'react';

interface MYC3LIUMLogoProps {
  size?: 16 | 32 | 64 | 128 | 256 | 512;
  className?: string;
  glow?: boolean;
}

const logoFiles: Record<number, string> = {
  16: '/myc3lium-logo-16px.svg',
  32: '/myc3lium-logo-32px.svg',
  64: '/myc3lium-logo-64px.svg',
  128: '/myc3lium-logo-128px.svg',
  256: '/myc3lium-logo-256px.svg',
  512: '/myc3lium-logo-512px.svg',
};

export const MYC3LIUMLogo: React.FC<MYC3LIUMLogoProps> = ({
  size = 128,
  className = '',
  glow = false,
}) => {
  const clearance = Math.round(size * 0.1); // 10% safe zone
  
  return (
    <div 
      className={`myc3lium-logo-wrapper ${className}`}
      style={{ padding: `${clearance}px` }}
    >
      <img
        src={logoFiles[size]}
        alt="MYC3LIUM"
        width={size}
        height={size}
        style={{
          display: 'block',
          filter: glow ? 'drop-shadow(0 0 8px rgba(255, 107, 0, 0.6))' : 'none',
          transition: 'filter 150ms ease-out',
        }}
      />
    </div>
  );
};

// Usage:
// <MYC3LIUMLogo size={128} glow={true} />
```

---

## VI. QUICK REFERENCE FOR DEVELOPERS

### Checklist: Logo Implementation

- [ ] **Select correct variant** based on display size (see Section I)
- [ ] **Maintain 10% clearance** around logo (see safe zone rules)
- [ ] **Use approved background** (#0A0A0A or dark variants)
- [ ] **Set explicit width/height** in HTML for performance
- [ ] **Include alt text** for accessibility
- [ ] **Test at all breakpoints** (responsive design)
- [ ] **Verify contrast** if using non-standard background
- [ ] **Generate favicon package** for web deployment
- [ ] **No unauthorized modifications** (colors, rotation, effects)

### File Naming Convention

```
myc3lium-logo-{SIZE}px.svg        // Standard variants
myc3lium-logo-spec.svg             // Technical specification drawing
favicon-{SIZE}x{SIZE}.png          // Raster exports for favicons
android-chrome-{SIZE}x{SIZE}.png   // Android PWA icons
apple-touch-icon.png               // iOS home screen icon (128×128)
```

### Color Variables (Copy-Paste)

```css
/* CSS */
--myc3lium-substrate: #3D3630;
--myc3lium-hyphae: #FF6B00;
--myc3lium-void: #0A0A0A;
--myc3lium-dormant: #636764;
--myc3lium-selection: #50D8D7;
```

```scss
/* Sass */
$myc3lium-substrate: #3D3630;
$myc3lium-hyphae: #FF6B00;
$myc3lium-void: #0A0A0A;
$myc3lium-dormant: #636764;
$myc3lium-selection: #50D8D7;
```

```javascript
// JavaScript/TypeScript
export const MYC3LIUM_COLORS = {
  substrate: '#3D3630',
  hyphae: '#FF6B00',
  void: '#0A0A0A',
  dormant: '#636764',
  selection: '#50D8D7',
} as const;
```

### Performance Tips

1. **Prefer SVG over PNG** for web (smaller file size, scalable)
2. **Inline small variants** (<2KB) to reduce HTTP requests
3. **Preload hero logos** for faster LCP:
   ```html
   <link rel="preload" as="image" href="/myc3lium-logo-512px.svg">
   ```
4. **Use CSS containment** for logo containers:
   ```css
   .logo-container {
     contain: layout style paint;
   }
   ```

---

## VII. TECHNICAL SPECIFICATIONS SUMMARY

| Property | Value |
|----------|-------|
| **Grid System** | 16px base unit, 64px major grid |
| **Safe Zone** | 10% of canvas size (all sides) |
| **Aspect Ratio** | 1:1 (square) |
| **M Stem Width** | 64px (at 512px scale) |
| **"3" Stroke Width** | 20px (512px), 10px (256px), 6px (128px), 4px (64px) |
| **Chamfer Angle** | 45° |
| **Rotation Geometry** | 90° clockwise (applied to "3" element) |
| **viewBox** | `0 0 {SIZE} {SIZE}` (matches canvas) |
| **File Format** | SVG 1.1, UTF-8 encoding |
| **Branching Pattern** | Present at ≥256px only, 60% opacity |

---

**END OF IMPLEMENTATION GUIDE**

*For design questions or logo variant requests, refer to the complete color system at `/tmp/myc3lium-color-system.md` or consult the technical spec drawing `myc3lium-logo-spec.svg`.*
