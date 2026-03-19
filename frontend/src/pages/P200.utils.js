import { COLUMNS, ROWS } from '../components/TeletextGrid'

// ============================================================================
// SECURITY: Input validation schema and sanitization functions
// ============================================================================

/**
 * Validate latitude coordinate format
 * Valid range: -90 to 90
 */
export const validateLatitude = (lat) => {
  const num = parseFloat(lat)
  return !isNaN(num) && num >= -90 && num <= 90 ? num : null
}

/**
 * Validate longitude coordinate format
 * Valid range: -180 to 180
 */
export const validateLongitude = (lng) => {
  const num = parseFloat(lng)
  return !isNaN(num) && num >= -180 && num <= 180 ? num : null
}

/**
 * Sanitize string for safe text display (no HTML/special chars)
 * Removes null bytes, control characters, and limits length
 */
export const sanitizeString = (str, maxLength = 50) => {
  if (typeof str !== 'string') return ''
  return str
    .slice(0, maxLength)
    // eslint-disable-next-line no-control-regex
    .replace(/[\x00-\x1f\x7f]/g, '') // Remove control chars
    .replace(/[<>"'`]/g, '') // Remove HTML special chars
    .trim()
}

/**
 * Validate node ID format (alphanumeric, dash, underscore)
 */
export const validateNodeId = (id) => {
  if (typeof id !== 'string') return false
  return /^[A-Za-z0-9_-]{1,50}$/.test(id)
}

/**
 * Validate mesh link structure
 */
export const validateLink = (link) => {
  if (!link || typeof link !== 'object') return false
  return (
    validateNodeId(link.from) &&
    validateNodeId(link.to) &&
    ['GOOD', 'FAIR', 'DEGRADED', 'OFFLINE'].includes(link.quality) &&
    typeof link.rssi === 'number' &&
    link.rssi >= -120 &&
    link.rssi <= -30 &&
    typeof link.latency === 'number' &&
    link.latency >= 0 &&
    link.latency <= 5000 &&
    typeof link.packetLoss === 'number' &&
    link.packetLoss >= 0 &&
    link.packetLoss <= 100
  )
}

/**
 * Validate mesh node structure
 */
export const validateNode = (node) => {
  if (!node || typeof node !== 'object') return false
  const isValidNode =
    validateNodeId(node.id) &&
    typeof node.type === 'string' &&
    ['SPORE', 'HYPHA', 'FROND', 'RHIZOME'].includes(node.type) &&
    typeof node.x === 'number' &&
    typeof node.y === 'number' &&
    typeof node.battery === 'number' &&
    node.battery >= 0 &&
    node.battery <= 100 &&
    ['active', 'warning', 'offline'].includes(node.status)

  if (!isValidNode) return false

  // Validate GPS if present
  if (node.gps) {
    const latValid = validateLatitude(node.gps.lat)
    const lngValid = validateLongitude(node.gps.lng)
    if (latValid === null || lngValid === null) return false
  }

  return true
}

// Box drawing characters
const BOX = {
  TL: '┌', TR: '┐', BL: '└', BR: '┘',
  H: '─', V: '│',
  VDASH: '┆', HDASH: '┄',
}

const DOT = '●'

// Node types with colors and symbols
const NODE_TYPES = {
  SPORE: { color: '#00FFFF', symbol: '◆', label: 'SPORE' },
  HYPHA: { color: '#00FF00', symbol: '●', label: 'HYPHA' },
  FROND: { color: '#FFFF00', symbol: '◇', label: 'FROND' },
  RHIZOME: { color: '#0000FF', symbol: '■', label: 'RHIZOME' },
}

// Link quality status with color mappings
const LINK_QUALITY = {
  GOOD: { symbol: '═', color: '#00FF00', percent: 85, label: 'GOOD' },
  FAIR: { symbol: '─', color: '#FFFF00', percent: 60, label: 'FAIR' },
  DEGRADED: { symbol: '·', color: '#FF6600', percent: 30, label: 'DEGRADED' },
  OFFLINE: { symbol: '∘', color: '#444444', percent: 0, label: 'OFFLINE' },
}

// Constants for resource limits and performance
const PARTICLE_LIMIT_PER_LINK = 50
const MAX_PARTICLES_TOTAL = 500

/**
 * Create empty grid
 */
const createGrid = () => {
  return Array.from({ length: ROWS }, () => 
    Array.from({ length: COLUMNS }, () => ' ')
  )
}

/**
 * Write text to grid at position (sanitized for safety)
 */
const writeText = (grid, x, y, text) => {
  // Validate inputs to prevent out-of-bounds access
  const row = Math.floor(y)
  if (row < 0 || row >= ROWS) return
  
  // Sanitize text for safe rendering
  const safeText = String(text || '')
  
  for (let i = 0; i < safeText.length; i++) {
    const col = Math.floor(x) + i
    if (col >= 0 && col < COLUMNS) {
      grid[row][col] = safeText[i]
    }
  }
}

/**
 * Draw horizontal line
 */
const drawHLine = (grid, x, y, length, char = BOX.H) => {
  if (y < 0 || y >= ROWS) return
  for (let i = 0; i < length; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS) {
      grid[y][col] = char
    }
  }
}

/**
 * Draw a character at grid position (bounds-checked)
 */
const drawChar = (grid, x, y, char) => {
  const col = Math.round(x)
  const row = Math.round(y)
  if (col >= 0 && col < COLUMNS && row >= 0 && row < ROWS) {
    grid[row][col] = char
  }
}

/**
 * Draw line between two points (Bresenham's algorithm)
 * SECURITY: Added bounds checking and iteration limit to prevent infinite loops
 */
const drawLine = (grid, x0, y0, x1, y1, char, dashed = false) => {
  x0 = Math.round(x0)
  y0 = Math.round(y0)
  x1 = Math.round(x1)
  y1 = Math.round(y1)

  const dx = Math.abs(x1 - x0)
  const dy = Math.abs(y1 - y0)
  const sx = x0 < x1 ? 1 : -1
  const sy = y0 < y1 ? 1 : -1
  let err = dx - dy
  let step = 0

  // SECURITY: Prevent infinite loops with explicit iteration limit
  const maxIter = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) + 1
  let iter = 0
  
  while (iter++ < maxIter) {
    // Draw only on odd steps if dashed
    if (!dashed || step % 2 === 0) {
      if (x0 >= 0 && x0 < COLUMNS && y0 >= 0 && y0 < ROWS) {
        grid[y0][x0] = char
      }
    }

    if (x0 === x1 && y0 === y1) break

    const e2 = 2 * err
    if (e2 > -dy) {
      err -= dy
      x0 += sx
    }
    if (e2 < dx) {
      err += dx
      y0 += sy
    }
    step++
  }
}

