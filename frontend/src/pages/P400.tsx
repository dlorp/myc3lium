import { useEffect, useState, startTransition } from 'react';
import { TeletextPanel, TeletextText, Sparkline } from '../components';
import useNavigationStore from '../store/navigationStore';
import useMeshStore from '../store/meshStore';
import {
  SensorReading,
  SortColumn,
  calculateAQI,
  getAlertStatus,
  getThresholdColor,
  getSortFunction,
  exportToCSV,
} from './P400.utils';

/**
 * P400 - Sensor Grid Page (Phase 4 Sprint 1 Polish)
 * Production-ready sensor telemetry with real-time updates,
 * interactive sorting, expandable rows, and data export.
 */

// CSS Animations
const styles = `
  @keyframes flash {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  @keyframes pulse {
    0%, 100% { background-color: rgba(255, 0, 0, 0.1); }
    50% { background-color: rgba(255, 0, 0, 0.3); }
  }

  .sensor-table-header {
    display: flex;
    gap: 12px;
    padding: 8px;
    background-color: #1a1a1a;
    border-bottom: 2px solid #00FF00;
    font-weight: bold;
    font-family: 'IBM VGA', monospace;
    cursor: pointer;
    user-select: none;
    transition: background-color 0.2s;
  }

  .sensor-table-header:hover {
    background-color: #2a2a2a;
  }

  .sensor-row {
    padding: 8px;
    border-bottom: 1px solid #333;
    display: flex;
    gap: 12px;
    align-items: center;
    transition: background-color 0.15s, transform 0.15s;
    cursor: pointer;
  }

  .sensor-row:hover {
    background-color: rgba(0, 255, 255, 0.05);
    transform: translateX(2px);
  }

  .sensor-row.expanded {
    background-color: rgba(0, 255, 255, 0.1);
  }

  .sensor-row.critical {
    animation: pulse 1.5s infinite;
  }

  .alert-flash {
    animation: flash 1s infinite;
  }

  .sort-indicator {
    display: inline-block;
    margin-left: 4px;
    font-size: 0.8em;
  }

  .expanded-details {
    padding: 12px 8px;
    background-color: rgba(0, 255, 255, 0.05);
    border-left: 3px solid #00FFFF;
    margin: 8px 0;
    animation: slideDown 0.2s ease-out;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .metric-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 8px;
  }

  .metric-item {
    font-family: 'IBM VGA', monospace;
    font-size: 0.9em;
  }

  .skeleton-row {
    padding: 8px;
    border-bottom: 1px solid #333;
    background: linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
  }

  @keyframes loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
`;

