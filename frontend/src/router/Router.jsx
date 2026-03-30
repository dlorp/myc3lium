import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { useEffect } from 'react'
import P100 from '../pages/P100'
import P200 from '../pages/P200'
import P300 from '../pages/P300'
import P400 from '../pages/P400'
import P500 from '../pages/P500'
import P600 from '../pages/P600'
import Login from '../pages/Login'
import Setup from '../pages/Setup'
import PageInput from '../components/PageInput'
import NavigationBar from '../components/NavigationBar'
import useNavigationStore from '../store/navigationStore'
import useAuthStore from '../store/authStore'
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
    if (page >= 100 && page <= 999) {
      navigateTo(page)
    }
  }, [pageNumber, navigateTo])
  
  return children
}

/**
 * AuthGuard - Redirects to /login when auth is required and user is not authenticated.
 * Passes through when auth is disabled (authRequired=false).
 * Does NOT call checkAuth — that's done once in AuthProvider at the app root (M8).
 */
// eslint-disable-next-line react/prop-types
const AuthGuard = ({ children }) => {
  const { isAuthenticated, authRequired, loading } = useAuthStore()

  if (loading) {
    return null
  }

  if (authRequired && !isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

/**
 * AuthProvider - Calls checkAuth once at app root, shared via Zustand (M8).
 */
// eslint-disable-next-line react/prop-types
const AuthProvider = ({ children }) => {
  const checkAuth = useAuthStore((state) => state.checkAuth)

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return children
}

/**
 * Router - Main router component with page-number URL scheme
 */
const Router = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
      <PageInput />
      <NavigationBar />

      <Routes>
        {/* Login page — always accessible */}
        <Route path="/login" element={<Login />} />

        {/* Index page */}
        <Route
          path="/p/100"
          element={
            <AuthGuard>
              <PageRoute>
                <P100 />
              </PageRoute>
            </AuthGuard>
          }
        />
        
        {/* P200 - Lattice Map */}
        <Route
          path="/p/200"
          element={
            <AuthGuard>
              <PageRoute>
                <P200 />
              </PageRoute>
            </AuthGuard>
          }
        />

        {/* P300 - Messaging Inbox */}
        <Route
          path="/p/300"
          element={
            <AuthGuard>
              <PageRoute>
                <P300 />
              </PageRoute>
            </AuthGuard>
          }
        />

        {/* P400 - Tactical Map */}
        <Route
          path="/p/400"
          element={
            <AuthGuard>
              <PageRoute>
                <P400 />
              </PageRoute>
            </AuthGuard>
          }
        />

        {/* P500 - Intelligence Hub */}
        <Route
          path="/p/500"
          element={
            <AuthGuard>
              <PageRoute>
                <P500 />
              </PageRoute>
            </AuthGuard>
          }
        />

        {/* P600 - Radio Config */}
        <Route
          path="/p/600"
          element={
            <AuthGuard>
              <PageRoute>
                <P600 />
              </PageRoute>
            </AuthGuard>
          }
        />

        {/* Generic page route (100-800) */}
        <Route
          path="/p/:pageNumber"
          element={
            <AuthGuard>
              <PageRoute>
                <PagePlaceholder />
              </PageRoute>
            </AuthGuard>
          }
        />
        
        {/* First-boot setup wizard */}
        <Route path="/setup" element={<Setup />} />

        {/* Default redirect to index */}
        <Route path="/" element={<Navigate to="/p/100" replace />} />
        <Route path="*" element={<Navigate to="/p/100" replace />} />
      </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default Router
