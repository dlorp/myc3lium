import { COLUMNS, ROWS } from '../components/TeletextGrid'

// Box drawing characters
const BOX = {
  TL: '┌', TR: '┐', BL: '└', BR: '┘',
  H: '─', V: '│',
  TLH: '╔', TRH: '╗', BLH: '╚', BRH: '╝',
  HH: '═',
}

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
 * Get mock radio configuration data
 */
export const getMockRadioConfig = () => {
  return {
    lora: {
      enabled: true,
      freq: '915.000 MHz',
      sf: '7 / 9 (long range)',
      bw: '125 kHz',
      cr: '4/5',
      txPower: '20 dBm (1W EIRP)',
      preamble: '8 symbols',
      sync: '0x12 private',
      status: 'TX/RX ACTIVE'
    },
    halow: {
      enabled: true,
      ssid: 'MYC3LIUM_HALOW',
      freq: '2339.1 MHz',
      mode: '802.11ah STA',
      txPower: '20 dBm',
      snr: '37 dB GOOD',
      bitrate: '2.5 Mbps',
      status: 'ASSOCIATED'
    },
    sdr: {
      enabled: false,
      center: '915.000 MHz',
      bw: '2.4 MHz',
      gain: '32.8 dB AGC',
      ppm: '0 correction',
      range: '300Hz-2.3GHz',
      driver: 'SoapySDR',
      status: 'STANDBY'
    },
    mesh: {
      batmanAdv: 'MESH OK',
      rns: 'E2E ENCRYPTED',
      meshtastic: 'BRIDGE ACTIVE',
      fccCompliance: 'FCC Part 15.247'
    }
  }
}

/**
 * Render radio configuration interface
 * 
 * Grid is 40 cols x 25 rows - vertical stacked layout
 */
export const renderRadioConfig = (data) => {
  const grid = createGrid()

  // Title and separator
  writeText(grid, 1, 0, 'RADIO CONFIG')
  writeText(grid, 14, 0, BOX.H.repeat(COLUMNS - 15))
  writeText(grid, 1, 1, 'P600')
  writeText(grid, 7, 1, BOX.H.repeat(COLUMNS - 8))

  let row = 3

  // LoRa Section
  writeText(grid, 1, row, 'LoRa')
  writeText(grid, 7, row, BOX.H.repeat(4))
  writeText(grid, 12, row, '915 MHz SX1262')
  row++
  drawBox(grid, 1, row, COLUMNS - 2, 5)
  row++
  
  const loraItems = [
    ['FREQ', data.lora.freq],
    ['SF', data.lora.sf.substring(0, 18)],
    ['TX', data.lora.txPower.substring(0, 18)],
    ['ST', data.lora.status]
  ]
  
  loraItems.forEach(([key, value]) => {
    writeText(grid, 3, row, key)
    writeText(grid, 8, row, value)
    row++
  })

  row++ // spacing

  // HaLow Section
  writeText(grid, 1, row, 'HaLow')
  writeText(grid, 8, row, BOX.H.repeat(4))
  writeText(grid, 13, row, '902-928')
  row++
  drawBox(grid, 1, row, COLUMNS - 2, 5)
  row++
  
  const halowItems = [
    ['SSID', data.halow.ssid],
    ['FREQ', data.halow.freq],
    ['SNR', data.halow.snr],
    ['ST', data.halow.status]
  ]
  
  halowItems.forEach(([key, value]) => {
    writeText(grid, 3, row, key)
    writeText(grid, 9, row, value)
    row++
  })

  row++ // spacing

  // SDR Section
  writeText(grid, 1, row, 'SDR')
  writeText(grid, 6, row, BOX.H.repeat(4))
  writeText(grid, 11, row, 'RTL-SDR')
  row++
  drawBox(grid, 1, row, COLUMNS - 2, 4)
  row++
  
  const sdrItems = [
    ['GAIN', data.sdr.gain],
    ['DRV', data.sdr.driver],
    ['ST', data.sdr.status]
  ]
  
  sdrItems.forEach(([key, value]) => {
    writeText(grid, 3, row, key)
    writeText(grid, 9, row, value)
    row++
  })

  // Footer - mesh network status
  const footerY = ROWS - 2
  drawHLine(grid, 0, footerY - 1, COLUMNS, BOX.H)
  
  // Compact mesh status
  writeText(grid, 1, footerY, `BATMAN ${DOT} RNS ${DOT} MESHTASTIC ${DOT} FCC`)

  // Hotkey hints
  writeText(grid, 1, footerY + 1, '[L] [H] [D] [S] [A] [ESC]')

  return grid
}

/**
 * Update radio config based on user selection
 * (Placeholder for future interactive controls)
 */
export const updateRadioConfig = (currentConfig, interface_name, param, value) => {
  const updated = { ...currentConfig }
  
  if (updated[interface_name]) {
    updated[interface_name] = {
      ...updated[interface_name],
      [param]: value
    }
  }
  
  return updated
}
