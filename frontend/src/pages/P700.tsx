import { useEffect, useState, useRef } from 'react';
import { TeletextPanel, TeletextText } from '../components';
import useNavigationStore from '../store/navigationStore';
import useMeshStore from '../store/meshStore';

/**
 * P700 - Node Log Page
 * Event log with real-time scrolling and auto-scroll toggle
 */

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  source: string;
  message: string;
}

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
  const logEndRef = useRef<HTMLDivElement>(null);

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
        source: `NODE/${node.callsign}`,
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
        source: `THREAD/${thread.radio_type}`,
        message: `${thread.source_id.slice(0, 8)} ↔ ${thread.target_id.slice(0, 8)} | Quality: ${quality.toFixed(0)}% | RSSI: ${thread.rssi || 'N/A'} dBm`,
      });
    });

    // Sort by timestamp descending
    newEntries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    setLogEntries(newEntries);
  }, [nodes, messages, threads]);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logEntries, autoScroll]);

  // Add new log entries periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const mockEvents = [
        { level: 'INFO' as const, source: 'SYSTEM', message: 'Heartbeat received from mesh network' },
        { level: 'DEBUG' as const, source: 'RADIO', message: 'LoRa packet received, processing...' },
        { level: 'INFO' as const, source: 'ROUTING', message: 'Route table updated (23 routes)' },
        { level: 'WARNING' as const, source: 'BATTERY', message: 'Low battery warning on node SPORE-42' },
        { level: 'DEBUG' as const, source: 'TELEMETRY', message: 'Sensor data collected from 12 nodes' },
      ];

      const randomEvent = mockEvents[Math.floor(Math.random() * mockEvents.length)];
      
      setLogEntries((prev) => [
        {
          id: `event-${Date.now()}`,
          timestamp: new Date().toISOString(),
          level: randomEvent.level,
          source: randomEvent.source,
          message: randomEvent.message,
        },
        ...prev.slice(0, 99), // Keep last 100 entries
      ]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === 'a') {
        setAutoScroll((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'INFO': return 'cyan';
      case 'DEBUG': return 'gray';
      case 'WARNING': return 'yellow';
      case 'ERROR': return 'red';
      default: return 'white';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'INFO': return '●';
      case 'DEBUG': return '○';
      case 'WARNING': return '⚠';
      case 'ERROR': return '✖';
      default: return '·';
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#000', 
      minHeight: '100vh',
      fontFamily: 'IBM VGA, monospace'
    }}>
      <TeletextPanel 
        title={`EVENT LOG ● ${logEntries.length} ENTRIES ${autoScroll ? '● AUTO-SCROLL ON' : ''}`} 
        color="magenta"
      >
        <div 
          style={{ 
            maxHeight: '600px', 
            overflowY: 'auto',
            paddingRight: '8px'
          }}
        >
          {logEntries.length === 0 ? (
            <TeletextText color="gray">NO LOG ENTRIES</TeletextText>
          ) : (
            logEntries.map((entry) => (
              <div 
                key={entry.id} 
                style={{ 
                  marginBottom: '8px', 
                  paddingBottom: '8px', 
                  borderBottom: '1px solid #1a1a1a',
                  display: 'flex',
                  gap: '12px'
                }}
              >
                <TeletextText color="gray">{formatTime(entry.timestamp)}</TeletextText>
                <TeletextText color={getLevelColor(entry.level) as 'cyan' | 'magenta' | 'yellow' | 'green'}>
                  {getLevelIcon(entry.level)} [{entry.level.padEnd(7, ' ')}]
                </TeletextText>
                <TeletextText color="cyan">[{entry.source}]</TeletextText>
                <TeletextText color="white">{entry.message}</TeletextText>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </TeletextPanel>

      <div style={{ marginTop: '16px' }}>
        <TeletextText color="gray">
          [100] MENU • [A] TOGGLE AUTO-SCROLL • [ESC] CLEAR • {autoScroll ? '⬇ SCROLLING' : '⏸ PAUSED'}
        </TeletextText>
      </div>
    </div>
  );
};

export default P700;
