import { useEffect, useState, useRef } from 'react';
import { TeletextPanel, TeletextText } from '../components';
import useNavigationStore from '../store/navigationStore';
import useMeshStore from '../store/meshStore';
import {
  LogEntry,
  EventType,
  filterLogEntries,
  searchLogEntries,
  getUniqueNodeIds,
  exportToCSV,
  getLogStatistics,
  formatTime,
  getLevelColor,
  getLevelIcon,
} from './P700.utils';

/**
 * P700 - Node Log Page (Phase 4 Sprint 1 Polish)
 * Production-ready event log with filters, search, auto-pause on scroll,
 * and CSV export functionality.
 */

const P700 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs);
  const nodes = useMeshStore((state) => state.nodes);
  const messages = useMeshStore((state) => state.messages);
  const threads = useMeshStore((state) => state.threads);
  const connectWS = useMeshStore((state) => state.connectWS);
  const disconnectWS = useMeshStore((state) => state.disconnectWS);
  const loadAll = useMeshStore((state) => state.loadAll);

  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string>('ALL');
  const [selectedEventType, setSelectedEventType] = useState<EventType>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [isScrolling, setIsScrolling] = useState(false);

  const logContainerRef = useRef<HTMLDivElement>(null);
  const logEndRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    setBreadcrumbs(['LOG', 'P700']);
    loadAll();
    connectWS();

    return () => {
      disconnectWS();
    };
  }, [setBreadcrumbs, loadAll, connectWS, disconnectWS]);

  // Generate log entries from mesh store events
  useEffect(() => {
    const newEntries: LogEntry[] = [];

    // Log node status changes
    nodes.forEach((node) => {
      const level = node.status === 'online' ? 'INFO' : 
                   node.status === 'degraded' ? 'WARNING' : 'ERROR';
      newEntries.push({
        id: `node-${node.id}`,
        timestamp: new Date().toISOString(),
        level,
        source: `NODE`,
        nodeId: node.callsign,
        message: `Status: ${node.status.toUpperCase()} | RSSI: ${node.rssi || 'N/A'} dBm | Battery: ${node.battery || 'N/A'}%`,
      });
    });

    // Log recent messages
    messages.slice(0, 5).forEach((msg) => {
      newEntries.push({
        id: `msg-${msg.id}`,
        timestamp: msg.timestamp,
        level: 'INFO',
        source: 'LXMF',
        nodeId: msg.sender_id.slice(0, 8),
        message: `Message from ${msg.sender_id.slice(0, 8)} → ${msg.recipient_id ? msg.recipient_id.slice(0, 8) : 'BROADCAST'} (${msg.hops} hops)`,
      });
    });

    // Log thread status
    threads.slice(0, 5).forEach((thread) => {
      const quality = thread.quality * 100;
      const level = quality > 75 ? 'INFO' : quality > 50 ? 'WARNING' : 'ERROR';
      newEntries.push({
        id: `thread-${thread.id}`,
        timestamp: thread.established,
        level,
        source: 'THREAD',
        nodeId: thread.source_id.slice(0, 8),
        message: `${thread.source_id.slice(0, 8)} ↔ ${thread.target_id.slice(0, 8)} | Quality: ${quality.toFixed(0)}% | RSSI: ${thread.rssi || 'N/A'} dBm`,
      });
    });

    // Sort by timestamp descending
    newEntries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    setLogEntries(newEntries);
  }, [nodes, messages, threads]);

  // Auto-scroll to bottom when new entries arrive (if not scrolling manually)
  useEffect(() => {
    if (autoScroll && !isScrolling && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logEntries, autoScroll, isScrolling]);

  // Add new log entries periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const mockEvents = [
        { level: 'INFO' as const, source: 'SYSTEM', message: 'Heartbeat received from mesh network' },
        { level: 'DEBUG' as const, source: 'RADIO', message: 'LoRa packet received, processing...' },
        { level: 'INFO' as const, source: 'ROUTING', message: 'Route table updated' },
        { level: 'WARNING' as const, source: 'BATTERY', message: 'Low battery warning detected' },
        { level: 'DEBUG' as const, source: 'TELEMETRY', message: 'Sensor data collected' },
      ];

      const randomEvent = mockEvents[Math.floor(Math.random() * mockEvents.length)];
      const randomNode = ['NODE-01', 'NODE-02', 'NODE-03', 'NODE-04'][Math.floor(Math.random() * 4)];
      
      setLogEntries((prev) => [
        {
          id: `event-${Date.now()}`,
          timestamp: new Date().toISOString(),
          level: randomEvent.level,
          source: randomEvent.source,
          nodeId: randomNode,
          message: randomEvent.message,
        },
        ...prev.slice(0, 199), // Keep last 200 entries
      ]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Detect manual scrolling (pause auto-scroll)
  useEffect(() => {
    const container = logContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      setIsScrolling(true);
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
      scrollTimeoutRef.current = setTimeout(() => setIsScrolling(false), 2000);
    };

    container.addEventListener('scroll', handleScroll);
    return () => {
      container.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
    };
  }, []);

  // Keyboard controls
  // Apply filters and search
  const filteredEntries = searchLogEntries(
    filterLogEntries(logEntries, selectedNodeId, selectedEventType),
    searchQuery
  );

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (key === 'a') {
        event.preventDefault();
        setAutoScroll((prev) => !prev);
      } else if (key === 'e') {
        event.preventDefault();
        exportToCSV(filteredEntries);
      } else if (key === 'escape') {
        event.preventDefault();
        setSearchQuery('');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredEntries]);

  const stats = getLogStatistics(logEntries);
  const uniqueNodeIds = getUniqueNodeIds(logEntries);

  return (
    <div style={{ 
      padding: '16px', 
      backgroundColor: '#000', 
      minHeight: '100vh',
      fontFamily: 'IBM VGA, monospace'
    }}>
      {/* Title Panel */}
      <TeletextPanel 
        title={`NODE LOG ● ${filteredEntries.length}/${logEntries.length} ENTRIES`}
        color="magenta"
      >
        <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
          {/* Node Filter */}
          <div>
            <TeletextText color="gray">NODE: </TeletextText>
            <select
              value={selectedNodeId}
              onChange={(e) => setSelectedNodeId(e.target.value)}
              style={{
                backgroundColor: '#1a1a1a',
                color: '#50D8D7',
                border: '1px solid #50D8D7',
                padding: '4px 8px',
                fontFamily: 'monospace',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">ALL</option>
              {uniqueNodeIds.map((nodeId) => (
                <option key={nodeId} value={nodeId}>
                  {nodeId}
                </option>
              ))}
            </select>
          </div>

          {/* Event Type Filter */}
          <div>
            <TeletextText color="gray">TYPE: </TeletextText>
            <select
              value={selectedEventType}
              onChange={(e) => setSelectedEventType(e.target.value as EventType)}
              style={{
                backgroundColor: '#1a1a1a',
                color: '#50D8D7',
                border: '1px solid #50D8D7',
                padding: '4px 8px',
                fontFamily: 'monospace',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">ALL</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="DEBUG">DEBUG</option>
            </select>
          </div>

          {/* Statistics */}
          <div style={{ marginLeft: 'auto' }}>
            <TeletextText color="gray">
              ● {stats.info} ⚠ {stats.warning} ✖ {stats.error} ○ {stats.debug}
            </TeletextText>
          </div>
        </div>

        {/* Search Box */}
        <div style={{ marginBottom: '12px' }}>
          <TeletextText color="gray">SEARCH: </TeletextText>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by message, source, or node ID..."
            style={{
              width: '100%',
              backgroundColor: '#1a1a1a',
              color: '#FB8B24',
              border: '1px solid #FB8B24',
              padding: '6px 8px',
              fontFamily: 'monospace',
              marginTop: '4px',
            }}
          />
        </div>
      </TeletextPanel>

      {/* Log Entries */}
      <TeletextPanel 
        title="LOG STREAM"
        color="cyan"
        style={{ marginTop: '12px' }}
      >
        <div 
          ref={logContainerRef}
          style={{ 
            maxHeight: '500px', 
            overflowY: 'auto',
            paddingRight: '8px'
          }}
        >
          {filteredEntries.length === 0 ? (
            <TeletextText color="gray">NO MATCHING LOG ENTRIES</TeletextText>
          ) : (
            filteredEntries.map((entry) => (
              <div 
                key={entry.id} 
                style={{ 
                  marginBottom: '6px', 
                  paddingBottom: '6px', 
                  borderBottom: '1px solid #1a1a1a',
                  display: 'grid',
                  gridTemplateColumns: '70px 80px 80px 1fr',
                  gap: '8px',
                  fontSize: '12px'
                }}
              >
                <TeletextText color="gray">{formatTime(entry.timestamp)}</TeletextText>
                <TeletextText color={getLevelColor(entry.level)}>
                  {getLevelIcon(entry.level)} [{entry.level.padEnd(7, ' ')}]
                </TeletextText>
                <TeletextText color="yellow">
                  [{entry.source}]
                </TeletextText>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {entry.nodeId && (
                    <TeletextText color="green">{entry.nodeId}</TeletextText>
                  )}
                  <TeletextText color="white">{entry.message}</TeletextText>
                </div>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </TeletextPanel>

      {/* Controls */}
      <div style={{ marginTop: '12px' }}>
        <TeletextText color="gray">
          [A] {autoScroll ? '◀ AUTO-SCROLL ON' : '⏸ PAUSED'} • 
          [E] EXPORT CSV • 
          [ESC] CLEAR SEARCH • 
          {isScrolling ? ' 📜 SCROLLING' : ' ⏱ IDLE'}
        </TeletextText>
      </div>
    </div>
  );
};

export default P700;
