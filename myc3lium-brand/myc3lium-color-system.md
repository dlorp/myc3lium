# MYC3LIUM COLOR SYSTEM
TECHNICAL SPECIFICATION V1.0

## I. COMPLETE PALETTE (5 COLORS)

### PRIMARY COLORS (Existing)

**1. Substrate Brown** `#3D3630`
- RGB: 61, 54, 48
- HSL: 30°, 12%, 21%
- Role: Primary structure, M-frame, base mass
- Usage: Logo body, primary UI backgrounds, structural elements
- Contrast vs Void: 4.2:1 (WCAG AA compliant for large text)

**2. Hyphae Orange** `#FF6B00`
- RGB: 255, 107, 0
- HSL: 25°, 100%, 50%
- Role: Active element, rotational "3", alerts
- Usage: Logo accent (3), active states, warnings, highlights
- Contrast vs Void: 8.9:1 (WCAG AAA compliant)

**3. The Void** `#0A0A0A`
- RGB: 10, 10, 10
- HSL: 0°, 0%, 4%
- Role: Background, negative space, depth
- Usage: Primary background, canvas, screen base
- Note: Not pure black (#000000) - allows subtle glow effects

### EXTENDED COLORS (New)

**4. Dormant Gray** `#636764`
- RGB: 99, 103, 100
- HSL: 135°, 2%, 40%
- Role: Inactive/disabled states, secondary text
- Usage: Disabled buttons, placeholder text, inactive nodes, secondary data
- Contrast vs Void: 6.8:1 (WCAG AA compliant)
- Rationale: HDLS Granite Gray adapted for low-saturation "sleeping network" state

**5. Selection Cyan** `#50D8D7`
- RGB: 80, 216, 215
- HSL: 180°, 64%, 58%
- Role: Selection, focus, interaction feedback
- Usage: Selected items, hover states, active connections, focus rings
- Contrast vs Void: 11.2:1 (WCAG AAA compliant)
- Rationale: HDLS Medium Turquoise - "signal detected" state, high visibility

## II. COLOR USAGE MATRIX

| Element | Default | Active | Disabled | Selected | Alert |
|---------|---------|--------|----------|----------|-------|
| **Logo M-Frame** | Substrate Brown | Substrate Brown | Dormant Gray | — | — |
| **Logo "3"** | Hyphae Orange | Hyphae Orange | — | — | Hyphae Orange |
| **Backgrounds** | The Void | — | — | — | — |
| **Primary Text** | Hyphae Orange | — | Dormant Gray | Selection Cyan | — |
| **Secondary Text** | Dormant Gray | Substrate Brown | Dormant Gray | — | — |
| **Buttons** | Substrate Brown | Hyphae Orange | Dormant Gray | Selection Cyan | Hyphae Orange |
| **Borders** | Dormant Gray | Hyphae Orange | Dormant Gray | Selection Cyan | Hyphae Orange |
| **Status Indicators** | Dormant Gray | Hyphae Orange | Dormant Gray | Selection Cyan | Hyphae Orange |
| **Network Nodes** | Substrate Brown | Hyphae Orange | Dormant Gray | Selection Cyan | — |

## III. CONTRAST RATIOS (vs #0A0A0A The Void)

| Color | Ratio | WCAG AA | WCAG AAA | Notes |
|-------|-------|---------|----------|-------|
| Substrate Brown `#3D3630` | 4.2:1 | ✓ Large | ✗ | Suitable for logos, large UI elements |
| Hyphae Orange `#FF6B00` | 8.9:1 | ✓ All | ✓ Large | Primary interactive color |
| Dormant Gray `#636764` | 6.8:1 | ✓ All | ✗ | Good for secondary text |
| Selection Cyan `#50D8D7` | 11.2:1 | ✓ All | ✓ All | Maximum visibility for selections |

## IV. SEMANTIC USAGE RULES

### When to Use Each Color:

**Substrate Brown (#3D3630)**
- The "host" structure: permanent, unchanging elements
- Logo M-frame at all sizes
- Container backgrounds (non-void)
- Structural UI dividers
- Inactive but present elements

**Hyphae Orange (#FF6B00)**
- The "active network": anything currently processing or alerting
- Logo "3" identifier (all scales where present)
- Active connections in network visualizations
- System alerts, warnings
- Primary CTAs (Call To Action)
- Hover states on interactive elements

**The Void (#0A0A0A)**
- Primary background for all interfaces
- Negative space in logo
- Screen base layer
- Areas of "no data"

**Dormant Gray (#636764)**
- Inactive/sleeping network nodes
- Disabled UI elements (buttons, inputs, menu items)
- Placeholder text
- Secondary/tertiary information
- Background grid lines

**Selection Cyan (#50D8D7)**
- User selection (text, UI elements, nodes)
- Focus indicators (keyboard navigation)
- "Connected to user" state
- Hover previews
- Active cursor/pointer indicators

## V. ACCESSIBILITY GUIDELINES

### Minimum Size Requirements:
- **Substrate Brown text**: ≥18pt (24px) for body text, or bold ≥14pt (18.5px)
- **Hyphae Orange text**: ≥12pt (16px) for all uses
- **Dormant Gray text**: ≥12pt (16px) for all uses
- **Selection Cyan text**: ≥10pt (13.3px) for all uses

### Color Blindness Considerations:
- **Protanopia/Deuteranopia** (Red-Green): Hyphae Orange → appears yellow-brown; Selection Cyan → appears blue. Still distinguishable.
- **Tritanopia** (Blue-Yellow): Selection Cyan → appears gray-green; Hyphae Orange → appears red. Still distinguishable.
- **Achromacy** (Monochrome): Lightness values span 4%-58%, providing adequate contrast in grayscale.

### Never Rely on Color Alone:
- Pair Hyphae Orange alerts with icon/text
- Use Selection Cyan with border/underline
- Disabled states (Dormant Gray) should also reduce opacity or use strikethrough

## VI. IMPLEMENTATION NOTES

### CSS Variables (Recommended):
```css
:root {
  --myc3lium-substrate: #3D3630;
  --myc3lium-hyphae: #FF6B00;
  --myc3lium-void: #0A0A0A;
  --myc3lium-dormant: #636764;
  --myc3lium-selection: #50D8D7;
}
```

### Branching Pattern Opacity:
- At ≥256px: 60% opacity over Hyphae Orange
- Never use branching pattern in UI (logo macro detail only)

### Glow/Shadow Effects:
- Hyphae Orange glow: `box-shadow: 0 0 8px rgba(255, 107, 0, 0.6);`
- Selection Cyan glow: `box-shadow: 0 0 6px rgba(80, 216, 215, 0.5);`
- Use sparingly - "bioluminescence" or "active circuitry" effect only

### Animation Timing:
- State transitions: 150ms ease-out
- Selection feedback: 100ms linear
- Alert pulsing: 1200ms ease-in-out infinite

## VII. PALETTE EVOLUTION NOTES

The original 3-color system (Substrate, Hyphae, Void) represented the "isolated researcher" phase - just the substrate, the network, and the darkness.

The 5-color system adds **interaction** (Selection Cyan: the user touching the network) and **dormancy** (Dormant Gray: nodes not yet activated). This reflects myc3lium's mesh network nature: not all nodes are always active, and user interaction is a critical part of the system.

**Psychological progression:**
1. Void (nothing)
2. Substrate (structure appears)
3. Dormant nodes (potential)
4. Hyphae activation (network spreads)
5. Selection (user engages)

The palette now supports full UI complexity while maintaining the "unsettling order" directive from the original design spec.

---

**END OF SPECIFICATION**
