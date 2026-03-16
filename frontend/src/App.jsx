import TeletextGrid, { COLUMNS, ROWS } from './components/TeletextGrid'
import './App.css'

const padLine = (line) => line.padEnd(COLUMNS, ' ').slice(0, COLUMNS)

const buildSampleContent = () => {
  const lines = [
    'MYC3LIUM TELETYPE  |  SERVICE 001',
    '========================================',
    'SYSTEM STATUS: NOMINAL',
    'NODE COUNT  : 042',
    'LAST SYNC   : 12:45:07 UTC',
    'UPLINK      : STABLE',
    '----------------------------------------',
    'HEADLINES',
    '* SPORENET EXPANDS INTO NEW SECTORS',
    '* BIOFIBER YIELD UP 12.4% THIS CYCLE',
    '* GREENHOUSE ARRAY READY FOR DAWN',
    '----------------------------------------',
    'NEXT TRANSMISSION WINDOW',
    'T-00:14:32',
    'CHANNEL: AMBER/PRIME',
    '----------------------------------------',
    'DATASTREAMS',
    'A: SENSOR GRID  |  OK',
    'B: HVAC MATRIX  |  OK',
    'C: POWER FLOW   |  OK',
    'D: IRRIGATION   |  OK',
    '----------------------------------------',
    'PRESS [ENTER] TO REFRESH',
  ]

  const padded = lines.map(padLine)
  while (padded.length < ROWS) {
    padded.push(padLine(''))
  }

  return padded.slice(0, ROWS).map((line) => line.split(''))
}

function App() {
  const content = buildSampleContent()

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">LIVE CRT FEED</div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

export default App
