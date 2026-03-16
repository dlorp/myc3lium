import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useNavigationStore from '../store/navigationStore'

/**
 * PageInput - Number-key navigation handler
 * Captures 3-digit page numbers (100-800) and navigates
 * ESC key navigates back in history
 */
const PageInput = () => {
  const navigate = useNavigate()
  const navigateBack = useNavigationStore((state) => state.navigateBack)
  const [buffer, setBuffer] = useState('')
  const timeoutRef = useRef(null)
  
  useEffect(() => {
    const handleKeyDown = (e) => {
      // ESC - navigate back
      if (e.key === 'Escape') {
        e.preventDefault()
        navigateBack()
        const currentPage = useNavigationStore.getState().currentPage
        navigate(`/p/${currentPage}`)
        setBuffer('')
        return
      }
      
      // Number keys - build page number
      if (e.key >= '0' && e.key <= '9') {
        e.preventDefault()
        const newBuffer = (buffer + e.key).slice(-3)
        setBuffer(newBuffer)
        
        // Clear existing timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }
        
        // Auto-navigate after 1.5s of no input
        timeoutRef.current = setTimeout(() => {
          if (newBuffer.length > 0) {
            const pageNumber = parseInt(newBuffer, 10)
            if (pageNumber >= 100 && pageNumber <= 800) {
              useNavigationStore.getState().navigateTo(pageNumber)
              navigate(`/p/${pageNumber}`)
            }
            setBuffer('')
          }
        }, 1500)
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [buffer, navigate, navigateBack])
  
  // Visual feedback for number buffer
  if (buffer.length === 0) return null
  
  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      backgroundColor: '#FB8B24',
      color: '#000',
      padding: '8px 16px',
      fontFamily: 'monospace',
      fontSize: '20px',
      fontWeight: 'bold',
      zIndex: 9999,
      border: '2px solid #F4E409',
      boxShadow: '0 0 10px rgba(251, 139, 36, 0.5)',
    }}>
      P{buffer.padEnd(3, '_')}
    </div>
  )
}

export default PageInput
