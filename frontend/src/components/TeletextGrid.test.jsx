import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import TeletextGrid, { COLUMNS, ROWS } from './TeletextGrid'

vi.mock('@react-three/fiber', async () => {
  const React = await import('react')
  return {
    Canvas: ({ children }) => <div data-testid="r3f-canvas">{children}</div>,
    useFrame: () => {},
    useThree: () => ({ viewport: { width: 10, height: 10 } }),
  }
})

vi.mock('@react-three/drei', () => ({
  OrthographicCamera: () => null,
}))

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    fillRect: vi.fn(),
    fillText: vi.fn(),
    clearRect: vi.fn(),
    measureText: vi.fn(() => ({ width: 10 })),
    set fillStyle(_) {},
    set font(_) {},
    set textBaseline(_) {},
  }))
})

describe('TeletextGrid', () => {
  it('renders a 40x25 teletext grid container', () => {
    const content = Array.from({ length: ROWS }, () =>
      Array.from({ length: COLUMNS }, () => ' '),
    )

    render(<TeletextGrid content={content} />)

    const grid = screen.getByTestId('teletext-grid')
    expect(grid).toBeInTheDocument()
    expect(grid).toHaveAttribute('data-cols', String(COLUMNS))
    expect(grid).toHaveAttribute('data-rows', String(ROWS))
    expect(screen.getByTestId('r3f-canvas')).toBeInTheDocument()
  })
})
