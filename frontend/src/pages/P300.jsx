import { useEffect } from 'react'
import TeletextGrid, { COLUMNS, ROWS } from '../components/TeletextGrid'
import useNavigationStore from '../store/navigationStore'

/**
 * P300 - Messaging Inbox
 * Placeholder implementation - full feature set pending
 */
const P300 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs)
  
  useEffect(() => {
    setBreadcrumbs(['MESSAGES', 'P300'])
  }, [setBreadcrumbs])
  
  const buildContent = () => {
    const lines = [
      'INBOX ● P300 ● LXMF / RETICULUM',
      '─'.repeat(COLUMNS),
      '',
      'Message inbox placeholder.',
      '',
      'Full implementation includes:',
      '- Scrollable message list',
      '- Status indicators (NEW/READ/SENT)',
      '- Keyboard navigation',
      '- Message detail view',
      '- Reticulum mesh integration',
    ]
    
    const padded = lines.map(l => l.padEnd(COLUMNS, ' ').slice(0, COLUMNS))
    while (padded.length < ROWS) {
      padded.push(' '.repeat(COLUMNS))
    }
    
    return padded.slice(0, ROWS).map(line => line.split(''))
  }
  
  return (
    <div className="teletext-demo">
      <div className="teletext-overlay">P300 - INBOX</div>
      <TeletextGrid content={buildContent()} showFps />
    </div>
  )
}

export default P300
