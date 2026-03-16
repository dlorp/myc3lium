import { useEffect } from 'react'
import TeletextGrid, { COLUMNS, ROWS } from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'

const padLine = (line) => line.padEnd(COLUMNS, ' ').slice(0, COLUMNS)

/**
 * P100 - Index page
 * Main entry point for teletext navigation
 */
const P100 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  
  useEffect(() => {
    setBreadcrumbs(['INDEX'])
  }, [setBreadcrumbs])
  
  const buildContent = () => {
    const lines = [
      'MYC3LIUM TELETYPE  |  P100 INDEX',
      '========================================',
      '',
      'MAIN SERVICES',
      '  200 - SYSTEM STATUS',
      '  300 - NODE NETWORK',
      '  400 - DATA STREAMS',
      '  500 - OPERATIONS',
      '  600 - ANALYTICS',
      '  700 - CONFIGURATION',
      '  800 - DIAGNOSTICS',
      '',
      '----------------------------------------',
      'QUICK ACCESS',
      '  201 - CURRENT UPTIME',
      '  301 - NODE MAP',
      '  401 - LIVE SENSORS',
      '  501 - ACTIVE TASKS',
      '',
      '----------------------------------------',
      'NAVIGATION',
      '  TYPE PAGE NUMBER (100-800)',
      '  ESC TO GO BACK',
      '',
      '========================================',
    ]
    
    const padded = lines.map(padLine)
    while (padded.length < ROWS) {
      padded.push(padLine(''))
    }
    
    return padded.slice(0, ROWS).map((line) => line.split(''))
  }
  
  const content = buildContent()
  
  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P100 - INDEX</div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

export default P100
