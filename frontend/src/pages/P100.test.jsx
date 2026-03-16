import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import P100, { renderDashboard, getMockData } from './P100'
import useNavigationStore from '../store/navigationStore'
import { COLUMNS, ROWS } from '../components/TeletextGrid'

describe('P100 Dashboard', () => {
  beforeEach(() => {
    useNavigationStore.setState({
      currentPage: 100,
      history: [100],
      breadcrumbs: [],
    })
  })
  
  it('renders dashboard page', () => {
    render(<P100 />)
    expect(screen.getByText(/P100 - DASHBOARD/)).toBeInTheDocument()
  })
  
  it('sets breadcrumbs to DASHBOARD', () => {
    render(<P100 />)
    
    const state = useNavigationStore.getState()
    expect(state.breadcrumbs).toEqual(['DASHBOARD'])
  })
  
  it('displays teletext grid', () => {
    const { container } = render(<P100 />)
    
    const canvas = container.querySelector('canvas')
    expect(canvas).toBeInTheDocument()
  })

  describe('getMockData', () => {
    it('returns valid data structure', () => {
      const data = getMockData()
      
      expect(data.nodes).toBeDefined()
      expect(data.nodes.online).toBeGreaterThan(0)
      expect(data.nodes.total).toBeGreaterThanOrEqual(data.nodes.online)
      
      expect(data.messages).toBeDefined()
      expect(data.messages.unread).toBeGreaterThanOrEqual(0)
      
      expect(data.satellite).toBeDefined()
      expect(data.satellite.nextPass).toBeDefined()
      expect(data.satellite.minutesUntil).toBeGreaterThan(0)
      
      expect(data.battery).toBeDefined()
      expect(data.battery.percent).toBeGreaterThan(0)
      expect(data.battery.percent).toBeLessThanOrEqual(100)
      
      expect(data.gps).toBeDefined()
      expect(data.gps.locked).toBe(true)
      
      expect(data.radio).toBeDefined()
      expect(data.radio.lora).toBeDefined()
      expect(data.radio.halow).toBeDefined()
      expect(data.radio.wifi).toBeDefined()
      
      expect(data.system).toBeDefined()
      expect(data.system.uptime).toBeDefined()
    })
  })

  describe('renderDashboard', () => {
    it('creates valid grid dimensions', () => {
      const data = getMockData()
      const grid = renderDashboard(data)
      
      expect(grid).toHaveLength(ROWS)
      grid.forEach(row => {
        expect(row).toHaveLength(COLUMNS)
      })
    })
    
    it('contains expected menu items', () => {
      const data = getMockData()
      const grid = renderDashboard(data)
      const gridText = grid.map(row => row.join('')).join('\n')
      
      expect(gridText).toContain('MYC3LIUM')
      expect(gridText).toContain('[200] MESH')
      expect(gridText).toContain('[300] MSG')
      expect(gridText).toContain('[400] MAP')
      expect(gridText).toContain('[500] INTEL')
      expect(gridText).toContain('[600] CONFIG')
      expect(gridText).toContain('RADIO STATUS')
    })

    it('displays GPS lock status', () => {
      const dataLocked = getMockData()
      const gridLocked = renderDashboard(dataLocked)
      const textLocked = gridLocked.map(row => row.join('')).join('\n')
      expect(textLocked).toContain('[GPS: LOCK]')
      
      const dataWait = { ...dataLocked, gps: { locked: false, satellites: 3 } }
      const gridWait = renderDashboard(dataWait)
      const textWait = gridWait.map(row => row.join('')).join('\n')
      expect(textWait).toContain('[GPS: WAIT]')
    })

    it('displays battery percentage', () => {
      const data = getMockData()
      const grid = renderDashboard(data)
      const gridText = grid.map(row => row.join('')).join('\n')
      
      expect(gridText).toContain(`${data.battery.percent}%`)
    })

    it('displays node count', () => {
      const data = getMockData()
      const grid = renderDashboard(data)
      const gridText = grid.map(row => row.join('')).join('\n')
      
      expect(gridText).toContain(`${data.nodes.online}/${data.nodes.total}`)
    })

    it('displays unread message count', () => {
      const data = getMockData()
      data.messages.unread = 5
      const grid = renderDashboard(data)
      const gridText = grid.map(row => row.join('')).join('\n')
      
      expect(gridText).toContain('5 unread')
    })

    it('handles zero unread messages', () => {
      const data = getMockData()
      data.messages.unread = 0
      const grid = renderDashboard(data)
      const gridText = grid.map(row => row.join('')).join('\n')
      
      expect(gridText).toContain('No unread')
    })

    it('displays radio status bars', () => {
      const data = getMockData()
      const grid = renderDashboard(data)
      const gridText = grid.map(row => row.join('')).join('\n')
      
      expect(gridText).toContain('LoRa')
      expect(gridText).toContain('HaLow')
      expect(gridText).toContain('WiFi')
      expect(gridText).toContain('[TX/RX]')
      expect(gridText).toContain('[ASSOC]')
      expect(gridText).toContain('[BATMAN]')
    })
  })

  describe('keyboard navigation', () => {
    it('navigates to P200 on key 2', () => {
      render(<P100 />)
      
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '2' }))
      
      const state = useNavigationStore.getState()
      expect(state.currentPage).toBe(200)
    })

    it('navigates to P300 on key 3', () => {
      render(<P100 />)
      
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '3' }))
      
      const state = useNavigationStore.getState()
      expect(state.currentPage).toBe(300)
    })
  })
})
