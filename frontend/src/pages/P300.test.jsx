import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import P300 from './P300'

describe('P300', () => {
  it('renders without crashing', () => {
    render(<BrowserRouter><P300 /></BrowserRouter>)
    expect(screen.getByText(/P300/)).toBeInTheDocument()
  })
})
