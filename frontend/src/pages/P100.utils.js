import { COLUMNS, ROWS } from '../components/TeletextGrid'

// Box drawing characters
const BOX = {
  TL: '┌', TR: '┐', BL: '└', BR: '┘',
  H: '─', V: '│',
  TLH: '╔', TRH: '╗', BLH: '╚', BRH: '╝',
  HH: '═',
}

const BLOCK = '▓'
const BLOCK_LIGHT = '░'
const ARROW = '▸'
const DOT = '●'

/**
 * Create empty grid
 */
const createGrid = () => {
  return Array.from({ length: ROWS }, () => 
    Array.from({ length: COLUMNS }, () => ' ')
  )
}

/**
 * Write text to grid at position
 */
const writeText = (grid, x, y, text) => {
  if (y < 0 || y >= ROWS) return
  for (let i = 0; i < text.length; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS) {
      grid[y][col] = text[i]
    }
  }
}

/**
 * Draw horizontal line
 */
const drawHLine = (grid, x, y, length, char = BOX.H) => {
  for (let i = 0; i < length; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS && y >= 0 && y < ROWS) {
      grid[y][col] = char
    }
  }
}

/**
 * Draw vertical line
 */
const drawVLine = (grid, x, y, length, char = BOX.V) => {
  for (let i = 0; i < length; i++) {
    const row = y + i
    if (row >= 0 && row < ROWS && x >= 0 && x < COLUMNS) {
      grid[row][x] = char
    }
  }
}

/**
 * Draw box
 */
const drawBox = (grid, x, y, width, height, heavy = false) => {
  const { tl, tr, bl, br, h, v } = heavy ? 
    { tl: BOX.TLH, tr: BOX.TRH, bl: BOX.BLH, br: BOX.BRH, h: BOX.HH, v: BOX.V } :
    { tl: BOX.TL, tr: BOX.TR, bl: BOX.BL, br: BOX.BR, h: BOX.H, v: BOX.V }

  // Corners
  if (x >= 0 && x < COLUMNS) {
    if (y >= 0 && y < ROWS) grid[y][x] = tl
    if (y + height - 1 >= 0 && y + height - 1 < ROWS) grid[y + height - 1][x] = bl
  }
  if (x + width - 1 >= 0 && x + width - 1 < COLUMNS) {
    if (y >= 0 && y < ROWS) grid[y][x + width - 1] = tr
    if (y + height - 1 >= 0 && y + height - 1 < ROWS) {
      grid[y + height - 1][x + width - 1] = br
    }
  }

  // Horizontal lines
  drawHLine(grid, x + 1, y, width - 2, h)
  drawHLine(grid, x + 1, y + height - 1, width - 2, h)

  // Vertical lines
  drawVLine(grid, x, y + 1, height - 2, v)
  drawVLine(grid, x + width - 1, y + 1, height - 2, v)
}

/**
 * Draw progress bar
 */
const drawProgressBar = (grid, x, y, width, percent) => {
  const filled = Math.round((width * percent) / 100)
  for (let i = 0; i < width; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS && y >= 0 && y < ROWS) {
      grid[y][col] = i < filled ? BLOCK : BLOCK_LIGHT
    }
  }
}

/**
 * Format time HH:MM
 */
