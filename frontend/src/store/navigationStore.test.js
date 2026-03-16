import { describe, it, expect, beforeEach } from 'vitest'
import useNavigationStore from './navigationStore'

describe('navigationStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useNavigationStore.setState({
      currentPage: 100,
      history: [100],
      breadcrumbs: [],
    })
  })
  
  it('initializes with page 100', () => {
    const state = useNavigationStore.getState()
    expect(state.currentPage).toBe(100)
    expect(state.history).toEqual([100])
    expect(state.breadcrumbs).toEqual([])
  })
  
  it('navigates to a new page', () => {
    const { navigateTo } = useNavigationStore.getState()
    
    navigateTo(200)
    
    const state = useNavigationStore.getState()
    expect(state.currentPage).toBe(200)
    expect(state.history).toEqual([100, 200])
  })
  
  it('clamps page numbers to valid range', () => {
    const { navigateTo } = useNavigationStore.getState()
    
    navigateTo(50) // Below minimum
    expect(useNavigationStore.getState().currentPage).toBe(100)
    
    navigateTo(900) // Above maximum
    expect(useNavigationStore.getState().currentPage).toBe(800)
  })
  
  it('navigates back in history', () => {
    const { navigateTo, navigateBack } = useNavigationStore.getState()
    
    navigateTo(200)
    navigateTo(300)
    navigateBack()
    
    const state = useNavigationStore.getState()
    expect(state.currentPage).toBe(200)
    expect(state.history).toEqual([100, 200])
  })
  
  it('does not go back beyond initial page', () => {
    const { navigateBack } = useNavigationStore.getState()
    
    navigateBack()
    
    const state = useNavigationStore.getState()
    expect(state.currentPage).toBe(100)
    expect(state.history).toEqual([100])
  })
  
  it('sets breadcrumbs', () => {
    const { setBreadcrumbs } = useNavigationStore.getState()
    
    setBreadcrumbs(['INDEX', 'P200'])
    
    const state = useNavigationStore.getState()
    expect(state.breadcrumbs).toEqual(['INDEX', 'P200'])
  })
  
  it('clears history', () => {
    const { navigateTo, clearHistory } = useNavigationStore.getState()
    
    navigateTo(200)
    navigateTo(300)
    clearHistory()
    
    const state = useNavigationStore.getState()
    expect(state.history).toEqual([300])
  })
  
  it('maintains history across multiple navigations', () => {
    const { navigateTo } = useNavigationStore.getState()
    
    navigateTo(200)
    navigateTo(300)
    navigateTo(400)
    
    const state = useNavigationStore.getState()
    expect(state.currentPage).toBe(400)
    expect(state.history).toEqual([100, 200, 300, 400])
  })
})
