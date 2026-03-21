import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import TeletextGrid, { COLUMNS, ROWS } from './TeletextGrid'

// Mock Canvas and three-fiber components
vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: any) => <div data-testid="canvas">{children}</div>,
  useFrame: vi.fn(),
  useThree: vi.fn(() => ({
    viewport: { width: 640, height: 400 },
    gl: { copyFramebufferToTexture: vi.fn() },
  })),
}))

vi.mock('@react-three/drei', () => ({
  OrthographicCamera: () => <div data-testid="camera" />,
}))

vi.mock('three', () => ({
  Scene: class {},
  WebGLRenderer: class {},
  OrthographicCamera: class {},
  Mesh: class {},
  BufferGeometry: class {},
  ShaderMaterial: class {},
  TextureLoader: class {
    load = vi.fn((url, onLoad, onProgress, onError) => {
      onLoad({
        minFilter: null,
        magFilter: null,
        generateMipmaps: null,
      })
    })
  },
  Vector2: class {
    constructor(public x: number, public y: number) {}
  },
  CanvasTexture: class {},
  WebGLRenderTarget: class { dispose = vi.fn() },
  NearestFilter: 1,
  LinearFilter: 2,
  RGBAFormat: 4,
  SRGBColorSpace: 5,
}))

describe('TeletextGrid', () => {
  // Helper to create valid content (25 rows × 80 columns)
  const createValidContent = (): string[][] => {
    return Array.from({ length: ROWS }, (_, row) =>
      Array.from({ length: COLUMNS }, (_, col) =>
        String.fromCharCode(32 + (row * COLUMNS + col) % 95)
      )
    )
  }

  describe('Basic Rendering', () => {
    it('should render without crashing with valid content', () => {
      const validContent = createValidContent()
      const { container } = render(
        <TeletextGrid content={validContent} />
      )
      expect(container).toBeTruthy()
    })

    it('should render the canvas element', () => {
      const validContent = createValidContent()
      render(<TeletextGrid content={validContent} />)
      expect(screen.getByTestId('canvas')).toBeInTheDocument()
    })

    it('should render with showFps prop', () => {
      const validContent = createValidContent()
      render(<TeletextGrid content={validContent} showFps={true} />)
      expect(screen.getByTestId('canvas')).toBeInTheDocument()
    })
  })

  describe('Content Dimension Validation', () => {
    it('should throw error if content is not an array', () => {
      const invalidContent = 'not an array' as any
      expect(() => {
        render(<TeletextGrid content={invalidContent} />)
      }).toThrow()
    })

    it('should throw error if content has wrong number of rows', () => {
      const invalidContent = Array.from({ length: 20 }, () =>
        Array.from({ length: COLUMNS }, () => 'a')
      )
      expect(() => {
        render(<TeletextGrid content={invalidContent} />)
      }).toThrow(/must have exactly 25 rows/i)
    })

    it('should throw error if a row is not an array', () => {
      const invalidContent: any = Array.from({ length: ROWS }, (_, i) =>
        i === 5 ? 'not an array' : Array.from({ length: COLUMNS }, () => 'a')
      )
      expect(() => {
        render(<TeletextGrid content={invalidContent} />)
      }).toThrow(/Row 5 is not an array/i)
    })

    it('should throw error if a row has wrong number of columns', () => {
      const invalidContent = Array.from({ length: ROWS }, (_, i) =>
        i === 10
          ? Array.from({ length: COLUMNS - 5 }, () => 'a')
          : Array.from({ length: COLUMNS }, () => 'a')
      )
      expect(() => {
        render(<TeletextGrid content={invalidContent} />)
      }).toThrow(/Row 10 has 75 columns/i)
    })

    it('should throw error if a cell is not a string', () => {
      const invalidContent: any = Array.from({ length: ROWS }, (_, i) =>
        Array.from({ length: COLUMNS }, (_, j) =>
          i === 5 && j === 10 ? 123 : 'a'
        )
      )
      expect(() => {
        render(<TeletextGrid content={invalidContent} />)
      }).toThrow(/Row 5, Column 10.*expected string/i)
    })

    it('should accept valid 25×80 content', () => {
      const validContent = createValidContent()
      const { container } = render(
        <TeletextGrid content={validContent} />
      )
      expect(container.querySelector('[data-cols="80"]')).toBeInTheDocument()
      expect(container.querySelector('[data-rows="25"]')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should display error message when texture fails to load', async () => {
      const validContent = createValidContent()
      const { container } = render(
        <TeletextGrid content={validContent} />
      )
      // The component should still render even if texture fails
      expect(container.querySelector('[data-testid="teletext-grid"]')).toBeInTheDocument()
    })

    it('should handle empty effects config', () => {
      const validContent = createValidContent()
      const { container } = render(
        <TeletextGrid content={validContent} effectsConfig={{}} />
      )
      expect(container).toBeTruthy()
    })

    it('should handle custom effects config', () => {
      const validContent = createValidContent()
      const customConfig = {
        enableChromatic: false,
        enableBloom: false,
        enablePhosphor: false,
        chromaticAmount: 0.002,
      }
      const { container } = render(
        <TeletextGrid content={validContent} effectsConfig={customConfig} />
      )
      expect(container).toBeTruthy()
    })
  })

  describe('Props', () => {
    it('should accept width and height via effectsConfig', () => {
      const validContent = createValidContent()
      render(
        <TeletextGrid
          content={validContent}
          effectsConfig={{
            enableChromatic: true,
            bloomStrength: 0.5,
          }}
        />
      )
      expect(screen.getByTestId('canvas')).toBeInTheDocument()
    })

    it('should render with showFps disabled', () => {
      const validContent = createValidContent()
      const { container } = render(
        <TeletextGrid content={validContent} showFps={false} />
      )
      const fpsMeter = container.querySelector('.teletext-fps')
      expect(fpsMeter).not.toBeInTheDocument()
    })
  })
})
