import { useEffect, useState, useRef } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import { 
  renderIntelligenceHub, 
  getMockIntelData,
  updateSatellitePasses,
  updateRFSpectrum,
  updateSensorData
} from './P500.utils'

const P500 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  const navigateTo = useNavigationStore((state) => state.navigateTo)
  
  const intelDataRef = useRef(getMockIntelData())
  const [intelData, setIntelData] = useState(intelDataRef.current)
  
  const [viewMode, setViewMode] = useState('sat')
  
  const [frame, setFrame] = useState(0)

  useEffect(() => {
    setBreadcrumbs(['INTELLIGENCE', 'P500'])
  }, [setBreadcrumbs])

  useEffect(() => {
    const interval = setInterval(() => {
      setFrame(prev => prev + 1)
      
      setIntelData(prev => {
        const updated = { ...prev }
        
        if (viewMode === 'sat') {
          updateSatellitePasses(updated.satellites)
        }
        
        if (viewMode === 'rf') {
          updateRFSpectrum(updated.spectrum)
        }
        
        if (viewMode === 'tel' && frame % 5 === 0) {
          updateSensorData(updated.sensors)
        }
        
        return updated
      })
    }, 100)

    return () => clearInterval(interval)
  }, [frame, viewMode])

  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase()

      if (key === 's') {
        setViewMode('sat')
      } else if (key === 'r') {
        setViewMode('rf')
      } else if (key === 't') {
        setViewMode('tel')
      } else if (key === '1') {
        navigateTo(100)
      } else if (key === '2') {
        navigateTo(200)
      } else if (key === '3') {
        navigateTo(300)
      } else if (key === '4') {
        navigateTo(400)
      } else if (key === '6') {
        navigateTo(600)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigateTo])

  const content = renderIntelligenceHub(intelData, viewMode, frame)

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P500 - INTELLIGENCE HUB</div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

export default P500
