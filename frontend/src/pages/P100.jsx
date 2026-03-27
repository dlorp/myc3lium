import { useEffect, useState } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import useMeshStore from '../store/meshStore'
import { renderDashboard, getMockData } from './P100.utils'
import { 
  fetchMeshStatus, 
  fetchRadioStatus, 
  fetchMeshStatistics 
} from '../services/api'
import { getWebSocketClient } from '../services/ws'

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

  // Dashboard data state
  const [data, setData] = useState(getMockData())
  const [meshStatus, setMeshStatus] = useState(null)
  const [radioStatus, setRadioStatus] = useState(null)
  const [statistics, setStatistics] = useState(null)

  // Fetch mesh data from API
  const fetchMeshData = async () => {
    try {
      const [status, radios, stats] = await Promise.all([
        fetchMeshStatus(),
        fetchRadioStatus(),
        fetchMeshStatistics(),
      ])
      setMeshStatus(status)
      setRadioStatus(radios)
      setStatistics(stats)
    } catch (error) {
      console.error('[P100] Failed to fetch mesh data:', error)
    }
  }

  useEffect(() => {
    setBreadcrumbs(['DASHBOARD'])

    // Load initial data and connect WebSocket
    loadAll()
    connectWS()
    fetchMeshData()

    // Set up WebSocket listener for mesh_update events
    const wsClient = getWebSocketClient()
    const unsubscribe = wsClient.on('mesh_update', () => {
      console.log('[P100] Mesh update received, refreshing data')
      fetchMeshData()
    })

    return () => {
      disconnectWS()
      unsubscribe()
    }
  }, [setBreadcrumbs, loadAll, connectWS, disconnectWS])

  // Update dashboard data when mesh store or API data changes
  useEffect(() => {
    const onlineNodes = nodes.filter((n) => n.status === 'online').length
    
    // Map radio status from API
    const radioData = {
      lora: { enabled: true, status: 'DOWN', strength: 0 },
      halow: { enabled: true, status: 'DOWN', strength: 0 },
      wifi: { enabled: true, status: 'OFFLINE', strength: 0 },
    }

    if (radioStatus) {
      // Map HaLow radio (case-sensitive check for "up")
      if (radioStatus.halow0) {
        const halow = radioStatus.halow0
        radioData.halow = {
          enabled: true,
          status: halow.status === 'up' ? 'UP' : 'DOWN',
          strength: halow.status === 'up' && halow.throughput 
            ? Math.min(100, Math.round((halow.throughput / 20000000) * 100)) // Scale to 0-100%
            : 0,
        }
      }

      // Map LoRa radio
      if (radioStatus.lora0) {
        const lora = radioStatus.lora0
        radioData.lora = {
          enabled: true,
          status: lora.status === 'up' ? 'TX/RX' : 'DOWN',
          strength: lora.status === 'up' && lora.throughput 
            ? Math.min(100, Math.round((lora.throughput / 5000000) * 100)) // Scale to 0-100%
            : 0,
        }
      }
    }

    // WiFi status from BATMAN mesh (check outside radioStatus block)
    if (meshStatus?.batman?.available) {
      radioData.wifi = {
        enabled: true,
        status: 'BATMAN',
        strength: meshStatus.batman.neighbor_count > 0
          ? Math.min(100, 50 + (meshStatus.batman.neighbor_count * 10)) // Scale based on neighbors
          : 50,
      }
    }

    // Calculate uptime from statistics (mgmt_tx packets at ~50/sec)
    let uptime = '00:00:00'
    if (statistics?.available && statistics.data?.mgmt_tx) {
      const uptimeSeconds = Math.floor(statistics.data.mgmt_tx / 50)
      const hours = Math.floor(uptimeSeconds / 3600)
      const minutes = Math.floor((uptimeSeconds % 3600) / 60)
      const seconds = uptimeSeconds % 60
      uptime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }

    setData((prevData) => ({
      ...prevData,
      nodes: {
        online: onlineNodes,
        total: nodes.length > 0 ? nodes.length : (meshStatus?.batman?.neighbor_count || 0),
      },
      messages: {
        unread: messages.length,
      },
      radio: radioData,
      system: {
        ...prevData.system,
        uptime,
      },
      wsStatus: wsConnected ? 'CONNECTED' : 'DISCONNECTED',
    }))
  }, [nodes, threads, messages, wsConnected, meshStatus, radioStatus, statistics])

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
      <TeletextGrid content={content} showFps />
    </div>
  )
}

export default P100