const formatTime = () => {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

/**
 * Mock system data (will be replaced with WebSocket updates)
 */
export const getMockData = () => ({
  nodes: {
    online: 5,
    total: 7,
  },
  messages: {
    unread: 3,
  },
  satellite: {
    nextPass: '19:34',
    minutesUntil: 42,
  },
  battery: {
    percent: 74,
    hoursRemaining: 5.3,
  },
  gps: {
    locked: true,
    satellites: 8,
  },
  radio: {
    lora: { enabled: true, status: 'TX/RX', strength: 85 },
    halow: { enabled: true, status: 'ASSOC', strength: 72 },
    wifi: { enabled: true, status: 'BATMAN', strength: 91 },
  },
  system: {
    uptime: '04:22:37',
    cpu: 23,
    temp: 52,
  },
})

/**
 * Render P100 dashboard to grid
 */
export const renderDashboard = (data) => {
  const grid = createGrid()

  // Header - now spanning 80 columns
  writeText(grid, 1, 0, `${DOT}MYC3LIUM NEXUS TERMINAL${DOT}`)
  writeText(grid, 32, 0, `${formatTime()}`)
  writeText(grid, 45, 0, `[GPS: ${data.gps.locked ? 'LOCK' : 'WAIT'}]`)
  writeText(grid, 70, 0, `BATT: ${data.battery.percent}%`)
  drawHLine(grid, 0, 1, COLUMNS)

  // Title banner - expanded for 80 columns
  drawBox(grid, 2, 2, 76, 3, true)
  writeText(grid, 20, 3, '══════ MYC3LIUM - TACTICAL MESH NEXUS TERMINAL ══════')

  // Menu section - compressed spacing
  let row = 6

  // [200] MESH NETWORK
  writeText(grid, 2, row, `[200] MESH ${ARROW}${data.nodes.online}/${data.nodes.total} online`)
  row++

  // [300] MESSAGING
  const msgText = data.messages.unread === 0 ? 'No unread' : `${data.messages.unread} unread`
  writeText(grid, 2, row, `[300] MSG ${ARROW}${msgText}`)
  row++

  // [400] TACTICAL MAP
  writeText(grid, 2, row, `[400] MAP ${ARROW}GPS + Waypoints`)
  row++

  // [500] INTELLIGENCE
  writeText(grid, 2, row, `[500] INTEL ${ARROW}Sat + RF + Sensors`)
  row++

  // [600] CONFIGURATION
  writeText(grid, 2, row, `[600] CFG ${ARROW}System Settings`)
  row++

  row++ // Separator

  // Radio Status Section - expanded for 80 columns with wider progress bars
  writeText(grid, 2, row, `${BOX.HH}${BOX.HH}RADIO STATUS${BOX.HH}${'═'.repeat(63)}`)
  row++

  // LoRa
  writeText(grid, 2, row, `LoRa  [${data.radio.lora.status}]`)
  drawProgressBar(grid, 20, row, 40, data.radio.lora.strength)
  writeText(grid, 62, row, `${data.radio.lora.strength}% Signal`)
  row++

  // HaLow
  writeText(grid, 2, row, `HaLow [${data.radio.halow.status}]`)
  drawProgressBar(grid, 20, row, 40, data.radio.halow.strength)
  writeText(grid, 62, row, `${data.radio.halow.strength}% Signal`)
  row++

  // WiFi
  writeText(grid, 2, row, `WiFi  [${data.radio.wifi.status}]`)
  drawProgressBar(grid, 20, row, 40, data.radio.wifi.strength)
  writeText(grid, 62, row, `${data.radio.wifi.strength}% Signal`)
  row++

  row++ // Separator

  // Satellite
  writeText(grid, 2, row, `${BOX.HH}${BOX.HH}NEXT SATELLITE PASS${BOX.HH}${'═'.repeat(56)}`)
  row++
  writeText(grid, 2, row, `Acquisition of Signal (AOS): ${data.satellite.nextPass} UTC (T-${data.satellite.minutesUntil} minutes)`)
  row++

  row++ // Separator

  // System Stats
  writeText(grid, 2, row, `${BOX.HH}${BOX.HH}SYSTEM STATUS${BOX.HH}${'═'.repeat(62)}`)
  row++
  writeText(grid, 2, row, `Uptime: ${data.system.uptime}                CPU Load: ${data.system.cpu}%               Temperature: ${data.system.temp}°C`)
  row++

  // Footer
  drawHLine(grid, 0, ROWS - 2, COLUMNS)
  writeText(grid, 2, ROWS - 1, 'Type page number (100-800) to navigate │ [H]elp │ [Q]uit │ [R]efresh')

  return grid
}
