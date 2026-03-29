import { describe, it, expect, beforeEach } from 'vitest'
import {
  getMockMeshData,
  updateNodePositions,
  generateParticles,
  renderLatticeMap,
  validateLatitude,
  validateLongitude,
  sanitizeString,
  validateNodeId,
  validateLink,
  validateNode,
  calculateQualityPercent,
  formatGpsCoordinates,
} from './P200.utils'
import { COLUMNS, ROWS } from '../components/TeletextGrid'

describe('P200 - Lattice Map', () => {
  let meshData

  beforeEach(() => {
    meshData = getMockMeshData()
  })

  // ========================================================================
  // SECURITY TESTS - Input Validation
  // ========================================================================
  
  describe('Input Validation - GPS Coordinates', () => {
    it('should validate latitude within valid range', () => {
      expect(validateLatitude(0)).toBe(0)
      expect(validateLatitude(45.5)).toBe(45.5)
      expect(validateLatitude(-90)).toBe(-90)
      expect(validateLatitude(90)).toBe(90)
    })

    it('should reject latitude outside valid range', () => {
      expect(validateLatitude(91)).toBeNull()
      expect(validateLatitude(-91)).toBeNull()
      expect(validateLatitude(NaN)).toBeNull()
    })

    it('should validate longitude within valid range', () => {
      expect(validateLongitude(0)).toBe(0)
      expect(validateLongitude(100)).toBe(100)
      expect(validateLongitude(-180)).toBe(-180)
      expect(validateLongitude(180)).toBe(180)
    })

    it('should reject longitude outside valid range', () => {
      expect(validateLongitude(181)).toBeNull()
      expect(validateLongitude(-181)).toBeNull()
      expect(validateLongitude(NaN)).toBeNull()
    })

    it('should format GPS coordinates safely', () => {
      expect(formatGpsCoordinates({ lat: 47.6062, lng: -122.3321 }))
        .toMatch(/^-?\d+\.\d+,-?\d+\.\d+$/)
    })

    it('should return INVALID for bad GPS coordinates', () => {
      expect(formatGpsCoordinates({ lat: 91, lng: -122.3321 })).toBe('INVALID')
      expect(formatGpsCoordinates({ lat: 47.6062, lng: 181 })).toBe('INVALID')
    })

    it('should return N/A for missing GPS', () => {
      expect(formatGpsCoordinates(null)).toBe('N/A')
      expect(formatGpsCoordinates(undefined)).toBe('N/A')
    })
  })

  describe('Input Validation - String Sanitization', () => {
    it('should sanitize control characters', () => {
      const input = 'TEST\x00\x01\x02'
      const result = sanitizeString(input)
      expect(result).toBe('TEST')
      expect(result).not.toContain('\x00')
    })

    it('should sanitize HTML special characters', () => {
      const input = 'TEST<script>alert("xss")</script>'
      const result = sanitizeString(input)
      expect(result).not.toContain('<')
      expect(result).not.toContain('>')
      expect(result).not.toContain('"')
    })

    it('should limit string length', () => {
      const input = 'A'.repeat(100)
      const result = sanitizeString(input, 50)
      expect(result.length).toBeLessThanOrEqual(50)
    })

    it('should trim whitespace', () => {
      expect(sanitizeString('  TEST  ')).toBe('TEST')
      expect(sanitizeString('\tTEST\n')).toBe('TEST')
    })
  })

  describe('Input Validation - Node IDs', () => {
    it('should validate correct node IDs', () => {
      expect(validateNodeId('SPORE-01')).toBe(true)
      expect(validateNodeId('NODE_01')).toBe(true)
      expect(validateNodeId('N1')).toBe(true)
      expect(validateNodeId('node-a1')).toBe(true)
    })

    it('should reject invalid node IDs', () => {
      expect(validateNodeId('SPORE<01')).toBe(false)
      expect(validateNodeId('NODE 01')).toBe(false)
      expect(validateNodeId('')).toBe(false)
      expect(validateNodeId(123)).toBe(false)
      expect(validateNodeId(null)).toBe(false)
    })

    it('should enforce maximum length', () => {
      const longId = 'A'.repeat(51)
      expect(validateNodeId(longId)).toBe(false)
    })
  })

  describe('Input Validation - Links', () => {
    it('should validate correct link structure', () => {
      const validLink = {
        from: 'NODE-01',
        to: 'NODE-02',
        quality: 'GOOD',
        rssi: -72,
        latency: 8,
        packetLoss: 0,
      }
      expect(validateLink(validLink)).toBe(true)
    })

    it('should reject invalid link quality', () => {
      const invalidLink = {
        from: 'NODE-01',
        to: 'NODE-02',
        quality: 'INVALID',
        rssi: -72,
        latency: 8,
        packetLoss: 0,
      }
      expect(validateLink(invalidLink)).toBe(false)
    })

    it('should reject RSSI outside valid range', () => {
      const invalidLink = {
        from: 'NODE-01',
        to: 'NODE-02',
        quality: 'GOOD',
        rssi: -200,
        latency: 8,
        packetLoss: 0,
      }
      expect(validateLink(invalidLink)).toBe(false)
    })

    it('should reject negative latency', () => {
      const invalidLink = {
        from: 'NODE-01',
        to: 'NODE-02',
        quality: 'GOOD',
        rssi: -72,
        latency: -10,
        packetLoss: 0,
      }
      expect(validateLink(invalidLink)).toBe(false)
    })

    it('should reject packet loss outside 0-100%', () => {
      const invalidLink = {
        from: 'NODE-01',
        to: 'NODE-02',
        quality: 'GOOD',
        rssi: -72,
        latency: 8,
        packetLoss: 150,
      }
      expect(validateLink(invalidLink)).toBe(false)
    })
  })

  describe('Input Validation - Nodes', () => {
    it('should validate correct node structure', () => {
      const validNode = {
        id: 'NODE-01',
        type: 'SPORE',
        x: 10,
        y: 10,
        battery: 50,
        status: 'active',
        gps: { lat: 47.6062, lng: -122.3321 },
      }
      expect(validateNode(validNode)).toBe(true)
    })

    it('should reject invalid node type', () => {
      const invalidNode = {
        id: 'NODE-01',
        type: 'INVALID',
        x: 10,
        y: 10,
        battery: 50,
        status: 'active',
      }
      expect(validateNode(invalidNode)).toBe(false)
    })

    it('should reject battery outside 0-100%', () => {
      const invalidNode = {
        id: 'NODE-01',
        type: 'SPORE',
        x: 10,
        y: 10,
        battery: 150,
        status: 'active',
      }
      expect(validateNode(invalidNode)).toBe(false)
    })

    it('should reject invalid status', () => {
      const invalidNode = {
        id: 'NODE-01',
        type: 'SPORE',
        x: 10,
        y: 10,
        battery: 50,
        status: 'invalid',
      }
      expect(validateNode(invalidNode)).toBe(false)
    })

    it('should reject invalid GPS', () => {
      const invalidNode = {
        id: 'NODE-01',
        type: 'SPORE',
        x: 10,
        y: 10,
        battery: 50,
        status: 'active',
        gps: { lat: 91, lng: -122.3321 },
      }
      expect(validateNode(invalidNode)).toBe(false)
    })
  })

  // ========================================================================
  // DATA STRUCTURE TESTS
  // ========================================================================

  describe('getMockMeshData', () => {
    it('should return mesh data with nodes, links, and routes', () => {
      expect(meshData).toHaveProperty('nodes')
      expect(meshData).toHaveProperty('links')
      expect(meshData).toHaveProperty('routeTable')
      expect(Array.isArray(meshData.nodes)).toBe(true)
      expect(Array.isArray(meshData.links)).toBe(true)
      expect(Array.isArray(meshData.routeTable)).toBe(true)
    })

    it('should have valid node structure', () => {
      expect(meshData.nodes.length).toBeGreaterThan(0)
      meshData.nodes.forEach(node => {
        expect(node).toHaveProperty('id')
        expect(node).toHaveProperty('type')
        expect(node).toHaveProperty('x')
        expect(node).toHaveProperty('y')
        expect(node).toHaveProperty('battery')
        expect(node).toHaveProperty('status')
        expect(validateNode(node)).toBe(true)
      })
    })

    it('should have valid link structure', () => {
      expect(meshData.links.length).toBeGreaterThan(0)
      meshData.links.forEach(link => {
        expect(link).toHaveProperty('from')
        expect(link).toHaveProperty('to')
        expect(link).toHaveProperty('quality')
        expect(link).toHaveProperty('rssi')
        expect(link).toHaveProperty('latency')
        expect(link).toHaveProperty('packetLoss')
        expect(validateLink(link)).toBe(true)
      })
    })

    it('should have different node types', () => {
      const types = new Set(meshData.nodes.map(n => n.type))
      expect(types.size).toBeGreaterThan(1)
      expect(types.has('SPORE')).toBe(true)
    })

    it('should have links between existing nodes', () => {
      const nodeIds = new Set(meshData.nodes.map(n => n.id))
      meshData.links.forEach(link => {
        expect(nodeIds.has(link.from)).toBe(true)
        expect(nodeIds.has(link.to)).toBe(true)
      })
    })
  })

  // ========================================================================
  // PHYSICS & SIMULATION TESTS
  // ========================================================================

  describe('updateNodePositions', () => {
    it('should initialize velocities on first call', () => {
      const nodes = [
        { id: 'A', x: 10, y: 10 },
        { id: 'B', x: 20, y: 20 },
      ]
      const links = []
      const bounds = { maxX: 40, maxY: 25 }

      updateNodePositions(nodes, links, bounds)

      nodes.forEach(node => {
        expect(node).toHaveProperty('vx')
        expect(node).toHaveProperty('vy')
      })
    })

    it('should keep nodes within bounds', () => {
      const nodes = [
        { id: 'A', x: -5, y: -5 },
        { id: 'B', x: 50, y: 50 },
      ]
      const links = []
      const bounds = { maxX: 40, maxY: 25 }

      updateNodePositions(nodes, links, bounds)

      nodes.forEach(node => {
        expect(node.x).toBeGreaterThanOrEqual(0)
        expect(node.x).toBeLessThanOrEqual(bounds.maxX)
        expect(node.y).toBeGreaterThanOrEqual(0)
        expect(node.y).toBeLessThanOrEqual(bounds.maxY)
      })
    })

    it('should apply repulsion force between nodes', () => {
      const nodes = [
        { id: 'A', x: 20, y: 20, vx: 0, vy: 0 },
        { id: 'B', x: 20, y: 20, vx: 0, vy: 0 },
      ]
      const links = []
      const bounds = { maxX: 40, maxY: 25 }

      updateNodePositions(nodes, links, bounds)

      // Nodes at same position should repel each other
      const moved = nodes.some(n => Math.abs(n.vx) > 0 || Math.abs(n.vy) > 0)
      expect(moved).toBe(true)
    })

    it('should apply attraction force along links', () => {
      const nodes = [
        { id: 'A', x: 5, y: 5, vx: 0, vy: 0 },
        { id: 'B', x: 35, y: 20, vx: 0, vy: 0 },
      ]
      const links = [{ from: 'A', to: 'B', quality: 'GOOD', rssi: -72, latency: 8, packetLoss: 0 }]
      const bounds = { maxX: 40, maxY: 25 }

      const initialDist = Math.hypot(
        nodes[1].x - nodes[0].x,
        nodes[1].y - nodes[0].y
      )

      updateNodePositions(nodes, links, bounds)

      // Nodes should move toward each other
      const newDist = Math.hypot(
        nodes[1].x - nodes[0].x,
        nodes[1].y - nodes[0].y
      )

      expect(newDist).toBeLessThan(initialDist)
    })

    it('should handle null/undefined inputs gracefully', () => {
      expect(() => updateNodePositions(null, [], {})).not.toThrow()
      expect(() => updateNodePositions([], null, {})).not.toThrow()
      expect(() => updateNodePositions([], [], null)).not.toThrow()
    })
  })

  describe('generateParticles', () => {
    it('should generate particles for each link', () => {
      const nodes = [
        { id: 'A', x: 10, y: 10 },
        { id: 'B', x: 20, y: 20 },
      ]
      const links = [
        { from: 'A', to: 'B', quality: 'GOOD', rssi: -72, latency: 8, packetLoss: 0 },
      ]

      const particles = generateParticles(links, nodes, 0)

      expect(particles.length).toBeGreaterThan(0)
    })

    it('should create more particles for GOOD quality links', () => {
      const nodes = [
        { id: 'A', x: 10, y: 10 },
        { id: 'B', x: 20, y: 20 },
        { id: 'C', x: 15, y: 15 },
      ]
      const links = [
        { from: 'A', to: 'B', quality: 'GOOD', rssi: -72, latency: 8, packetLoss: 0 },
        { from: 'B', to: 'C', quality: 'DEGRADED', rssi: -91, latency: 98, packetLoss: 11 },
      ]

      const particles = generateParticles(links, nodes, 0)
      const goodLinkParticles = particles.filter(p => p.link.quality === 'GOOD')
      const degradedLinkParticles = particles.filter(p => p.link.quality === 'DEGRADED')

      expect(goodLinkParticles.length).toBeGreaterThanOrEqual(degradedLinkParticles.length)
    })

    it('should position particles along the link path', () => {
      const nodes = [
        { id: 'A', x: 10, y: 10 },
        { id: 'B', x: 20, y: 10 },
      ]
      const links = [
        { from: 'A', to: 'B', quality: 'GOOD', rssi: -72, latency: 8, packetLoss: 0 },
      ]

      const particles = generateParticles(links, nodes, 0)

      particles.forEach(particle => {
        expect(particle.x).toBeGreaterThanOrEqual(10)
        expect(particle.x).toBeLessThanOrEqual(20)
        expect(particle.y).toBe(10)
      })
    })

    it('should skip invalid links', () => {
      const nodes = [
        { id: 'A', x: 10, y: 10 },
        { id: 'B', x: 20, y: 20 },
      ]
      const links = [
        { from: 'A', to: 'B', quality: 'INVALID', rssi: -72, latency: 8, packetLoss: 0 },
      ]

      // Should not throw and should return empty array
      expect(() => generateParticles(links, nodes, 0)).not.toThrow()
    })

    it('should cap total particles to prevent exhaustion', () => {
      const nodes = Array.from({ length: 100 }, (_, i) => ({
        id: `NODE-${i}`,
        x: Math.random() * 30,
        y: Math.random() * 15,
      }))

      const links = []
      for (let i = 0; i < 50; i++) {
        links.push({
          from: `NODE-${i}`,
          to: `NODE-${i + 1}`,
          quality: 'GOOD',
          rssi: -72,
          latency: 8,
          packetLoss: 0,
        })
      }

      const particles = generateParticles(links, nodes, 0)
      // Should be capped at reasonable limit
      expect(particles.length).toBeLessThan(600)
    })
  })

  describe('calculateQualityPercent', () => {
    it('should return 0 for null/undefined links', () => {
      expect(calculateQualityPercent(null)).toBe(0)
      expect(calculateQualityPercent(undefined)).toBe(0)
    })

    it('should calculate quality between 0-100', () => {
      const link = { rssi: -72, latency: 8, packetLoss: 0 }
      const quality = calculateQualityPercent(link)
      expect(quality).toBeGreaterThanOrEqual(0)
      expect(quality).toBeLessThanOrEqual(100)
    })

    it('should handle extreme RSSI values', () => {
      const goodLink = { rssi: -30, latency: 8, packetLoss: 0 }
      const badLink = { rssi: -120, latency: 8, packetLoss: 0 }
      
      expect(calculateQualityPercent(goodLink)).toBeGreaterThan(
        calculateQualityPercent(badLink)
      )
    })

    it('should handle extreme latency values', () => {
      const lowLatency = { rssi: -72, latency: 0, packetLoss: 0 }
      const highLatency = { rssi: -72, latency: 200, packetLoss: 0 }
      
      expect(calculateQualityPercent(lowLatency)).toBeGreaterThan(
        calculateQualityPercent(highLatency)
      )
    })
  })

  // ========================================================================
  // RENDERING TESTS
  // ========================================================================

  describe('renderLatticeMap', () => {
    it('should return a grid with correct dimensions', () => {
      const grid = renderLatticeMap(meshData, null, null, 0, null, null, null, true)

      expect(grid.length).toBe(ROWS)
      grid.forEach(row => {
        expect(row.length).toBe(COLUMNS)
      })
    })

    it('should render header', () => {
      const grid = renderLatticeMap(meshData, null, null, 0, null, null, null, true)
      const headerRow = grid[0].join('')

      expect(headerRow).toContain('LATTICE MAP')
      expect(headerRow).toContain('P200')
    })

    it('should show node count in header', () => {
      const grid = renderLatticeMap(meshData, null, null, 0, null, null, null, true)
      const headerRow = grid[0].join('')

      expect(headerRow).toContain(`${meshData.nodes.length}`)
      expect(headerRow).toContain('CELLS')
    })

    it('should render footer with instructions', () => {
      const grid = renderLatticeMap(meshData, null, null, 0, null, null, null, true)
      const footerRow = grid[ROWS - 1].join('')

      expect(footerRow).toContain('outes')
      expect(footerRow).toContain('ode')
      expect(footerRow).toContain('ink')
    })

    it('should display summary stats when no selection', () => {
      const grid = renderLatticeMap(meshData, null, null, 0, null, null, null, true)
      const detailRows = grid.slice(ROWS - 7, ROWS - 1).map(r => r.join(''))
      const detailText = detailRows.join(' ')

      expect(detailText).toContain('MESH TOPOLOGY')
      expect(detailText).toContain('Links')
    })

    it('should display node details when node selected', () => {
      const selectedNode = meshData.nodes[0]
      const grid = renderLatticeMap(meshData, selectedNode, null, 0, null, null, null, true)
      const detailRows = grid.slice(ROWS - 7, ROWS - 1).map(r => r.join(''))
      const detailText = detailRows.join(' ')

      expect(detailText).toContain('NODE')
      expect(detailText).toContain('Type')
      expect(detailText).toContain('Batt')
    })

    it('should display link details when link selected', () => {
      const selectedLink = meshData.links[0]
      const grid = renderLatticeMap(meshData, null, selectedLink, 0, null, null, null, true)
      const detailRows = grid.slice(ROWS - 7, ROWS - 1).map(r => r.join(''))
      const detailText = detailRows.join(' ')

      expect(detailText).toContain('LINK')
      expect(detailText).toContain('RSSI')
      expect(detailText).toContain('dBm')
      expect(detailText).toContain('Loss')
    })

    it('should render legend', () => {
      const grid = renderLatticeMap(meshData, null, null, 0, null, null, null, true)
      const legendRow = grid[ROWS - 2].join('')

      expect(legendRow).toContain('SPORE')
      expect(legendRow).toContain('HYPHA')
      expect(legendRow).toContain('FROND')
      expect(legendRow).toContain('RHIZOME')
    })

    it('should place all characters within grid bounds', () => {
      const grid = renderLatticeMap(meshData, null, null, 0, null, null, null, true)

      // Every cell should be a valid character
      grid.forEach((row) => {
        row.forEach((char) => {
          expect(typeof char).toBe('string')
          expect(char.length).toBe(1)
        })
      })
    })

    it('should handle invalid mesh data gracefully', () => {
      expect(() => renderLatticeMap(null, null, null, 0, null, null, null, true)).not.toThrow()
      expect(() => renderLatticeMap({}, null, null, 0, null, null, null, true)).not.toThrow()
    })

    it('should sanitize node IDs in rendering', () => {
      const maliciousNode = {
        ...meshData.nodes[0],
        id: 'NODE<script>alert("xss")</script>',
      }
      
      const customMesh = {
        ...meshData,
        nodes: [maliciousNode, ...meshData.nodes.slice(1)],
      }

      const grid = renderLatticeMap(customMesh, maliciousNode, null, 0, null, null, null, true)
      const gridText = grid.map(r => r.join('')).join(' ')
      
      // Should not contain script tags
      expect(gridText).not.toContain('<')
      expect(gridText).not.toContain('>')
    })
  })
})