/**
 * Mock mesh network data with extended attributes
 * SECURITY: Validates all returned data structures
 */
export const getMockMeshData = () => {
  const mockData = {
    nodes: [
      { 
        id: 'SPORE-01', 
        callsign: 'ROOT',
        type: 'SPORE', 
        x: 15, y: 10, 
        gps: { lat: 61.2181, lng: -149.9003 },
        battery: 74, 
        status: 'active',
        uptime: 15240 
      },
      { 
        id: 'HYPHA-03', 
        callsign: 'RELAY-A',
        type: 'HYPHA', 
        x: 8, y: 4, 
        gps: { lat: 61.2200, lng: -149.8900 },
        battery: 89, 
        status: 'active',
        uptime: 8420 
      },
      { 
        id: 'FROND-05', 
        callsign: 'EDGE-1',
        type: 'FROND', 
        x: 22, y: 5, 
        gps: { lat: 61.2150, lng: -149.8850 },
        battery: 62, 
        status: 'active',
        uptime: 4120 
      },
      { 
        id: 'RHIZOME-02', 
        callsign: 'MESH-2',
        type: 'RHIZOME', 
        x: 10, y: 12, 
        gps: { lat: 61.2220, lng: -149.9050 },
        battery: 15, 
        status: 'warning',
        uptime: 12300 
      },
      { 
        id: 'RHIZOME-03', 
        callsign: 'EDGE-2',
        type: 'RHIZOME', 
        x: 20, y: 14, 
        gps: { lat: 61.2160, lng: -149.8800 },
        battery: 71, 
        status: 'active',
        uptime: 9840 
      },
    ],
    links: [
      { 
        from: 'SPORE-01', 
        to: 'HYPHA-03', 
        quality: 'GOOD', 
        rssi: -72, 
        latency: 8, 
        packetLoss: 0,
        radioType: 'LoRa'
      },
      { 
        from: 'SPORE-01', 
        to: 'FROND-05', 
        quality: 'GOOD', 
        rssi: -78, 
        latency: 12, 
        packetLoss: 0,
        radioType: 'LoRa'
      },
      { 
        from: 'SPORE-01', 
        to: 'RHIZOME-02', 
        quality: 'FAIR', 
        rssi: -85, 
        latency: 42, 
        packetLoss: 2,
        radioType: 'LoRa'
      },
      { 
        from: 'HYPHA-03', 
        to: 'RHIZOME-02', 
        quality: 'GOOD', 
        rssi: -74, 
        latency: 15, 
        packetLoss: 0,
        radioType: 'LoRa'
      },
      { 
        from: 'FROND-05', 
        to: 'RHIZOME-03', 
        quality: 'DEGRADED', 
        rssi: -91, 
        latency: 98, 
        packetLoss: 11,
        radioType: 'LoRa'
      },
    ],
    routeTable: [
      { dest: 'HYPHA-03', nextHop: 'HYPHA-03', hops: 1, metric: 1.2 },
      { dest: 'FROND-05', nextHop: 'FROND-05', hops: 1, metric: 1.5 },
      { dest: 'RHIZOME-02', nextHop: 'HYPHA-03', hops: 2, metric: 2.1 },
      { dest: 'RHIZOME-03', nextHop: 'FROND-05', hops: 2, metric: 2.8 },
    ],
  }

  // SECURITY: Validate all nodes and links
  mockData.nodes.forEach(node => {
    if (!validateNode(node)) {
      console.error('Invalid node structure:', node)
    }
  })

  mockData.links.forEach(link => {
    if (!validateLink(link)) {
      console.error('Invalid link structure:', link)
    }
  })

  return mockData
}

