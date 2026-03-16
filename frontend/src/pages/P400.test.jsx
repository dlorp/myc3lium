import { describe, it, expect } from 'vitest'
import {
  calculateDistance,
  calculateBearing,
  getMockGPSData,
  renderTacticalMap,
} from './P400.utils'

describe('P400.utils', () => {
  describe('calculateDistance', () => {
    it('calculates distance between two GPS coordinates', () => {
      const lat1 = 61.2181
      const lon1 = -149.9003
      const lat2 = 61.3012
      const lon2 = -150.1204
      
      const distance = calculateDistance(lat1, lon1, lat2, lon2)
      
      // Distance should be approximately 17-20 km
      expect(distance).toBeGreaterThan(15)
      expect(distance).toBeLessThan(25)
    })
    
    it('returns 0 for same coordinates', () => {
      const lat = 61.2181
      const lon = -149.9003
      
      const distance = calculateDistance(lat, lon, lat, lon)
      
      expect(distance).toBeCloseTo(0, 1)
    })
  })
  
  describe('calculateBearing', () => {
    it('calculates bearing between two GPS coordinates', () => {
      const lat1 = 61.2181
      const lon1 = -149.9003
      const lat2 = 61.3012
      const lon2 = -150.1204
      
      const bearing = calculateBearing(lat1, lon1, lat2, lon2)
      
      // Bearing should be in valid range
      expect(bearing).toBeGreaterThanOrEqual(0)
      expect(bearing).toBeLessThan(360)
    })
    
    it('calculates north bearing correctly', () => {
      const lat1 = 0
      const lon1 = 0
      const lat2 = 1
      const lon2 = 0
      
      const bearing = calculateBearing(lat1, lon1, lat2, lon2)
      
      // Should be approximately 0° (north)
      expect(bearing).toBeCloseTo(0, 0)
    })
    
    it('calculates east bearing correctly', () => {
      const lat1 = 0
      const lon1 = 0
      const lat2 = 0
      const lon2 = 1
      
      const bearing = calculateBearing(lat1, lon1, lat2, lon2)
      
      // Should be approximately 90° (east)
      expect(bearing).toBeCloseTo(90, 0)
    })
  })
  
  describe('getMockGPSData', () => {
    it('returns valid GPS data structure', () => {
      const data = getMockGPSData()
      
      expect(data).toHaveProperty('currentPosition')
      expect(data).toHaveProperty('nodes')
      expect(data).toHaveProperty('waypoints')
    })
    
    it('includes current position with required fields', () => {
      const data = getMockGPSData()
      const pos = data.currentPosition
      
      expect(pos).toHaveProperty('lat')
      expect(pos).toHaveProperty('lon')
      expect(pos).toHaveProperty('alt')
      expect(pos).toHaveProperty('accuracy')
      expect(pos).toHaveProperty('satellites')
      expect(pos).toHaveProperty('fixType')
      
      expect(pos.lat).toBeTypeOf('number')
      expect(pos.lon).toBeTypeOf('number')
      expect(pos.fixType).toBe('3D-FIX')
    })
    
    it('includes nodes with required fields', () => {
      const data = getMockGPSData()
      
      expect(data.nodes).toBeInstanceOf(Array)
      expect(data.nodes.length).toBeGreaterThan(0)
      
      const node = data.nodes[0]
      expect(node).toHaveProperty('id')
      expect(node).toHaveProperty('type')
      expect(node).toHaveProperty('lat')
      expect(node).toHaveProperty('lon')
      expect(node).toHaveProperty('status')
    })
    
    it('includes waypoints with required fields', () => {
      const data = getMockGPSData()
      
      expect(data.waypoints).toBeInstanceOf(Array)
      expect(data.waypoints.length).toBeGreaterThan(0)
      
      const wp = data.waypoints[0]
      expect(wp).toHaveProperty('id')
      expect(wp).toHaveProperty('name')
      expect(wp).toHaveProperty('lat')
      expect(wp).toHaveProperty('lon')
      expect(wp).toHaveProperty('type')
    })
    
    it('includes expected node types', () => {
      const data = getMockGPSData()
      const types = data.nodes.map(n => n.type)
      
      expect(types).toContain('SPORE')
      expect(types).toContain('HYPHA')
      expect(types).toContain('FROND')
      expect(types).toContain('RHIZOME')
    })
  })
  
  describe('renderTacticalMap', () => {
    it('renders map grid with correct dimensions', () => {
      const data = getMockGPSData()
      const grid = renderTacticalMap(data, 0, 0, 1)
      
      expect(grid).toBeInstanceOf(Array)
      expect(grid.length).toBe(25) // ROWS
      expect(grid[0].length).toBe(40) // COLUMNS
    })
    
    it('includes header text', () => {
      const data = getMockGPSData()
      const grid = renderTacticalMap(data, 0, 0, 1)
      
      const headerRow = grid[0].join('')
      expect(headerRow).toContain('P400')
      expect(headerRow).toContain('TACTICAL MAP')
    })
    
    it('includes GPS status line', () => {
      const data = getMockGPSData()
      const grid = renderTacticalMap(data, 0, 0, 1)
      
      const statusRow = grid[2].join('')
      expect(statusRow).toContain('°N')
      expect(statusRow).toContain('°W')
      expect(statusRow).toContain('SV') // Satellites
    })
    
    it('includes node list in bottom panel', () => {
      const data = getMockGPSData()
      const grid = renderTacticalMap(data, 0, 0, 1)
      
      const bottomRows = grid.slice(-6).map(row => row.join(''))
      const bottomText = bottomRows.join('')
      
      expect(bottomText).toContain('NODES:')
      expect(bottomText).toContain('km') // Distance units
    })
    
    it('includes waypoint list in bottom panel', () => {
      const data = getMockGPSData()
      const grid = renderTacticalMap(data, 0, 0, 1)
      
      const bottomRows = grid.slice(-6).map(row => row.join(''))
      const bottomText = bottomRows.join('')
      
      expect(bottomText).toContain('WAYPOINTS:')
    })
    
    it('includes control hints', () => {
      const data = getMockGPSData()
      const grid = renderTacticalMap(data, 0, 0, 1)
      
      const lastRow = grid[24].join('')
      expect(lastRow).toContain('Pan')
      expect(lastRow).toContain('Zoom')
    })
    
    it('shows selected node details when provided', () => {
      const data = getMockGPSData()
      const selectedNode = data.nodes[1] // HYPHA-03
      const grid = renderTacticalMap(data, 0, 0, 1, selectedNode)
      
      const allText = grid.map(row => row.join('')).join('')
      
      expect(allText).toContain(selectedNode.id)
      expect(allText).toContain('NODE:')
    })
    
    it('renders compass rose', () => {
      const data = getMockGPSData()
      const grid = renderTacticalMap(data, 0, 0, 1)
      
      const allText = grid.map(row => row.join('')).join('')
      
      expect(allText).toContain('N')
      expect(allText).toContain('W')
      expect(allText).toContain('E')
      expect(allText).toContain('S')
    })
    
    it('handles different zoom levels', () => {
      const data = getMockGPSData()
      
      const grid1 = renderTacticalMap(data, 0, 0, 1)
      const grid2 = renderTacticalMap(data, 0, 0, 2)
      
      // Both should render valid grids
      expect(grid1.length).toBe(25)
      expect(grid2.length).toBe(25)
      
      // Zoom level should be displayed in header
      const header1 = grid1[0].join('')
      const header2 = grid2[0].join('')
      
      expect(header1).toContain('Z:1')
      expect(header2).toContain('Z:2')
    })
    
    it('handles pan offsets', () => {
      const data = getMockGPSData()
      
      const grid1 = renderTacticalMap(data, 0, 0, 1)
      const grid2 = renderTacticalMap(data, 5, 5, 1)
      
      // Both should render valid grids
      expect(grid1.length).toBe(25)
      expect(grid2.length).toBe(25)
      
      // Grids should differ due to pan
      const text1 = grid1.map(r => r.join('')).join('')
      const text2 = grid2.map(r => r.join('')).join('')
      
      expect(text1).not.toBe(text2)
    })
  })
})
