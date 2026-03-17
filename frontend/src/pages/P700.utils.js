/**
 * P700.utils.js - Sensor Grid Utilities
 * 
 * Helper functions for sensor data generation, processing, and rendering.
 * Separated from component to maintain react-refresh compliance.
 */

const ROWS = 25
const COLUMNS = 40

/**
 * Generate mock sensor data for testing
 */
export const getMockSensorData = () => {
  const sensors = [
    {
      id: 'SPORE-01',
      callsign: 'Nexus',
      temp: 12.1,
      humidity: 34,
      pressure: 1013,
      aqi: 8,
      status: 'GOOD',
      trend: [11.5, 11.8, 12.0, 11.9, 12.1, 12.1, 12.0, 12.1],
    },
    {
      id: 'RHIZOME-02',
      callsign: 'Ravine Stream',
      temp: 6.4,
      humidity: 87,
      pressure: 1007,
      aqi: 12,
      status: 'GOOD',
      trend: [6.2, 6.3, 6.4, 6.3, 6.4, 6.5, 6.4, 6.4],
    },
    {
      id: 'RHIZOME-03',
      callsign: 'Ridge Overlook',
      temp: 18.2,
      humidity: 45,
      pressure: 1015,
      aqi: 15,
      status: 'WARNING',
      trend: [6.5, 8.2, 12.1, 15.3, 17.8, 18.1, 18.2, 18.2],
    },
    {
      id: 'RHIZOME-08',
      callsign: 'Valley Floor',
      temp: 7.1,
      humidity: 82,
      pressure: 1011,
      aqi: 10,
      status: 'GOOD',
      trend: [7.0, 7.1, 7.0, 7.1, 7.2, 7.1, 7.1, 7.1],
    },
    {
      id: 'RHIZOME-12',
      callsign: 'Storm Watch',
      temp: 5.8,
      humidity: 91,
      pressure: 1009,
      aqi: 7,
      status: 'WARNING',
      trend: [6.1, 6.0, 5.9, 5.9, 5.8, 5.8, 5.8, 5.8],
    },
    {
      id: 'RHIZOME-15',
      callsign: 'Treeline',
      temp: 4.2,
      humidity: 78,
      pressure: 1012,
      aqi: 9,
      status: 'GOOD',
      trend: [4.5, 4.4, 4.3, 4.3, 4.2, 4.2, 4.2, 4.2],
    },
  ]

  return {
    sensors,
    lastUpdate: new Date(),
    thresholds: {
      temp: { warning: 15, critical: 20 },
      humidity: { warning: 85, critical: 92 },
      pressure: { warning: 995, critical: 990 },
      aqi: { warning: 50, critical: 100 },
    },
  }
}

/**
 * Update sensor readings with simulated drift
 */
export const updateSensorReadings = (sensorData) => {
  const updated = { ...sensorData }
  
  updated.sensors = sensorData.sensors.map(sensor => {
    // Simulate sensor drift
    let newTemp = sensor.temp + (Math.random() - 0.5) * 0.3
    let newHumidity = sensor.humidity + Math.floor((Math.random() - 0.5) * 4)
    let newPressure = sensor.pressure + Math.floor((Math.random() - 0.5) * 3)
    let newAqi = sensor.aqi + Math.floor((Math.random() - 0.5) * 2)

    // Clamp to realistic ranges
    newTemp = Math.max(-20, Math.min(40, newTemp))
    newHumidity = Math.max(0, Math.min(100, newHumidity))
    newPressure = Math.max(980, Math.min(1040, newPressure))
    newAqi = Math.max(0, Math.min(500, newAqi))

    // Update trend history
    const newTrend = [...sensor.trend.slice(1), newTemp]

    // Determine status based on thresholds
    let status = 'GOOD'
    if (newTemp >= sensorData.thresholds.temp.critical ||
        newHumidity >= sensorData.thresholds.humidity.critical ||
        newAqi >= sensorData.thresholds.aqi.critical) {
      status = 'CRITICAL'
    } else if (newTemp >= sensorData.thresholds.temp.warning ||
               newHumidity >= sensorData.thresholds.humidity.warning ||
               newAqi >= sensorData.thresholds.aqi.warning) {
      status = 'WARNING'
    }

    return {
      ...sensor,
      temp: newTemp,
      humidity: newHumidity,
      pressure: newPressure,
      aqi: newAqi,
      trend: newTrend,
      status,
    }
  })

  updated.lastUpdate = new Date()
  return updated
}

/**
 * Sort sensors by given field
 */
const sortSensors = (sensors, sortBy) => {
  const sorted = [...sensors]
  
  switch (sortBy) {
    case 'temp':
      sorted.sort((a, b) => b.temp - a.temp)
      break
    case 'humidity':
      sorted.sort((a, b) => b.humidity - a.humidity)
      break
    case 'pressure':
      sorted.sort((a, b) => b.pressure - a.pressure)
      break
    case 'aqi':
      sorted.sort((a, b) => b.aqi - a.aqi)
      break
    case 'id':
    default:
      sorted.sort((a, b) => a.id.localeCompare(b.id))
      break
  }
  
  return sorted
}

/**
 * Filter sensors by status
 */
const filterSensors = (sensors, statusFilter) => {
  if (statusFilter === 'all') return sensors
  if (statusFilter === 'warning') {
    return sensors.filter(s => s.status === 'WARNING' || s.status === 'CRITICAL')
  }
  if (statusFilter === 'critical') {
    return sensors.filter(s => s.status === 'CRITICAL')
  }
  return sensors
}

/**
 * Generate ASCII sparkline for trend data
 */