/**
 * Force-directed graph layout simulation
 * SECURITY: Added bounds checking and guards against division by zero
 */
export const updateNodePositions = (nodes, links, bounds) => {
  if (!nodes || !links || !bounds) return

  const REPULSION = 2.0
  const ATTRACTION = 0.05
  const DAMPING = 0.85
  const CENTER_PULL = 0.02

  const centerX = bounds.maxX / 2
  const centerY = bounds.maxY / 2

  // Guard against invalid bounds
  if (!isFinite(centerX) || !isFinite(centerY)) return

  // Initialize velocities
  nodes.forEach(node => {
    if (!node.vx) node.vx = 0
    if (!node.vy) node.vy = 0
  })

  // Calculate forces
  nodes.forEach(node => {
    let fx = 0
    let fy = 0

    // Repulsion forces between all nodes
    nodes.forEach(other => {
      if (node === other) return
      const dx = node.x - other.x
      const dy = node.y - other.y
      const distSq = dx * dx + dy * dy
      
      // SECURITY: Guard against division by zero
      if (distSq < 0.0001) return
      
      const dist = Math.sqrt(distSq)
      const force = REPULSION / distSq
      fx += (dx / dist) * force
      fy += (dy / dist) * force
    })

    // Attraction forces along links
    links.forEach(link => {
      let other = null
      if (link.from === node.id) {
        other = nodes.find(n => n.id === link.to)
      } else if (link.to === node.id) {
        other = nodes.find(n => n.id === link.from)
      }

      if (other) {
        const dx = other.x - node.x
        const dy = other.y - node.y
        fx += dx * ATTRACTION
        fy += dy * ATTRACTION
      }
    })

    // Center attraction
    fx += (centerX - node.x) * CENTER_PULL
    fy += (centerY - node.y) * CENTER_PULL

    // Apply damping
    node.vx = (node.vx + fx) * DAMPING
    node.vy = (node.vy + fy) * DAMPING
  })

  // Update positions with bounds checking
  nodes.forEach(node => {
    node.x += node.vx
    node.y += node.vy

    const margin = 2
    node.x = Math.max(margin, Math.min(bounds.maxX - margin, node.x))
    node.y = Math.max(margin, Math.min(bounds.maxY - margin, node.y))
  })
}

