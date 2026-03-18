/**
 * P200: LatticeMapPage - Mesh Topology Graph
 * 
 * Displays a visual graph of the mesh network topology:
 * - Nodes are color-coded by type
 * - Threads (connections) are color-coded by quality
 * - Click on nodes to view details
 */

import React, { useEffect, useState } from 'react';
import TeletextPanel from '../components/TeletextPanel';
import NodeBadge from '../components/NodeBadge';
import ThreadIndicator from '../components/ThreadIndicator';
import useMeshStore from '../store/meshStore';
import type { Node, Thread } from '../services/api';

const LatticeMapPage: React.FC = () => {
  const {
    nodes,
    threads,
    nodesLoading,
    threadsLoading,
    loadAll,
    connectWS,
    disconnectWS,
  } = useMeshStore();

  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  useEffect(() => {
    loadAll();
    connectWS();

    return () => {
      disconnectWS();
    };
  }, [loadAll, connectWS, disconnectWS]);

  // Map node status to NodeBadge status format
  const mapNodeStatus = (status: string): 'ONLINE' | 'DEGRADED' | 'OFFLINE' => {
    const upperStatus = status.toUpperCase();
    if (upperStatus === 'ONLINE') return 'ONLINE';
    if (upperStatus === 'DEGRADED') return 'DEGRADED';
    return 'OFFLINE';
  };

  // Map thread quality (0-100) to ThreadIndicator quality
  const mapThreadQuality = (quality: number): 'GOOD' | 'FAIR' | 'DEGRADED' => {
    if (quality >= 75) return 'GOOD';
    if (quality >= 40) return 'FAIR';
    return 'DEGRADED';
  };

  // Get node type color
  const getNodeTypeColor = (type: string): string => {
    switch (type) {
      case 'SPORE':
        return '#00FFFF'; // cyan
      case 'HYPHA':
        return '#FF00FF'; // magenta
      case 'FROND':
        return '#FFFF00'; // yellow
      case 'RHIZOME':
        return '#00FF00'; // green
      default:
        return '#FFFFFF'; // white
    }
  };

  // Get thread type symbol
  const getThreadSymbol = (radioType: string): string => {
    switch (radioType) {
      case 'LoRa':
        return '~';
      case 'HaLow':
        return '≈';
      case 'WiFi':
        return '━';
      default:
        return '-';
    }
  };

  // Find threads for a specific node
  const getNodeThreads = (nodeId: string): Thread[] => {
    return threads.filter(
      (t) => t.source_id === nodeId || t.target_id === nodeId
    );
  };

  if (nodesLoading || threadsLoading) {
    return (
      <div style={{ padding: '20px', fontFamily: 'IBM VGA, monospace', color: '#00FFFF' }}>
        Loading lattice map...
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Topology Graph Panel */}
      <TeletextPanel title="MESH TOPOLOGY" color="cyan">
        <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '16px', lineHeight: '1.8' }}>
          {nodes.length === 0 ? (
            <div style={{ color: '#808080' }}>No nodes in network</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {nodes.map((node) => {
                const nodeThreads = getNodeThreads(node.id);
                const typeColor = getNodeTypeColor(node.type);
                
                return (
                  <div key={node.id}>
                    <div
                      style={{
                        cursor: 'pointer',
                        padding: '4px',
                        backgroundColor: selectedNode?.id === node.id ? '#222222' : 'transparent',
                      }}
                      onClick={() => setSelectedNode(node)}
                    >
                      <span style={{ color: typeColor }}>
                        [{node.type}]
                      </span>{' '}
                      <NodeBadge
                        node={{
                          id: node.id,
                          callsign: node.callsign,
                          type: node.type,
                          status: mapNodeStatus(node.status),
                        }}
                      />
                    </div>
                    {/* Show threads for this node */}
                    {nodeThreads.length > 0 && (
                      <div style={{ paddingLeft: '32px', fontSize: '14px' }}>
                        {nodeThreads.map((thread) => {
                          const isSource = thread.source_id === node.id;
                          const peerId = isSource ? thread.target_id : thread.source_id;
                          const peerNode = nodes.find((n) => n.id === peerId);
                          const symbol = getThreadSymbol(thread.radio_type);
                          
                          return (
                            <div key={thread.id} style={{ color: '#888888' }}>
                              {symbol.repeat(3)} <ThreadIndicator quality={mapThreadQuality(thread.quality)} />{' '}
                              <span style={{ color: '#AAAAAA' }}>
                                {thread.radio_type} → {peerNode?.callsign || peerId}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </TeletextPanel>

      {/* Node Details Panel (shown when node selected) */}
      {selectedNode && (
        <TeletextPanel title="NODE DETAILS" color="magenta">
          <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '16px', lineHeight: '1.8', color: '#FF00FF' }}>
            <div>ID       : {selectedNode.id}</div>
            <div>CALLSIGN : {selectedNode.callsign}</div>
            <div>TYPE     : {selectedNode.type}</div>
            <div>STATUS   : {selectedNode.status.toUpperCase()}</div>
            {selectedNode.rssi !== null && (
              <div>RSSI     : {selectedNode.rssi} dBm</div>
            )}
            {selectedNode.battery !== null && (
              <div>BATTERY  : {selectedNode.battery}%</div>
            )}
            <div>LAST SEEN: {new Date(selectedNode.last_seen).toLocaleString()}</div>
            {selectedNode.position && (
              <div>
                POSITION : {selectedNode.position.lat.toFixed(6)}, {selectedNode.position.lon.toFixed(6)}
              </div>
            )}
            <div style={{ marginTop: '12px', color: '#00FFFF' }}>
              THREADS  : {getNodeThreads(selectedNode.id).length} active
            </div>
          </div>
        </TeletextPanel>
      )}

      {/* Legend */}
      <TeletextPanel title="LEGEND" color="yellow">
        <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '14px', lineHeight: '1.6' }}>
          <div style={{ marginBottom: '8px', color: '#FFFF00' }}>NODE TYPES:</div>
          <div style={{ paddingLeft: '16px' }}>
            <div><span style={{ color: '#00FFFF' }}>SPORE</span> - Sensor node</div>
            <div><span style={{ color: '#FF00FF' }}>HYPHA</span> - Router node</div>
            <div><span style={{ color: '#FFFF00' }}>FROND</span> - Edge node</div>
            <div><span style={{ color: '#00FF00' }}>RHIZOME</span> - Gateway</div>
          </div>
          <div style={{ marginTop: '8px', marginBottom: '8px', color: '#FFFF00' }}>THREAD TYPES:</div>
          <div style={{ paddingLeft: '16px' }}>
            <div>~ LoRa</div>
            <div>≈ HaLow</div>
            <div>━ WiFi</div>
          </div>
        </div>
      </TeletextPanel>
    </div>
  );
};

export default LatticeMapPage;
