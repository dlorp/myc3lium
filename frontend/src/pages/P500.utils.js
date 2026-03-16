import { COLUMNS, ROWS } from '../components/TeletextGrid'

const BOX = { TL: '┌', TR: '┐', BL: '└', BR: '┘', H: '─', V: '│', TLH: '╔', TRH: '╗', BLH: '╚', BRH: '╝', HH: '═' }
const DOT = '●'
const ARROW = '▸'
const BLOCK = '▓'
const BLOCK_LIGHT = '░'

const createGrid = () => Array.from({ length: ROWS }, () => Array.from({ length: COLUMNS }, () => ' '))

const writeText = (grid, x, y, text) => {
  if (y < 0 || y >= ROWS) return
  for (let i = 0; i < text.length; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS) grid[y][col] = text[i]
  }
}

const drawHLine = (grid, x, y, length, char = BOX.H) => {
  for (let i = 0; i < length; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS && y >= 0 && y < ROWS) grid[y][col] = char
  }
}

const drawBox = (grid, x, y, width, height) => {
  if (x >= 0 && x < COLUMNS && y >= 0 && y < ROWS) grid[y][x] = BOX.TL
  if (x >= 0 && x < COLUMNS && y + height - 1 >= 0 && y + height - 1 < ROWS) grid[y + height - 1][x] = BOX.BL
  if (x + width - 1 >= 0 && x + width - 1 < COLUMNS && y >= 0 && y < ROWS) grid[y][x + width - 1] = BOX.TR
  if (x + width - 1 >= 0 && x + width - 1 < COLUMNS && y + height - 1 >= 0 && y + height - 1 < ROWS) grid[y + height - 1][x + width - 1] = BOX.BR
  drawHLine(grid, x + 1, y, width - 2, BOX.H)
  drawHLine(grid, x + 1, y + height - 1, width - 2, BOX.H)
  for (let i = 0; i < height - 2; i++) {
    const row = y + 1 + i
    if (row >= 0 && row < ROWS) {
      if (x >= 0 && x < COLUMNS) grid[row][x] = BOX.V
      if (x + width - 1 >= 0 && x + width - 1 < COLUMNS) grid[row][x + width - 1] = BOX.V
    }
  }
}

