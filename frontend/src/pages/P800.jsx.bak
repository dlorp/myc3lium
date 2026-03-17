import { useEffect, useState, useRef } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'
import { renderLLMChat, getMockData, simulateLLMResponse, MESSAGE_ROLES } from './P800.utils'

/**
 * P800 - Local LLM Chat Interface
 * 
 * Chat interface for local LLM (Phi-3-mini-4k).
 * 
 * Features:
 * - Chat message history display with role-based formatting
 * - Input area for user prompts
 * - Model status indicator (loaded/idle/generating)
 * - Token count display
 * - Clear conversation button
 * - Mock LLM responses (echo + prefix for now)
 * 
 * Future: Integration with llama.cpp backend
 */

const P800 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  const navigateTo = useNavigationStore((state) => state.navigateTo)
  
  const [data, setData] = useState(getMockData())
  const [inputValue, setInputValue] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    setBreadcrumbs(['LOCAL LLM', 'P800'])
  }, [setBreadcrumbs])

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  /**
   * Handle sending user message
   */
  const handleSend = () => {
    const trimmed = inputValue.trim()
    if (!trimmed || isGenerating) return

    // Add user message
    const userMessage = {
      role: MESSAGE_ROLES.USER,
      content: trimmed,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
    }

    setData(prevData => ({
      ...prevData,
      messages: [...prevData.messages, userMessage],
      tokenCount: prevData.tokenCount + Math.ceil(trimmed.length / 4), // Rough approximation
    }))

    setInputValue('')
    setIsGenerating(true)

    // Simulate LLM response delay (500-1500ms)
    const delay = 500 + Math.random() * 1000
    setTimeout(() => {
      const llmMessage = simulateLLMResponse(trimmed)
      
      setData(prevData => ({
        ...prevData,
        messages: [...prevData.messages, llmMessage],
        tokenCount: prevData.tokenCount + Math.ceil(llmMessage.content.length / 4),
        status: 'idle',
      }))
      
      setIsGenerating(false)
      
      // Refocus input
      if (inputRef.current) {
        inputRef.current.focus()
      }
    }, delay)

    // Update status to generating
    setData(prevData => ({
      ...prevData,
      status: 'generating',
    }))
  }

  /**
   * Handle clear conversation
   */
  const handleClear = () => {
    if (window.confirm('Clear conversation history?')) {
      setData(getMockData())
      setInputValue('')
    }
  }

  /**
   * Handle keyboard shortcuts
   */
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Ctrl+Enter to send
      if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault()
        handleSend()
      }
      // Escape to clear input
      else if (event.key === 'Escape') {
        event.preventDefault()
        setInputValue('')
      }
      // Navigation shortcuts (when input not focused)
      else if (document.activeElement !== inputRef.current) {
        if (event.key === '1') {
          navigateTo(100)
        } else if (event.key === '2') {
          navigateTo(200)
        } else if (event.key === '3') {
          navigateTo(300)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigateTo, inputValue, isGenerating]) // eslint-disable-line react-hooks/exhaustive-deps

  const content = renderLLMChat(data, inputValue, isGenerating)

  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P800 - LOCAL LLM</div>
      <TeletextGrid content={content} showFps />
      
      {/* Hidden input for keyboard handling */}
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.ctrlKey) {
            e.preventDefault()
            handleSend()
          }
        }}
        style={{
          position: 'absolute',
          top: '-1000px',
          left: '-1000px',
        }}
        aria-label="Message input"
      />
      
      {/* Control buttons (hidden but functional) */}
      <div style={{ display: 'none' }}>
        <button onClick={handleSend} disabled={isGenerating || !inputValue.trim()}>
          Send
        </button>
        <button onClick={handleClear}>
          Clear
        </button>
      </div>
    </div>
  )
}

export default P800
