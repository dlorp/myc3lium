import { useEffect, useState } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import useMeshStore from '../store/meshStore'
import { renderDashboard, getMockData } from './P100.utils'

/**
 * P100 - Dashboard Page
 * 
 * Main menu / system overview dashboard. First page users see.
 * 
 * Features:
 * - System status summary (nodes, unread messages, next sat pass, battery)
 * - Menu navigation to subsystems
 * - Radio status bars (LoRa/HaLow/WiFi) - color-coded
 * - GPS lock indicator
 * - Clock display
 * - WebSocket connection for live updates
 */

const P100 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  const navigateTo = useNavigationStore((state) => state.navigateTo)

  // Get live mesh data
  const nodes = useMeshStore((state) => state.nodes)
  const threads = useMeshStore((state) => state.threads)
  const messages = useMeshStore((state) => state.messages)
  const wsConnected = useMeshStore((state) => state.wsConnected)
  const loadAll = useMeshStore((state) => state.loadAll)
  const connectWS = useMeshStore((state) => state.connectWS)
  const disconnectWS = useMeshStore((state) => state.disconnectWS)

  // Merge live data with mock data for display
  const [data, setData] = useState(getMockData())

  useEffect(() => {
    setBreadcrumbs(['DASHBOARD'])

    // Load initial data and connect WebSocket
    loadAll()
    connectWS()

    return () => {
      disconnectWS()
    }
  }, [setBreadcrumbs, loadAll, connectWS, disconnectWS])

  // Update data when mesh store changes
  useEffect(() => {
    const onlineNodes = nodes.filter((n) => n.status === 'online').length
    
    setData((prevData) => ({
      ...prevData,
      nodes: {
        online: onlineNodes,
        total: nodes.length,
      },
      messages: {
        ...prevData.messages,
        unread: messages.length,
      },
      // Add WebSocket status indicator (can be displayed in custom field)
      wsStatus: wsConnected ? 'CONNECTED' : 'DISCONNECTED',
    }))
  }, [nodes, threads, messages, wsConnected])

  // Update clock every second
  useEffect(() => {
    const interval = setInterval(() => {
      setData(prevData => ({ ...prevData }))
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key

      if (key === '2') {
        navigateTo(200)
      } else if (key === '3') {
        navigateTo(300)
      } else if (key === '4') {
        navigateTo(400)
      } else if (key === '5') {
        navigateTo(500)
      } else if (key === '6') {
        navigateTo(600)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigateTo])

  const content = renderDashboard(data)

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P100 - DASHBOARD</div>
      <TeletextGrid 
        content={content} 
        showFps 
        effectsConfig={{
          enablePhosphor: false,
          enableFlicker: false,
          enableNoise: false,
          enableChromatic: false,
          enableBloom: false,
        }}
      />
    </div>
  )
}

export default P100
