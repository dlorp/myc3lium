import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import '../styles/teletext.css';

/**
 * P900 - Intelligence Dashboard
 * 
 * Real-time intelligence gathering and visualization:
 * - Mesh topology (force-directed graph)
 * - RSSI heatmap overlay
 * - Position tracking
 * - RF source detection
 * - ATAK integration status
 */

interface MeshNode {
  id: string;
  position: { lat: number; lon: number; alt: number };
  radio: 'lora' | 'halow' | 'wifi';
  rssi: number;
  neighbors: string[];
}

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
  const [meshNodes, setMeshNodes] = useState<MeshNode[]>([]);
  const [rfSources, setRFSources] = useState<RFSource[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapPoint[]>([]);
  const [atakConnected, setAtakConnected] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/intelligence');
    
    ws.onopen = () => {
      console.log('Intelligence WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'topology_update':
          setMeshNodes(data.nodes);
          break;
        case 'rssi_measurement':
          updateHeatmap(data);
          break;
        case 'rf_source_detected':
          setRFSources(prev => [...prev, data.source]);
          break;
        case 'atak_status':
          setAtakConnected(data.connected);
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    wsRef.current = ws;
    
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

  // 3D mesh topology visualization
  useEffect(() => {
    if (!canvasRef.current || meshNodes.length === 0) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      canvasRef.current.width / canvasRef.current.height,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current });

    // Create nodes
    meshNodes.forEach((node, idx) => {
      const geometry = new THREE.SphereGeometry(0.5, 16, 16);
      
      // Color by radio type
      const colors = {
        lora: 0xff0000,
        halow: 0x00ff00,
        wifi: 0x0000ff
      };
      
      const material = new THREE.MeshBasicMaterial({
        color: colors[node.radio]
      });
      
      const sphere = new THREE.Mesh(geometry, material);
      
      // Position nodes in 3D space (layout algorithm)
      sphere.position.set(
        Math.cos(idx * 0.5) * 5,
        Math.sin(idx * 0.3) * 3,
        idx * 0.2 - meshNodes.length * 0.1
      );
      
      scene.add(sphere);
      
      // Create edges to neighbors
      node.neighbors.forEach(neighborId => {
        const neighborIdx = meshNodes.findIndex(n => n.id === neighborId);
        if (neighborIdx > idx) {  // Avoid duplicate edges
          const points = [
            sphere.position,
            new THREE.Vector3(
              Math.cos(neighborIdx * 0.5) * 5,
              Math.sin(neighborIdx * 0.3) * 3,
              neighborIdx * 0.2 - meshNodes.length * 0.1
            )
          ];
          
          const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
          const lineMaterial = new THREE.LineBasicMaterial({
            color: 0xffffff,
            opacity: 0.3,
            transparent: true
          });
          
          const line = new THREE.Line(lineGeometry, lineMaterial);
          scene.add(line);
        }
      });
    });

    camera.position.z = 15;

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      scene.rotation.y += 0.005;
      renderer.render(scene, camera);
    };

    animate();

    return () => {
      renderer.dispose();
    };
  }, [meshNodes]);

  return (
    <div className="teletext-page">
      <div className="teletext-header">
        <span className="teletext-title">P900</span>
        <span className="teletext-separator">│</span>
        <span>INTELLIGENCE</span>
        <span className="teletext-separator">│</span>
        <span className={`status-${atakConnected ? 'online' : 'offline'}`}>
          ATAK {atakConnected ? 'CONNECTED' : 'OFFLINE'}
        </span>
      </div>

      <div className="intelligence-grid">
        {/* Mesh Topology Visualization */}
        <div className="panel topology-panel">
          <div className="panel-header">MESH TOPOLOGY</div>
          <canvas 
            ref={canvasRef} 
            width={600} 
            height={400}
            className="topology-canvas"
          />
          <div className="topology-legend">
            <span className="legend-item">
              <span className="legend-color" style={{background: '#ff0000'}}></span>
              LoRa
            </span>
            <span className="legend-item">
              <span className="legend-color" style={{background: '#00ff00'}}></span>
              HaLow
            </span>
            <span className="legend-item">
              <span className="legend-color" style={{background: '#0000ff'}}></span>
              WiFi
            </span>
          </div>
        </div>

        {/* RF Sources List */}
        <div className="panel rf-sources-panel">
          <div className="panel-header">RF SOURCES DETECTED</div>
          <div className="rf-sources-list">
            {rfSources.length === 0 ? (
              <div className="no-data">No RF sources detected</div>
            ) : (
              <table className="rf-table">
                <thead>
                  <tr>
                    <th>FREQ (MHz)</th>
                    <th>RSSI</th>
                    <th>POSITION</th>
                    <th>AGE</th>
                  </tr>
                </thead>
                <tbody>
                  {rfSources.slice(-10).reverse().map(source => (
                    <tr key={source.id}>
                      <td>{(source.frequency / 1e6).toFixed(3)}</td>
                      <td>{source.rssi} dBm</td>
                      <td>
                        {source.position 
                          ? `${source.position.lat.toFixed(4)}, ${source.position.lon.toFixed(4)}`
                          : 'Unknown'
                        }
                      </td>
                      <td>{Math.floor((Date.now() - source.timestamp) / 1000)}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Node Status */}
        <div className="panel nodes-panel">
          <div className="panel-header">MESH NODES ({meshNodes.length})</div>
          <div className="nodes-list">
            {meshNodes.map(node => (
              <div key={node.id} className="node-item">
                <span className="node-id">{node.id}</span>
                <span className={`node-radio radio-${node.radio}`}>
                  {node.radio.toUpperCase()}
                </span>
                <span className="node-rssi">
                  {node.rssi} dBm
                </span>
                <span className="node-neighbors">
                  {node.neighbors.length} link{node.neighbors.length !== 1 ? 's' : ''}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* RSSI Heatmap */}
        <div className="panel heatmap-panel">
          <div className="panel-header">SIGNAL STRENGTH HEATMAP</div>
          <div className="heatmap-container">
            {heatmapData.length > 0 ? (
              <div className="heatmap-points">
                {heatmapData.map((point, idx) => {
                  // Simple ASCII heatmap representation
                  const intensity = Math.floor((point.value + 120) / 5);  // Normalize -120 to 0 dBm
                  const char = intensity > 10 ? '█' : intensity > 5 ? '▓' : intensity > 2 ? '░' : '·';
                  
                  return (
                    <span key={idx} className="heatmap-point">
                      {char}
                    </span>
                  );
                })}
              </div>
            ) : (
              <div className="no-data">No signal data collected</div>
            )}
          </div>
        </div>

        {/* ATAK Integration Status */}
        <div className="panel atak-panel">
          <div className="panel-header">ATAK INTEGRATION</div>
          <div className="atak-status">
            <div className="status-row">
              <span>Status:</span>
              <span className={atakConnected ? 'status-good' : 'status-bad'}>
                {atakConnected ? '● CONNECTED' : '○ DISCONNECTED'}
              </span>
            </div>
            <div className="status-row">
              <span>Video Feeds:</span>
              <span>{meshNodes.filter(n => n.id.includes('cam')).length}</span>
            </div>
            <div className="status-row">
              <span>CoT Messages Sent:</span>
              <span>--</span>
            </div>
            <div className="status-row">
              <span>Multicast Group:</span>
              <span>239.2.3.1:6969</span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .intelligence-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          grid-template-rows: auto auto auto;
          gap: 1rem;
          padding: 1rem;
        }

        .panel {
          border: 2px solid #0f0;
          background: #000;
          padding: 0.5rem;
        }

        .panel-header {
          color: #0f0;
          font-weight: bold;
          margin-bottom: 0.5rem;
          border-bottom: 1px solid #0f0;
          padding-bottom: 0.25rem;
        }

        .topology-panel {
          grid-column: 1 / 2;
          grid-row: 1 / 3;
        }

        .topology-canvas {
          width: 100%;
          background: #000;
          border: 1px solid #0a0;
        }

        .topology-legend {
          display: flex;
          gap: 1rem;
          margin-top: 0.5rem;
          font-size: 0.8rem;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .legend-color {
          display: inline-block;
          width: 1rem;
          height: 1rem;
          border: 1px solid #0f0;
        }

        .rf-sources-panel {
          grid-column: 2 / 3;
          grid-row: 1 / 2;
        }

        .rf-table {
          width: 100%;
          font-size: 0.8rem;
          border-collapse: collapse;
        }

        .rf-table th {
          color: #0f0;
          text-align: left;
          border-bottom: 1px solid #0a0;
          padding: 0.25rem;
        }

        .rf-table td {
          color: #0f0;
          padding: 0.25rem;
        }

        .nodes-panel {
          grid-column: 2 / 3;
          grid-row: 2 / 3;
        }

        .nodes-list {
          max-height: 300px;
          overflow-y: auto;
          font-size: 0.8rem;
        }

        .node-item {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
          gap: 0.5rem;
          padding: 0.25rem;
          border-bottom: 1px solid #0a0;
        }

        .node-id {
          color: #0f0;
        }

        .node-radio {
          font-weight: bold;
        }

        .radio-lora { color: #f00; }
        .radio-halow { color: #0f0; }
        .radio-wifi { color: #00f; }

        .heatmap-panel {
          grid-column: 1 / 2;
          grid-row: 3 / 4;
        }

        .heatmap-points {
          font-family: monospace;
          line-height: 1;
          letter-spacing: 0.1em;
          color: #0f0;
        }

        .atak-panel {
          grid-column: 2 / 3;
          grid-row: 3 / 4;
        }

        .atak-status {
          font-size: 0.9rem;
        }

        .status-row {
          display: flex;
          justify-content: space-between;
          padding: 0.25rem 0;
          border-bottom: 1px solid #0a0;
        }

        .status-good { color: #0f0; }
        .status-bad { color: #f00; }

        .no-data {
          color: #666;
          text-align: center;
          padding: 2rem;
        }

        .status-online { color: #0f0; }
        .status-offline { color: #f00; }
      `}</style>
    </div>
  );
};

export default P900;
