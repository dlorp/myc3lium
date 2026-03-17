/**
 * CRT Shader Effect Presets
 * 
 * Curated configurations for different aesthetic targets.
 * Underground polish, tested stable at 60fps.
 */

export const CRT_PRESETS = {
  /**
   * DEFAULT - Balanced underground aesthetic
   * All effects enabled, tuned for teletext display
   */
  default: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: true,
    enableFlicker: true,
    chromaticAmount: 0.001,
    bloomStrength: 0.45,
    phosphorDecay: 0.88,
    noiseAmount: 0.04,
    flickerAmount: 0.012,
  },

  /**
   * BASEMENT - Maximum demoscene vibes
   * Cranked effects for 3am coding sessions
   */
  basement: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: true,
    enableFlicker: true,
    chromaticAmount: 0.0018,
    bloomStrength: 0.62,
    phosphorDecay: 0.92,
    noiseAmount: 0.07,
    flickerAmount: 0.022,
  },

  /**
   * CLEAN - Minimal effects, maximum readability
   * Subtle CRT feel without distraction
   */
  clean: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: false,
    enableNoise: false,
    enableFlicker: false,
    chromaticAmount: 0.0005,
    bloomStrength: 0.28,
    phosphorDecay: 0.0,
    noiseAmount: 0.0,
    flickerAmount: 0.0,
  },

  /**
   * WAREZ - 90s BBS scroller aesthetic
   * Phosphor trails, heavy glow, VHS noise
   */
  warez: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: true,
    enableFlicker: true,
    chromaticAmount: 0.0014,
    bloomStrength: 0.55,
    phosphorDecay: 0.94,
    noiseAmount: 0.08,
    flickerAmount: 0.018,
  },

  /**
   * BROADCAST - Television signal aesthetic
   * Moderate noise, scan artifacts, subtle decay
   */
  broadcast: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: true,
    enableFlicker: true,
    chromaticAmount: 0.0012,
    bloomStrength: 0.38,
    phosphorDecay: 0.85,
    noiseAmount: 0.05,
    flickerAmount: 0.015,
  },

  /**
   * LABORATORY - Clinical monitoring display
   * Sharp, stable, minimal bloom, no flicker
   */
  laboratory: {
    enableChromatic: false,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: false,
    enableFlicker: false,
    chromaticAmount: 0.0,
    bloomStrength: 0.22,
    phosphorDecay: 0.82,
    noiseAmount: 0.0,
    flickerAmount: 0.0,
  },

  /**
   * EPILEPSY_SAFE - No flicker, no rapid changes
   * Accessibility-first configuration
   */
  epilepsySafe: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: false,
    enableNoise: false,
    enableFlicker: false,
    chromaticAmount: 0.0008,
    bloomStrength: 0.35,
    phosphorDecay: 0.0,
    noiseAmount: 0.0,
    flickerAmount: 0.0,
  },

  /**
   * PERFORMANCE - Low-end hardware optimization
   * Minimal GPU load, skip expensive effects
   */
  performance: {
    enableChromatic: false,
    enableBloom: false,
    enablePhosphor: false,
    enableNoise: false,
    enableFlicker: false,
    chromaticAmount: 0.0,
    bloomStrength: 0.0,
    phosphorDecay: 0.0,
    noiseAmount: 0.0,
    flickerAmount: 0.0,
  },

  /**
   * AMBER_GLOW - Emphasize retro terminal warmth
   * Heavy bloom, subtle trails, minimal noise
   */
  amberGlow: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: true,
    enableFlicker: true,
    chromaticAmount: 0.0006,
    bloomStrength: 0.68,
    phosphorDecay: 0.86,
    noiseAmount: 0.03,
    flickerAmount: 0.008,
  },

  /**
   * GHOST_IN_THE_SHELL - Cyberpunk terminal aesthetic
   * Heavy phosphor trails, chromatic aberration, flicker
   */
  cyberpunk: {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: true,
    enableFlicker: true,
    chromaticAmount: 0.0022,
    bloomStrength: 0.58,
    phosphorDecay: 0.96,
    noiseAmount: 0.06,
    flickerAmount: 0.025,
  },

  /**
   * OSCILLOSCOPE - Scientific instrument display
   * Phosphor trails prominent, minimal chromatic, no flicker
   */
  oscilloscope: {
    enableChromatic: false,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: false,
    enableFlicker: false,
    chromaticAmount: 0.0,
    bloomStrength: 0.42,
    phosphorDecay: 0.94,
    noiseAmount: 0.0,
    flickerAmount: 0.0,
  },
}

/**
 * Get preset by name (case-insensitive)
 * @param {string} name - Preset name
 * @returns {object} Effect configuration
 */
export function getPreset(name) {
  const key = name.toLowerCase()
  return CRT_PRESETS[key] || CRT_PRESETS.default
}

/**
 * List available preset names
 * @returns {string[]} Array of preset names
 */
export function listPresets() {
  return Object.keys(CRT_PRESETS)
}

export default CRT_PRESETS
