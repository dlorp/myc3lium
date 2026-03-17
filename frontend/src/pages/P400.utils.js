import { COLUMNS, ROWS } from '../components/TeletextGrid'

// Box drawing characters
const BOX = {
  TL: '┌', TR: '┐', BL: '└', BR: '┘',
  H: '─', V: '│',
}

// Map symbols
const SYMBOLS = {
  SPORE: '◆',    // Base station
  HYPHA: '●',    // Relay node
  FROND: '◇',    // Sensor node
  RHIZOME: '■',  // Environmental sensor
  CURRENT: '⊕',  // Current position marker
  WAYPOINT: '▸', // Waypoint marker
}

// Terrain characters (ASCII art height map)
const TERRAIN = {
  WATER: '≈',
  LOW: '.',
  MED: '·',
  HIGH: '^',
  PEAK: '▲',
}

// Node type markers
const NODE_TYPES = {
  SPORE: { symbol: SYMBOLS.SPORE, char: 'S' },
  HYPHA: { symbol: SYMBOLS.HYPHA, char: 'H' },
  FROND: { symbol: SYMBOLS.FROND, char: 'F' },
  RHIZOME: { symbol: SYMBOLS.RHIZOME, char: 'R' },
}

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
  const row = Math.floor(y)
  if (row < 0 || row >= ROWS) return
  for (let i = 0; i < text.length; i++) {
    const col = Math.floor(x) + i
    if (col >= 0 && col < COLUMNS) {
      grid[row][col] = text[i]
    }
  }
}

/**
 * Draw horizontal line
 */
const drawHLine = (grid, y, char = BOX.H) => {
  for (let x = 0; x < COLUMNS; x++) {
    if (y >= 0 && y < ROWS) {
      grid[y][x] = char
    }
  }
}

/**
 * Draw a character at grid position
 */
const drawChar = (grid, x, y, char) => {
  const col = Math.floor(x)
  const row = Math.floor(y)
  if (col >= 0 && col < COLUMNS && row >= 0 && row < ROWS) {
    grid[row][col] = char
  }
}

/**
 * Simple 2D noise function for terrain generation
 */
const noise2D = (x, y, seed = 0) => {
  const n = Math.sin(x * 12.9898 + y * 78.233 + seed) * 43758.5453
  return n - Math.floor(n)
}

/**
 * Fractal Brownian Motion for terrain heightmap
 */
const fbm = (x, y) => {
  let value = 0
  let amplitude = 1
  let frequency = 1
  
  for (let i = 0; i < 4; i++) {
    value += amplitude * noise2D(x * frequency, y * frequency, i)
    amplitude *= 0.5
    frequency *= 2
  }
  
  return value / 2 // Normalize to ~0-1 range
}

/**
 * Generate terrain heightmap for map display
 */
const generateTerrain = (width, height, offsetX = 0, offsetY = 0, zoom = 1) => {
  const terrain = []
  
  for (let y = 0; y < height; y++) {
    const row = []
    for (let x = 0; x < width; x++) {
      const worldX = (x + offsetX) * zoom * 0.08
      const worldY = (y + offsetY) * zoom * 0.08
      const height = fbm(worldX, worldY)
      
      row.push(height)
    }
    terrain.push(row)
  }
  
  return terrain
}

/**
 * Render terrain as ASCII characters
 */
const renderTerrain = (grid, terrain, viewX, viewY, viewWidth, viewHeight) => {
  for (let y = 0; y < viewHeight && y < terrain.length; y++) {
    for (let x = 0; x < viewWidth && x < terrain[0].length; x++) {
      const height = terrain[y][x]
      let char = ' '
      
      if (height < 0.2) {
        char = TERRAIN.WATER
      } else if (height < 0.35) {
        char = TERRAIN.LOW
      } else if (height < 0.5) {
        char = TERRAIN.MED
      } else if (height < 0.7) {
        char = TERRAIN.HIGH
      } else {
        char = TERRAIN.PEAK
      }
      
      const screenX = viewX + x
      const screenY = viewY + y
      
      drawChar(grid, screenX, screenY, char)
    }
  }
}

/**
 * Calculate distance between two GPS coordinates (Haversine formula)
 * Returns distance in kilometers
 */
export const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371 // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2)
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

/**
 * Calculate bearing between two GPS coordinates
 * Returns bearing in degrees (0-360)
 */
export const calculateBearing = (lat1, lon1, lat2, lon2) => {
  const dLon = (lon2 - lon1) * Math.PI / 180
  const lat1Rad = lat1 * Math.PI / 180
  const lat2Rad = lat2 * Math.PI / 180
  
  const y = Math.sin(dLon) * Math.cos(lat2Rad)
  const x = Math.cos(lat1Rad) * Math.sin(lat2Rad) -
           Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon)
  
  const bearing = Math.atan2(y, x) * 180 / Math.PI
  return (bearing + 360) % 360
}