const drawSparkline = (grid, x, y, width, data) => {
  if (data.length === 0 || y < 0 || y >= ROWS) return
  const max = Math.max(...data), min = Math.min(...data), range = max - min || 1
  const chars = ['_', '.', ':', ';', '|', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']
  for (let i = 0; i < Math.min(width, data.length); i++) {
    const val = data[data.length - width + i] || data[i]
    const normalized = (val - min) / range
    const charIndex = Math.floor(normalized * (chars.length - 1))
    const col = x + i
    if (col >= 0 && col < COLUMNS) grid[y][col] = chars[charIndex] || '_'
  }
}

export const getMockIntelData = () => ({
  satellites: [
    { name: 'NOAA-19 APT', azimuth: 214, elevation: 42, frequency: '137.100 MHz', mode: 'APT', pass: true, eta: 'NOW', maxEl: '68°', aos: null, los: null },
    { name: 'METEOR-M2', azimuth: null, elevation: null, frequency: '137.900 MHz', mode: 'LRPT', pass: false, eta: '14m', maxEl: '72°', aos: '14:42', los: '14:51' },
    { name: 'NOAA-15', azimuth: null, elevation: null, frequency: '137.620 MHz', mode: 'APT', pass: false, eta: '47m', maxEl: '44°', aos: '15:15', los: '15:24' },
    { name: 'ISS', azimuth: null, elevation: null, frequency: '145.800 MHz', mode: 'FM', pass: false, eta: '2h12m', maxEl: '81°', aos: '16:40', los: '16:48' },
  ],
  spectrum: { centerFreq: 915.0, span: 2.4, gain: 32.8, rbw: 10, waterfall: [] },
  sensors: [
    { id: 'RHIZOME-02', callsign: 'Ravine', temp: 6.4, humidity: 87, pressure: 1007, motion: false, battery: 81, status: 'GOOD', trend: [6.1, 6.2, 6.3, 6.4, 6.4, 6.5, 6.4, 6.4] },
    { id: 'RHIZOME-03', callsign: 'Ridge', temp: 18.2, humidity: 45, pressure: 1015, motion: true, battery: 68, status: 'FAIR', trend: [6.5, 8.2, 12.1, 15.4, 16.8, 17.5, 18.0, 18.2] },
  ],
})

export const updateSatellitePasses = (satellites) => {
  satellites.forEach(sat => {
    if (sat.pass && sat.elevation !== null) {
      sat.elevation = Math.max(0, sat.elevation + (Math.random() - 0.3) * 2)
      sat.azimuth = (sat.azimuth + Math.random() * 1.5) % 360
      if (sat.elevation < 1) { sat.pass = false; sat.elevation = null; sat.azimuth = null }
    }
  })
}

export const updateRFSpectrum = (spectrum) => {
  const width = COLUMNS - 4, row = []
  for (let i = 0; i < width; i++) {
    const freq = i / width
    let intensity = Math.random() * 0.15
    if (Math.abs(freq - 0.5) < 0.02) intensity += 0.6 + Math.random() * 0.2
    if (Math.abs(freq - 0.7) < 0.03) intensity += 0.5 + Math.random() * 0.15
    row.push(Math.min(1, intensity))
  }
  spectrum.waterfall.unshift(row)
  if (spectrum.waterfall.length > 15) spectrum.waterfall.pop()
}

export const updateSensorData = (sensors) => {
  sensors.forEach(sensor => {
    sensor.temp = Math.max(0, sensor.temp + (Math.random() - 0.5) * 0.3)
    sensor.trend.shift(); sensor.trend.push(sensor.temp)
    sensor.humidity = Math.max(0, Math.min(100, sensor.humidity + (Math.random() - 0.5) * 2))
    sensor.pressure = Math.max(950, Math.min(1050, sensor.pressure + (Math.random() - 0.5) * 0.5))
    if (Math.random() < 0.1) sensor.motion = !sensor.motion
  })
}

const renderSatelliteView = (grid, satellites) => {
  let row = 3
  writeText(grid, 2, row, `${BOX.HH}${BOX.HH} SATELLITE TRACKER ${BOX.HH} pyorbital + SatDump ${BOX.HH}${BOX.HH}${BOX.HH}`)
  row += 2
  writeText(grid, 2, row, 'SAT'); writeText(grid, 16, row, 'AZ'); writeText(grid, 22, row, 'EL'); writeText(grid, 28, row, 'FREQ'); writeText(grid, 40, row, 'ETA'); writeText(grid, 48, row, 'AOS'); writeText(grid, 56, row, 'LOS'); writeText(grid, 64, row, 'MAX'); row++
  drawHLine(grid, 2, row, COLUMNS - 4, BOX.H); row++
  satellites.forEach((sat, i) => {
    const prefix = sat.pass ? `${ARROW} ` : '  '
    writeText(grid, 2, row + i * 2, prefix + sat.name)
    writeText(grid, 16, row + i * 2, sat.azimuth !== null ? sat.azimuth.toFixed(0) + '°' : '---')
    writeText(grid, 22, row + i * 2, sat.elevation !== null ? sat.elevation.toFixed(0) + '°' : '---')
    writeText(grid, 28, row + i * 2, sat.frequency)
    writeText(grid, 40, row + i * 2, sat.eta)
    writeText(grid, 48, row + i * 2, sat.aos || '---')
    writeText(grid, 56, row + i * 2, sat.los || '---')
    writeText(grid, 64, row + i * 2, sat.maxEl)
    writeText(grid, 2, row + i * 2 + 1, `  MODE: ${sat.mode}`)
  })
}

const renderRFSpectrumView = (grid, spectrum) => {
  let row = 3
  writeText(grid, 2, row, `${BOX.HH}${BOX.HH} RF SPECTRUM ${BOX.HH} RTL-SDR + SoapySDR ${BOX.HH}${BOX.HH}${BOX.HH}${BOX.HH}${BOX.HH}`)
  row += 2
  const waterfallY = row, waterfallHeight = 15, waterfallX = 2, waterfallWidth = COLUMNS - 4
  drawBox(grid, waterfallX, waterfallY, waterfallWidth, waterfallHeight)
  spectrum.waterfall.forEach((rowData, i) => {
    const y = waterfallY + 1 + i
    if (y >= waterfallY + waterfallHeight - 1) return
    rowData.forEach((intensity, x) => {
      const col = waterfallX + 1 + x
      if (col >= waterfallX + waterfallWidth - 1) return
      let char = ' '
      if (intensity < 0.2) char = ' '
      else if (intensity < 0.4) char = '.'
      else if (intensity < 0.6) char = ':'
      else if (intensity < 0.8) char = BLOCK_LIGHT
      else char = BLOCK
      if (col >= 0 && col < COLUMNS && y >= 0 && y < ROWS) grid[y][col] = char
    })
  })
  row = waterfallY + waterfallHeight + 1
  writeText(grid, 2, row, `CENTER: ${spectrum.centerFreq.toFixed(3)} MHz`)
  writeText(grid, 26, row, `SPAN: ${spectrum.span} MHz`); row++
  writeText(grid, 2, row, `GAIN: ${spectrum.gain} dB`)
  writeText(grid, 26, row, `RBW: ${spectrum.rbw} kHz`)
}

const renderSensorTelemetryView = (grid, sensors) => {
  let row = 3
  writeText(grid, 2, row, `${BOX.HH}${BOX.HH} SENSOR TELEMETRY ${BOX.HH} RHIZOME GRID ${BOX.HH}${BOX.HH}${BOX.HH}${BOX.HH}${BOX.HH}`)
  row += 2
  writeText(grid, 2, row, 'NODE'); writeText(grid, 18, row, 'TEMP'); writeText(grid, 26, row, 'HUM'); writeText(grid, 32, row, 'PRES'); writeText(grid, 40, row, 'MOT'); writeText(grid, 46, row, 'BAT'); writeText(grid, 52, row, 'TREND'); writeText(grid, 66, row, 'ST'); row++
  drawHLine(grid, 2, row, COLUMNS - 4, BOX.H); row++
  sensors.forEach((sensor) => {
    writeText(grid, 2, row, `${sensor.id} //${sensor.callsign}`)
    writeText(grid, 18, row, sensor.temp.toFixed(1) + '°C')
    writeText(grid, 26, row, sensor.humidity.toFixed(0) + '%')
    writeText(grid, 32, row, sensor.pressure.toFixed(0) + 'mb')
    writeText(grid, 40, row, sensor.motion ? 'YES' : 'NO')
    writeText(grid, 46, row, sensor.battery + '%')
    drawSparkline(grid, 52, row, 12, sensor.trend)
    writeText(grid, 66, row, sensor.status)
    row += 2
  })
  drawHLine(grid, 2, ROWS - 3, COLUMNS - 4, BOX.H)
  writeText(grid, 2, ROWS - 2, `${sensors.length} RHIZOME NODES ONLINE ${DOT} CBOR TELEMETRY`)
}

export const renderIntelligenceHub = (data, viewMode) => {
  const grid = createGrid()
  writeText(grid, 2, 0, `${DOT}INTELLIGENCE HUB${DOT}`)
  drawHLine(grid, 0, 1, COLUMNS)
  const satTab = viewMode === 'sat' ? `[S]SATELLITE` : ` S SATELLITE `
  const rfTab = viewMode === 'rf' ? `[R]SPECTRUM` : ` R SPECTRUM `
  const telTab = viewMode === 'tel' ? `[T]SENSORS` : ` T SENSORS `
  writeText(grid, 2, 2, satTab + ' ' + rfTab + ' ' + telTab)
  if (viewMode === 'sat') renderSatelliteView(grid, data.satellites)
  else if (viewMode === 'rf') renderRFSpectrumView(grid, data.spectrum)
  else if (viewMode === 'tel') renderSensorTelemetryView(grid, data.sensors)
  drawHLine(grid, 0, ROWS - 1, COLUMNS)
  writeText(grid, 2, ROWS - 1, 'S=Sat  R=RF  T=Sensors')
  return grid
}
