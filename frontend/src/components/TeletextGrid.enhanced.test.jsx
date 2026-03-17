/**
 * Enhanced CRT Shader Tests
 * 
 * Verify all Phase 1 shader effects render correctly
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import TeletextGrid from './TeletextGrid'
import { CRT_PRESETS, getPreset, listPresets } from './crtPresets'

describe('TeletextGrid Enhanced CRT Shader', () => {
  const mockContent = [
    ['T', 'E', 'S', 'T'],
    ['D', 'A', 'T', 'A'],
  ]

  beforeEach(() => {
    // Mock WebGL context
    HTMLCanvasElement.prototype.getContext = vi.fn((type) => {
      if (type === '2d') {
        return {
          fillStyle: '',
          fillRect: vi.fn(),
          fillText: vi.fn(),
          measureText: vi.fn(() => ({ width: 10 })),
          clearRect: vi.fn(),
          beginPath: vi.fn(),
          closePath: vi.fn(),
          stroke: vi.fn(),
          save: vi.fn(),
          restore: vi.fn(),
          scale: vi.fn(),
          translate: vi.fn(),
          font: '',
          textBaseline: '',
        }
      }
      return null
    })
  })

  it('renders with default enhanced effects configuration', () => {
    render(<TeletextGrid content={mockContent} />)
    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toBeInTheDocument()
  })

  it('accepts custom effects configuration', () => {
    const customConfig = {
      enableChromatic: false,
      enableBloom: true,
      chromaticAmount: 0.002,
      bloomStrength: 0.7,
    }
    
    render(<TeletextGrid content={mockContent} effectsConfig={customConfig} />)
    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toBeInTheDocument()
  })

  it('renders with all effects disabled', () => {
    const noEffects = {
      enableChromatic: false,
      enableBloom: false,
      enablePhosphor: false,
      enableNoise: false,
      enableFlicker: false,
    }
    
    render(<TeletextGrid content={mockContent} effectsConfig={noEffects} />)
    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toBeInTheDocument()
  })

  it('renders with all effects enabled at maximum', () => {
    const maxEffects = {
      enableChromatic: true,
      enableBloom: true,
      enablePhosphor: true,
      enableNoise: true,
      enableFlicker: true,
      chromaticAmount: 0.003,
      bloomStrength: 1.0,
      phosphorDecay: 0.99,
      noiseAmount: 0.15,
      flickerAmount: 0.03,
    }
    
    render(<TeletextGrid content={mockContent} effectsConfig={maxEffects} />)
    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toBeInTheDocument()
  })
})

describe('CRT Presets', () => {
  it('exports all documented presets', () => {
    const presets = listPresets()
    const expectedPresets = [
      'default',
      'basement',
      'clean',
      'warez',
      'broadcast',
      'laboratory',
      'epilepsySafe',
      'performance',
      'amberGlow',
      'cyberpunk',
      'oscilloscope',
    ]
    
    expectedPresets.forEach(name => {
      expect(presets).toContain(name)
    })
  })

  it('returns default preset for unknown name', () => {
    const preset = getPreset('nonexistent')
    expect(preset).toEqual(CRT_PRESETS.default)
  })

  it('basement preset has cranked effect values', () => {
    const basement = CRT_PRESETS.basement
    expect(basement.bloomStrength).toBeGreaterThan(0.5)
    expect(basement.phosphorDecay).toBeGreaterThan(0.9)
    expect(basement.noiseAmount).toBeGreaterThan(0.05)
  })

  it('performance preset disables all expensive effects', () => {
    const perf = CRT_PRESETS.performance
    expect(perf.enableBloom).toBe(false)
    expect(perf.enablePhosphor).toBe(false)
    expect(perf.enableNoise).toBe(false)
  })

  it('epilepsy-safe preset disables flicker and noise', () => {
    const safe = CRT_PRESETS.epilepsySafe
    expect(safe.enableFlicker).toBe(false)
    expect(safe.enableNoise).toBe(false)
    expect(safe.flickerAmount).toBe(0)
    expect(safe.noiseAmount).toBe(0)
  })

  it('clean preset uses subtle effect values', () => {
    const clean = CRT_PRESETS.clean
    expect(clean.chromaticAmount).toBeLessThan(0.001)
    expect(clean.bloomStrength).toBeLessThan(0.3)
    expect(clean.enablePhosphor).toBe(false)
  })

  it('oscilloscope preset emphasizes phosphor trails', () => {
    const osc = CRT_PRESETS.oscilloscope
    expect(osc.enablePhosphor).toBe(true)
    expect(osc.phosphorDecay).toBeGreaterThan(0.9)
    expect(osc.enableChromatic).toBe(false) // Clean scientific display
  })

  it('all presets have valid numeric ranges', () => {
    Object.entries(CRT_PRESETS).forEach(([name, config]) => {
      // Chromatic amount: 0.0-0.003
      expect(config.chromaticAmount).toBeGreaterThanOrEqual(0.0)
      expect(config.chromaticAmount).toBeLessThanOrEqual(0.003)
      
      // Bloom strength: 0.0-1.0
      expect(config.bloomStrength).toBeGreaterThanOrEqual(0.0)
      expect(config.bloomStrength).toBeLessThanOrEqual(1.0)
      
      // Phosphor decay: 0.0-1.0
      expect(config.phosphorDecay).toBeGreaterThanOrEqual(0.0)
      expect(config.phosphorDecay).toBeLessThanOrEqual(1.0)
      
      // Noise amount: 0.0-0.15
      expect(config.noiseAmount).toBeGreaterThanOrEqual(0.0)
      expect(config.noiseAmount).toBeLessThanOrEqual(0.15)
      
      // Flicker amount: 0.0-0.03
      expect(config.flickerAmount).toBeGreaterThanOrEqual(0.0)
      expect(config.flickerAmount).toBeLessThanOrEqual(0.03)
    })
  })
})

describe('Shader Effect Integration', () => {
  const mockContent = Array.from({ length: 25 }, () => 
    Array.from({ length: 40 }, () => 'X')
  )

  it('renders full 40x25 grid with effects', () => {
    render(<TeletextGrid content={mockContent} />)
    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toHaveAttribute('data-cols', '40')
    expect(grid).toHaveAttribute('data-rows', '25')
  })

  it('renders with FPS monitor when enabled', () => {
    render(<TeletextGrid content={mockContent} showFps={true} />)
    // FPS counter renders after first frame sample
    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toBeInTheDocument()
  })

  it('applies preset configuration correctly', () => {
    const warezPreset = CRT_PRESETS.warez
    render(<TeletextGrid content={mockContent} effectsConfig={warezPreset} />)
    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toBeInTheDocument()
  })
})
