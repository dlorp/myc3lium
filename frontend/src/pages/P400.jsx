import { useEffect, useState, useRef } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import { renderTacticalMap, getMockGPSData } from './P400.utils'

/**
 * P400 - Tactical Map Page
 * 
 * GPS-based tactical map showing node positions and waypoints.
 * 
 * Features:
 * - ASCII map grid with terrain heightmap
 * - Node position indicators by type (SPORE/HYPHA/FROND/RHIZOME)
 * - Current position marker
 * - Waypoint markers
 * - Distance/bearing calculations to nodes and waypoints
 * - Pan/zoom keyboard controls
 * - Compass rose
 * - GPS status (fix type, satellites, accuracy)
 * - Mock GPS data generator
 * 
 * Controls:
 * - Arrow keys: Pan map
 * - +/-: Zoom in/out
 * - W: Toggle waypoint list
 * - N: Cycle through nodes
 * - ESC: Clear selection
 */

const P400 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  
  // GPS data (will be updated via WebSocket in future)
  const gpsDataRef = useRef(getMockGPSData())
  const [gpsData] = useState(gpsDataRef.current)
  
  // View state
  const [panX, setPanX] = useState(0)
  const [panY, setPanY] = useState(0)
  const [zoom, setZoom] = useState(1)
  const [selectedNode, setSelectedNode] = useState(null)
  
  // Animation frame for updates
  const [, setFrame] = useState(0)

  useEffect(() => {
    setBreadcrumbs(['MAP', 'P400'])
  }, [setBreadcrumbs])

  // Animation loop (for future real-time updates)
  useEffect(() => {
    const interval = setInterval(() => {
      setFrame(prev => prev + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase()

      // Pan controls
      if (key === 'arrowup') {
        event.preventDefault()
        setPanY(prev => prev - 2)
      } else if (key === 'arrowdown') {
        event.preventDefault()
        setPanY(prev => prev + 2)
      } else if (key === 'arrowleft') {
        event.preventDefault()
        setPanX(prev => prev - 3)
      } else if (key === 'arrowright') {
        event.preventDefault()
        setPanX(prev => prev + 3)
      }
      
      // Zoom controls
      else if (key === '+' || key === '=') {
        event.preventDefault()
        setZoom(prev => Math.min(3, prev + 0.2))
      } else if (key === '-' || key === '_') {
        event.preventDefault()
        setZoom(prev => Math.max(0.5, prev - 0.2))
      }
      
      // Reset view
      else if (key === '0' || key === 'home') {
        event.preventDefault()
        setPanX(0)
        setPanY(0)
        setZoom(1)
        setSelectedNode(null)
      }
      
      // Cycle through nodes
      else if (key === 'n') {
        event.preventDefault()
        const currentIndex = selectedNode 
          ? gpsData.nodes.findIndex(n => n.id === selectedNode.id)
          : -1
        const nextIndex = (currentIndex + 1) % gpsData.nodes.length
        setSelectedNode(gpsData.nodes[nextIndex])
      }
      
      // Clear selection
      else if (key === 'escape') {
        event.preventDefault()
        setSelectedNode(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [gpsData, selectedNode])

  const content = renderTacticalMap(gpsData, panX, panY, zoom, selectedNode)

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P400 - TACTICAL MAP</div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

export default P400
