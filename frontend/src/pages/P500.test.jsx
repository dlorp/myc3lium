import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import P500 from './P500'
import { renderIntelligenceHub, getMockIntelData } from './P500.utils'
import useNavigationStore from '../store/navigationStore'
import { COLUMNS, ROWS } from '../components/TeletextGrid'

describe('P500 Intelligence Hub', () => {
  beforeEach(() => {
    useNavigationStore.setState({ currentPage: 500, history: [100, 500], breadcrumbs: [] })
  })
  
  it('renders intelligence hub page', () => {
    render(<P500 />)
    expect(screen.getByText(/P500 - INTELLIGENCE HUB/)).toBeInTheDocument()
  })
  
  it('sets breadcrumbs correctly', () => {
    render(<P500 />)
    expect(useNavigationStore.getState().breadcrumbs).toEqual(['INTELLIGENCE', 'P500'])
  })

  it('getMockIntelData returns valid structure', () => {
    const data = getMockIntelData()
    expect(data.satellites).toBeDefined()
    expect(data.spectrum).toBeDefined()
    expect(data.sensors).toBeDefined()
  })

  it('renderIntelligenceHub returns correct grid dimensions', () => {
    const data = getMockIntelData()
    const grid = renderIntelligenceHub(data, 'sat')
    expect(grid.length).toBe(ROWS)
    expect(grid[0].length).toBe(COLUMNS)
  })
})
