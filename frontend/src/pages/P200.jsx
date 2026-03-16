import { useEffect, useState, useRef } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import { renderLatticeMap, getMockMeshData } from './P200.utils'

/**
 * P200 - Lattice Map Page
 * 
 * Force-directed graph visualization of mesh network topology.
 * 
 * Features:
 * - Force-directed graph layout with physics simulation
 * - Nodes colored by type (SPORE/HYPHA/FROND/RHIZOME)
 * - Links colored by quality (GOOD/FAIR/DEGRADED)
 * - Animated data flow particles along links
 * - Click node → expand detail panel (hop count, battery, uptime)
 * - Click link → show RSSI, latency, packet loss
 * - Route table display
 * - Mock mesh data (WebSocket updates later)
 */

const P200 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)

  // Mesh data (will be updated via WebSocket in future)
  const meshDataRef = useRef(getMockMeshData())
  const [meshData] = useState(meshDataRef.current)

  // Selected node/link for detail panel
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedLink, setSelectedLink] = useState(null)

  // Animation frame counter
  const [frame, setFrame] = useState(0)

  // View mode (graph or routes)
  const [viewMode, setViewMode] = useState('graph') // 'graph' or 'routes'

  useEffect(() => {
    setBreadcrumbs(['LATTICE', 'P200'])
  }, [setBreadcrumbs])

  // Animation loop for particle flow
  useEffect(() => {
    const interval = setInterval(() => {
      setFrame(prev => prev + 1)
    }, 100) // ~10 fps animation

    return () => clearInterval(interval)
  }, [])

  // Force simulation for graph layout (runs less frequently)
  useEffect(() => {
    const graphBounds = {
      maxX: 40 - 1,
      maxY: 25 - 8,
    }

    const interval = setInterval(() => {
      // Dynamically import to avoid circular dependency issues in tests
      import('./P200.utils').then(({ updateNodePositions }) => {
        updateNodePositions(meshData.nodes, meshData.links, graphBounds)
      })
    }, 300) // Update physics every 300ms

    return () => clearInterval(interval)
  }, [meshData])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase()

      if (key === 'r') {
        // Toggle routes view
        setViewMode(prev => prev === 'graph' ? 'routes' : 'graph')
      } else if (key === 'n') {
        // Cycle through nodes
        const currentIndex = selectedNode 
          ? meshData.nodes.findIndex(n => n.id === selectedNode.id)
          : -1
        const nextIndex = (currentIndex + 1) % meshData.nodes.length
        setSelectedNode(meshData.nodes[nextIndex])
        setSelectedLink(null)
      } else if (key === 'l') {
        // Cycle through links
        const currentIndex = selectedLink
          ? meshData.links.findIndex(l => 
              l.from === selectedLink.from && l.to === selectedLink.to
            )
          : -1
        const nextIndex = (currentIndex + 1) % meshData.links.length
        setSelectedLink(meshData.links[nextIndex])
        setSelectedNode(null)
      } else if (key === 'escape') {
        // Clear selection
        setSelectedNode(null)
        setSelectedLink(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [meshData, selectedNode, selectedLink])

  const content = viewMode === 'graph'
    ? renderLatticeMap(meshData, selectedNode, selectedLink, frame)
    : renderRoutesTable(meshData)

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">
        P200 - LATTICE MAP {viewMode === 'routes' ? '(ROUTES)' : ''}
      </div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

/**
 * Render routes table view
 */
const renderRoutesTable = (meshData) => {
  const ROWS = 25
  const COLUMNS = 40
  
  const grid = Array.from({ length: ROWS }, () => 
    Array.from({ length: COLUMNS }, () => ' ')
  )

  const writeText = (x, y, text) => {
    if (y < 0 || y >= ROWS) return
    for (let i = 0; i < text.length; i++) {
      const col = x + i
      if (col >= 0 && col < COLUMNS) {
        grid[y][col] = text[i]
      }
    }
  }

  const drawHLine = (y) => {
    for (let x = 0; x < COLUMNS; x++) {
      grid[y][x] = '─'
    }
  }

  // Header
  writeText(1, 0, 'ROUTE TABLE ● P200')
  drawHLine(1)

  // Table headers
  writeText(2, 3, 'DEST')
  writeText(15, 3, 'NEXT HOP')
  writeText(28, 3, 'HOPS')
  writeText(34, 3, 'METRIC')
  drawHLine(4)

  // Route entries
  meshData.routeTable.forEach((route, i) => {
    const y = 5 + i
    if (y >= ROWS - 3) return

    writeText(2, y, route.dest)
    writeText(15, y, route.nextHop)
    writeText(28, y, String(route.hops))
    writeText(34, y, route.metric.toFixed(1))
  })

  // Footer
  drawHLine(ROWS - 3)
  writeText(2, ROWS - 2, `${meshData.routeTable.length} routes`)
  writeText(2, ROWS - 1, '[R]eturn to graph [ESC]clear')

  return grid
}

export default P200
