import { create } from 'zustand'

/**
 * Navigation store for teletext-style page routing
 * Tracks current page, history, and breadcrumbs
 */
const useNavigationStore = create((set, get) => ({
  // Current page number (100-800)
  currentPage: 100,
  
  // Page history for back navigation
  history: [100],
  
  // Breadcrumb trail for contextual navigation
  breadcrumbs: [],
  
  // Navigate to a new page
  navigateTo: (pageNumber) => {
    const state = get()
    const validPage = Math.max(100, Math.min(800, pageNumber))
    
    set({
      currentPage: validPage,
      history: [...state.history, validPage],
    })
  },
  
  // Navigate back in history
  navigateBack: () => {
    const state = get()
    if (state.history.length <= 1) return
    
    const newHistory = state.history.slice(0, -1)
    const previousPage = newHistory[newHistory.length - 1]
    
    set({
      currentPage: previousPage,
      history: newHistory,
    })
  },
  
  // Set breadcrumbs for current page context
  setBreadcrumbs: (crumbs) => set({ breadcrumbs: crumbs }),
  
  // Clear history (reset)
  clearHistory: () => set({ history: [get().currentPage] }),
}))

export default useNavigationStore