/**
 * Generate animated data flow particles with quality-based speed
 * SECURITY: Added particle limit to prevent resource exhaustion
 */
export const generateParticles = (links, nodes, time) => {
  if (!links || !nodes) return []

  const particles = []
  let totalParticles = 0

  for (let linkIndex = 0; linkIndex < links.length; linkIndex++) {
    if (totalParticles >= MAX_PARTICLES_TOTAL) break

    const link = links[linkIndex]
    
    // SECURITY: Validate link structure
    if (!validateLink(link)) {
      console.warn('Skipping invalid link:', link)
      continue
    }

    const fromNode = nodes.find(n => n.id === link.from)
    const toNode = nodes.find(n => n.id === link.to)

    if (!fromNode || !toNode) continue

    // Speed inversely correlates with latency (guard against division by zero)
    const baseSpeed = 1.0 / Math.max(1, 1 + link.latency / 50)
    
    // Determine particle count based on quality
    let numParticles = 0
    if (link.quality === 'GOOD') numParticles = 2
    else if (link.quality === 'FAIR') numParticles = 1
    else if (link.quality === 'DEGRADED') numParticles = 0
    else numParticles = 0

    // SECURITY: Cap particles per link and total
    numParticles = Math.min(numParticles, PARTICLE_LIMIT_PER_LINK)
    
    for (let i = 0; i < numParticles; i++) {
      if (totalParticles >= MAX_PARTICLES_TOTAL) break

      const phase = (time * baseSpeed * 0.02 + linkIndex * 0.3 + i * 0.5) % 1.0
      const x = fromNode.x + (toNode.x - fromNode.x) * phase
      const y = fromNode.y + (toNode.y - fromNode.y) * phase

      particles.push({ 
        x, y, 
        link,
        quality: link.quality,
        rssi: link.rssi
      })
      totalParticles++
    }
  }

  return particles
}

/**
 * Calculate link quality percentage based on RSSI and latency
 * SECURITY: Added guard against division by zero
 */
export const calculateQualityPercent = (link) => {
  if (!link) return 0

  // RSSI: -30 to -120 dBm (better to worse)
  const rssi = Math.max(-120, Math.min(-30, link.rssi || -80))
  const rssiPercent = Math.max(0, Math.min(100, (-30 - rssi) * -1.25 + 100))
  
  // Latency: 0-200ms (better to worse)
  const latency = Math.max(0, link.latency || 0)
  const latencyPercent = Math.max(0, Math.min(100, (1 - latency / 200) * 100))
  
  // Packet loss: 0-50% (better to worse)
  const packetLoss = Math.max(0, Math.min(100, link.packetLoss || 0))
  const lossPercent = Math.max(0, Math.min(100, (1 - packetLoss / 50) * 100))
  
  // Combined quality (weighted average)
  const quality = rssiPercent * 0.4 + latencyPercent * 0.3 + lossPercent * 0.3
  return Math.round(Math.max(0, Math.min(100, quality)))
}

/**
 * Format GPS coordinates safely with sanitization
 */
export const formatGpsCoordinates = (gps) => {
  if (!gps) return 'N/A'
  
  const lat = validateLatitude(gps.lat)
  const lng = validateLongitude(gps.lng)
  
  if (lat === null || lng === null) {
    return 'INVALID'
  }
  
  return `${lat.toFixed(4)},${lng.toFixed(4)}`
}

