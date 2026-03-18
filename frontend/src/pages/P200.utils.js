import { COLUMNS, ROWS } from '../components/TeletextGrid'

// Box drawing characters
const BOX = {
  TL: '┌', TR: '┐', BL: '└', BR: '┘',
  H: '─', V: '│',
  VDASH: '┆', HDASH: '┄',
}

const DOT = '●'
const ARROW = '▸'

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
const drawHLine = (grid, x, y, length, char = BOX.H) => {
  for (let i = 0; i < length; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS && y >= 0 && y < ROWS) {
      grid[y][col] = char
    }
  }
}

/**
 * Draw a character at grid position
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

  let maxIter = 100
  while (maxIter-- > 0) {
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
 */
export const getMockMeshData = () => ({
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
})

/**
 * Force-directed graph layout simulation
 */
export const updateNodePositions = (nodes, links, bounds) => {
  const REPULSION = 2.0
  const ATTRACTION = 0.05
  const DAMPING = 0.85
  const CENTER_PULL = 0.02

  const centerX = bounds.maxX / 2
  const centerY = bounds.maxY / 2

  nodes.forEach(node => {
    if (!node.vx) node.vx = 0
    if (!node.vy) node.vy = 0
  })

  nodes.forEach(node => {
    let fx = 0
    let fy = 0

    nodes.forEach(other => {
      if (node === other) return
      const dx = node.x - other.x
      const dy = node.y - other.y
      const distSq = dx * dx + dy * dy + 0.01
      const dist = Math.sqrt(distSq)
      const force = REPULSION / distSq
      fx += (dx / dist) * force
      fy += (dy / dist) * force
    })

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

    fx += (centerX - node.x) * CENTER_PULL
    fy += (centerY - node.y) * CENTER_PULL

    node.vx = (node.vx + fx) * DAMPING
    node.vy = (node.vy + fy) * DAMPING
  })

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
 */
export const generateParticles = (links, nodes, time) => {
  const particles = []

  links.forEach((link, linkIndex) => {
    const fromNode = nodes.find(n => n.id === link.from)
    const toNode = nodes.find(n => n.id === link.to)

    if (!fromNode || !toNode) return

    // Speed inversely correlates with latency
    const baseSpeed = 1.0 / (1 + link.latency / 50)
    const numParticles = link.quality === 'GOOD' ? 2 : (link.quality === 'DEGRADED' ? 0 : 1)
    
    for (let i = 0; i < numParticles; i++) {
      const phase = (time * baseSpeed * 0.02 + linkIndex * 0.3 + i * 0.5) % 1.0
      const x = fromNode.x + (toNode.x - fromNode.x) * phase
      const y = fromNode.y + (toNode.y - fromNode.y) * phase

      particles.push({ 
        x, y, 
        link,
        quality: link.quality,
        rssi: link.rssi
      })
    }
  })

  return particles
}

/**
 * Calculate link quality percentage based on RSSI and latency
 */
export const calculateQualityPercent = (link) => {
  // RSSI: -30 to -120 dBm (better to worse)
  const rssiPercent = Math.max(0, Math.min(100, (-30 - link.rssi) * -1.25 + 100))
  
  // Latency: 0-200ms (better to worse)
  const latencyPercent = Math.max(0, Math.min(100, (1 - link.latency / 200) * 100))
  
  // Packet loss: 0-50% (better to worse)
  const lossPercent = Math.max(0, Math.min(100, (1 - (link.packetLoss || 0) / 50) * 100))
  
  // Combined quality
  return Math.round((rssiPercent * 0.4 + latencyPercent * 0.3 + lossPercent * 0.3))
}

/**
 * Render P200 lattice map with enhanced animations and interactivity
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
    const fromNode = meshData.nodes.find(n => n.id === link.from)
    const toNode = meshData.nodes.find(n => n.id === link.to)

    if (fromNode && toNode) {
      const isDegraded = link.quality === 'DEGRADED'
      const isOffline = link.quality === 'OFFLINE'
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

  // Draw nodes with glow effect (represented by surrounding markers)
  meshData.nodes.forEach(node => {
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

    // Label nodes
    if (node.type === 'SPORE' || (selectedNode && selectedNode.id === node.id)) {
      const labelX = Math.min(x + 2, COLUMNS - node.id.length - 1)
      const labelY = y
      if (labelY >= 0 && labelY < ROWS) {
        writeText(grid, labelX, labelY, node.id)
      }
    }
  })

  // Detail panel at bottom
  drawHLine(grid, 0, ROWS - 7, COLUMNS)

  if (selectedNode) {
    // Node detail with extended info
    writeText(grid, 2, ROWS - 6, `NODE: ${selectedNode.id} (${selectedNode.callsign})`)
    writeText(grid, 2, ROWS - 5, `Type: ${selectedNode.type} | Batt: ${selectedNode.battery}%`)
    writeText(grid, 2, ROWS - 4, `GPS: ${selectedNode.gps.lat.toFixed(4)},${selectedNode.gps.lng.toFixed(4)}`)
    writeText(grid, 22, ROWS - 5, `Status: ${selectedNode.status.toUpperCase()}`)
    writeText(grid, 22, ROWS - 4, `Up: ${Math.floor(selectedNode.uptime / 60)}m`)
  } else if (selectedLink) {
    // Link detail with quality percentage
    const qualityPercent = calculateQualityPercent(selectedLink)
    writeText(grid, 2, ROWS - 6, `LINK: ${selectedLink.from.substring(0, 8)} → ${selectedLink.to.substring(0, 8)}`)
    writeText(grid, 2, ROWS - 5, `RSSI: ${selectedLink.rssi}dBm | Lat: ${selectedLink.latency}ms | Loss: ${selectedLink.packetLoss}%`)
    writeText(grid, 2, ROWS - 4, `Quality: ${qualityPercent}% [${selectedLink.quality}] | Radio: ${selectedLink.radioType}`)
  } else {
    // Summary stats
    const goodLinks = meshData.links.filter(l => l.quality === 'GOOD').length
    const fairLinks = meshData.links.filter(l => l.quality === 'FAIR').length
    const degradedLinks = meshData.links.filter(l => l.quality === 'DEGRADED').length
    const activeNodes = meshData.nodes.filter(n => n.status === 'active').length

    writeText(grid, 2, ROWS - 6, `MESH TOPOLOGY SUMMARY`)
    writeText(grid, 2, ROWS - 5, `Active: ${activeNodes}/${meshData.nodes.length} | Links: ${meshData.links.length}`)
    writeText(grid, 2, ROWS - 4, `Good: ${goodLinks} | Fair: ${fairLinks} | Degraded: ${degradedLinks}`)
    writeText(grid, 22, ROWS - 5, `Avg Quality: ${Math.round(
      meshData.links.reduce((sum, l) => sum + calculateQualityPercent(l), 0) / meshData.links.length
    )}%`)
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
 */
export const renderRoutesTable = (meshData) => {
  const ROWS_LOCAL = 25
  const COLUMNS_LOCAL = 40
  
  const grid = Array.from({ length: ROWS_LOCAL }, () => 
    Array.from({ length: COLUMNS_LOCAL }, () => ' ')
  )

  const writeTextLocal = (x, y, text) => {
    if (y < 0 || y >= ROWS_LOCAL) return
    for (let i = 0; i < text.length; i++) {
      const col = x + i
      if (col >= 0 && col < COLUMNS_LOCAL) {
        grid[y][col] = text[i]
      }
    }
  }

  const drawHLineLocal = (y) => {
    for (let x = 0; x < COLUMNS_LOCAL; x++) {
      grid[y][x] = '─'
    }
  }

  writeTextLocal(1, 0, 'ROUTE TABLE ● P200')
  drawHLineLocal(1)

  writeTextLocal(2, 3, 'DEST')
  writeTextLocal(15, 3, 'NEXT HOP')
  writeTextLocal(28, 3, 'HOPS')
  writeTextLocal(34, 3, 'METRIC')
  drawHLineLocal(4)

  meshData.routeTable.forEach((route, i) => {
    const y = 5 + i
    if (y >= ROWS_LOCAL - 3) return

    writeTextLocal(2, y, route.dest)
    writeTextLocal(15, y, route.nextHop)
    writeTextLocal(28, y, String(route.hops))
    writeTextLocal(34, y, route.metric.toFixed(1))
  })

  drawHLineLocal(ROWS_LOCAL - 3)
  writeTextLocal(2, ROWS_LOCAL - 2, `${meshData.routeTable.length} routes`)
  writeTextLocal(2, ROWS_LOCAL - 1, '[R]eturn to graph [ESC]clear')

  return grid
}
