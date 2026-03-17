import { useEffect } from 'react'
import TeletextGrid, { COLUMNS, ROWS } from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import useMeshStore from '../store/meshStore'

/**
 * P300 - Messaging Inbox
 * Live message feed from mesh network
 */
const P300 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  
  // Get live messages from store
  const messages = useMeshStore((state) => state.messages)
  const messagesLoading = useMeshStore((state) => state.messagesLoading)
  const messagesError = useMeshStore((state) => state.messagesError)
  const loadMessages = useMeshStore((state) => state.loadMessages)
  const connectWS = useMeshStore((state) => state.connectWS)
  const disconnectWS = useMeshStore((state) => state.disconnectWS)
  
  useEffect(() => {
    setBreadcrumbs(['MESSAGES', 'P300'])

    // Load initial messages and connect WebSocket
    loadMessages()
    connectWS()

    return () => {
      disconnectWS()
    }
  }, [setBreadcrumbs, loadMessages, connectWS, disconnectWS])
  
  const buildContent = () => {
    const grid = Array.from({ length: ROWS }, () => 
      Array.from({ length: COLUMNS }, () => ' ')
    )

    const writeText = (x, y, text) => {
      if (y < 0 || y >= ROWS) return
      for (let i = 0; i < text.length && x + i < COLUMNS; i++) {
        grid[y][x + i] = text[i]
      }
    }

    const drawHLine = (y) => {
      for (let x = 0; x < COLUMNS; x++) {
        grid[y][x] = '─'
      }
    }

    // Header
    writeText(0, 0, `INBOX ● P300 ● ${messages.length} MESSAGES`)
    drawHLine(1)

    // Loading state
    if (messagesLoading) {
      writeText(5, 10, 'LOADING MESSAGES...')
      return grid
    }

    // Error state
    if (messagesError) {
      writeText(5, 8, `ERROR: ${messagesError}`)
      writeText(5, 10, 'Press R to retry')
      return grid
    }

    // No messages
    if (messages.length === 0) {
      writeText(5, 10, 'NO MESSAGES')
      return grid
    }

    // Table header
    writeText(0, 3, 'FROM')
    writeText(15, 3, 'TO')
    writeText(28, 3, 'HOPS')
    writeText(35, 3, 'TIME')
    drawHLine(4)

    // Message list (show first 15 messages)
    const displayMessages = messages.slice(0, 15)
    displayMessages.forEach((msg, index) => {
      const y = 5 + index
      if (y >= ROWS - 2) return

      // Truncate IDs for display
      const from = msg.sender_id.slice(0, 12)
      const to = msg.recipient_id ? msg.recipient_id.slice(0, 12) : 'BROADCAST'
      
      // Format timestamp (show HH:MM)
      const time = new Date(msg.timestamp)
      const timeStr = `${String(time.getHours()).padStart(2, '0')}:${String(time.getMinutes()).padStart(2, '0')}`

      writeText(0, y, from)
      writeText(15, y, to)
      writeText(28, y, String(msg.hops))
      writeText(35, y, timeStr)

      // Show content preview on next line if space
      if (y + 1 < ROWS - 2) {
        const preview = msg.content.slice(0, 36)
        writeText(2, y + 1, `"${preview}${msg.content.length > 36 ? '...' : ''}"`)
      }
    })

    // Footer
    drawHLine(ROWS - 2)
    writeText(0, ROWS - 1, '[100]MENU [301]COMPOSE [ESC]CLEAR')

    return grid
  }
  
  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P300 - INBOX</div>
      <TeletextGrid content={buildContent()} showFps />
    </div>
  )
}

export default P300
