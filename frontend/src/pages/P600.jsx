import { useEffect, useState } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import { renderRadioConfig, getMockRadioConfig } from './P600.utils'

/**
 * P600 - Radio Configuration Page
 * 
 * Hardware configuration interface for mesh radio systems.
 * 
 * Features:
 * - LoRa transceiver settings (freq, SF, BW, CR, power)
 * - HaLow 802.11ah settings (SSID, freq, mode, SNR)
 * - SDR configuration (RTL-SDR / SoapySDR parameters)
 * - Network layer status (BATMAN-ADV, Reticulum, Meshtastic)
 * - Real-time status indicators
 * - FCC compliance display
 * 
 * Keyboard shortcuts:
 * - L: LoRa interface focus
 * - H: HaLow interface focus
 * - D: SDR interface focus
 * - S: Save configuration
 * - A: Apply changes
 * - R: Reset to defaults
 * - ESC: Return to dashboard
 */

const P600 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  const navigateTo = useNavigationStore((state) => state.navigateTo)
  const [radioConfig, setRadioConfig] = useState(getMockRadioConfig())

  useEffect(() => {
    setBreadcrumbs(['RADIO', 'P600'])
  }, [setBreadcrumbs])

  // Keyboard navigation and controls
  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase()

      // Interface selection (future: use for interactive editing)
      // if (key === 'l') { ... }
      
      // Config actions
      if (key === 's') {
        // Save config (future: persist to backend)
        console.log('Save config:', radioConfig)
      } else if (key === 'a') {
        // Apply config (future: send to hardware)
        console.log('Apply config:', radioConfig)
      } else if (key === 'r') {
        // Reset to defaults
        setRadioConfig(getMockRadioConfig())
      }
      
      // Navigation
      else if (key === 'escape' || key === '1') {
        navigateTo(100)
      } else if (key === '2') {
        navigateTo(200)
      } else if (key === '3') {
        navigateTo(300)
      } else if (key === '4') {
        navigateTo(400)
      } else if (key === '5') {
        navigateTo(500)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigateTo, radioConfig])

  const content = renderRadioConfig(radioConfig)

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P600 - RADIO CONFIG</div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

export default P600