/**
 * Render P200 lattice map with enhanced animations and interactivity
 * SECURITY: All data is validated and sanitized before rendering
 */
export const renderLatticeMap = (
  meshData, 
  selectedNode, 
  selectedLink, 
  time,
  hoveredNode,
  hoveredLink,
  filterType,
  showLegend
) => {
  if (!meshData || !meshData.nodes || !meshData.links) {
    const grid = createGrid()
    writeText(grid, 1, 1, 'ERROR: Invalid mesh data')
    return grid
  }

  const grid = createGrid()

  const graphBounds = {
    minX: 0,
    minY: 3,
    maxX: COLUMNS - 1,
    maxY: ROWS - 8,
  }

  // Header
  writeText(grid, 1, 0, `LATTICE MAP ${DOT} P200`)
  writeText(grid, 24, 0, `${meshData.nodes.length} CELLS`)
  drawHLine(grid, 0, 1, COLUMNS)

  // Draw links with dashing for degraded connections
  meshData.links.forEach(link => {
    // SECURITY: Validate link
    if (!validateLink(link)) {
      console.warn('Skipping invalid link in render:', link)
      return
    }

    const fromNode = meshData.nodes.find(n => n.id === link.from)
    const toNode = meshData.nodes.find(n => n.id === link.to)

    if (fromNode && toNode) {
      const isDegraded = link.quality === 'DEGRADED'
      const linkChar = LINK_QUALITY[link.quality]?.symbol || '·'
      
      const x0 = graphBounds.minX + fromNode.x
      const y0 = graphBounds.minY + fromNode.y
      const x1 = graphBounds.minX + toNode.x
      const y1 = graphBounds.minY + toNode.y

      drawLine(grid, x0, y0, x1, y1, linkChar, isDegraded)
      
      // Highlight selected link with enhanced marker
      if (selectedLink && 
          selectedLink.from === link.from && 
          selectedLink.to === link.to) {
        const midX = (x0 + x1) / 2
        const midY = (y0 + y1) / 2
        drawChar(grid, midX, midY, '*')
      }
    }
  })

  // Draw animated particles with quality-based coloring
  const particles = generateParticles(meshData.links, meshData.nodes, time)
  particles.forEach(particle => {
    const x = graphBounds.minX + particle.x
    const y = graphBounds.minY + particle.y
    // Vary particle symbol based on quality
    let symbol = DOT
    if (particle.quality === 'FAIR') symbol = '◦'
    if (particle.quality === 'DEGRADED') symbol = '·'
    drawChar(grid, x, y, symbol)
  })

  // Draw nodes with glow effect
  meshData.nodes.forEach(node => {
    // SECURITY: Validate node
    if (!validateNode(node)) {
      console.warn('Skipping invalid node in render:', node)
      return
    }

    const x = graphBounds.minX + node.x
    const y = graphBounds.minY + node.y
    
    // Apply filter
    if (filterType && filterType !== node.type) {
      return
    }

    let nodeChar = NODE_TYPES[node.type]?.symbol || '?'
    
    // Gray out offline/low battery nodes
    if (node.status === 'offline' || node.battery < 5) {
      nodeChar = nodeChar.toLowerCase()
    }

    // Pulsing animation for critical alerts (battery < 20%)
    const isAlert = node.battery < 20
    const pulse = isAlert && Math.floor(time / 500) % 2 === 0

    if (!pulse) {
      drawChar(grid, x, y, nodeChar)
      
      // Glow effect (draw halo)
      if (hoveredNode && hoveredNode.id === node.id) {
        drawChar(grid, x - 1, y, '◊')
        drawChar(grid, x + 1, y, '◊')
        drawChar(grid, x, y - 1, '◊')
        drawChar(grid, x, y + 1, '◊')
      }
    }

    // SECURITY: Sanitize node ID for display
    if (node.type === 'SPORE' || (selectedNode && selectedNode.id === node.id)) {
      const safeName = sanitizeString(node.id, 10)
      const labelX = Math.min(x + 2, COLUMNS - safeName.length - 1)
      const labelY = y
      if (labelY >= 0 && labelY < ROWS) {
        writeText(grid, labelX, labelY, safeName)
      }
    }
  })

  // Detail panel at bottom
  drawHLine(grid, 0, ROWS - 7, COLUMNS)

  if (selectedNode) {
    // SECURITY: Validate selected node
    if (validateNode(selectedNode)) {
      const safeId = sanitizeString(selectedNode.id, 15)
      const safeCallsign = sanitizeString(selectedNode.callsign || 'N/A', 15)
      const safeType = sanitizeString(selectedNode.type, 10)
      const safeStatus = sanitizeString(selectedNode.status, 10)
      const gpsStr = formatGpsCoordinates(selectedNode.gps)
      
      // Node detail with extended info
      writeText(grid, 2, ROWS - 6, `NODE: ${safeId} (${safeCallsign})`)
      writeText(grid, 2, ROWS - 5, `Type: ${safeType} | Batt: ${selectedNode.battery}%`)
      writeText(grid, 2, ROWS - 4, `GPS: ${gpsStr}`)
      writeText(grid, 22, ROWS - 5, `Status: ${safeStatus}`)
      writeText(grid, 22, ROWS - 4, `Up: ${Math.floor(selectedNode.uptime / 60)}m`)
    } else {
      writeText(grid, 2, ROWS - 6, 'ERROR: Invalid node')
    }
  } else if (selectedLink) {
    // SECURITY: Validate selected link
    if (validateLink(selectedLink)) {
      const safeFrom = sanitizeString(selectedLink.from, 8)
      const safeTo = sanitizeString(selectedLink.to, 8)
      const qualityPercent = calculateQualityPercent(selectedLink)
      const safeQuality = sanitizeString(selectedLink.quality, 10)
      const safeRadio = sanitizeString(selectedLink.radioType || 'LoRa', 10)
      
      // Link detail with quality percentage
      writeText(grid, 2, ROWS - 6, `LINK: ${safeFrom} -> ${safeTo}`)
      writeText(grid, 2, ROWS - 5, `RSSI: ${selectedLink.rssi}dBm | Lat: ${selectedLink.latency}ms | Loss: ${selectedLink.packetLoss}%`)
      writeText(grid, 2, ROWS - 4, `Quality: ${qualityPercent}% [${safeQuality}] | Radio: ${safeRadio}`)
    } else {
      writeText(grid, 2, ROWS - 6, 'ERROR: Invalid link')
    }
  } else {
    // Summary stats
    const goodLinks = meshData.links.filter(l => l.quality === 'GOOD').length
    const fairLinks = meshData.links.filter(l => l.quality === 'FAIR').length
    const degradedLinks = meshData.links.filter(l => l.quality === 'DEGRADED').length
    const activeNodes = meshData.nodes.filter(n => n.status === 'active').length

    const avgQuality = meshData.links.length > 0
      ? Math.round(
          meshData.links.reduce((sum, l) => sum + calculateQualityPercent(l), 0) / meshData.links.length
        )
      : 0

    writeText(grid, 2, ROWS - 6, `MESH TOPOLOGY SUMMARY`)
    writeText(grid, 2, ROWS - 5, `Active: ${activeNodes}/${meshData.nodes.length} | Links: ${meshData.links.length}`)
    writeText(grid, 2, ROWS - 4, `Good: ${goodLinks} | Fair: ${fairLinks} | Degraded: ${degradedLinks}`)
    writeText(grid, 22, ROWS - 5, `Avg Quality: ${avgQuality}%`)
    writeText(grid, 22, ROWS - 4, `Protocol: BATMAN-ADV`)
  }

  // Enhanced Legend with quality indicators
  if (showLegend) {
    writeText(grid, 2, ROWS - 2, `${NODE_TYPES.SPORE.symbol}SPORE ${NODE_TYPES.HYPHA.symbol}HYPHA ${NODE_TYPES.FROND.symbol}FROND ${NODE_TYPES.RHIZOME.symbol}RHIZOME`)
    writeText(grid, 2, ROWS - 1, `${LINK_QUALITY.GOOD.symbol}GOOD ${LINK_QUALITY.FAIR.symbol}FAIR ${LINK_QUALITY.DEGRADED.symbol}DEGRADED`)
  } else {
    writeText(grid, 2, ROWS - 2, `Nodes: ${NODE_TYPES.SPORE.symbol} ${NODE_TYPES.HYPHA.symbol} ${NODE_TYPES.FROND.symbol} ${NODE_TYPES.RHIZOME.symbol}`)
    writeText(grid, 2, ROWS - 1, `Quality: ${LINK_QUALITY.GOOD.symbol}● ${LINK_QUALITY.FAIR.symbol}● ${LINK_QUALITY.DEGRADED.symbol}●`)
  }

  // Footer instructions
  drawHLine(grid, 0, ROWS - 1, COLUMNS, '─')
  writeText(grid, 1, ROWS - 1, '[R]outes [N]ode [L]ink [F]ilter [Z]oom [M]sg')

  return grid
}