const generateSparkline = (trend, width = 8) => {
  if (!trend || trend.length === 0) return ' '.repeat(width)
  
  const min = Math.min(...trend)
  const max = Math.max(...trend)
  const range = max - min || 1
  
  const chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
  
  const sparkline = trend.slice(-width).map(value => {
    const normalized = (value - min) / range
    const index = Math.min(chars.length - 1, Math.floor(normalized * chars.length))
    return chars[index]
  }).join('')
  
  return sparkline.padEnd(width, ' ')
}

/**
 * Render sensor grid view
 */
export const renderSensorGrid = (
  sensorData,
  selectedIndex,
  sortBy,
  statusFilter,
  viewMode,
  updateCount
) => {
  const grid = Array.from({ length: ROWS }, () =>
    Array.from({ length: COLUMNS }, () => ' ')
  )

  const writeText = (x, y, text, maxWidth = COLUMNS) => {
    if (y < 0 || y >= ROWS) return
    const truncated = text.slice(0, maxWidth)
    for (let i = 0; i < truncated.length; i++) {
      const col = x + i
      if (col >= 0 && col < COLUMNS) {
        grid[y][col] = truncated[i]
      }
    }
  }

  const drawHLine = (y, char = '─') => {
    for (let x = 0; x < COLUMNS; x++) {
      grid[y][x] = char
    }
  }

  // Filter and sort sensors
  const filteredSensors = filterSensors(sensorData.sensors, statusFilter)
  const sortedSensors = sortSensors(filteredSensors, sortBy)

  if (viewMode === 'detail' && sortedSensors.length > 0) {
    // Detail view for selected sensor
    const sensor = sortedSensors[selectedIndex] || sortedSensors[0]
    
    writeText(1, 0, `SENSOR DETAIL ● ${sensor.id}`)
    drawHLine(1)
    
    writeText(2, 3, `Callsign: "${sensor.callsign}"`)
    writeText(2, 4, `Status: ${sensor.status}`)
    drawHLine(5)
    
    // Metrics with thresholds
    writeText(2, 7, 'TEMPERATURE')
    writeText(2, 8, `Current: ${sensor.temp.toFixed(1)}°C`)
    writeText(2, 9, `Warn: ${sensorData.thresholds.temp.warning}°C | Crit: ${sensorData.thresholds.temp.critical}°C`)
    writeText(2, 10, `Trend: ${generateSparkline(sensor.trend, 20)}`)
    
    writeText(2, 12, 'HUMIDITY')
    writeText(2, 13, `Current: ${sensor.humidity}%`)
    writeText(2, 14, `Warn: ${sensorData.thresholds.humidity.warning}% | Crit: ${sensorData.thresholds.humidity.critical}%`)
    
    writeText(2, 16, 'PRESSURE')
    writeText(2, 17, `Current: ${sensor.pressure} mb`)
    
    writeText(2, 19, 'AIR QUALITY INDEX')
    writeText(2, 20, `Current: ${sensor.aqi}`)
    writeText(2, 21, `Warn: ${sensorData.thresholds.aqi.warning} | Crit: ${sensorData.thresholds.aqi.critical}`)
    
    drawHLine(ROWS - 3)
    writeText(2, ROWS - 2, '[ESC] Return to grid')
    
  } else {
    // Grid view
    writeText(1, 0, `SENSOR GRID ● ${sortedSensors.length} nodes`)
    writeText(30, 0, `#${updateCount}`)
    drawHLine(1)
    
    // Column headers
    writeText(2, 3, 'NODE')
    writeText(14, 3, 'TEMP')
    writeText(21, 3, 'HUM')
    writeText(26, 3, 'PRES')
    writeText(32, 3, 'AQI')
    writeText(36, 3, 'ST')
    drawHLine(4)
    
    // Sensor rows (max 15 visible)
    const visibleStart = Math.max(0, Math.min(selectedIndex - 7, sortedSensors.length - 15))
    const visibleSensors = sortedSensors.slice(visibleStart, visibleStart + 15)
    
    visibleSensors.forEach((sensor, i) => {
      const y = 5 + i
      const isSelected = (visibleStart + i) === selectedIndex
      
      // Selection indicator
      if (isSelected) {
        writeText(0, y, '>')
      }
      
      // Node ID
      writeText(2, y, sensor.id.slice(0, 11))
      
      // Temperature (colored by threshold)
      const tempStr = sensor.temp.toFixed(1) + '°'
      writeText(14, y, tempStr.padStart(6))
      
      // Humidity
      writeText(21, y, String(sensor.humidity).padStart(3) + '%')
      
      // Pressure
      writeText(26, y, String(sensor.pressure).padStart(4))
      
      // AQI
      writeText(32, y, String(sensor.aqi).padStart(3))
      
      // Status badge
      const statusChar = sensor.status === 'GOOD' ? '●' : sensor.status === 'WARNING' ? '▲' : '✕'
      writeText(36, y, statusChar)
      
      // Sparkline (compact)
      const sparkline = generateSparkline(sensor.trend, 8)
      writeText(COLUMNS - 9, y, sparkline)
    })
    
    // Footer
    drawHLine(ROWS - 4)
    writeText(2, ROWS - 3, `Sort: [${sortBy.toUpperCase()}]  Filter: [${statusFilter.toUpperCase()}]`)
    writeText(2, ROWS - 2, `[↑↓]Nav [ENTER]Detail [T/H/P/A]Sort [S]Filter`)
    writeText(2, ROWS - 1, `Updated: ${sensorData.lastUpdate.toLocaleTimeString()}`)
  }

  return grid
}
