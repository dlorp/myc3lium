import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import PageInput from './PageInput'
import useNavigationStore from '../store/navigationStore'

describe('PageInput', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    useNavigationStore.setState({
      currentPage: 100,
      history: [100],
      breadcrumbs: [],
    })
  })
  
  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })
  
  const renderPageInput = () => {
    return render(
      <MemoryRouter initialEntries={['/p/100']}>
        <PageInput />
      </MemoryRouter>
    )
  }
  
  it('does not show buffer initially', () => {
    const { container } = renderPageInput()
    // Buffer indicator only shows when there are digits
    const bufferElement = container.querySelector('div[style*="position: fixed"]')
    expect(bufferElement).toBeNull()
  })
  
  it('shows buffer when number key pressed', () => {
    renderPageInput()
    
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '2' }))
    })
    
    expect(screen.getByText(/P2__/)).toBeInTheDocument()
  })
  
  it('builds 3-digit buffer', () => {
    renderPageInput()
    
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '2' }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '0' }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '0' }))
    })
    
    expect(screen.getByText(/P200/)).toBeInTheDocument()
  })
  
  it('navigates after timeout', () => {
    renderPageInput()
    
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '2' }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '0' }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '0' }))
    })
    
    expect(useNavigationStore.getState().currentPage).toBe(100)
    
    act(() => {
      vi.advanceTimersByTime(1500)
    })
    
    expect(useNavigationStore.getState().currentPage).toBe(200)
  })
  
  it('only keeps last 3 digits', () => {
    renderPageInput()
    
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '1' }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '2' }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '3' }))
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '4' }))
    })
    
    expect(screen.getByText(/P234/)).toBeInTheDocument()
  })
  
  it('resets timeout on each keypress', () => {
    renderPageInput()
    
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '2' }))
      vi.advanceTimersByTime(1000)
      
      window.dispatchEvent(new KeyboardEvent('keydown', { key: '0' }))
      vi.advanceTimersByTime(1000)
    })
    
    // Should not have navigated yet (timeout resets)
    expect(useNavigationStore.getState().currentPage).toBe(100)
    
    act(() => {
      vi.advanceTimersByTime(500)
    })
    
    // Now should have navigated
    expect(useNavigationStore.getState().currentPage).toBe(200)
  })
})
