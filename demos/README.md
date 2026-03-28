# Demoscene Effects Collection

Classic 1990s demoscene effects reimplemented in ASCII + 256-color ANSI.

## Effects

### 1. Plasma Field (`plasma-field.py`)

**Inspired by:** Amiga/DOS demos (1992-1998)

Real-time plasma field visualization using sine wave interference patterns.

**Features:**
- Four sine wave components (classic plasma formula)
- PSX-inspired 256-color palette (blues, purples, pinks)
- ASCII character gradient (density-based)
- Smooth animation (30 FPS target)
- Automatically detects terminal size

**Usage:**
```bash
python3 plasma-field.py
```

**Controls:**
- Ctrl+C: Exit

**Technique:**
```python
P(x,y,t) = sin(x/8 + t) + sin(y/8 + t) + sin((x+y)/16 + t) + sin(sqrt(x²+y²)/8 + t)
```

Multiple sine waves interfere to create organic flowing patterns. Time parameter `t` animates the field. Output normalized to [0,1] and mapped to color palette + ASCII gradient.

---

### 2. 3D Tunnel (`tunnel-effect.py`)

**Inspired by:** Second Reality (Future Crew, 1993)

Real-time 3D tunnel visualization using polar coordinate transformation.

**Features:**
- Polar coordinate lookup tables (optimized)
- Perspective depth mapping (1/distance)
- Animated checkerboard texture scrolling
- Depth-based fog/shading
- Character aspect ratio compensation (2x)

**Usage:**
```bash
python3 tunnel-effect.py
```

**Controls:**
- Ctrl+C: Exit

**Technique:**
```python
# Convert screen coords to polar coords
distance = sqrt(dx² + dy²)
angle = atan2(dy, dx)

# Tunnel depth (perspective)
depth = 32.0 / distance + time

# Texture mapping
u = angle * 4 / π
v = depth

# Checkerboard pattern
pattern = (int(u + time*2) % 2 + int(depth) % 2) % 2

# Depth fog
intensity = 1.0 / (1.0 + distance/20.0)
```

Polar coordinates create radial symmetry. 1/distance creates perspective (far = small, near = large). Scrolling time parameter animates depth. Fog effect simulates atmospheric depth.

---

## Technical Details

### Color Support

Both demos detect color support automatically:
- TTY terminals with `TERM != "dumb"`: 256-color ANSI
- Non-TTY or dumb terminals: ASCII-only fallback

### Performance

**Target:** 30 FPS  
**Actual:** 25-30 FPS on modern hardware (M1 Mac, Intel i7)

Optimizations:
- Pre-calculated lookup tables (tunnel effect)
- Integer color indexing (no floating-point palette lookups)
- Minimal string concatenation per frame

### Aesthetic

**PSX-inspired palette:**
- Plasma: Blues → Purples → Pinks → Whites
- Tunnel: Deep Blues → Cyans → Whites

**ASCII gradients:**
- Plasma: ` .:-=+*#%@` (10 chars, density-based)
- Tunnel: ` .'^\`",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$` (69 chars, fine-grained)

---

## Historical Context

### Demoscene (1980s-1990s)

**Definition:** Underground computer art movement focused on real-time audiovisual demos.

**Key Groups:**
- Future Crew (Second Reality, 1993 — legendary PC demo)
- Triton (Crystal Dream II, 1993 — Amiga)
- Farbrausch (fr-08: .the .product, 2000 — 64KB intro)

**Common Effects:**
1. **Plasma** — Sine wave interference (this collection)
2. **Tunnel** — Polar coordinate 3D (this collection)
3. **Rotozoomer** — Rotation + zoom texture mapping
4. **Metaballs** — Organic blob physics
5. **Fire** — Particle simulation
6. **Starfield** — 3D depth scrolling

**Constraints:**
- Limited hardware (386/486, Amiga 500/1200)
- Real-time rendering (no pre-rendering)
- Size limits (64KB intros, 4KB demos)

**Philosophy:**
> "Constraints breed creativity. Limited hardware forces elegant algorithms."

Modern equivalents: Shadertoy (WebGL), PICO-8 (fantasy console), demoscene is still active (Revision party, Assembly)

---

## Future Effects

**Planned additions:**
- [ ] Rotozoomer (texture rotation + zoom)
- [ ] Metaballs (2D blob simulation)
- [ ] Fire effect (particle upward convection)
- [ ] Starfield (3D depth scrolling)
- [ ] Copper bars (raster effects)
- [ ] Moire patterns (interference grids)

**Advanced:**
- [ ] Raymarching (distance fields, 3D primitives)
- [ ] Voxel landscape (Comanche-style terrain)
- [ ] Particle systems (attraction/repulsion)

---

## References

**Demoscene:**
- [Pouet.net](https://www.pouet.net/) — Demo archive
- [Scene.org](https://www.scene.org/) — File archive
- [Demoscene Wikipedia](https://en.wikipedia.org/wiki/Demoscene)

**Techniques:**
- [Plasma Effect Tutorial](http://lodev.org/cgtutor/plasma.html) — Lode's Computer Graphics Tutorial
- [Tunnel Effect Tutorial](http://lodev.org/cgtutor/tunnel.html) — Polar coordinate technique
- [Second Reality Source Code](https://github.com/mtuomi/SecondReality) — Original assembly

**Modern:**
- [Shadertoy](https://www.shadertoy.com/) — WebGL demos
- [PICO-8](https://www.lexaloffle.com/pico-8.php) — Fantasy console
- [Revision](https://2023.revision-party.net/) — Annual demoparty

---

## License

MIT License — Classic techniques, modern implementation.

**Attribution:**
- Plasma field: Classic sine wave interference (public domain algorithm)
- Tunnel effect: Inspired by Second Reality (Future Crew, 1993)
- PSX palette: Original (dlorp, 2026)

---

**Session:** Deep Work Session 3/6 (CREATIVE)  
**Date:** 2026-03-28  
**Time:** 02:00 AM AKDT
