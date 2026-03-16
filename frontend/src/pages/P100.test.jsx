import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import P100 from './P100'
import useNavigationStore from '../store/navigationStore'

describe('P100', () => {
  beforeEach(() => {
    useNavigationStore.setState({
      currentPage: 100,
      history: [100],
      breadcrumbs: [],
    })
  })
  
  it('renders index page', () => {
    render(<P100 />)
    expect(screen.getByText(/P100 - INDEX/)).toBeInTheDocument()
  })
  
  it('sets breadcrumbs', () => {
    render(<P100 />)
    
    const state = useNavigationStore.getState()
    expect(state.breadcrumbs).toEqual(['INDEX'])
  })
  
  it('displays main service categories', () => {
    const { container } = render(<P100 />)
    
    // Check that content grid is rendered
    const canvas = container.querySelector('canvas')
    expect(canvas).toBeInTheDocument()
  })
})
