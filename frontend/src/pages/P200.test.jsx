import { describe, it, expect, beforeEach } from 'vitest'
import {
  getMockMeshData,
  updateNodePositions,
  generateParticles,
  renderLatticeMap,
} from './P200.utils'
import { COLUMNS, ROWS } from '../components/TeletextGrid'

describe('P200 - Lattice Map', () => {
  let meshData

  beforeEach(() => {
    meshData = getMockMeshData()
  })

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
        expect(node).toHaveProperty('hopCount')
        expect(node).toHaveProperty('battery')
        expect(node).toHaveProperty('uptime')
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
        { id: 'B', x: 20, y: 20, vx: 0, vy: 0 }, // Same position
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
      const links = [{ from: 'A', to: 'B' }]
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
  })

  describe('generateParticles', () => {
    it('should generate particles for each link', () => {
      const nodes = [
        { id: 'A', x: 10, y: 10 },
        { id: 'B', x: 20, y: 20 },
      ]
      const links = [
        { from: 'A', to: 'B', quality: 'GOOD' },
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
        { from: 'A', to: 'B', quality: 'GOOD' },
        { from: 'B', to: 'C', quality: 'DEGRADED' },
      ]

      const particles = generateParticles(links, nodes, 0)
      const goodLinkParticles = particles.filter(p => p.link.quality === 'GOOD')
      const degradedLinkParticles = particles.filter(p => p.link.quality === 'DEGRADED')

      expect(goodLinkParticles.length).toBeGreaterThan(degradedLinkParticles.length)
    })

    it('should position particles along the link path', () => {
      const nodes = [
        { id: 'A', x: 10, y: 10 },
        { id: 'B', x: 20, y: 10 },
      ]
      const links = [
        { from: 'A', to: 'B', quality: 'GOOD' },
      ]

      const particles = generateParticles(links, nodes, 0)

      particles.forEach(particle => {
        // Particles should be between the two nodes
        expect(particle.x).toBeGreaterThanOrEqual(10)
        expect(particle.x).toBeLessThanOrEqual(20)
        expect(particle.y).toBe(10)
      })
    })
  })

  describe('renderLatticeMap', () => {
    it('should return a grid with correct dimensions', () => {
      const grid = renderLatticeMap(meshData, null, null, 0)

      expect(grid.length).toBe(ROWS)
      grid.forEach(row => {
        expect(row.length).toBe(COLUMNS)
      })
    })

    it('should render header', () => {
      const grid = renderLatticeMap(meshData, null, null, 0)
      const headerRow = grid[0].join('')

      expect(headerRow).toContain('LATTICE MAP')
      expect(headerRow).toContain('P200')
    })

    it('should show node count in header', () => {
      const grid = renderLatticeMap(meshData, null, null, 0)
      const headerRow = grid[0].join('')

      expect(headerRow).toContain(`${meshData.nodes.length}`)
      expect(headerRow).toContain('CELLS')
    })

    it('should render footer with instructions', () => {
      const grid = renderLatticeMap(meshData, null, null, 0)
      const footerRow = grid[ROWS - 1].join('')

      expect(footerRow).toContain('outes')
      expect(footerRow).toContain('ode')
      expect(footerRow).toContain('ink')
    })

    it('should display summary stats when no selection', () => {
      const grid = renderLatticeMap(meshData, null, null, 0)
      const detailRows = grid.slice(ROWS - 7, ROWS - 1).map(r => r.join(''))
      const detailText = detailRows.join(' ')

      expect(detailText).toContain('MESH TOPOLOGY')
      expect(detailText).toContain('Links')
    })

    it('should display node details when node selected', () => {
      const selectedNode = meshData.nodes[0]
      const grid = renderLatticeMap(meshData, selectedNode, null, 0)
      const detailRows = grid.slice(ROWS - 7, ROWS - 1).map(r => r.join(''))
      const detailText = detailRows.join(' ')

      expect(detailText).toContain('NODE')
      expect(detailText).toContain(selectedNode.id)
      expect(detailText).toContain('Type')
      expect(detailText).toContain('Hops')
      expect(detailText).toContain('Batt')
    })

    it('should display link details when link selected', () => {
      const selectedLink = meshData.links[0]
      const grid = renderLatticeMap(meshData, null, selectedLink, 0)
      const detailRows = grid.slice(ROWS - 7, ROWS - 1).map(r => r.join(''))
      const detailText = detailRows.join(' ')

      expect(detailText).toContain('LINK')
      expect(detailText).toContain('RSSI')
      expect(detailText).toContain('dBm')
      expect(detailText).toContain('Loss')
    })

    it('should render legend', () => {
      const grid = renderLatticeMap(meshData, null, null, 0)
      const legendRow = grid[ROWS - 2].join('')

      expect(legendRow).toContain('SPORE')
      expect(legendRow).toContain('HYPHA')
      expect(legendRow).toContain('FROND')
      expect(legendRow).toContain('RHIZOME')
    })

    it('should place all characters within grid bounds', () => {
      const grid = renderLatticeMap(meshData, null, null, 0)

      // Every cell should be a valid character
      grid.forEach((row) => {
        row.forEach((char) => {
          expect(typeof char).toBe('string')
          expect(char.length).toBe(1)
        })
      })
    })
  })
})
