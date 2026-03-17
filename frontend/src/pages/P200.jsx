import { useEffect, useState, useRef } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import useMeshStore from '../store/meshStore'
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
 * - Live API and WebSocket updates
 */

const P200 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)

  // Get live mesh data from store
  const nodes = useMeshStore((state) => state.nodes)
  const threads = useMeshStore((state) => state.threads)
  const nodesLoading = useMeshStore((state) => state.nodesLoading)
  const threadsLoading = useMeshStore((state) => state.threadsLoading)
  const nodesError = useMeshStore((state) => state.nodesError)
  const threadsError = useMeshStore((state) => state.threadsError)
  const loadAll = useMeshStore((state) => state.loadAll)
  const connectWS = useMeshStore((state) => state.connectWS)
  const disconnectWS = useMeshStore((state) => state.disconnectWS)

  // Mesh data ref with fallback to mock data
  const meshDataRef = useRef(getMockMeshData())
  
  // Transform API data to mesh data format
  const [meshData, setMeshData] = useState(meshDataRef.current)

  // Selected node/link for detail panel
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedLink, setSelectedLink] = useState(null)

  // Animation frame counter
  const [frame, setFrame] = useState(0)

  // View mode (graph or routes)
  const [viewMode, setViewMode] = useState('graph') // 'graph' or 'routes'

  useEffect(() => {
    setBreadcrumbs(['LATTICE', 'P200'])

    // Load initial data and connect WebSocket
    loadAll()
    connectWS()

    // Cleanup: disconnect WebSocket on unmount
    return () => {
      disconnectWS()
    }
  }, [setBreadcrumbs, loadAll, connectWS, disconnectWS])

  // Transform API data to internal mesh data format
  useEffect(() => {
    if (nodes.length === 0 && threads.length === 0) {
      // No data yet, use mock data as fallback
      return
    }

    // Convert nodes to internal format with positions
    const transformedNodes = nodes.map((node, index) => ({
      id: node.id,
      type: node.type,
      callsign: node.callsign,
      status: node.status,
      battery: node.battery || 0,
      rssi: node.rssi || 0,
      // Initialize positions in a circle if not set
      x: meshDataRef.current.nodes[index]?.x ?? 15 + Math.cos(index * 0.5) * 10,
      y: meshDataRef.current.nodes[index]?.y ?? 12 + Math.sin(index * 0.5) * 8,
      vx: 0,
      vy: 0,
    }))

    // Convert threads to internal links format
    const transformedLinks = threads.map((thread) => ({
      from: thread.source_id,
      to: thread.target_id,
      quality: thread.quality,
      rssi: thread.rssi || -80,
      latency: thread.latency || 50,
      radioType: thread.radio_type,
    }))

    // Generate route table from graph structure
    const routeTable = generateRouteTable(transformedNodes, transformedLinks)

    setMeshData({
      nodes: transformedNodes,
      links: transformedLinks,
      routeTable,
    })
  }, [nodes, threads])

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

  // Show loading state
  if (nodesLoading || threadsLoading) {
    const loadingGrid = Array.from({ length: 25 }, () => 
      Array.from({ length: 40 }, () => ' ')
    )
    loadingGrid[12][15] = 'L'
    loadingGrid[12][16] = 'O'
    loadingGrid[12][17] = 'A'
    loadingGrid[12][18] = 'D'
    loadingGrid[12][19] = 'I'
    loadingGrid[12][20] = 'N'
    loadingGrid[12][21] = 'G'
    loadingGrid[12][22] = '.'
    loadingGrid[12][23] = '.'
    loadingGrid[12][24] = '.'

    return (
      <div className="teletext-demo">
        <div className="teletext-overlay">
          P200 - LATTICE MAP (LOADING)
        </div>
        <TeletextGrid content={loadingGrid} showFps />
      </div>
    )
  }

  // Show error state
  if (nodesError || threadsError) {
    const errorGrid = Array.from({ length: 25 }, () => 
      Array.from({ length: 40 }, () => ' ')
    )
    const errorMsg = nodesError || threadsError || 'Unknown error'
    const lines = [`ERROR: ${errorMsg}`, '', 'Press R to retry']
    lines.forEach((line, i) => {
      for (let j = 0; j < line.length && j < 40; j++) {
        errorGrid[10 + i][j] = line[j]
      }
    })

    return (
      <div className="teletext-demo">
        <div className="teletext-overlay">
          P200 - LATTICE MAP (ERROR)
        </div>
        <TeletextGrid content={errorGrid} showFps />
      </div>
    )
  }

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
 * Generate route table from graph structure (simple shortest path)
 */
const generateRouteTable = (nodes, links) => {
  // Simple routing: for each node, find next hop to reach it
  const routes = []
  
  // Build adjacency map
  const adjacency = new Map()
  links.forEach((link) => {
    if (!adjacency.has(link.from)) adjacency.set(link.from, [])
    if (!adjacency.has(link.to)) adjacency.set(link.to, [])
    adjacency.get(link.from).push({ node: link.to, quality: link.quality })
    adjacency.get(link.to).push({ node: link.from, quality: link.quality })
  })

  // Assume first node is "this" node
  const thisNode = nodes[0]?.id
  if (!thisNode) return []

  // BFS to find shortest path to each node
  nodes.forEach((targetNode) => {
    if (targetNode.id === thisNode) return

    const visited = new Set()
    const queue = [{ node: thisNode, path: [thisNode], metric: 0 }]
    
    while (queue.length > 0) {
      const { node, path, metric } = queue.shift()
      
      if (node === targetNode.id) {
        // Found path
        const nextHop = path.length > 1 ? path[1] : targetNode.id
        routes.push({
          dest: targetNode.callsign || targetNode.id,
          nextHop: nodes.find((n) => n.id === nextHop)?.callsign || nextHop,
          hops: path.length - 1,
          metric: metric.toFixed(1),
        })
        break
      }

      if (visited.has(node)) continue
      visited.add(node)

      const neighbors = adjacency.get(node) || []
      neighbors.forEach(({ node: neighborId, quality }) => {
        if (!visited.has(neighborId)) {
          queue.push({
            node: neighborId,
            path: [...path, neighborId],
            metric: metric + (1 - quality),
          })
        }
      })
    }
  })

  return routes
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
