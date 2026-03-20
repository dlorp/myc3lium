import React, { useState, useEffect } from 'react';
import TeletextPanel from '../components/TeletextPanel';
import '../styles/teletext.css';

/**
 * P900 - Intelligence & ATAK Integration
 * 
 * Specialized intelligence features:
 * - RF source detection (TDOA localization)
 * - RSSI heatmap overlay
 * - ATAK integration status
 * - Spectrum monitoring
 * 
 * Note: Network topology is on P200 (LatticeMapPage)
 */

interface RFSource {
  id: string;
  frequency: number;
  rssi: number;
  position?: { lat: number; lon: number };
  timestamp: number;
}

interface HeatmapPoint {
  lat: number;
  lon: number;
  value: number;
}

const P900: React.FC = () => {
  const [rfSources, setRFSources] = useState<RFSource[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapPoint[]>([]);
  const [atakConnected, setAtakConnected] = useState(false);
  const [atakStats, setAtakStats] = useState({
    videoFeeds: 0,
    cotMessagesSent: 0,
    multicastGroup: '239.2.3.1:6969'
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/intelligence');
    
    ws.onopen = () => {
      console.log('Intelligence WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'rssi_measurement':
          updateHeatmap(data);
          break;
        case 'rf_source_detected':
          setRFSources(prev => [...prev, data.source]);
          break;
        case 'atak_status':
          setAtakConnected(data.connected);
          if (data.stats) {
            setAtakStats(data.stats);
          }
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, []);

  // Update heatmap data
  const updateHeatmap = (measurement: any) => {
    setHeatmapData(prev => {
      const updated = [...prev];
      updated.push({
        lat: measurement.lat,
        lon: measurement.lon,
        value: measurement.rssi
      });
      
      // Keep last 100 points
      if (updated.length > 100) {
        updated.shift();
      }
      
      return updated;
    });
  };

  // Generate ASCII heatmap
  const renderHeatmap = () => {
    if (heatmapData.length === 0) {
      return <div style={{ color: '#666' }}>No signal data collected</div>;
    }

    const chars = ['·', '░', '▒', '▓', '█'];
    
    return (
      <div style={{ fontFamily: 'monospace', lineHeight: '1', letterSpacing: '0.1em' }}>
        {heatmapData.slice(-50).map((point, idx) => {
          const intensity = Math.floor((point.value + 120) / 24); // Normalize -120 to 0 dBm
          const charIndex = Math.max(0, Math.min(chars.length - 1, intensity));
          return <span key={idx}>{chars[charIndex]}</span>;
        })}
      </div>
    );
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '24px', color: '#00FFFF', fontFamily: 'IBM VGA, monospace' }}>
          P900 │ INTELLIGENCE & ATAK
        </span>
        <span style={{ 
          marginLeft: '20px', 
          fontSize: '16px',
          color: atakConnected ? '#00FF00' : '#FF0000',
          fontFamily: 'IBM VGA, monospace'
        }}>
          {atakConnected ? '● ATAK CONNECTED' : '○ ATAK OFFLINE'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* RF Sources Panel */}
        <TeletextPanel title="RF SOURCES DETECTED" color="cyan">
          <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '14px' }}>
            {rfSources.length === 0 ? (
              <div style={{ color: '#666' }}>No RF sources detected</div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #00FFFF' }}>
                    <th style={{ textAlign: 'left', padding: '4px' }}>FREQ (MHz)</th>
                    <th style={{ textAlign: 'left', padding: '4px' }}>RSSI</th>
                    <th style={{ textAlign: 'left', padding: '4px' }}>POSITION</th>
                    <th style={{ textAlign: 'left', padding: '4px' }}>AGE</th>
                  </tr>
                </thead>
                <tbody>
                  {rfSources.slice(-10).reverse().map(source => (
                    <tr key={source.id} style={{ borderBottom: '1px solid #004444' }}>
                      <td style={{ padding: '4px', color: '#00FFFF' }}>
                        {(source.frequency / 1e6).toFixed(3)}
                      </td>
                      <td style={{ padding: '4px', color: '#00FFFF' }}>
                        {source.rssi} dBm
                      </td>
                      <td style={{ padding: '4px', color: '#00FFFF' }}>
                        {source.position 
                          ? `${source.position.lat.toFixed(4)}, ${source.position.lon.toFixed(4)}`
                          : 'Unknown'
                        }
                      </td>
                      <td style={{ padding: '4px', color: '#00FFFF' }}>
                        {Math.floor((Date.now() - source.timestamp) / 1000)}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </TeletextPanel>

        {/* ATAK Integration Status */}
        <TeletextPanel title="ATAK INTEGRATION" color="magenta">
          <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '14px', lineHeight: '1.8' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #440044', padding: '4px 0' }}>
              <span style={{ color: '#FF00FF' }}>Status:</span>
              <span style={{ color: atakConnected ? '#00FF00' : '#FF0000' }}>
                {atakConnected ? '● CONNECTED' : '○ DISCONNECTED'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #440044', padding: '4px 0' }}>
              <span style={{ color: '#FF00FF' }}>Video Feeds:</span>
              <span style={{ color: '#00FFFF' }}>{atakStats.videoFeeds}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #440044', padding: '4px 0' }}>
              <span style={{ color: '#FF00FF' }}>CoT Messages:</span>
              <span style={{ color: '#00FFFF' }}>{atakStats.cotMessagesSent}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
              <span style={{ color: '#FF00FF' }}>Multicast:</span>
              <span style={{ color: '#00FFFF', fontSize: '12px' }}>{atakStats.multicastGroup}</span>
            </div>
          </div>
        </TeletextPanel>

        {/* RSSI Heatmap */}
        <TeletextPanel title="SIGNAL STRENGTH HEATMAP" color="yellow">
          <div style={{ color: '#FFFF00' }}>
            {renderHeatmap()}
          </div>
        </TeletextPanel>

        {/* Spectrum Info */}
        <TeletextPanel title="SPECTRUM MONITORING" color="green">
          <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '14px', lineHeight: '1.8', color: '#00FF00' }}>
            <div>LoRa 915 MHz: Active</div>
            <div>HaLow 900 MHz: Active</div>
            <div>WiFi 2.4 GHz: Active</div>
            <div>WiFi 5 GHz: Active</div>
            <div style={{ marginTop: '12px', color: '#888888' }}>
              TDOA localization: {rfSources.filter(s => s.position).length} sources positioned
            </div>
          </div>
        </TeletextPanel>
      </div>

      {/* Legend */}
      <div style={{ marginTop: '20px' }}>
        <TeletextPanel title="LEGEND" color="cyan">
          <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '12px', lineHeight: '1.6', color: '#00FFFF' }}>
            <div><strong>RF Source Detection:</strong> Passive TDOA (Time Difference of Arrival) localization</div>
            <div><strong>ATAK Integration:</strong> Cursor on Target (CoT) protocol for tactical mapping</div>
            <div><strong>Heatmap:</strong> Real-time RSSI measurements across mesh (· weak → █ strong)</div>
            <div style={{ marginTop: '8px', color: '#888888' }}>
              Network topology: See P200 (Lattice Map)
            </div>
          </div>
        </TeletextPanel>
      </div>
    </div>
  );
};

export default P900;
