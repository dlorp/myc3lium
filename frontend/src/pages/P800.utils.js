import { COLUMNS, ROWS } from '../components/TeletextGrid'

// Box drawing characters
const BOX = {
  TL: '┌', TR: '┐', BL: '└', BR: '┘',
  H: '─', V: '│',
}

const ARROW_USER = '▸'
const ARROW_LLM = '◈'
const DOT_SYS = '◉'

/**
 * Message role constants
 */
export const MESSAGE_ROLES = {
  SYSTEM: 'SYS',
  USER: 'USER',
  LLM: 'LLM',
}

/**
 * Model status constants
 */
export const MODEL_STATUS = {
  LOADED: 'loaded',
  IDLE: 'idle',
  GENERATING: 'generating',
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
  if (y < 0 || y >= ROWS) return
  for (let i = 0; i < text.length; i++) {
    const col = x + i
    if (col >= 0 && col < COLUMNS) {
      grid[y][col] = text[i]
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
 * Draw box border
 */
const drawBox = (grid, x, y, width, height) => {
  // Corners
  if (y >= 0 && y < ROWS && x >= 0 && x < COLUMNS) grid[y][x] = BOX.TL
  if (y >= 0 && y < ROWS && x + width - 1 >= 0 && x + width - 1 < COLUMNS) {
    grid[y][x + width - 1] = BOX.TR
  }
  if (y + height - 1 >= 0 && y + height - 1 < ROWS && x >= 0 && x < COLUMNS) {
    grid[y + height - 1][x] = BOX.BL
  }
  if (y + height - 1 >= 0 && y + height - 1 < ROWS && x + width - 1 >= 0 && x + width - 1 < COLUMNS) {
    grid[y + height - 1][x + width - 1] = BOX.BR
  }
  
  // Horizontal lines
  drawHLine(grid, x + 1, y, width - 2, BOX.H)
  drawHLine(grid, x + 1, y + height - 1, width - 2, BOX.H)
  
  // Vertical lines
  for (let i = 1; i < height - 1; i++) {
    if (y + i >= 0 && y + i < ROWS) {
      if (x >= 0 && x < COLUMNS) grid[y + i][x] = BOX.V
      if (x + width - 1 >= 0 && x + width - 1 < COLUMNS) {
        grid[y + i][x + width - 1] = BOX.V
      }
    }
  }
}

/**
 * Wrap text to fit within width, breaking on words
 */
const wrapText = (text, maxWidth) => {
  const words = text.split(' ')
  const lines = []
  let currentLine = ''
  
  for (const word of words) {
    const testLine = currentLine ? `${currentLine} ${word}` : word
    if (testLine.length <= maxWidth) {
      currentLine = testLine
    } else {
      if (currentLine) lines.push(currentLine)
      // If single word is too long, break it
      if (word.length > maxWidth) {
        let remaining = word
        while (remaining.length > maxWidth) {
          lines.push(remaining.slice(0, maxWidth))
          remaining = remaining.slice(maxWidth)
        }
        currentLine = remaining
      } else {
        currentLine = word
      }
    }
  }
  
  if (currentLine) lines.push(currentLine)
  return lines
}

/**
 * Get mock initial data
 */
export const getMockData = () => {
  const now = new Date()
  const timeString = now.toLocaleTimeString('en-US', { hour12: false })
  
  return {
    modelName: 'Qwen2.5-7B-Instruct-Q4',
    status: MODEL_STATUS.IDLE,
    tokenCount: 248,
    maxTokens: 8192,
    temperature: 0.7,
    messages: [
      {
        role: MESSAGE_ROLES.SYSTEM,
        content: 'MYC3LIUM local intelligence initialized.',
        timestamp: timeString,
      },
      {
        role: MESSAGE_ROLES.SYSTEM,
        content: 'Access: Lattice (5/7 nodes) · Messages (3) · Sensors (6) · SDR',
        timestamp: timeString,
      },
    ],
  }
}

/**
 * Simulate LLM response (mock implementation)
 */
export const simulateLLMResponse = (userInput) => {
  const now = new Date()
  const timeString = now.toLocaleTimeString('en-US', { hour12: false })
  
  // Simple mock: echo with prefix and some canned responses
  let response = ''
  
  const lower = userInput.toLowerCase()
  
  if (lower.includes('temp') || lower.includes('temperature')) {
    response = 'RHIZOME-02: 6.1°C→6.4°C stable · RHIZOME-03: 6.5°C→18.2°C WARNING'
  } else if (lower.includes('sensor') || lower.includes('rhizome')) {
    response = 'RHIZOME nodes reporting nominal. Temperature variance detected on RHIZOME-03.'
  } else if (lower.includes('rf') || lower.includes('signal')) {
    response = '908.500 MHz FSK bursts (2s every 30s) detected. Classification: Likely weather station. No threat.'
  } else if (lower.includes('lattice') || lower.includes('node')) {
    response = 'Lattice status: 5/7 cells online · 8 threads active · 2 degraded. BATMAN-ADV + RNS E2E encrypted.'
  } else if (lower.includes('battery') || lower.includes('power')) {
    response = 'SPORE-01: 74% (~5h 20m) · CRITICAL: SPORE-06 12% battery remaining.'
  } else if (lower.includes('hello') || lower.includes('hi')) {
    response = 'MYC3LIUM intelligence ready. Query available: lattice, sensors, RF, battery, messages.'
  } else {
    // Generic echo response
    response = `Query received: "${userInput}". Processing local context...`
  }
  
  return {
    role: MESSAGE_ROLES.LLM,
    content: response,
    timestamp: timeString,
  }
}
/**
 * Render the LLM chat interface
 */
export const renderLLMChat = (data, inputValue = '', isGenerating = false) => {
  const grid = createGrid()
  
  // Header - must fit in 40 columns
  writeText(grid, 0, 0, 'LOCAL LLM P800')
  drawHLine(grid, 0, 1, COLUMNS, BOX.H)
  
  // Status bar (right side of header)
  const statusText = `${data.tokenCount}/${data.maxTokens}t`
  writeText(grid, COLUMNS - statusText.length, 0, statusText)
  
  // Model status indicator
  let statusIndicator = ''
  if (data.status === MODEL_STATUS.GENERATING || isGenerating) {
    statusIndicator = '⚡ GENERATING'
  } else if (data.status === MODEL_STATUS.IDLE) {
    statusIndicator = '● IDLE'
  } else {
    statusIndicator = '○ LOADED'
  }
  writeText(grid, 2, 2, statusIndicator)
  
  // Message history area (rows 4 to ROWS-9)
  const messageAreaStart = 4
  const messageAreaEnd = ROWS - 9
  const messageAreaHeight = messageAreaEnd - messageAreaStart
  
  let currentRow = messageAreaStart
  const maxMessageWidth = COLUMNS - 6 // Leave margins
  
  // Render messages (scroll to show latest)
  const visibleMessages = [...data.messages]
  
  // Calculate lines needed for each message
  const messageLinesMap = []
  
  for (const msg of visibleMessages) {
    const rolePrefix = msg.role === MESSAGE_ROLES.USER 
      ? `${ARROW_USER} USER` 
      : msg.role === MESSAGE_ROLES.LLM 
      ? `${ARROW_LLM} LLM`
      : `${DOT_SYS} SYS`
    
    const wrappedContent = wrapText(msg.content, maxMessageWidth - 2)
    const linesNeeded = 1 + wrappedContent.length + 1 // role line + content lines + spacing
    
    messageLinesMap.push({
      msg,
      rolePrefix,
      wrappedContent,
      linesNeeded,
    })
  }
  
  // If messages overflow, show only the most recent ones that fit
  let linesToShow = 0
  let startIndex = messageLinesMap.length
  
  for (let i = messageLinesMap.length - 1; i >= 0; i--) {
    if (linesToShow + messageLinesMap[i].linesNeeded <= messageAreaHeight) {
      linesToShow += messageLinesMap[i].linesNeeded
      startIndex = i
    } else {
      break
    }
  }
  
  // Render visible messages
  for (let i = startIndex; i < messageLinesMap.length; i++) {
    const { msg, rolePrefix, wrappedContent } = messageLinesMap[i]
    
    if (currentRow >= messageAreaEnd) break
    
    // Role and timestamp line
    writeText(grid, 2, currentRow, rolePrefix)
    writeText(grid, COLUMNS - msg.timestamp.length - 2, currentRow, msg.timestamp)
    currentRow++
    
    // Content lines
    for (const line of wrappedContent) {
      if (currentRow >= messageAreaEnd) break
      writeText(grid, 4, currentRow, line)
      currentRow++
    }
    
    // Spacing
    currentRow++
  }
  
  // Separator before input
  drawHLine(grid, 0, ROWS - 8, COLUMNS, BOX.H)
  
  // Input box
  const inputBoxY = ROWS - 7
  drawBox(grid, 0, inputBoxY, COLUMNS, 5)
  
  // Input prompt
  if (inputValue) {
    // Show actual input
    const truncatedInput = inputValue.length > COLUMNS - 4 
      ? inputValue.slice(-(COLUMNS - 4)) 
      : inputValue
    writeText(grid, 2, inputBoxY + 2, truncatedInput)
    
    // Cursor at end of input (blinking)
    if (!isGenerating) {
      const cursorPos = Math.min(inputValue.length, COLUMNS - 4)
      const showCursor = Math.floor(Date.now() / 500) % 2 === 0
      if (showCursor) {
        writeText(grid, 2 + cursorPos, inputBoxY + 2, '█')
      }
    }
  } else {
    // Show placeholder when empty
    writeText(grid, 2, inputBoxY + 2, 'TYPE MESSAGE...')
    // Cursor at start (blinking)
    if (!isGenerating) {
      const showCursor = Math.floor(Date.now() / 500) % 2 === 0
      if (showCursor) {
        writeText(grid, 2, inputBoxY + 2, '█')
      }
    }
  }
  
  // Footer
  drawHLine(grid, 0, ROWS - 2, COLUMNS, BOX.H)
  
  // Footer info - need to fit in 40 columns total
  const footerLeft = 'llama.cpp RAM:4.2GB'
  writeText(grid, 0, ROWS - 1, footerLeft)
  
  // Instructions (right side)
  const footerRight = 'Enter:SEND Esc:CLR'
  writeText(grid, COLUMNS - footerRight.length, ROWS - 1, footerRight)
  
  return grid
}
