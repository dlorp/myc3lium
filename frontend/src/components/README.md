# MYC3LIUM Component Library

**Phase 3: Teletext UI Components**

This directory contains 8 reusable React/TypeScript components for building the MYC3LIUM WebUI's teletext-style tactical interface.

## Components

### 1. TeletextPanel

Bordered panel with header using box-drawing characters.

```tsx
import { TeletextPanel } from './components';

<TeletextPanel title="MYC3LIUM ─══─ LATTICE ACTIVE ─══─ 09:57" color="cyan">
  <p>Panel content goes here</p>
</TeletextPanel>
```

**Props:**
- `title: string` - Header text
- `children: ReactNode` - Panel content
- `color?: 'cyan' | 'magenta' | 'yellow' | 'green'` - Border color (default: cyan)

---

### 2. TeletextText

Colored text block with IBM VGA font and optional blink animation.

```tsx
import { TeletextText } from './components';

<TeletextText color="cyan">Active threads: 5</TeletextText>
<TeletextText color="red" blink>ALERT</TeletextText>
```

**Props:**
- `color: 'cyan' | 'magenta' | 'yellow' | 'green' | 'blue' | 'white' | 'gray' | 'red'`
- `children: ReactNode` - Text content
- `blink?: boolean` - Enable blinking animation (default: false)

---

### 3. StatusBar

Horizontal colored bar showing percentage/status with block characters.

```tsx
import { StatusBar } from './components';

<StatusBar value={85} color="cyan" label="GOOD" />
<StatusBar value={45} color="yellow" label="FAIR" />
<StatusBar value={10} color="red" label="CRITICAL" />
```

**Props:**
- `value: number` - Progress value (0-100)
- `color: ColorType` - Bar color
- `label: string` - Status label

**Visual:**
```
GOOD: █████████████▓▓▓▓▓▓▓ (85%)
```

---

### 4. ProgressBar

Compact battery/signal strength indicator with brackets.

```tsx
import { ProgressBar } from './components';

<ProgressBar value={80} max={100} color="green" showPercentage />
```

**Props:**
- `value: number` - Current value
- `max: number` - Maximum value
- `color: ColorType` - Bar color
- `showPercentage?: boolean` - Show percentage text (default: true)

**Visual:**
```
[████████░░] 80%
```

---

### 5. Sparkline

Mini line graph for telemetry data (canvas-based).

```tsx
import { Sparkline } from './components';

const tempData = [12, 15, 18, 14, 20, 22, 19, 24];

<Sparkline data={tempData} width={120} height={30} color="cyan" />
```

**Props:**
- `data: number[]` - Data points to plot
- `width?: number` - Canvas width in pixels (default: 120)
- `height?: number` - Canvas height in pixels (default: 30)
- `color?: ColorType` - Line color (default: cyan)

---

### 6. CommandInput

Bottom command bar with blinking cursor.

```tsx
import { CommandInput } from './components';

const handleCommand = (cmd: string) => {
  console.log('Command:', cmd);
};

<CommandInput 
  onSubmit={handleCommand} 
  placeholder="THREAD LIST | SENSOR GRID" 
/>
```

**Props:**
- `onSubmit: (command: string) => void` - Callback on Enter key
- `placeholder?: string` - Input placeholder text

**Visual:**
```
COMMAND: THREAD LIST | SENSOR GRID ▐▌▐
```

---

### 7. NodeBadge

Node ID + callsign + status indicator.

```tsx
import { NodeBadge } from './components';

const node = {
  id: 'SPORE-01',
  callsign: 'Nexus',
  type: 'SPORE',
  status: 'ONLINE'
};

<NodeBadge node={node} />
```

**Props:**
- `node: { id: string; callsign: string; type: string; status: NodeStatus }`
  - `status: 'ONLINE' | 'DEGRADED' | 'OFFLINE'`

**Visual:**
```
◉ SPORE-01 // "Nexus"     (cyan = online)
◐ HYPHA-03 // "Ranger"    (orange = degraded)
○ RHIZOME-02 // "Stream"  (gray = offline)
```

---

### 8. ThreadIndicator

Connection quality dots (signal strength).

```tsx
import { ThreadIndicator } from './components';

<ThreadIndicator quality="GOOD" />
<ThreadIndicator quality="FAIR" />
<ThreadIndicator quality="DEGRADED" />
```

**Props:**
- `quality: 'GOOD' | 'FAIR' | 'DEGRADED'`

**Visual:**
```
GOOD:      ●●●●● (cyan)
FAIR:      ●●●○○ (yellow)
DEGRADED:  ●○○○○ (orange)
```

---

## Color Palette

All components use the MYC3LIUM color palette:

```css
Primary:
#00FFFF  Cyan     (active, good status)
#FF00FF  Magenta  (warnings, highlights)
#FFFF00  Yellow   (alerts, callsigns)
#00FF00  Green    (status indicators)

Secondary:
#0080FF  Blue     (info panels)
#FFFFFF  White    (primary text)
#808080  Gray     (secondary text, inactive)
#000000  Black    (background)

Accent:
#FF8000  Orange   (degraded status)
#FF0000  Red      (critical alerts)
```

---

## Typography

All components use **IBM VGA 8×16** monospace font.

To ensure proper rendering, add this to your global CSS:

```css
@font-face {
  font-family: 'IBM VGA';
  src: url('/fonts/ibm-vga-8x16.woff2') format('woff2');
}

body {
  font-family: 'IBM VGA', monospace;
}
```

---

## Usage Example

See `src/pages/ComponentDemo.tsx` for a complete demo showcasing all components.

```tsx
import React from 'react';
import {
  TeletextPanel,
  TeletextText,
  StatusBar,
  ProgressBar,
  NodeBadge,
} from './components';

export const MyPage = () => {
  const node = {
    id: 'SPORE-01',
    callsign: 'Nexus',
    type: 'SPORE',
    status: 'ONLINE'
  };

  return (
    <TeletextPanel title="SYSTEM STATUS" color="cyan">
      <NodeBadge node={node} />
      <StatusBar value={85} color="green" label="HEALTH" />
      <ProgressBar value={72} max={100} color="cyan" showPercentage />
      <TeletextText color="white">All systems nominal</TeletextText>
    </TeletextPanel>
  );
};
```

---

## Design Principles

1. **Teletext aesthetic** - BBC Ceefax inspired, 80-column grid
2. **Responsive** - Works on mobile, tablet, desktop
3. **Zero dependencies** - Pure React + vanilla CSS
4. **TypeScript** - Full type safety
5. **Accessible** - Keyboard navigation, high contrast support

---

## Testing

Run tests with:

```bash
npm test
```

Build for production:

```bash
npm run build
```

---

## Contributing

When adding new components:

1. Create `.tsx` file in `src/components/`
2. Export from `src/components/index.ts`
3. Follow existing naming conventions
4. Use MYC3LIUM color palette
5. Add TypeScript types for all props
6. Test on mobile devices

---

**Status:** ✅ Complete (8/8 components)  
**Last Updated:** 2026-03-17
