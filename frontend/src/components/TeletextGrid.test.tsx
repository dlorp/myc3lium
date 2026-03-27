import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import TeletextGrid, { COLUMNS, ROWS } from './TeletextGrid'

// Mock canvas context since jsdom doesn't support canvas
const mockGetContext = vi.fn(() => ({
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  fillText: vi.fn(),
  drawImage: vi.fn(),
  putImageData: vi.fn(),
  createImageData: vi.fn(() => ({ data: new Uint8ClampedArray(4) })),
  getImageData: vi.fn(() => ({ data: new Uint8ClampedArray(4) })),
  font: '',
  fillStyle: '',
  textBaseline: '',
}))

beforeEach(() => {
  HTMLCanvasElement.prototype.getContext = mockGetContext as any
  // Don't actually call the RAF callback to avoid infinite recursion
  vi.spyOn(window, 'requestAnimationFrame').mockImplementation(() => 0)
  vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => {})
})

const makeContent = (): string[][] => {
  return Array.from({ length: ROWS }, () =>
    Array.from({ length: COLUMNS }, () => ' ')
  )
}

describe('TeletextGrid', () => {
  describe('Constants', () => {
    it('should export 80 columns', () => {
      expect(COLUMNS).toBe(80)
    })

    it('should export 25 rows', () => {
      expect(ROWS).toBe(25)
    })
  })

  describe('Rendering', () => {
    it('should render the container with data-testid', () => {
      render(<TeletextGrid content={makeContent()} />)
      const el = screen.getByTestId('teletext-grid')
      expect(el).toBeInTheDocument()
      expect(el).toHaveAttribute('data-cols', '80')
      expect(el).toHaveAttribute('data-rows', '25')
    })

    it('should render a canvas element', () => {
      const { container } = render(<TeletextGrid content={makeContent()} />)
      const canvas = container.querySelector('canvas')
      expect(canvas).toBeInTheDocument()
    })

    it('should render with correct background color', () => {
      render(<TeletextGrid content={makeContent()} />)
      const el = screen.getByTestId('teletext-grid')
      expect(el.style.background).toBe('rgb(14, 11, 2)')
    })

    it('should handle empty content gracefully', () => {
      render(<TeletextGrid content={[]} />)
      expect(screen.getByTestId('teletext-grid')).toBeInTheDocument()
    })

    it('should handle undefined content gracefully', () => {
      render(<TeletextGrid content={undefined as any} />)
      expect(screen.getByTestId('teletext-grid')).toBeInTheDocument()
    })
  })

  describe('FPS display', () => {
    it('should not show FPS by default', () => {
      render(<TeletextGrid content={makeContent()} />)
      expect(screen.queryByText(/FPS/)).not.toBeInTheDocument()
    })

    it('should accept showFps prop', () => {
      render(<TeletextGrid content={makeContent()} showFps />)
      // FPS counter appears after first second; just check no crash
      expect(screen.getByTestId('teletext-grid')).toBeInTheDocument()
    })
  })

  describe('Props', () => {
    it('should accept effectsConfig without crashing', () => {
      render(
        <TeletextGrid
          content={makeContent()}
          effectsConfig={{
            enableChromatic: false,
            enableBloom: false,
          }}
        />
      )
      expect(screen.getByTestId('teletext-grid')).toBeInTheDocument()
    })
  })
})
