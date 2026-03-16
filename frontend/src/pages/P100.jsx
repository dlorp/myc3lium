import { useEffect, useState } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
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
 * - WebSocket connection for live updates (future)
 */

const P100 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  const navigateTo = useNavigationStore((state) => state.navigateTo)
  const [data, setData] = useState(getMockData())

  useEffect(() => {
    setBreadcrumbs(['DASHBOARD'])
  }, [setBreadcrumbs])

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
