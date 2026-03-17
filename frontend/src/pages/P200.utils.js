import { COLUMNS, ROWS } from '../components/TeletextGrid'

// Box drawing characters
const BOX = {
  TL: '┌', TR: '┐', BL: '└', BR: '┘',
  H: '─', V: '│',
}

const DOT = '●'
const ARROW = '▸'

// Node types with colors (represented as character symbols for ASCII rendering)
const NODE_TYPES = {
  SPORE: { color: 'cyan', symbol: '◆' },     // #00FFFF
  HYPHA: { color: 'green', symbol: '●' },    // #00FF00
  FROND: { color: 'yellow', symbol: '◇' },   // #FFFF00
  RHIZOME: { color: 'blue', symbol: '■' },   // #0000FF
}

// Link quality status
const LINK_QUALITY = {
  GOOD: { symbol: '═', color: 'cyan' },      // Cyan
  FAIR: { symbol: '─', color: 'yellow' },    // Yellow
  DEGRADED: { symbol: '·', color: 'orange' }, // Orange
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
 * Draw box (currently unused but kept for future expansion)
 */
// eslint-disable-next-line no-unused-vars
const drawBox = (grid, x, y, width, height) => {
  // Corners
  if (x >= 0 && x < COLUMNS) {
    if (y >= 0 && y < ROWS) grid[y][x] = BOX.TL
    if (y + height - 1 >= 0 && y + height - 1 < ROWS) {
      grid[y + height - 1][x] = BOX.BL
    }
  }
  if (x + width - 1 >= 0 && x + width - 1 < COLUMNS) {
    if (y >= 0 && y < ROWS) grid[y][x + width - 1] = BOX.TR
    if (y + height - 1 >= 0 && y + height - 1 < ROWS) {
      grid[y + height - 1][x + width - 1] = BOX.BR
    }
  }

  // Horizontal lines
  drawHLine(grid, x + 1, y, width - 2, BOX.H)
  drawHLine(grid, x + 1, y + height - 1, width - 2, BOX.H)

  // Vertical lines
  for (let i = 1; i < height - 1; i++) {
    const row = y + i
    if (row >= 0 && row < ROWS) {
      if (x >= 0 && x < COLUMNS) grid[row][x] = BOX.V
      if (x + width - 1 >= 0 && x + width - 1 < COLUMNS) {
        grid[row][x + width - 1] = BOX.V
      }
    }
  }
}

/**
 * Draw a character at grid position (for nodes/particles)
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
const drawLine = (grid, x0, y0, x1, y1, char) => {
  x0 = Math.round(x0)
  y0 = Math.round(y0)
  x1 = Math.round(x1)
  y1 = Math.round(y1)

  const dx = Math.abs(x1 - x0)
  const dy = Math.abs(y1 - y0)
  const sx = x0 < x1 ? 1 : -1
  const sy = y0 < y1 ? 1 : -1
  let err = dx - dy

  let maxIter = 100 // Safety limit
  while (maxIter-- > 0) {
    if (x0 >= 0 && x0 < COLUMNS && y0 >= 0 && y0 < ROWS) {
      grid[y0][x0] = char
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
  }
}

/**
 * Mock mesh network data
 */
export const getMockMeshData = () => ({
  nodes: [
    { id: 'SPORE-01', type: 'SPORE', x: 40, y: 12, hopCount: 0, battery: 74, uptime: 15240 },
    { id: 'HYPHA-03', type: 'HYPHA', x: 16, y: 6, hopCount: 1, battery: 89, uptime: 8420 },
    { id: 'FROND-05', type: 'FROND', x: 64, y: 8, hopCount: 1, battery: 62, uptime: 4120 },
    { id: 'RHIZOME-02', type: 'RHIZOME', x: 24, y: 18, hopCount: 2, battery: 55, uptime: 12300 },
    { id: 'RHIZOME-03', type: 'RHIZOME', x: 56, y: 16, hopCount: 2, battery: 71, uptime: 9840 },
  ],
  links: [
    { from: 'SPORE-01', to: 'HYPHA-03', quality: 'GOOD', rssi: -72, latency: 8, packetLoss: 0 },
    { from: 'SPORE-01', to: 'FROND-05', quality: 'GOOD', rssi: -78, latency: 12, packetLoss: 0 },
    { from: 'SPORE-01', to: 'RHIZOME-02', quality: 'FAIR', rssi: -85, latency: 42, packetLoss: 2 },
    { from: 'HYPHA-03', to: 'RHIZOME-02', quality: 'GOOD', rssi: -74, latency: 15, packetLoss: 0 },
    { from: 'FROND-05', to: 'RHIZOME-03', quality: 'DEGRADED', rssi: -91, latency: 98, packetLoss: 11 },
  ],
  routeTable: [
    { dest: 'HYPHA-03', nextHop: 'HYPHA-03', hops: 1, metric: 1.2 },
    { dest: 'FROND-05', nextHop: 'FROND-05', hops: 1, metric: 1.5 },
    { dest: 'RHIZOME-02', nextHop: 'HYPHA-03', hops: 2, metric: 2.1 },
    { dest: 'RHIZOME-03', nextHop: 'FROND-05', hops: 2, metric: 2.8 },
  ],
})

/**
 * Simple force-directed graph layout simulation
 * Updates node positions based on physics
 */
export const updateNodePositions = (nodes, links, bounds) => {
  const REPULSION = 2.0
  const ATTRACTION = 0.05
  const DAMPING = 0.85
  const CENTER_PULL = 0.02

  const centerX = bounds.maxX / 2
  const centerY = bounds.maxY / 2

  // Initialize velocities if not present
  nodes.forEach(node => {
    if (!node.vx) node.vx = 0
    if (!node.vy) node.vy = 0
  })

  // Calculate forces
  nodes.forEach(node => {
    let fx = 0
    let fy = 0

    // Repulsion between all nodes
    nodes.forEach(other => {
      if (node === other) return
      const dx = node.x - other.x
      const dy = node.y - other.y
      const distSq = dx * dx + dy * dy + 0.01 // Avoid division by zero
      const dist = Math.sqrt(distSq)
      const force = REPULSION / distSq
      fx += (dx / dist) * force
      fy += (dy / dist) * force
    })

    // Attraction along links
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

    // Pull toward center
    fx += (centerX - node.x) * CENTER_PULL
    fy += (centerY - node.y) * CENTER_PULL

    // Update velocity
    node.vx = (node.vx + fx) * DAMPING
    node.vy = (node.vy + fy) * DAMPING
  })

  // Apply velocity and boundary constraints
  nodes.forEach(node => {
    node.x += node.vx
    node.y += node.vy

    // Keep within bounds (with margin)
    const margin = 2
    node.x = Math.max(margin, Math.min(bounds.maxX - margin, node.x))
    node.y = Math.max(margin, Math.min(bounds.maxY - margin, node.y))
  })
}

/**
 * Generate animated data flow particles along links
 */
export const generateParticles = (links, nodes, time) => {
  const particles = []

  links.forEach((link, linkIndex) => {
    const fromNode = nodes.find(n => n.id === link.from)
    const toNode = nodes.find(n => n.id === link.to)

    if (!fromNode || !toNode) return

    // Create particles at different phases along the link
    const numParticles = link.quality === 'GOOD' ? 2 : 1
    for (let i = 0; i < numParticles; i++) {
      const phase = (time * 0.02 + linkIndex * 0.3 + i * 0.5) % 1.0
      const x = fromNode.x + (toNode.x - fromNode.x) * phase
      const y = fromNode.y + (toNode.y - fromNode.y) * phase

      particles.push({ x, y, link })
    }
  })

  return particles
}

/**
 * Render P200 lattice map to grid
 */
export const renderLatticeMap = (meshData, selectedNode, selectedLink, time) => {
  const grid = createGrid()

  // Define graph bounds (leaving space for UI)
  const graphBounds = {
    minX: 0,
    minY: 3,
    maxX: COLUMNS - 1,
    maxY: ROWS - 8,
  }

  // Note: updateNodePositions should be called externally before render
  // to keep render function pure

  // Header
  writeText(grid, 1, 0, `LATTICE MAP ${DOT} P200`)
  writeText(grid, 24, 0, `${meshData.nodes.length} CELLS`)
  drawHLine(grid, 0, 1, COLUMNS)

  // Draw links first (so they're under nodes)
  meshData.links.forEach(link => {
    const fromNode = meshData.nodes.find(n => n.id === link.from)
    const toNode = meshData.nodes.find(n => n.id === link.to)

    if (fromNode && toNode) {
      const linkChar = LINK_QUALITY[link.quality]?.symbol || '·'
      const x0 = graphBounds.minX + fromNode.x
      const y0 = graphBounds.minY + fromNode.y
      const x1 = graphBounds.minX + toNode.x
      const y1 = graphBounds.minY + toNode.y

      drawLine(grid, x0, y0, x1, y1, linkChar)
    }
  })

  // Draw animated particles
  const particles = generateParticles(meshData.links, meshData.nodes, time)
  particles.forEach(particle => {
    const x = graphBounds.minX + particle.x
    const y = graphBounds.minY + particle.y
    drawChar(grid, x, y, DOT)
  })

  // Draw nodes
  meshData.nodes.forEach(node => {
    const x = graphBounds.minX + node.x
    const y = graphBounds.minY + node.y
    const nodeChar = NODE_TYPES[node.type]?.symbol || '?'

    drawChar(grid, x, y, nodeChar)

    // Label for selected node or central node
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
    // Node detail
    writeText(grid, 2, ROWS - 6, `NODE: ${selectedNode.id}`)
    writeText(grid, 2, ROWS - 5, `Type: ${selectedNode.type}`)
    writeText(grid, 2, ROWS - 4, `Hops: ${selectedNode.hopCount}`)
    writeText(grid, 22, ROWS - 5, `Batt: ${selectedNode.battery}%`)
    writeText(grid, 22, ROWS - 4, `Up: ${Math.floor(selectedNode.uptime / 60)}m`)
  } else if (selectedLink) {
    // Link detail
    writeText(grid, 2, ROWS - 6, `LINK: ${selectedLink.from} ${ARROW} ${selectedLink.to}`)
    writeText(grid, 2, ROWS - 5, `RSSI: ${selectedLink.rssi}dBm`)
    writeText(grid, 2, ROWS - 4, `Lat: ${selectedLink.latency}ms`)
    writeText(grid, 22, ROWS - 5, `Loss: ${selectedLink.packetLoss}%`)
    writeText(grid, 22, ROWS - 4, `Q: ${selectedLink.quality}`)
  } else {
    // Summary stats
    const goodLinks = meshData.links.filter(l => l.quality === 'GOOD').length
    const degradedLinks = meshData.links.filter(l => l.quality === 'DEGRADED').length

    writeText(grid, 2, ROWS - 6, `MESH TOPOLOGY`)
    writeText(grid, 2, ROWS - 5, `Links: ${meshData.links.length}`)
    writeText(grid, 2, ROWS - 4, `Good: ${goodLinks}`)
    writeText(grid, 22, ROWS - 5, `Degraded: ${degradedLinks}`)
    writeText(grid, 22, ROWS - 4, `Proto: BATMAN`)
  }

  // Legend
  writeText(grid, 2, ROWS - 2, `${NODE_TYPES.SPORE.symbol}SPORE ${NODE_TYPES.HYPHA.symbol}HYPHA`)
  writeText(grid, 18, ROWS - 2, `${NODE_TYPES.FROND.symbol}FROND ${NODE_TYPES.RHIZOME.symbol}RHIZOME`)

  // Footer instructions
  drawHLine(grid, 0, ROWS - 1, COLUMNS, '─')
  writeText(grid, 1, ROWS - 1, '[R]outes [N]ext node [L]ink detail')

  return grid
}
