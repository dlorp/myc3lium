import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import NavigationBar from './NavigationBar'
import useNavigationStore from '../store/navigationStore'

describe('NavigationBar', () => {
  beforeEach(() => {
    useNavigationStore.setState({
      currentPage: 100,
      history: [100],
      breadcrumbs: [],
    })
  })
  
  const renderNavigationBar = () => {
    return render(
      <BrowserRouter>
        <NavigationBar />
      </BrowserRouter>
    )
  }
  
  it('displays current page number', () => {
    renderNavigationBar()
    expect(screen.getByText('P100')).toBeInTheDocument()
  })
  
  it('shows PREV and NEXT links when not at boundaries', () => {
    useNavigationStore.setState({ currentPage: 200 })
    renderNavigationBar()
    
    expect(screen.getByText('PREV')).toBeInTheDocument()
    expect(screen.getByText('NEXT')).toBeInTheDocument()
  })
  
  it('does not show PREV at page 100', () => {
    useNavigationStore.setState({ currentPage: 100 })
    renderNavigationBar()
    
    expect(screen.queryByText('PREV')).not.toBeInTheDocument()
  })
  
  it('does not show NEXT at page 800', () => {
    useNavigationStore.setState({ currentPage: 800 })
    renderNavigationBar()
    
    expect(screen.queryByText('NEXT')).not.toBeInTheDocument()
  })
  
  it('shows INDEX link when not on page 100', () => {
    useNavigationStore.setState({ currentPage: 200 })
    renderNavigationBar()
    
    expect(screen.getByText('INDEX')).toBeInTheDocument()
  })
  
  it('shows category link', () => {
    useNavigationStore.setState({ currentPage: 250 })
    renderNavigationBar()
    
    expect(screen.getByText('P200')).toBeInTheDocument()
  })
  
  it('displays breadcrumbs', () => {
    useNavigationStore.setState({
      currentPage: 250,
      breadcrumbs: ['INDEX', 'P200', 'P250'],
    })
    renderNavigationBar()
    
    // Use getAllByText since INDEX appears in both breadcrumbs and links
    const indexElements = screen.getAllByText('INDEX')
    expect(indexElements.length).toBeGreaterThan(0)
    
    const p200Elements = screen.getAllByText('P200')
    expect(p200Elements.length).toBeGreaterThan(0)
    
    const p250Elements = screen.getAllByText('P250')
    expect(p250Elements.length).toBeGreaterThan(0)
  })
  
  it('shows navigation hints', () => {
    renderNavigationBar()
    
    expect(screen.getByText('TYPE PAGE#')).toBeInTheDocument()
    expect(screen.getByText('ESC=BACK')).toBeInTheDocument()
  })
  
  it('renders links with correct href', () => {
    useNavigationStore.setState({ currentPage: 200 })
    renderNavigationBar()
    
    const indexLink = screen.getByText('INDEX').closest('a')
    expect(indexLink).toHaveAttribute('href', '/p/100')
    
    const prevLink = screen.getByText('PREV').closest('a')
    expect(prevLink).toHaveAttribute('href', '/p/199')
    
    const nextLink = screen.getByText('NEXT').closest('a')
    expect(nextLink).toHaveAttribute('href', '/p/201')
  })
})