/**
 * Convert GPS coordinates to map grid coordinates
 */
const gpsToMapCoords = (lat, lon, centerLat, centerLon, zoom = 1) => {
  // Simple mercator-ish projection for small areas
  // Scale factor: ~111km per degree latitude, ~85km per degree longitude at 60°N
  const latScale = 111 / zoom
  const lonScale = 85 / zoom
  
  const dx = (lon - centerLon) * lonScale
  const dy = (centerLat - lat) * latScale // Inverted Y for screen coords
  
  return { x: dx, y: dy }
}

/**
 * Generate mock GPS data for nodes
 */
export const getMockGPSData = () => {
  const centerLat = 61.2181
  const centerLon = -149.9003
  
  return {
    currentPosition: {
      lat: centerLat,
      lon: centerLon,
      alt: 125,
      accuracy: 3.2,
      satellites: 8,
      fixType: '3D-FIX',
    },
    nodes: [
      {
        id: 'SPORE-01',
        callsign: 'NEXUS',
        type: 'SPORE',
        lat: centerLat,
        lon: centerLon,
        alt: 125,
        status: 'BASE',
        rssi: null,
        battery: 74,
      },
      {
        id: 'HYPHA-03',
        callsign: 'Ranger',
        type: 'HYPHA',
        lat: 61.3012,
        lon: -150.1204,
        alt: 892,
        status: 'GOOD',
        rssi: -78,
        battery: 85,
      },
      {
        id: 'FROND-02',
        callsign: 'Kestrel',
        type: 'FROND',
        lat: 61.2890,
        lon: -149.8441,
        alt: 1204,
        status: 'GOOD',
        rssi: -72,
        battery: 91,
      },
      {
        id: 'RHIZOME-02',
        callsign: 'Ravine',
        type: 'RHIZOME',
        lat: 61.2340,
        lon: -149.9780,
        alt: 188,
        status: 'GOOD',
        rssi: -82,
        battery: 81,
      },
      {
        id: 'RHIZOME-03',
        callsign: 'Ridge',
        type: 'RHIZOME',
        lat: 61.2778,
        lon: -149.8012,
        alt: 1022,
        status: 'FAIR',
        rssi: -88,
        battery: 68,
      },
    ],
    waypoints: [
      {
        id: 'WP-001',
        name: 'BASECAMP ALPHA',
        lat: centerLat,
        lon: centerLon,
        alt: 125,
        type: 'BASE',
      },
      {
        id: 'WP-002',
        name: 'CASTLE LAKE',
        lat: 61.3012,
        lon: -150.1204,
        alt: 892,
        type: 'POI',
      },
      {
        id: 'WP-003',
        name: 'RIDGE OVERLOOK',
        lat: 61.2890,
        lon: -149.8441,
        alt: 1204,
        type: 'OBS',
      },
    ],
  }
}

/**
 * Render tactical map with GPS nodes and waypoints
 */
