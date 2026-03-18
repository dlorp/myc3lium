import { useEffect, useState, useRef } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import useMeshStore from '../store/meshStore'
import { 
  renderLatticeMap, 
  renderRoutesTable,
  getMockMeshData, 
  updateNodePositions,
  calculateQualityPercent
} from './P200.utils'

/**
 * P200 - Lattice Map Page (Enhanced)
 * 
 * Force-directed graph visualization of mesh network topology with:
 * - Animated data flow particles (quality-based speed)
 * - Interactive tooltips on hover (node & link details)
 * - Zoom & pan controls (mouse wheel, click-drag, double-click)
 * - Visual polish: glows, animations, degraded indicators, critical alerts
 * - Interactive legend with filtering
 * - Quality-based particle visualization
 */

const P200 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)

  // Mesh data from store
  const nodes = useMeshStore((state) => state.nodes)
  const threads = useMeshStore((state) => state.threads)
  const nodesLoading = useMeshStore((state) => state.nodesLoading)
  const threadsLoading = useMeshStore((state) => state.threadsLoading)
  const nodesError = useMeshStore((state) => state.nodesError)
  const threadsError = useMeshStore((state) => state.threadsError)
  const loadAll = useMeshStore((state) => state.loadAll)
  const connectWS = useMeshStore((state) => state.connectWS)
  const disconnectWS = useMeshStore((state) => state.disconnectWS)

  // Mesh data ref with fallback to mock
  const meshDataRef = useRef(getMockMeshData())
  const [meshData, setMeshData] = useState(meshDataRef.current)

  // Selection state
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedLink, setSelectedLink] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)
  const [hoveredLink, setHoveredLink] = useState(null)

  // View & control state
  const [frame, setFrame] = useState(0)
  const [viewMode, setViewMode] = useState('graph') // 'graph' or 'routes'
  const [zoom, setZoom] = useState(1.0)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [filterType, setFilterType] = useState(null) // Filter by node type
  const [showLegend, setShowLegend] = useState(true)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  // Refs for interaction tracking
  const containerRef = useRef(null)
  const lastZoomTimeRef = useRef(0)

  // Initialize breadcrumbs and load data
  useEffect(() => {
    setBreadcrumbs(['LATTICE', 'P200'])
    loadAll()
    connectWS()

    return () => {
      disconnectWS()
    }
  }, [setBreadcrumbs, loadAll, connectWS, disconnectWS])

  // Transform API data to internal mesh format
  useEffect(() => {
    if (nodes.length === 0 && threads.length === 0) {
      return
    }

    const transformedNodes = nodes.map((node, index) => ({
      id: node.id,
      callsign: node.callsign || `NODE-${index}`,
      type: node.type,
      status: node.status,
      battery: node.battery || 50,
      rssi: node.rssi || -80,
      gps: node.gps || { lat: 61.2181, lng: -149.9003 },
      x: meshDataRef.current.nodes[index]?.x ?? 15 + Math.cos(index * 0.5) * 10,
      y: meshDataRef.current.nodes[index]?.y ?? 12 + Math.sin(index * 0.5) * 8,
      vx: 0,
      vy: 0,
    }))

    const transformedLinks = threads.map((thread) => ({
      from: thread.source_id,
      to: thread.target_id,
      quality: thread.quality,
      rssi: thread.rssi || -80,
      latency: thread.latency || 50,
      packetLoss: thread.packet_loss || 0,
      radioType: thread.radio_type || 'LoRa',
    }))

    const routeTable = generateRouteTable(transformedNodes, transformedLinks)

    setMeshData({
      nodes: transformedNodes,
      links: transformedLinks,
      routeTable,
    })
  }, [nodes, threads])

  // Animation loop for particles and pulses
  useEffect(() => {
    const interval = setInterval(() => {
      setFrame(prev => prev + 1)
    }, 50) // ~20fps animation for smooth particle flow

    return () => clearInterval(interval)
  }, [])

  // Physics simulation for force-directed layout
  useEffect(() => {
    const graphBounds = {
      maxX: 30,
      maxY: 15,
    }

    const interval = setInterval(() => {
      updateNodePositions(meshData.nodes, meshData.links, graphBounds)
    }, 300) // Update physics every 300ms

    return () => clearInterval(interval)
  }, [meshData])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase()

      if (key === 'r') {
        setViewMode(prev => prev === 'graph' ? 'routes' : 'graph')
      } else if (key === 'n') {
        const currentIndex = selectedNode 
          ? meshData.nodes.findIndex(n => n.id === selectedNode.id)
          : -1
        const nextIndex = (currentIndex + 1) % meshData.nodes.length
        setSelectedNode(meshData.nodes[nextIndex])
        setSelectedLink(null)
      } else if (key === 'l') {
        const currentIndex = selectedLink
          ? meshData.links.findIndex(l => 
              l.from === selectedLink.from && l.to === selectedLink.to
            )
          : -1
        const nextIndex = (currentIndex + 1) % meshData.links.length
        setSelectedLink(meshData.links[nextIndex])
        setSelectedNode(null)
      } else if (key === 'escape') {
        setSelectedNode(null)
        setSelectedLink(null)
        setHoveredNode(null)
        setHoveredLink(null)
      } else if (key === 'f') {
        // Cycle through node type filters
        const types = [null, 'SPORE', 'HYPHA', 'FROND', 'RHIZOME']
        const currentIndex = types.indexOf(filterType)
        setFilterType(types[(currentIndex + 1) % types.length])
      } else if (key === 'z') {
        // Reset zoom and pan
        setZoom(1.0)
        setPan({ x: 0, y: 0 })
      } else if (key === 'm') {
        // Toggle legend
        setShowLegend(prev => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [meshData, selectedNode, selectedLink, filterType])

  // Mouse wheel zoom
  const handleWheel = (e) => {
    e.preventDefault()
    const now = Date.now()
    
    // Debounce zoom events
    if (now - lastZoomTimeRef.current < 100) return
    lastZoomTimeRef.current = now

    const delta = e.deltaY > 0 ? 0.9 : 1.1 // Zoom out or in
    const newZoom = Math.max(1.0, Math.min(3.0, zoom * delta))
    setZoom(newZoom)
  }

  // Click-drag pan
  const handleMouseDown = (e) => {
    if (e.button === 0) { // Left click
      setIsDragging(true)
      setDragStart({ x: e.clientX, y: e.clientY })
    }
  }

  const handleMouseMove = (e) => {
    if (isDragging) {
      const dx = (e.clientX - dragStart.x) * 0.5
      const dy = (e.clientY - dragStart.y) * 0.5
      setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }))
      setDragStart({ x: e.clientX, y: e.clientY })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // Double-click to center on node
  const handleDoubleClick = () => {
    if (selectedNode) {
      // Animate zoom to selected node (TODO: implement smooth animation)
      setZoom(2.0)
      setPan({
        x: -selectedNode.x * 20 + 100,
        y: -selectedNode.y * 20 + 100,
      })
    }
  }

  // Loading state
  if (nodesLoading || threadsLoading) {
    const loadingGrid = Array.from({ length: 25 }, () => 
      Array.from({ length: 40 }, () => ' ')
    )
    const msg = 'LOADING MESH DATA...'
    for (let i = 0; i < msg.length; i++) {
      loadingGrid[12][15 + i] = msg[i]
    }

    return (
      <div className="teletext-demo">
        <div className="teletext-overlay">
          P200 - LATTICE MAP (LOADING)
        </div>
        <TeletextGrid content={loadingGrid} showFps />
      </div>
    )
  }

  // Error state
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

  // Render appropriate view
  const content = viewMode === 'graph'
    ? renderLatticeMap(
        meshData, 
        selectedNode, 
        selectedLink, 
        frame,
        hoveredNode,
        hoveredLink,
        filterType,
        showLegend
      )
    : renderRoutesTable(meshData)

  return (
    <div 
      className="teletext-demo"
      ref={containerRef}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onDoubleClick={handleDoubleClick}
      style={{
        transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
        transformOrigin: '0 0',
        cursor: isDragging ? 'grabbing' : 'grab',
        transition: isDragging ? 'none' : 'transform 0.3s ease-out',
      }}
    >
      <div className="teletext-overlay">
        P200 - LATTICE MAP {viewMode === 'routes' ? '(ROUTES)' : ''} {filterType ? `[${filterType}]` : ''} Z:{zoom.toFixed(1)}x
      </div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

/**
 * Generate route table from graph structure (BFS-based shortest path)
 */
const generateRouteTable = (nodes, links) => {
  const routes = []
  
  const adjacency = new Map()
  links.forEach((link) => {
    if (!adjacency.has(link.from)) adjacency.set(link.from, [])
    if (!adjacency.has(link.to)) adjacency.set(link.to, [])
    adjacency.get(link.from).push({ node: link.to, quality: link.quality })
    adjacency.get(link.to).push({ node: link.from, quality: link.quality })
  })

  const thisNode = nodes[0]?.id
  if (!thisNode) return []

  nodes.forEach((targetNode) => {
    if (targetNode.id === thisNode) return

    const visited = new Set()
    const queue = [{ node: thisNode, path: [thisNode], metric: 0 }]
    
    while (queue.length > 0) {
      const { node, path, metric } = queue.shift()
      
      if (node === targetNode.id) {
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
            metric: metric + (1 - (quality === 'GOOD' ? 0.8 : quality === 'FAIR' ? 0.5 : 0.2)),
          })
        }
      })
    }
  })

  return routes
}

export default P200