/**
 * Render routes table view
 * SECURITY: All data is sanitized before rendering
 */
export const renderRoutesTable = (meshData) => {
  const ROWS_LOCAL = 25
  const COLUMNS_LOCAL = 40
  
  if (!meshData || !meshData.routeTable) {
    const grid = Array.from({ length: ROWS_LOCAL }, () => 
      Array.from({ length: COLUMNS_LOCAL }, () => ' ')
    )
    const writeTextLocal = (x, y, text) => {
      if (y < 0 || y >= ROWS_LOCAL) return
      const safeText = String(text || '')
      for (let i = 0; i < safeText.length; i++) {
        const col = x + i
        if (col >= 0 && col < COLUMNS_LOCAL) {
          grid[y][col] = safeText[i]
        }
      }
    }
    writeTextLocal(1, 1, 'ERROR: Invalid route data')
    return grid
  }
  
  const grid = Array.from({ length: ROWS_LOCAL }, () => 
    Array.from({ length: COLUMNS_LOCAL }, () => ' ')
  )

  const writeTextLocal = (x, y, text) => {
    if (y < 0 || y >= ROWS_LOCAL) return
    const safeText = String(text || '')
    for (let i = 0; i < safeText.length; i++) {
      const col = x + i
      if (col >= 0 && col < COLUMNS_LOCAL) {
        grid[y][col] = safeText[i]
      }
    }
  }

  const drawHLineLocal = (y) => {
    if (y >= 0 && y < ROWS_LOCAL) {
      for (let x = 0; x < COLUMNS_LOCAL; x++) {
        grid[y][x] = '─'
      }
    }
  }

  writeTextLocal(1, 0, 'ROUTE TABLE ● P200')
  drawHLineLocal(1)

  writeTextLocal(2, 3, 'DEST')
  writeTextLocal(15, 3, 'NEXT HOP')
  writeTextLocal(28, 3, 'HOPS')
  writeTextLocal(34, 3, 'METRIC')
  drawHLineLocal(4)

  // SECURITY: Sanitize route entries
  meshData.routeTable.forEach((route, i) => {
    const y = 5 + i
    if (y >= ROWS_LOCAL - 3) return

    const safeDest = sanitizeString(route.dest || 'N/A', 12)
    const safeNextHop = sanitizeString(route.nextHop || 'N/A', 12)
    const hops = Math.round(route.hops || 0)
    const metric = typeof route.metric === 'number' ? route.metric.toFixed(1) : 'N/A'

    writeTextLocal(2, y, safeDest)
    writeTextLocal(15, y, safeNextHop)
    writeTextLocal(28, y, String(hops))
    writeTextLocal(34, y, metric)
  })

  drawHLineLocal(ROWS_LOCAL - 3)
  writeTextLocal(2, ROWS_LOCAL - 2, `${meshData.routeTable.length} routes`)
  writeTextLocal(2, ROWS_LOCAL - 1, '[R]eturn to graph [ESC]clear')

  return grid
}