export const renderTacticalMap = (gpsData, panX = 0, panY = 0, zoom = 1, selectedNode = null) => {
  const grid = createGrid()
  
  // Map viewport (leaving room for info panels)
  const mapStartY = 3
  const mapHeight = ROWS - mapStartY - 7
  const mapStartX = 0
  const mapWidth = COLUMNS
  
  // Generate terrain
  const terrain = generateTerrain(
    mapWidth,
    mapHeight,
    panX,
    panY,
    zoom
  )
  
  // Render terrain
  renderTerrain(grid, terrain, mapStartX, mapStartY, mapWidth, mapHeight)
  
  // Calculate map center in GPS coords
  const centerLat = gpsData.currentPosition.lat
  const centerLon = gpsData.currentPosition.lon
  
  // Map center in screen coords
  const screenCenterX = mapStartX + Math.floor(mapWidth / 2)
  const screenCenterY = mapStartY + Math.floor(mapHeight / 2)
  
  // Draw grid overlay (subtle)
  for (let y = mapStartY; y < mapStartY + mapHeight; y += 4) {
    for (let x = mapStartX; x < mapWidth; x += 6) {
      if (grid[y][x] === ' ' || grid[y][x] === TERRAIN.LOW) {
        grid[y][x] = '·'
      }
    }
  }
  
  // Draw nodes
  gpsData.nodes.forEach(node => {
    const coords = gpsToMapCoords(node.lat, node.lon, centerLat, centerLon, zoom)
    const screenX = screenCenterX + Math.round(coords.x) - panX
    const screenY = screenCenterY + Math.round(coords.y) - panY
    
    // Only draw if in viewport
    if (screenX >= mapStartX && screenX < mapStartX + mapWidth &&
        screenY >= mapStartY && screenY < mapStartY + mapHeight) {
      
      const nodeType = NODE_TYPES[node.type] || NODE_TYPES.HYPHA
      drawChar(grid, screenX, screenY, nodeType.symbol)
      
      // Draw node label
      const label = `${nodeType.char}`
      writeText(grid, screenX + 1, screenY, label)
    }
  })
  
  // Draw current position marker
  drawChar(grid, screenCenterX - panX, screenCenterY - panY, SYMBOLS.CURRENT)
  
  // Draw waypoints
  gpsData.waypoints.forEach(wp => {
    const coords = gpsToMapCoords(wp.lat, wp.lon, centerLat, centerLon, zoom)
    const screenX = screenCenterX + Math.round(coords.x) - panX
    const screenY = screenCenterY + Math.round(coords.y) - panY
    
    if (screenX >= mapStartX && screenX < mapStartX + mapWidth &&
        screenY >= mapStartY && screenY < mapStartY + mapHeight) {
      drawChar(grid, screenX, screenY, SYMBOLS.WAYPOINT)
    }
  })
  
  // Header
  writeText(grid, 1, 0, 'P400 TACTICAL MAP')
  writeText(grid, COLUMNS - 18, 0, `Z:${zoom.toFixed(1)} GPS:${gpsData.currentPosition.fixType}`)
  drawHLine(grid, 1)
  
  // GPS status line
  const gpsStatus = `${gpsData.currentPosition.lat.toFixed(4)}°N ${Math.abs(gpsData.currentPosition.lon).toFixed(4)}°W ±${gpsData.currentPosition.accuracy}m ${gpsData.currentPosition.satellites}SV`
  writeText(grid, 1, 2, gpsStatus)
  
  // Bottom info panel
  const infoY = ROWS - 6
  drawHLine(grid, infoY)
  
  // Node list
  writeText(grid, 1, infoY + 1, 'NODES:')
  gpsData.nodes.slice(0, 3).forEach((node, i) => {
    const dist = calculateDistance(
      gpsData.currentPosition.lat,
      gpsData.currentPosition.lon,
      node.lat,
      node.lon
    )
    const bearing = calculateBearing(
      gpsData.currentPosition.lat,
      gpsData.currentPosition.lon,
      node.lat,
      node.lon
    )
    
    const nodeType = NODE_TYPES[node.type] || NODE_TYPES.HYPHA
    const info = `${nodeType.symbol}${node.id.slice(-2)} ${dist.toFixed(1)}km ${Math.round(bearing)}°`
    writeText(grid, 1, infoY + 2 + i, info)
  })
  
  // Waypoint list (middle)
  writeText(grid, 30, infoY + 1, 'WAYPOINTS:')
  gpsData.waypoints.slice(0, 3).forEach((wp, i) => {
    const dist = calculateDistance(
      gpsData.currentPosition.lat,
      gpsData.currentPosition.lon,
      wp.lat,
      wp.lon
    )
    const bearing = calculateBearing(
      gpsData.currentPosition.lat,
      gpsData.currentPosition.lon,
      wp.lat,
      wp.lon
    )
    
    const info = `${SYMBOLS.WAYPOINT}${wp.name.slice(0, 6)} ${dist.toFixed(1)}km ${Math.round(bearing)}°`
    writeText(grid, 30, infoY + 2 + i, info)
  })
  
  // Controls
  const ctrlY = ROWS - 1
  writeText(grid, 1, ctrlY, '[ARROWS]Pan [+/-]Zoom [W]Waypts [ESC]Clear')
  
  // Selected node detail (if any)
  if (selectedNode) {
    const detailX = COLUMNS - 25
    const detailY = 3
    
    writeText(grid, detailX, detailY, `NODE: ${selectedNode.id}`)
    writeText(grid, detailX, detailY + 1, selectedNode.callsign || '')
    writeText(grid, detailX, detailY + 2, `${selectedNode.lat.toFixed(4)}°`)
    writeText(grid, detailX, detailY + 3, `${selectedNode.lon.toFixed(4)}°`)
    writeText(grid, detailX, detailY + 4, `ALT ${selectedNode.alt}m`)
    
    if (selectedNode.rssi) {
      writeText(grid, detailX, detailY + 5, `${selectedNode.rssi}dBm`)
    }
    
    writeText(grid, detailX, detailY + 6, `BAT ${selectedNode.battery}%`)
  }
  
  // Compass rose (top right)
  const compassX = COLUMNS - 6
  const compassY = 3
  writeText(grid, compassX, compassY - 1, '  N  ')
  writeText(grid, compassX, compassY, 'W + E')
  writeText(grid, compassX, compassY + 1, '  S  ')
  
  return grid
}
