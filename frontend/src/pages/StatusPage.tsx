/**
 * P100: StatusPage - System Overview Dashboard
 * 
 * Displays real-time system status including:
 * - System metrics (uptime, CPU, memory)
 * - Active node count
 * - Thread status by type (LoRa, HaLow, WiFi)
 * - Battery indicator
 */

import React, { useEffect, useState } from 'react';
import TeletextPanel from '../components/TeletextPanel';
import StatusBar from '../components/StatusBar';
import ProgressBar from '../components/ProgressBar';
import useMeshStore from '../store/meshStore';

interface SystemMetrics {
  uptime: number; // seconds
  cpuUsage: number; // 0-100
  memoryUsage: number; // 0-100
  batteryLevel: number; // 0-100
}

const StatusPage: React.FC = () => {
  const {
    nodes,
    threads,
    nodesLoading,
    threadsLoading,
    wsConnected,
    loadAll,
    connectWS,
    disconnectWS,
  } = useMeshStore();

  const [metrics, setMetrics] = useState<SystemMetrics>({
    uptime: 0,
    cpuUsage: 0,
    memoryUsage: 0,
    batteryLevel: 100,
  });

  useEffect(() => {
    // Load data and connect WebSocket on mount
    loadAll();
    connectWS();

    return () => {
      disconnectWS();
    };
  }, [loadAll, connectWS, disconnectWS]);

  useEffect(() => {
    // Simulate uptime counter
    const interval = setInterval(() => {
      setMetrics((prev) => ({
        ...prev,
        uptime: prev.uptime + 1,
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Calculate thread stats by type
  const threadStats = {
    LoRa: threads.filter((t) => t.radio_type === 'LoRa').length,
    HaLow: threads.filter((t) => t.radio_type === 'HaLow').length,
    WiFi: threads.filter((t) => t.radio_type === 'WiFi').length,
  };

  // Calculate active (online) nodes
  const activeNodes = nodes.filter((n) => n.status === 'online').length;
  const totalNodes = nodes.length;

  // Format uptime as HH:MM:SS
  const formatUptime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Determine battery color
  const getBatteryColor = (level: number): 'green' | 'yellow' | 'orange' | 'red' => {
    if (level > 75) return 'green';
    if (level > 50) return 'yellow';
    if (level > 25) return 'orange';
    return 'red';
  };

  if (nodesLoading || threadsLoading) {
    return (
      <div style={{ padding: '20px', fontFamily: 'IBM VGA, monospace', color: '#00FFFF' }}>
        Loading system status...
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* System Status Panel */}
      <TeletextPanel title="SYSTEM STATUS" color="cyan">
        <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '16px', lineHeight: '1.8', color: '#00FFFF' }}>
          <div>UPTIME: {formatUptime(metrics.uptime)}</div>
          <div style={{ marginTop: '8px' }}>
            <StatusBar value={metrics.cpuUsage} color="cyan" label="CPU   " />
          </div>
          <div>
            <StatusBar value={metrics.memoryUsage} color="magenta" label="MEMORY" />
          </div>
        </div>
      </TeletextPanel>

      {/* Network Status Panel */}
      <TeletextPanel title="NETWORK STATUS" color="green">
        <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '16px', lineHeight: '1.8', color: '#00FF00' }}>
          <div>ACTIVE NODES: {activeNodes} / {totalNodes}</div>
          <div style={{ marginTop: '12px', color: '#FFFF00' }}>THREAD STATUS:</div>
          <div style={{ paddingLeft: '16px', marginTop: '4px' }}>
            <div>LoRa  : {threadStats.LoRa.toString().padStart(2, '0')} active</div>
            <div>HaLow : {threadStats.HaLow.toString().padStart(2, '0')} active</div>
            <div>WiFi  : {threadStats.WiFi.toString().padStart(2, '0')} active</div>
          </div>
        </div>
      </TeletextPanel>

      {/* Battery & Connection Panel */}
      <TeletextPanel title="POWER & CONNECTION" color="yellow">
        <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '16px', lineHeight: '1.8' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: '#FFFF00' }}>BATTERY:</span>
            <ProgressBar 
              value={metrics.batteryLevel} 
              max={100} 
              color={getBatteryColor(metrics.batteryLevel)}
            />
          </div>
          <div style={{ marginTop: '12px', color: wsConnected ? '#00FF00' : '#FF0000' }}>
            WEBSOCKET: {wsConnected ? '● CONNECTED' : '○ DISCONNECTED'}
          </div>
        </div>
      </TeletextPanel>
    </div>
  );
};

export default StatusPage;
