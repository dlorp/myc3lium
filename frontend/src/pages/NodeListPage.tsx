/**
 * P201: NodeListPage - All Nodes Table
 * 
 * Displays a scrollable table of all nodes with:
 * - Columns: ID, Callsign, Type, Battery, Status
 * - Sort by status or battery
 * - Uses component library from PR #29
 */

import React, { useEffect, useState, useMemo } from 'react';
import TeletextPanel from '../components/TeletextPanel';
import NodeBadge from '../components/NodeBadge';
import StatusBar from '../components/StatusBar';
import useMeshStore from '../store/meshStore';

type SortField = 'id' | 'callsign' | 'type' | 'battery' | 'status';
type SortDirection = 'asc' | 'desc';

const NodeListPage: React.FC = () => {
  const {
    nodes,
    nodesLoading,
    loadAll,
    connectWS,
    disconnectWS,
  } = useMeshStore();

  const [sortField, setSortField] = useState<SortField>('status');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  useEffect(() => {
    loadAll();
    connectWS();

    return () => {
      disconnectWS();
    };
  }, [loadAll, connectWS, disconnectWS]);

  // Sort nodes based on current sort field and direction
  const sortedNodes = useMemo(() => {
    const sorted = [...nodes].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'id':
          comparison = a.id.localeCompare(b.id);
          break;
        case 'callsign':
          comparison = a.callsign.localeCompare(b.callsign);
          break;
        case 'type':
          comparison = a.type.localeCompare(b.type);
          break;
        case 'battery':
          comparison = (a.battery || 0) - (b.battery || 0);
          break;
        case 'status': {
          // Sort priority: online > degraded > offline
          const statusPriority: Record<string, number> = {
            online: 3,
            degraded: 2,
            offline: 1,
          };
          comparison = (statusPriority[a.status] || 0) - (statusPriority[b.status] || 0);
          break;
        }
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [nodes, sortField, sortDirection]);

  // Toggle sort direction or change sort field
  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Map node status to NodeBadge format
  const mapNodeStatus = (status: string): 'ONLINE' | 'DEGRADED' | 'OFFLINE' => {
    const upperStatus = status.toUpperCase();
    if (upperStatus === 'ONLINE') return 'ONLINE';
    if (upperStatus === 'DEGRADED') return 'DEGRADED';
    return 'OFFLINE';
  };

  // Get battery color based on level
  const getBatteryColor = (battery: number | null): 'green' | 'yellow' | 'orange' | 'red' | 'gray' => {
    if (battery === null) return 'gray';
    if (battery > 75) return 'green';
    if (battery > 50) return 'yellow';
    if (battery > 25) return 'orange';
    return 'red';
  };

  // Get sort indicator
  const getSortIndicator = (field: SortField): string => {
    if (field !== sortField) return '';
    return sortDirection === 'asc' ? ' ▲' : ' ▼';
  };

  if (nodesLoading) {
    return (
      <div style={{ padding: '20px', fontFamily: 'IBM VGA, monospace', color: '#00FFFF' }}>
        Loading node list...
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <TeletextPanel title={`NODE LIST (${nodes.length} total)`} color="cyan">
        <div style={{ fontFamily: 'IBM VGA, monospace', fontSize: '14px' }}>
          {/* Table Header */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '100px 150px 100px 100px 120px',
              gap: '8px',
              padding: '8px',
              borderBottom: '1px solid #00FFFF',
              color: '#00FFFF',
              fontWeight: 'bold',
            }}
          >
            <div
              style={{ cursor: 'pointer' }}
              onClick={() => handleSort('id')}
            >
              ID{getSortIndicator('id')}
            </div>
            <div
              style={{ cursor: 'pointer' }}
              onClick={() => handleSort('callsign')}
            >
              CALLSIGN{getSortIndicator('callsign')}
            </div>
            <div
              style={{ cursor: 'pointer' }}
              onClick={() => handleSort('type')}
            >
              TYPE{getSortIndicator('type')}
            </div>
            <div
              style={{ cursor: 'pointer' }}
              onClick={() => handleSort('battery')}
            >
              BATTERY{getSortIndicator('battery')}
            </div>
            <div
              style={{ cursor: 'pointer' }}
              onClick={() => handleSort('status')}
            >
              STATUS{getSortIndicator('status')}
            </div>
          </div>

          {/* Table Body */}
          <div
            style={{
              maxHeight: '500px',
              overflowY: 'auto',
            }}
          >
            {sortedNodes.length === 0 ? (
              <div style={{ padding: '16px', color: '#808080', textAlign: 'center' }}>
                No nodes available
              </div>
            ) : (
              sortedNodes.map((node) => (
                <div
                  key={node.id}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '100px 150px 100px 100px 120px',
                    gap: '8px',
                    padding: '8px',
                    borderBottom: '1px solid #333333',
                  }}
                >
                  {/* ID */}
                  <div style={{ color: '#AAAAAA', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {node.id.slice(0, 8)}
                  </div>

                  {/* Callsign */}
                  <div style={{ color: '#FFFF00' }}>
                    {node.callsign}
                  </div>

                  {/* Type */}
                  <div style={{ color: '#00FFFF' }}>
                    {node.type}
                  </div>

                  {/* Battery */}
                  <div>
                    {node.battery !== null ? (
                      <StatusBar
                        value={node.battery}
                        color={getBatteryColor(node.battery)}
                        label=""
                      />
                    ) : (
                      <span style={{ color: '#808080' }}>N/A</span>
                    )}
                  </div>

                  {/* Status */}
                  <div>
                    <NodeBadge
                      node={{
                        id: node.id,
                        callsign: node.callsign,
                        type: node.type,
                        status: mapNodeStatus(node.status),
                      }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer with stats */}
          <div
            style={{
              marginTop: '16px',
              padding: '8px',
              borderTop: '1px solid #00FFFF',
              color: '#00FFFF',
              display: 'flex',
              gap: '24px',
            }}
          >
            <div>
              ONLINE: {nodes.filter((n) => n.status === 'online').length}
            </div>
            <div style={{ color: '#FF8000' }}>
              DEGRADED: {nodes.filter((n) => n.status === 'degraded').length}
            </div>
            <div style={{ color: '#808080' }}>
              OFFLINE: {nodes.filter((n) => n.status === 'offline').length}
            </div>
          </div>

          {/* Sort instructions */}
          <div
            style={{
              marginTop: '12px',
              fontSize: '12px',
              color: '#888888',
              fontStyle: 'italic',
            }}
          >
            Click column headers to sort
          </div>
        </div>
      </TeletextPanel>
    </div>
  );
};

export default NodeListPage;
