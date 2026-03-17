import { useEffect, useState, useRef } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import { renderSensorGrid, getMockSensorData, updateSensorReadings } from './P700.utils'

/**
 * P700 - Sensor Grid Page
 * 
 * Environmental sensor monitoring grid for distributed sensor network.
 * 
 * Features:
 * - Multi-sensor data grid (temperature, humidity, pressure, air quality)
 * - Per-node sensor status with color-coded alerts
 * - Historical trend sparklines (ASCII mini-graphs)
 * - Alert threshold display (warning/critical states)
 * - Keyboard navigation between sensors
 * - Real-time data updates with mock generator
 * - Status badges (GOOD/WARNING/CRITICAL)
 * 
 * Controls:
 * - Up/Down arrows: Navigate between nodes
 * - Enter: View detailed sensor history
 * - T/H/P/A: Sort by temp/humidity/pressure/AQI
 * - S: Toggle status filter (all/warning/critical)
 * - ESC: Clear selection
 */

const P700 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  
  // Sensor data state
  const sensorDataRef = useRef(getMockSensorData())
  const [sensorData, setSensorData] = useState(sensorDataRef.current)
  
  // View state
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [sortBy, setSortBy] = useState('id') // 'id', 'temp', 'humidity', 'pressure', 'aqi'
  const [statusFilter, setStatusFilter] = useState('all') // 'all', 'warning', 'critical'
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'detail'
  
  // Update counter for display
  const [updateCount, setUpdateCount] = useState(0)

  useEffect(() => {
    setBreadcrumbs(['SENSORS', 'P700'])
  }, [setBreadcrumbs])

  // Sensor data update loop
  useEffect(() => {
    const interval = setInterval(() => {
      setSensorData(prev => {
        const updated = updateSensorReadings(prev)
        setUpdateCount(c => c + 1)
        return updated
      })
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [])

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase()

      // Filter current sensors based on status filter
      const filteredSensors = sensorData.sensors.filter(sensor => {
        if (statusFilter === 'all') return true
        if (statusFilter === 'warning') return sensor.status === 'WARNING' || sensor.status === 'CRITICAL'
        if (statusFilter === 'critical') return sensor.status === 'CRITICAL'
        return true
      })

      // Navigation
      if (key === 'arrowup') {
        event.preventDefault()
        setSelectedIndex(prev => Math.max(0, prev - 1))
      } else if (key === 'arrowdown') {
        event.preventDefault()
        setSelectedIndex(prev => Math.min(filteredSensors.length - 1, prev + 1))
      }
      
      // Sorting
      else if (key === 't') {
        event.preventDefault()
        setSortBy('temp')
      } else if (key === 'h') {
        event.preventDefault()
        setSortBy('humidity')
      } else if (key === 'p') {
        event.preventDefault()
        setSortBy('pressure')
      } else if (key === 'a') {
        event.preventDefault()
        setSortBy('aqi')
      } else if (key === 'i') {
        event.preventDefault()
        setSortBy('id')
      }
      
      // Status filter toggle
      else if (key === 's') {
        event.preventDefault()
        setStatusFilter(prev => {
          if (prev === 'all') return 'warning'
          if (prev === 'warning') return 'critical'
          return 'all'
        })
        setSelectedIndex(0) // Reset selection when filter changes
      }
      
      // View mode toggle
      else if (key === 'enter') {
        event.preventDefault()
        setViewMode(prev => prev === 'grid' ? 'detail' : 'grid')
      }
      
      // Clear selection
      else if (key === 'escape') {
        event.preventDefault()
        setSelectedIndex(0)
        setViewMode('grid')
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [sensorData, statusFilter])

  const content = renderSensorGrid(
    sensorData, 
    selectedIndex, 
    sortBy, 
    statusFilter, 
    viewMode,
    updateCount
  )

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">
        P700 - SENSOR GRID {statusFilter !== 'all' ? `(${statusFilter.toUpperCase()})` : ''}
      </div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

export default P700
