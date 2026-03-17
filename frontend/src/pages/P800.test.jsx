import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import P800 from './P800'
import { renderLLMChat, getMockData, simulateLLMResponse, MESSAGE_ROLES, MODEL_STATUS } from './P800.utils'
import useNavigationStore from '../store/navigationStore'
import { COLUMNS, ROWS } from '../components/TeletextGrid'

describe('P800 LLM Chat Interface', () => {
  beforeEach(() => {
    useNavigationStore.setState({
      currentPage: 800,
      history: [800],
      breadcrumbs: [],
    })
  })
  
  it('renders LLM chat page', () => {
    render(<P800 />)
    expect(screen.getByText(/P800 - LOCAL LLM/)).toBeInTheDocument()
  })
  
  it('sets breadcrumbs to LOCAL LLM', () => {
    render(<P800 />)
    
    const state = useNavigationStore.getState()
    expect(state.breadcrumbs).toEqual(['LOCAL LLM', 'P800'])
  })
  
  it('displays teletext grid', () => {
    const { container } = render(<P800 />)
    
    // Should have the teletext demo container
    const demo = container.querySelector('.teletext-demo')
    expect(demo).toBeTruthy()
  })
})

describe('P800.utils - getMockData', () => {
  it('returns initial mock data with correct structure', () => {
    const data = getMockData()
    
    expect(data).toHaveProperty('modelName')
    expect(data).toHaveProperty('status')
    expect(data).toHaveProperty('tokenCount')
    expect(data).toHaveProperty('maxTokens')
    expect(data).toHaveProperty('temperature')
    expect(data).toHaveProperty('messages')
    
    expect(data.modelName).toBe('Qwen2.5-7B-Instruct-Q4')
    expect(data.status).toBe(MODEL_STATUS.IDLE)
    expect(data.messages).toBeInstanceOf(Array)
    expect(data.messages.length).toBeGreaterThan(0)
  })
  
  it('includes system initialization messages', () => {
    const data = getMockData()
    
    const systemMessages = data.messages.filter(m => m.role === MESSAGE_ROLES.SYSTEM)
    expect(systemMessages.length).toBeGreaterThanOrEqual(2)
    
    expect(systemMessages[0].content).toContain('MYC3LIUM')
    expect(systemMessages[1].content).toContain('Access')
  })
  
  it('messages have required fields', () => {
    const data = getMockData()
    
    for (const msg of data.messages) {
      expect(msg).toHaveProperty('role')
      expect(msg).toHaveProperty('content')
      expect(msg).toHaveProperty('timestamp')
      
      expect(typeof msg.role).toBe('string')
      expect(typeof msg.content).toBe('string')
      expect(typeof msg.timestamp).toBe('string')
    }
  })
})

describe('P800.utils - simulateLLMResponse', () => {
  it('generates response for temperature query', () => {
    const response = simulateLLMResponse('Show me temp trends')
    
    expect(response.role).toBe(MESSAGE_ROLES.LLM)
    expect(response.content).toContain('RHIZOME')
    // Response contains temperature data (°C)
    expect(response.content).toContain('°C')
    expect(response).toHaveProperty('timestamp')
  })
  
  it('generates response for sensor query', () => {
    const response = simulateLLMResponse('What about sensors?')
    
    expect(response.role).toBe(MESSAGE_ROLES.LLM)
    expect(response.content.toLowerCase()).toContain('rhizome')
  })
  
  it('generates response for RF query', () => {
    const response = simulateLLMResponse('Any RF signals detected?')
    
    expect(response.role).toBe(MESSAGE_ROLES.LLM)
    expect(response.content).toContain('MHz')
  })
  
  it('generates response for lattice query', () => {
    const response = simulateLLMResponse('Lattice status')
    
    expect(response.role).toBe(MESSAGE_ROLES.LLM)
    expect(response.content.toLowerCase()).toContain('lattice')
  })
  
  it('generates response for battery query', () => {
    const response = simulateLLMResponse('Battery levels?')
    
    expect(response.role).toBe(MESSAGE_ROLES.LLM)
    expect(response.content.toLowerCase()).toContain('battery')
  })
  
  it('generates response for greeting', () => {
    const response = simulateLLMResponse('hello')
    
    expect(response.role).toBe(MESSAGE_ROLES.LLM)
    expect(response.content.toLowerCase()).toContain('ready')
  })
  
  it('generates generic echo for unknown query', () => {
    const response = simulateLLMResponse('random unknown query xyz')
    
    expect(response.role).toBe(MESSAGE_ROLES.LLM)
    expect(response.content).toContain('Query received')
    expect(response.content).toContain('random unknown query xyz')
  })
  
  it('includes timestamp in response', () => {
    const response = simulateLLMResponse('test')
    
    expect(response.timestamp).toBeTruthy()
    expect(typeof response.timestamp).toBe('string')
    // Should be in HH:MM:SS format
    expect(response.timestamp).toMatch(/^\d{2}:\d{2}:\d{2}$/)
  })
})

