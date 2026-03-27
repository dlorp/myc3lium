# Procedural Low-Poly Terrain Research - 2026-03-25

## Academic Paper: Procedural Low-Poly Terrain with Terracing

**Source:** arXiv:2505.09350 [cs.GR] - May 2025

### Problem Statement
Traditional heightmap-based terrain uses fixed vertex grids with triangles connecting indexed vertices. Creates smooth, continuous surfaces but:
- Lacks distinct low-poly aesthetic
- Grid structure too regular
- Not suitable for stylized/retro game visuals

### Proposed Solution
Generate random, **terraced** low-poly terrain with:
- Distinct biome regions
- Vegetation placement
- Chaotic, non-grid appearance

**Key insight:** Move away from regular grids toward **terracing** (stepped elevation levels) for PSX/low-poly look.

### Implementation Strategy (inferred)
- Height quantization into discrete levels (terraces)
- Irregular mesh generation (not grid-based)
- Biome-based texture/color variation
- Procedural vegetation scatter

**Relevance to dlorp's projects:**
- `psx-terra` - Direct application
- `gba-terra` - Downscaled version
- `ascii-terrain` - Text-mode terracing
- `t3rra1n` - ARG world generation

### Related Techniques to Research
1. Voronoi diagram terrain (irregular cells)
2. Marching squares for contour extraction
3. Delaunay triangulation for low-poly meshes
4. Height quantization algorithms
5. Biome transition blending

---

## PSX-Style Aesthetic Notes

From Reddit thread (r/godot - June 2024):
- Procedural worldmap with PSX inspiration
- Mount & Blade / Cossacks influence
- Focus on **chunky, faceted geometry**
- Limited color palettes per region

**Visual targets:**
- PS1 polygon jitter (affine texture mapping)
- Vertex snapping (no sub-pixel precision)
- Baked vertex colors (no real-time lighting)
- Low polygon density with visible facets
- Dithered color transitions
- 240p-style pixelation

---

## Terrain Generation Pipeline (Proposed)

1. **Base Noise**
   - Perlin/Simplex for height variation
   - Multiple octaves for detail levels

2. **Quantization**
   - Round heights to discrete terrace levels
   - Creates "stepped" appearance

3. **Mesh Generation**
   - Marching squares on quantized height
   - Generate contour polygons per level
   - Extrude walls between levels

4. **Biome Assignment**
   - Moisture + temperature maps
   - Discrete regions (no smooth blending)
   - Per-biome color palettes

5. **Vegetation Scatter**
   - Spawn on flat terrace surfaces
   - Simple billboard sprites or low-poly models
   - Density based on biome type

6. **PSX Post-Processing**
   - Vertex jitter shader
   - Color quantization (16-bit RGB → PSX palette)
   - Dithering for gradients

---

## Tools to Build
- Terraced heightmap generator (Rust/C++)
- Low-poly mesh simplifier
- PSX-style renderer (Three.js or raw WebGL)
- Biome painter (visual tool)

---

**Session ID:** main (deep work rotation 1/6)
**Sources:** arXiv:2505.09350, r/godot PSX worldmap thread
