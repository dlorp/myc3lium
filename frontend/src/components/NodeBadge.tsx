import React from 'react';

type NodeStatus = 'ONLINE' | 'DEGRADED' | 'OFFLINE';

interface Node {
  id: string;
  callsign: string;
  type: string;
  status: NodeStatus;
}

interface NodeBadgeProps {
  node: Node;
}

const statusColorMap: Record<NodeStatus, string> = {
  ONLINE: '#00FFFF',   // cyan
  DEGRADED: '#FF8000', // orange
  OFFLINE: '#808080',  // gray
};

const statusIconMap: Record<NodeStatus, string> = {
  ONLINE: '◉',
  DEGRADED: '◐',
  OFFLINE: '○',
};

export const NodeBadge: React.FC<NodeBadgeProps> = ({ node }) => {
  const statusColor = statusColorMap[node.status];
  const statusIcon = statusIconMap[node.status];

  const displayText = `${statusIcon} ${node.id} // "${node.callsign}"`;
  
  return (
    <span
      style={{
        fontFamily: 'IBM VGA, monospace',
        fontSize: '16px',
        lineHeight: '1.5',
        color: statusColor,
      }}
    >
      {displayText}
    </span>
  );
};

export default NodeBadge;
