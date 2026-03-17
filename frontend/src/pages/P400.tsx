import { useEffect, useState } from 'react';
import { TeletextPanel, TeletextText, Sparkline, StatusBar } from '../components';
import useNavigationStore from '../store/navigationStore';
import useMeshStore from '../store/meshStore';

/**
 * P400 - Sensor Grid Page
 * Telemetry table with real-time readings, sparklines, and color-coded warnings
 */

interface SensorReading {
  nodeId: string;
  callsign: string;
  temperature: number;
  humidity: number;
  pressure: number;
  battery: number;
  rssi: number;
  status: 'GOOD' | 'WARNING' | 'CRITICAL';
  tempHistory: number[];
  humidityHistory: number[];
}

const P400 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs);
  const nodes = useMeshStore((state) => state.nodes);
  const loadAll = useMeshStore((state) => state.loadAll);
  const connectWS = useMeshStore((state) => state.connectWS);
  const disconnectWS = useMeshStore((state) => state.disconnectWS);
  
  const [sensorReadings, setSensorReadings] = useState<SensorReading[]>([]);

  useEffect(() => {
    setBreadcrumbs(['SENSORS', 'P400']);
    loadAll();
    connectWS();

    return () => {
      disconnectWS();
    };
  }, [setBreadcrumbs, loadAll, connectWS, disconnectWS]);

  // Generate mock sensor data from nodes
  useEffect(() => {
    const readings: SensorReading[] = nodes.map((node) => {
      const temp = 20 + Math.random() * 15;
      const humidity = 40 + Math.random() * 40;
      const pressure = 1000 + Math.random() * 30;
      
      // Generate status based on thresholds
      let status: 'GOOD' | 'WARNING' | 'CRITICAL' = 'GOOD';
      if (temp > 30 || humidity > 75 || (node.battery && node.battery < 20)) {
        status = 'WARNING';
      }
      if (temp > 35 || humidity > 85 || (node.battery && node.battery < 10)) {
        status = 'CRITICAL';
      }

      // Generate history data for sparklines
      const tempHistory = Array.from({ length: 20 }, (_, i) => 
        temp + (Math.random() - 0.5) * 5
      );
      const humidityHistory = Array.from({ length: 20 }, (_, i) => 
        humidity + (Math.random() - 0.5) * 10
      );

      return {
        nodeId: node.id,
        callsign: node.callsign,
        temperature: temp,
        humidity,
        pressure,
        battery: node.battery || 0,
        rssi: node.rssi || -80,
        status,
        tempHistory,
        humidityHistory,
      };
    });

    setSensorReadings(readings);
  }, [nodes]);

  // Update sensor readings periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setSensorReadings((prev) => 
        prev.map((reading) => {
          const temp = reading.temperature + (Math.random() - 0.5) * 2;
          const humidity = reading.humidity + (Math.random() - 0.5) * 3;
          
          let status: 'GOOD' | 'WARNING' | 'CRITICAL' = 'GOOD';
          if (temp > 30 || humidity > 75 || reading.battery < 20) {
            status = 'WARNING';
          }
          if (temp > 35 || humidity > 85 || reading.battery < 10) {
            status = 'CRITICAL';
          }

          return {
            ...reading,
            temperature: temp,
            humidity,
            status,
            tempHistory: [...reading.tempHistory.slice(1), temp],
            humidityHistory: [...reading.humidityHistory.slice(1), humidity],
          };
        })
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'GOOD': return 'green';
      case 'WARNING': return 'yellow';
      case 'CRITICAL': return 'red';
      default: return 'gray';
    }
  };

  const getBatteryColor = (battery: number) => {
    if (battery > 50) return 'green';
    if (battery > 20) return 'yellow';
    return 'red';
  };

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#000', 
      minHeight: '100vh',
      fontFamily: 'IBM VGA, monospace'
    }}>
      <TeletextPanel title={`TELEMETRY GRID ● ${sensorReadings.length} NODES`} color="green">
        {sensorReadings.length === 0 ? (
          <TeletextText color="gray">NO SENSOR DATA AVAILABLE</TeletextText>
        ) : (
          <div>
            {sensorReadings.map((reading) => (
              <div 
                key={reading.nodeId} 
                style={{ 
                  marginBottom: '20px', 
                  borderBottom: '1px solid #333', 
                  paddingBottom: '12px' 
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <TeletextText color="cyan">
                    {reading.callsign} ({reading.nodeId.slice(0, 8)})
                  </TeletextText>
                  <TeletextText color={getStatusColor(reading.status) as any}>
                    [{reading.status}]
                  </TeletextText>
                </div>

                <div style={{ marginBottom: '8px' }}>
                  <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                    <div style={{ flex: 1 }}>
                      <TeletextText color="yellow">TEMP: {reading.temperature.toFixed(1)}°C</TeletextText>
                      <div style={{ marginTop: '4px' }}>
                        <Sparkline 
                          data={reading.tempHistory} 
                          width={150} 
                          height={30} 
                          color={reading.temperature > 30 ? 'red' : 'cyan'} 
                        />
                      </div>
                    </div>

                    <div style={{ flex: 1 }}>
                      <TeletextText color="yellow">HUMIDITY: {reading.humidity.toFixed(0)}%</TeletextText>
                      <div style={{ marginTop: '4px' }}>
                        <Sparkline 
                          data={reading.humidityHistory} 
                          width={150} 
                          height={30} 
                          color={reading.humidity > 75 ? 'red' : 'cyan'} 
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: '4px' }}>
                  <TeletextText color="gray">
                    PRESSURE: {reading.pressure.toFixed(1)} hPa ● RSSI: {reading.rssi} dBm
                  </TeletextText>
                </div>

                <div style={{ marginTop: '8px' }}>
                  <StatusBar 
                    value={reading.battery} 
                    color={getBatteryColor(reading.battery) as any} 
                    label={`BATTERY ${reading.battery.toFixed(0)}%`} 
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </TeletextPanel>

      <div style={{ marginTop: '16px' }}>
        <TeletextText color="gray">
          [100] MENU • [T] SORT TEMP • [H] SORT HUMIDITY • [ESC] CLEAR
        </TeletextText>
      </div>
    </div>
  );
};

export default P400;
