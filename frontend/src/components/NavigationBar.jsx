import { Link } from 'react-router-dom'
import useNavigationStore from '../store/navigationStore'

/**
 * NavigationBar - Bottom nav bar with contextual page links
 * Shows related pages based on current page context
 */
const NavigationBar = () => {
  const currentPage = useNavigationStore((state) => state.currentPage)
  const breadcrumbs = useNavigationStore((state) => state.breadcrumbs)
  
  // Generate contextual page links based on current page
  const getContextLinks = () => {
    const links = []
    
    // Always show index
    if (currentPage !== 100) {
      links.push({ page: 100, label: 'INDEX' })
    }
    
    // Category-based navigation (by hundreds)
    const category = Math.floor(currentPage / 100) * 100
    if (category !== currentPage) {
      links.push({ page: category, label: `P${category}` })
    }
    
    // Previous/Next in sequence
    if (currentPage > 100) {
      links.push({ page: currentPage - 1, label: 'PREV' })
    }
    if (currentPage < 800) {
      links.push({ page: currentPage + 1, label: 'NEXT' })
    }
    
    return links
  }
  
  const links = getContextLinks()
  
  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: '#636764',
      borderTop: '2px solid #FB8B24',
      padding: '12px 16px',
      display: 'flex',
      gap: '16px',
      alignItems: 'center',
      fontFamily: 'monospace',
      fontSize: '14px',
      zIndex: 1000,
    }}>
      {/* Current page indicator */}
      <div style={{
        color: '#F4E409',
        fontWeight: 'bold',
        marginRight: '8px',
      }}>
        P{currentPage.toString().padStart(3, '0')}
      </div>
      
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <div style={{
          color: '#50D8D7',
          display: 'flex',
          gap: '8px',
          marginRight: '16px',
        }}>
          {breadcrumbs.map((crumb, i) => (
            <span key={i}>
              {i > 0 && <span style={{ color: '#FB8B24' }}> ▸ </span>}
              {crumb}
            </span>
          ))}
        </div>
      )}
      
      {/* Contextual links */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginLeft: 'auto',
      }}>
        {links.map(({ page, label }) => (
          <Link
            key={page}
            to={`/p/${page}`}
            style={{
              color: '#FB8B24',
              textDecoration: 'none',
              padding: '4px 8px',
              border: '1px solid #FB8B24',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#FB8B24'
              e.target.style.color = '#000'
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent'
              e.target.style.color = '#FB8B24'
            }}
          >
            {label}
          </Link>
        ))}
      </div>
      
      {/* Navigation hint */}
      <div style={{
        color: '#636764',
        fontSize: '12px',
        marginLeft: '16px',
        borderLeft: '1px solid #FB8B24',
        paddingLeft: '16px',
      }}>
        <span style={{ color: '#50D8D7' }}>TYPE PAGE#</span>
        {' '}
        <span style={{ color: '#636764' }}>│</span>
        {' '}
        <span style={{ color: '#50D8D7' }}>ESC=BACK</span>
      </div>
    </div>
  )
}

export default NavigationBar