describe('P800.utils - renderLLMChat', () => {
  it('renders grid with correct dimensions', () => {
    const data = getMockData()
    const grid = renderLLMChat(data)
    
    expect(grid.length).toBe(ROWS)
    expect(grid[0].length).toBe(COLUMNS)
  })
  
  it('includes header with page identifier', () => {
    const data = getMockData()
    const grid = renderLLMChat(data)
    
    const headerRow = grid[0].join('')
    expect(headerRow).toContain('LOCAL LLM')
    expect(headerRow).toContain('P800')
  })
  
  it('displays token count', () => {
    const data = getMockData()
    const grid = renderLLMChat(data)
    
    const headerRow = grid[0].join('')
    // Token count shown as "248/8192t" format
    expect(headerRow).toMatch(/\d+\/\d+t/)
  })
  
  it('displays status indicator', () => {
    const data = getMockData()
    const grid = renderLLMChat(data, '', false)
    
    const statusRow = grid[2].join('')
    expect(statusRow).toMatch(/IDLE|LOADED|GENERATING/)
  })
  
  it('shows generating status when active', () => {
    const data = { ...getMockData(), status: MODEL_STATUS.GENERATING }
    const grid = renderLLMChat(data, '', true)
    
    const statusRow = grid[2].join('')
    expect(statusRow).toContain('GENERATING')
  })
  
  it('renders system messages', () => {
    const data = getMockData()
    const grid = renderLLMChat(data)
    
    const gridText = grid.map(row => row.join('')).join('\n')
    
    // Should contain system message indicators
    expect(gridText).toContain('SYS')
    expect(gridText).toContain('MYC3LIUM')
  })
  
  it('renders user messages with USER prefix', () => {
    const data = getMockData()
    data.messages.push({
      role: MESSAGE_ROLES.USER,
      content: 'Test user message',
      timestamp: '12:34:56',
    })
    
    const grid = renderLLMChat(data)
    const gridText = grid.map(row => row.join('')).join('\n')
    
    expect(gridText).toContain('USER')
    expect(gridText).toContain('Test user message')
  })
  
  it('renders LLM messages with LLM prefix', () => {
    const data = getMockData()
    data.messages.push({
      role: MESSAGE_ROLES.LLM,
      content: 'Test LLM response',
      timestamp: '12:34:57',
    })
    
    const grid = renderLLMChat(data)
    const gridText = grid.map(row => row.join('')).join('\n')
    
    expect(gridText).toContain('LLM')
    expect(gridText).toContain('Test LLM response')
  })
  
  it('displays input box with border', () => {
    const data = getMockData()
    const grid = renderLLMChat(data)
    
    // Input box should be near the bottom
    const bottomArea = grid.slice(-9).map(row => row.join('')).join('\n')
    
    // Should have box drawing characters
    expect(bottomArea).toMatch(/[┌┐└┘─│]/)
  })
  
  it('displays input placeholder when empty', () => {
    const data = getMockData()
    const grid = renderLLMChat(data, '')
    
    const gridText = grid.map(row => row.join('')).join('\n')
    // Placeholder may have cursor blinking over first character
    expect(gridText).toMatch(/[█T]YPE MESSAGE/)
  })
  
  it('displays user input when typing', () => {
    const data = getMockData()
    const inputValue = 'Hello LLM'
    const grid = renderLLMChat(data, inputValue)
    
    const gridText = grid.map(row => row.join('')).join('\n')
    expect(gridText).toContain(inputValue)
  })
  
  it('includes footer with llama.cpp and RAM info', () => {
    const data = getMockData()
    const grid = renderLLMChat(data)
    
    const footerRow = grid[ROWS - 1].join('')
    expect(footerRow).toContain('llama.cpp')
    expect(footerRow).toContain('RAM')
  })
  
  it('includes keyboard shortcuts in footer', () => {
    const data = getMockData()
    const grid = renderLLMChat(data)
    
    const footerRow = grid[ROWS - 1].join('')
    expect(footerRow).toContain('Enter:SEND')
    expect(footerRow).toMatch(/Esc|CLR/)
  })
  
  it('handles long messages with text wrapping', () => {
    const data = getMockData()
    const longMessage = 'A'.repeat(COLUMNS + 20) // Message longer than one line
    
    data.messages.push({
      role: MESSAGE_ROLES.USER,
      content: longMessage,
      timestamp: '12:00:00',
    })
    
    const grid = renderLLMChat(data)
    
    // Should not throw error and should wrap text
    expect(grid.length).toBe(ROWS)
    expect(grid[0].length).toBe(COLUMNS)
  })
  
  it('scrolls to show latest messages when overflow', () => {
    const data = getMockData()
    
    // Add many messages to force scrolling
    for (let i = 0; i < 50; i++) {
      data.messages.push({
        role: i % 2 === 0 ? MESSAGE_ROLES.USER : MESSAGE_ROLES.LLM,
        content: `Message ${i}`,
        timestamp: `12:${String(i).padStart(2, '0')}:00`,
      })
    }
    
    const grid = renderLLMChat(data)
    const gridText = grid.map(row => row.join('')).join('\n')
    
    // Should show most recent messages
    expect(gridText).toContain('Message 49')
    
    // Earlier messages should be scrolled out
    expect(gridText).not.toContain('Message 0')
  })
  
  it('truncates long input when displaying', () => {
    const data = getMockData()
    const veryLongInput = 'X'.repeat(COLUMNS * 2)
    
    const grid = renderLLMChat(data, veryLongInput)
    
    // Should not cause grid overflow
    expect(grid.length).toBe(ROWS)
    grid.forEach(row => {
      expect(row.length).toBe(COLUMNS)
    })
  })
})

describe('P800 - Message Role Constants', () => {
  it('defines all required message roles', () => {
    expect(MESSAGE_ROLES.SYSTEM).toBeDefined()
    expect(MESSAGE_ROLES.USER).toBeDefined()
    expect(MESSAGE_ROLES.LLM).toBeDefined()
    
    expect(typeof MESSAGE_ROLES.SYSTEM).toBe('string')
    expect(typeof MESSAGE_ROLES.USER).toBe('string')
    expect(typeof MESSAGE_ROLES.LLM).toBe('string')
  })
})

describe('P800 - Model Status Constants', () => {
  it('defines all required model statuses', () => {
    expect(MODEL_STATUS.LOADED).toBeDefined()
    expect(MODEL_STATUS.IDLE).toBeDefined()
    expect(MODEL_STATUS.GENERATING).toBeDefined()
    
    expect(typeof MODEL_STATUS.LOADED).toBe('string')
    expect(typeof MODEL_STATUS.IDLE).toBe('string')
    expect(typeof MODEL_STATUS.GENERATING).toBe('string')
  })
})
