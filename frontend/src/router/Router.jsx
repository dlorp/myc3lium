import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { useEffect } from 'react'
import P100 from '../pages/P100'
import PageInput from '../components/PageInput'
import NavigationBar from '../components/NavigationBar'
import useNavigationStore from '../store/navigationStore'
import TeletextGrid, { COLUMNS, ROWS } from '../components/TeletextGrid'

/**
 * PagePlaceholder - Generic page component for pages without custom content
 */
const PagePlaceholder = () => {
  const { pageNumber } = useParams()
  const page = parseInt(pageNumber, 10)
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  
  useEffect(() => {
    const category = Math.floor(page / 100) * 100
    setBreadcrumbs([`P${category}`, `P${page}`])
  }, [page, setBreadcrumbs])
  
  const padLine = (line) => line.padEnd(COLUMNS, ' ').slice(0, COLUMNS)
  
  const buildContent = () => {
    const lines = [
      `MYC3LIUM TELETYPE  |  P${page}`,
      '========================================',
      '',
      `PAGE ${page}`,
      '',
      'CONTENT PLACEHOLDER',
      '',
      'This page is under construction.',
      '',
      '----------------------------------------',
      'NAVIGATION',
      '  100 - Return to index',
      `  ${page - 1} - Previous page`,
      `  ${page + 1} - Next page`,
      '',
      '========================================',
    ]
    
    const padded = lines.map(padLine)
    while (padded.length < ROWS) {
      padded.push(padLine(''))
    }
    
    return padded.slice(0, ROWS).map((line) => line.split(''))
  }
  
  const content = buildContent()
  
  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P{page}</div>
      <TeletextGrid content={content} showFps />
    </div>
  )
}

/**
 * PageRoute - Wrapper to sync URL params with navigation store
 */
const PageRoute = ({ children }) => {
  const { pageNumber } = useParams()
  const navigateTo = useNavigationStore((state) => state.navigateTo)
  
  useEffect(() => {
    const page = parseInt(pageNumber, 10)
    if (page >= 100 && page <= 800) {
      navigateTo(page)
    }
  }, [pageNumber, navigateTo])
  
  return children
}

/**
 * Router - Main router component with page-number URL scheme
 */
const Router = () => {
  return (
    <BrowserRouter>
      <PageInput />
      <NavigationBar />
      
      <Routes>
        {/* Index page */}
        <Route
          path="/p/100"
          element={
            <PageRoute>
              <P100 />
            </PageRoute>
          }
        />
        
        {/* P200 - Lattice Map */}
        <Route
          path="/p/200"
          element={
            <PageRoute>
              <P200 />
            </PageRoute>
          }
        />
        
        {/* Generic page route (100-800) */}
        <Route
          path="/p/:pageNumber"
          element={
            <PageRoute>
              <PagePlaceholder />
            </PageRoute>
          }
        />
        
        {/* Default redirect to index */}
        <Route path="/" element={<Navigate to="/p/100" replace />} />
        <Route path="*" element={<Navigate to="/p/100" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default Router