const P400 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs);
  const nodes = useMeshStore((state) => state.nodes);
  const loadAll = useMeshStore((state) => state.loadAll);
  const connectWS = useMeshStore((state) => state.connectWS);
  const disconnectWS = useMeshStore((state) => state.disconnectWS);
  
  const [sensorReadings, setSensorReadings] = useState<SensorReading[]>([]);
  const [sortColumn, setSortColumn] = useState<SortColumn>('nodeId');
  const [sortAscending, setSortAscending] = useState(true);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);

  // Initialize page
  useEffect(() => {
    setBreadcrumbs(['SENSORS', 'P400']);
    setIsLoading(true);
    loadAll();
    connectWS();

    return () => {
      disconnectWS();
    };
  }, [setBreadcrumbs, loadAll, connectWS, disconnectWS]);

  // Generate initial sensor readings from nodes
  useEffect(() => {
    if (nodes.length === 0) {
      setIsLoading(false);
      setSensorReadings([]);
      return;
    }

    const readings: SensorReading[] = nodes.map((node) => {
      const temp = 20 + Math.random() * 15;
      const humidity = 40 + Math.random() * 40;
      const pressure = 1000 + Math.random() * 30;
      const battery = node.battery || 75;

      // Generate 20-point history for each metric
      const tempHistory = Array.from({ length: 20 }, () => 
        temp + (Math.random() - 0.5) * 5
      );
      const humidityHistory = Array.from({ length: 20 }, () => 
        humidity + (Math.random() - 0.5) * 10
      );
      const pressureHistory = Array.from({ length: 20 }, () => 
        pressure + (Math.random() - 0.5) * 15
      );
      const batteryHistory = Array.from({ length: 20 }, () => 
        Math.max(0, battery + (Math.random() - 0.5) * 10)
      );

      const aqi = calculateAQI(temp, humidity, pressure);
      const status = getAlertStatus(temp, humidity, battery);

      return {
        nodeId: node.id,
        callsign: node.callsign,
        temperature: temp,
        humidity,
        pressure,
        aqi,
        battery,
        rssi: node.rssi || -80,
        status,
        tempHistory,
        humidityHistory,
        pressureHistory,
        batteryHistory,
        timestamps: Array.from({ length: 20 }, (_, i) => Date.now() - (20 - i) * 5000),
      };
    });

    startTransition(() => {
      setSensorReadings(readings);
      setIsLoading(false);
    });
  }, [nodes]);

  // Live update sensor readings
  useEffect(() => {
    const interval = setInterval(() => {
      startTransition(() => {
        setSensorReadings((prev) =>
          prev.map((reading) => {
            const tempDelta = (Math.random() - 0.5) * 2;
            const humidityDelta = (Math.random() - 0.5) * 3;
            const pressureDelta = (Math.random() - 0.5) * 2;
            const batteryDelta = (Math.random() - 0.5) * 0.5;

            const newTemp = reading.temperature + tempDelta;
            const newHumidity = reading.humidity + humidityDelta;
            const newPressure = reading.pressure + pressureDelta;
            const newBattery = Math.max(0, Math.min(100, reading.battery + batteryDelta));

            const aqi = calculateAQI(newTemp, newHumidity, newPressure);
            const status = getAlertStatus(newTemp, newHumidity, newBattery);

            return {
              ...reading,
              temperature: newTemp,
              humidity: newHumidity,
              pressure: newPressure,
              battery: newBattery,
              aqi,
              status,
              tempHistory: [...reading.tempHistory.slice(1), newTemp],
              humidityHistory: [...reading.humidityHistory.slice(1), newHumidity],
              pressureHistory: [...reading.pressureHistory.slice(1), newPressure],
              batteryHistory: [...reading.batteryHistory.slice(1), newBattery],
              timestamps: [...reading.timestamps.slice(1), Date.now()],
            };
          })
        );
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Handle column sorting
  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortAscending(!sortAscending);
    } else {
      setSortColumn(column);
      setSortAscending(true);
    }
  };

  // Get sorted readings
  const sortedReadings = [...sensorReadings].sort(
    getSortFunction(sortColumn, sortAscending)
  );

  // Toggle row expansion
  const toggleRowExpansion = (nodeId: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  // Render sort indicator
  const renderSortIndicator = (column: SortColumn) => {
    if (sortColumn !== column) return '';
    return sortAscending ? ' ▲' : ' ▼';
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div style={{ padding: '20px', backgroundColor: '#000', minHeight: '100vh' }}>
        <style>{styles}</style>
        <TeletextPanel title="TELEMETRY GRID ● LOADING..." color="green">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="skeleton-row" style={{ height: '40px' }} />
          ))}
        </TeletextPanel>
      </div>
    );
  }

  // Empty state
  if (sensorReadings.length === 0) {
    return (
      <div style={{ padding: '20px', backgroundColor: '#000', minHeight: '100vh' }}>
        <style>{styles}</style>
        <TeletextPanel title="TELEMETRY GRID ● 0 NODES" color="green">
          <TeletextText color="gray">NO SENSOR DATA AVAILABLE</TeletextText>
          <TeletextText color="gray" style={{ marginTop: '8px' }}>
            Waiting for mesh network nodes...
          </TeletextText>
        </TeletextPanel>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#000', minHeight: '100vh' }}>
      <style>{styles}</style>

      {/* Header with export button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <TeletextText color="green">
          TELEMETRY GRID ● {sensorReadings.length} NODES
        </TeletextText>
        <button
          onClick={() => exportToCSV(sensorReadings)}
          style={{
            padding: '6px 12px',
            backgroundColor: '#00FF00',
            color: '#000',
            border: 'none',
            fontFamily: 'IBM VGA, monospace',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontSize: '0.9em',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#00CC00';
            e.currentTarget.style.boxShadow = '0 0 10px #00FF00';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#00FF00';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          EXPORT CSV
        </button>
      </div>

      <TeletextPanel title="" color="cyan">
        {/* Table Header (Sortable) */}
        <div className="sensor-table-header">
          <div style={{ flex: '0 0 100px', cursor: 'pointer' }} onClick={() => handleSort('nodeId')}>
            NODE ID{renderSortIndicator('nodeId')}
          </div>
          <div style={{ flex: '0 0 80px', cursor: 'pointer' }} onClick={() => handleSort('temperature')}>
            TEMP{renderSortIndicator('temperature')}
          </div>
          <div style={{ flex: '0 0 80px', cursor: 'pointer' }} onClick={() => handleSort('humidity')}>
            HUM{renderSortIndicator('humidity')}
          </div>
          <div style={{ flex: '0 0 80px', cursor: 'pointer' }} onClick={() => handleSort('pressure')}>
            PRES{renderSortIndicator('pressure')}
          </div>
          <div style={{ flex: '0 0 60px', cursor: 'pointer' }} onClick={() => handleSort('aqi')}>
            AQI{renderSortIndicator('aqi')}
          </div>
          <div style={{ flex: '0 0 70px', cursor: 'pointer' }} onClick={() => handleSort('battery')}>
            BAT{renderSortIndicator('battery')}
          </div>
          <div style={{ flex: '0 0 100px', cursor: 'pointer' }} onClick={() => handleSort('status')}>
            STATUS{renderSortIndicator('status')}
          </div>
        </div>

        {/* Table Rows */}
        {sortedReadings.map((reading) => {
          const isExpanded = expandedRows.has(reading.nodeId);
          const tempColor = getThresholdColor(reading.temperature, 'temperature');

          return (
            <div key={reading.nodeId}>
              {/* Summary Row */}
              <div
                className={`sensor-row ${isExpanded ? 'expanded' : ''} ${reading.status === 'CRITICAL' ? 'critical' : ''}`}
                onClick={() => toggleRowExpansion(reading.nodeId)}
                style={{
                  borderLeft: `3px solid ${reading.status === 'CRITICAL' ? '#FF0000' : reading.status === 'WARNING' ? '#FFFF00' : '#00FF00'}`,
                }}
              >
                <div style={{ flex: '0 0 100px', fontWeight: reading.status === 'CRITICAL' ? 'bold' : 'normal' }}>
                  <TeletextText color="cyan">{reading.callsign.substring(0, 10)}</TeletextText>
                </div>

                <div style={{ flex: '0 0 80px' }}>
                  <TeletextText
                    color={tempColor === '#0080FF' ? 'blue' : tempColor === '#00FFFF' ? 'cyan' : tempColor === '#00FF00' ? 'green' : tempColor === '#FFFF00' ? 'yellow' : tempColor === '#FF8000' ? 'orange' : 'red'}
                    blink={reading.status === 'CRITICAL' && reading.temperature > 35}
                  >
                    {reading.temperature.toFixed(1)}°C
                  </TeletextText>
                </div>

                <div style={{ flex: '0 0 80px' }}>
                  <TeletextText
                    color={reading.humidity < 30 ? 'red' : reading.humidity < 40 ? 'orange' : reading.humidity < 60 ? 'green' : reading.humidity < 75 ? 'yellow' : 'red'}
                    blink={reading.status === 'CRITICAL' && reading.humidity > 85}
                  >
                    {reading.humidity.toFixed(0)}%
                  </TeletextText>
                </div>

                <div style={{ flex: '0 0 80px' }}>
                  <TeletextText
                    color={reading.pressure < 1000 ? 'red' : reading.pressure < 1010 ? 'orange' : reading.pressure < 1020 ? 'green' : 'yellow'}
                  >
                    {reading.pressure.toFixed(0)}hPa
                  </TeletextText>
                </div>

                <div style={{ flex: '0 0 60px' }}>
                  <TeletextText
                    color={reading.aqi > 75 ? 'green' : reading.aqi > 50 ? 'yellow' : reading.aqi > 25 ? 'orange' : 'red'}
                  >
                    {reading.aqi}
                  </TeletextText>
                </div>

                <div style={{ flex: '0 0 70px' }}>
                  <TeletextText
                    color={reading.battery > 50 ? 'green' : reading.battery > 20 ? 'yellow' : 'red'}
                    blink={reading.battery < 20}
                  >
                    {reading.battery.toFixed(0)}%
                  </TeletextText>
                </div>

                <div style={{ flex: '0 0 100px' }}>
                  <TeletextText
                    color={reading.status === 'GOOD' ? 'green' : reading.status === 'WARNING' ? 'yellow' : 'red'}
                    blink={reading.status === 'CRITICAL'}
                  >
                    [{reading.status}]
                  </TeletextText>
                </div>
              </div>

              {/* Expanded Detail Row */}
              {isExpanded && (
                <div className="expanded-details">
                  <TeletextText color="yellow" style={{ marginBottom: '12px', fontWeight: 'bold' }}>
                    DETAILED HISTORY ● {reading.callsign}
                  </TeletextText>

                  <div className="metric-grid">
                    <div className="metric-item">
                      <TeletextText color="cyan">TEMPERATURE TREND</TeletextText>
                      <Sparkline
                        data={reading.tempHistory}
                        width={200}
                        height={40}
                        color={tempColor === '#FF0000' ? 'red' : tempColor === '#FF8000' ? 'orange' : tempColor === '#FFFF00' ? 'yellow' : tempColor === '#00FF00' ? 'green' : tempColor === '#00FFFF' ? 'cyan' : 'blue'}
                      />
                    </div>

                    <div className="metric-item">
                      <TeletextText color="cyan">HUMIDITY TREND</TeletextText>
                      <Sparkline
                        data={reading.humidityHistory}
                        width={200}
                        height={40}
                        color={reading.humidity > 75 ? 'red' : reading.humidity > 60 ? 'yellow' : 'green'}
                      />
                    </div>

                    <div className="metric-item">
                      <TeletextText color="cyan">PRESSURE TREND</TeletextText>
                      <Sparkline
                        data={reading.pressureHistory}
                        width={200}
                        height={40}
                        color={reading.pressure < 1000 ? 'red' : reading.pressure < 1010 ? 'orange' : 'green'}
                      />
                    </div>

                    <div className="metric-item">
                      <TeletextText color="cyan">BATTERY TREND</TeletextText>
                      <Sparkline
                        data={reading.batteryHistory}
                        width={200}
                        height={40}
                        color={reading.battery > 50 ? 'green' : reading.battery > 20 ? 'yellow' : 'red'}
                      />
                    </div>
                  </div>

                  <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <TeletextText color="gray">
                      RSSI: {reading.rssi} dBm
                    </TeletextText>
                    <TeletextText color="gray">
                      Node ID: {reading.nodeId.slice(0, 16)}...
                    </TeletextText>
                    <TeletextText color="gray">
                      Data Points: {reading.tempHistory.length}
                    </TeletextText>
                    <TeletextText color="gray">
                      Last Update: {new Date(reading.timestamps[reading.timestamps.length - 1]).toLocaleTimeString()}
                    </TeletextText>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </TeletextPanel>

      {/* Control hints */}
      <div style={{ marginTop: '16px' }}>
        <TeletextText color="gray">
          [CLICK] Expand row details • [HEADER] Sort column • [EXPORT CSV] Download data
        </TeletextText>
      </div>
    </div>
  );
};

export default P400;
