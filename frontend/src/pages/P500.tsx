import React, { useState } from 'react';
import {
  TeletextPanel,
  TeletextText,
  NodeBadge,
  StatusBar,
} from '../components';

interface FrondNode {
  id: string;
  callsign: string;
  type: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  gps: {
    lat: number;
    lon: number;
  };
  signal: number;
  streamUrl: string;
}

/**
 * P500: CameraPage - FROND live streams
 * Displays MJPEG streams from FROND nodes with controls
 */
export const CameraPage: React.FC = () => {
  const [isPaused, setIsPaused] = useState(false);
  const [selectedNode, setSelectedNode] = useState(0);

  // Mock FROND nodes with stream data
  const frondNodes: FrondNode[] = [
    {
      id: 'FROND-01',
      callsign: 'Canopy Watch',
      type: 'FROND',
      status: 'ONLINE',
      gps: { lat: 47.6062, lon: -122.3321 },
      signal: 85,
      streamUrl: 'https://picsum.photos/640/480?random=1',
    },
    {
      id: 'FROND-02',
      callsign: 'Forest Eye',
      type: 'FROND',
      status: 'ONLINE',
      gps: { lat: 47.6101, lon: -122.3420 },
      signal: 72,
      streamUrl: 'https://picsum.photos/640/480?random=2',
    },
  ];

  const activeNode = frondNodes[selectedNode];

  const handlePlayPause = () => {
    setIsPaused(!isPaused);
  };

  const formatGPS = (lat: number, lon: number): string => {
    const latDir = lat >= 0 ? 'N' : 'S';
    const lonDir = lon >= 0 ? 'E' : 'W';
    return `${Math.abs(lat).toFixed(4)}°${latDir} ${Math.abs(lon).toFixed(4)}°${lonDir}`;
  };

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <TeletextPanel title="P500 ─══─ CAMERA FEED ─══─ FROND NETWORK" color="cyan">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Node Selection */}
          <section>
            <TeletextText color="yellow">AVAILABLE STREAMS:</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {frondNodes.map((node, idx) => (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(idx)}
                  style={{
                    cursor: 'pointer',
                    backgroundColor: idx === selectedNode ? '#003333' : 'transparent',
                    padding: '4px',
                  }}
                >
                  <NodeBadge node={node} />
                </div>
              ))}
            </div>
          </section>

          {/* Stream Display */}
          <section>
            <TeletextText color="yellow">LIVE STREAM:</TeletextText>
            <div
              style={{
                marginTop: '8px',
                border: '2px solid #00FFFF',
                backgroundColor: '#111',
                position: 'relative',
                aspectRatio: '4/3',
                maxWidth: '640px',
              }}
            >
              {!isPaused ? (
                <img
                  src={activeNode.streamUrl}
                  alt={`Stream from ${activeNode.callsign}`}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    display: 'block',
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: '#000',
                  }}
                >
                  <TeletextText color="gray">║ PAUSED ║</TeletextText>
                </div>
              )}

              {/* Node Info Overlay */}
              <div
                style={{
                  position: 'absolute',
                  top: '8px',
                  left: '8px',
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  padding: '8px',
                  border: '1px solid #00FFFF',
                }}
              >
                <TeletextText color="cyan">{activeNode.id}</TeletextText>
                <br />
                <TeletextText color="white">GPS: {formatGPS(activeNode.gps.lat, activeNode.gps.lon)}</TeletextText>
                <br />
                <div style={{ marginTop: '4px' }}>
                  <StatusBar value={activeNode.signal} color="green" label="SIGNAL" />
                </div>
              </div>
            </div>
          </section>

          {/* Stream Controls */}
          <section>
            <TeletextText color="yellow">CONTROLS:</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', gap: '12px' }}>
              <button
                onClick={handlePlayPause}
                style={{
                  fontFamily: 'IBM VGA, monospace',
                  fontSize: '16px',
                  padding: '8px 16px',
                  backgroundColor: '#000',
                  color: '#00FFFF',
                  border: '1px solid #00FFFF',
                  cursor: 'pointer',
                }}
              >
                {isPaused ? '▶ PLAY' : '❚❚ PAUSE'}
              </button>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TeletextText color="white">FPS: 30</TeletextText>
                <TeletextText color="gray">|</TeletextText>
                <TeletextText color="white">BITRATE: 2.4 Mbps</TeletextText>
              </div>
            </div>
          </section>

          {/* Node Details */}
          <section>
            <TeletextPanel title={`NODE: ${activeNode.callsign}`} color="magenta">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div>
                  <TeletextText color="white">Node ID: </TeletextText>
                  <TeletextText color="cyan">{activeNode.id}</TeletextText>
                </div>
                <div>
                  <TeletextText color="white">Callsign: </TeletextText>
                  <TeletextText color="cyan">{activeNode.callsign}</TeletextText>
                </div>
                <div>
                  <TeletextText color="white">Type: </TeletextText>
                  <TeletextText color="cyan">{activeNode.type}</TeletextText>
                </div>
                <div>
                  <TeletextText color="white">Status: </TeletextText>
                  <TeletextText color="green">{activeNode.status}</TeletextText>
                </div>
                <div>
                  <TeletextText color="white">Coordinates: </TeletextText>
                  <TeletextText color="cyan">{formatGPS(activeNode.gps.lat, activeNode.gps.lon)}</TeletextText>
                </div>
              </div>
            </TeletextPanel>
          </section>

        </div>
      </TeletextPanel>
    </div>
  );
};

export default CameraPage;
