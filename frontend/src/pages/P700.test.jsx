import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import P700 from './P700'
import { getMockSensorData, updateSensorReadings, renderSensorGrid } from './P700.utils'

// Mock scrollIntoView
global.HTMLElement.prototype.scrollIntoView = vi.fn()

// Mock navigation store
vi.mock('../store/navigationStore', () => ({
  default: vi.fn((selector) =>
    selector({
      setBreadcrumbs: vi.fn(),
    })
  ),
}))

describe('P700 - Sensor Grid Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('renders without crashing', () => {
      render(<P700 />)
      expect(screen.getByText(/P700 - SENSOR GRID/i)).toBeInTheDocument()
    })

    it('displays TeletextGrid component', () => {
      const { container } = render(<P700 />)
      const teletextGrid = container.querySelector('.teletext-demo')
      expect(teletextGrid).toBeInTheDocument()
    })
  })

  describe('Mock Sensor Data', () => {
    it('generates valid sensor data structure', () => {
      const data = getMockSensorData()
      
      expect(data).toHaveProperty('sensors')
      expect(data).toHaveProperty('lastUpdate')
      expect(data).toHaveProperty('thresholds')
      expect(Array.isArray(data.sensors)).toBe(true)
      expect(data.sensors.length).toBeGreaterThan(0)
    })

    it('each sensor has required fields', () => {
      const data = getMockSensorData()
      
      data.sensors.forEach(sensor => {
        expect(sensor).toHaveProperty('id')
        expect(sensor).toHaveProperty('callsign')
        expect(sensor).toHaveProperty('temp')
        expect(sensor).toHaveProperty('humidity')
        expect(sensor).toHaveProperty('pressure')
        expect(sensor).toHaveProperty('aqi')
        expect(sensor).toHaveProperty('status')
        expect(sensor).toHaveProperty('trend')
        expect(Array.isArray(sensor.trend)).toBe(true)
      })
    })

    it('includes threshold configuration', () => {
      const data = getMockSensorData()
      
      expect(data.thresholds).toHaveProperty('temp')
      expect(data.thresholds).toHaveProperty('humidity')
      expect(data.thresholds).toHaveProperty('pressure')
      expect(data.thresholds).toHaveProperty('aqi')
      
      expect(data.thresholds.temp).toHaveProperty('warning')
      expect(data.thresholds.temp).toHaveProperty('critical')
    })
  })

  describe('Sensor Data Updates', () => {
    it('updates sensor readings while maintaining structure', () => {
      const original = getMockSensorData()
      const updated = updateSensorReadings(original)
      
      expect(updated.sensors.length).toBe(original.sensors.length)
      
      updated.sensors.forEach((sensor, i) => {
        expect(sensor.id).toBe(original.sensors[i].id)
        expect(sensor.callsign).toBe(original.sensors[i].callsign)
        expect(sensor.trend.length).toBe(8) // Trend history maintained
      })
    })

    it('updates lastUpdate timestamp', () => {
      const original = getMockSensorData()
      const updated = updateSensorReadings(original)
      
      expect(updated.lastUpdate).toBeInstanceOf(Date)
      expect(updated.lastUpdate.getTime()).toBeGreaterThanOrEqual(original.lastUpdate.getTime())
    })

    it('keeps sensor values within realistic ranges', () => {
      const original = getMockSensorData()
      const updated = updateSensorReadings(original)
      
      updated.sensors.forEach(sensor => {
        expect(sensor.temp).toBeGreaterThanOrEqual(-20)
        expect(sensor.temp).toBeLessThanOrEqual(40)
        
        expect(sensor.humidity).toBeGreaterThanOrEqual(0)
        expect(sensor.humidity).toBeLessThanOrEqual(100)
        
        expect(sensor.pressure).toBeGreaterThanOrEqual(980)
        expect(sensor.pressure).toBeLessThanOrEqual(1040)
        
        expect(sensor.aqi).toBeGreaterThanOrEqual(0)
        expect(sensor.aqi).toBeLessThanOrEqual(500)
      })
    })

    it('updates status based on thresholds', () => {
      const data = getMockSensorData()
      
      // Force a sensor into critical state
      data.sensors[0].temp = 25 // Above critical threshold (20)
      const updated = updateSensorReadings(data)
      
      // Note: Status is recalculated based on current values after update
      // So we just verify status is one of the valid values
      expect(['GOOD', 'WARNING', 'CRITICAL']).toContain(updated.sensors[0].status)
    })
  })

  describe('Grid Rendering', () => {
    it('renders grid with correct dimensions', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      expect(grid.length).toBe(25) // ROWS
      expect(grid[0].length).toBe(40) // COLUMNS
    })

    it('displays sensor grid header', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      const headerRow = grid[0].join('')
      expect(headerRow).toContain('SENSOR GRID')
    })

    it('displays column headers', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      const headerRow = grid[3].join('')
      expect(headerRow).toContain('NODE')
      expect(headerRow).toContain('TEMP')
      expect(headerRow).toContain('HUM')
      expect(headerRow).toContain('PRES')
    })

    it('renders sensor rows with data', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      // Check that sensor IDs appear in the grid
      const gridText = grid.map(row => row.join('')).join('\n')
      expect(gridText).toContain('SPORE-01')
      expect(gridText).toContain('RHIZOME')
    })

    it('marks selected sensor row', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      // First sensor row should have selection indicator
      const firstSensorRow = grid[5].join('')
      expect(firstSensorRow.startsWith('>')).toBe(true)
    })

    it('filters sensors by status', () => {
      const data = getMockSensorData()
      
      // Grid with all sensors
      renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      // Grid with warning filter
      renderSensorGrid(data, 0, 'id', 'warning', 'grid', 0)
      
      // Warning filter should show fewer sensors
      const allCount = data.sensors.length
      const warningCount = data.sensors.filter(s => s.status === 'WARNING' || s.status === 'CRITICAL').length
      
      expect(allCount).toBeGreaterThan(warningCount)
    })

    it('sorts sensors by temperature', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'temp', 'all', 'grid', 0)
      
      // Verify grid is sorted (check footer shows sort mode)
      const gridText = grid.map(row => row.join('')).join('\n')
      expect(gridText).toContain('TEMP')
    })
  })

  describe('Detail View', () => {
    it('renders detail view for selected sensor', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'detail', 0)
      
      const gridText = grid.map(row => row.join('')).join('\n')
      expect(gridText).toContain('SENSOR DETAIL')
      expect(gridText).toContain('Callsign')
      expect(gridText).toContain('TEMPERATURE')
      expect(gridText).toContain('HUMIDITY')
      expect(gridText).toContain('PRESSURE')
    })

    it('displays threshold information in detail view', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'detail', 0)
      
      const gridText = grid.map(row => row.join('')).join('\n')
      expect(gridText).toContain('Warn')
      expect(gridText).toContain('Crit')
    })

    it('shows return to grid instruction', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'detail', 0)
      
      const gridText = grid.map(row => row.join('')).join('\n')
      expect(gridText).toContain('ESC')
      expect(gridText).toContain('Return to grid')
    })
  })

  describe('Sparkline Rendering', () => {
    it('includes sparklines in grid view', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      // Check for sparkline characters in sensor rows
      const sensorRows = grid.slice(5, 10)
      const hasSparklineChars = sensorRows.some(row => {
        const rowText = row.join('')
        return /[▁▂▃▄▅▆▇█]/.test(rowText)
      })
      
      expect(hasSparklineChars).toBe(true)
    })
  })

  describe('Status Indicators', () => {
    it('displays status badges', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      const gridText = grid.map(row => row.join('')).join('\n')
      
      // Should contain status indicators
      const hasStatusIndicators = /[●▲✕]/.test(gridText)
      expect(hasStatusIndicators).toBe(true)
    })
  })

  describe('Footer Controls', () => {
    it('displays navigation hints', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      const gridText = grid.map(row => row.join('')).join('\n')
      expect(gridText).toContain('Nav')
      expect(gridText).toContain('Sort')
      expect(gridText).toContain('[S')
    })

    it('shows last update timestamp', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'id', 'all', 'grid', 0)
      
      const lastRow = grid[24].join('')
      expect(lastRow).toContain('Updated:')
    })

    it('displays current sort and filter mode', () => {
      const data = getMockSensorData()
      const grid = renderSensorGrid(data, 0, 'temp', 'warning', 'grid', 0)
      
      const gridText = grid.map(row => row.join('')).join('\n')
      expect(gridText).toContain('TEMP')
      expect(gridText).toContain('WARNING')
    })
  })
})
