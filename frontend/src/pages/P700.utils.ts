/**
 * P700 Utilities - Node Log Page
 * Filtering, searching, sorting, and export functions
 */

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  source: string;
  nodeId?: string;
  message: string;
}

export type EventType = 'ALL' | 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';

/**
 * Filter log entries by node ID and event type
 */
export const filterLogEntries = (
  entries: LogEntry[],
  nodeId: string | 'ALL',
  eventType: EventType
): LogEntry[] => {
  return entries.filter((entry) => {
    const nodeMatch = nodeId === 'ALL' || entry.nodeId === nodeId;
    const typeMatch = eventType === 'ALL' || entry.level === eventType;
    return nodeMatch && typeMatch;
  });
};

/**
 * Search log entries by message content
 */
export const searchLogEntries = (
  entries: LogEntry[],
  query: string
): LogEntry[] => {
  if (!query.trim()) return entries;
  const lowerQuery = query.toLowerCase();
  return entries.filter((entry) =>
    entry.message.toLowerCase().includes(lowerQuery) ||
    entry.source.toLowerCase().includes(lowerQuery) ||
    entry.nodeId?.toLowerCase().includes(lowerQuery)
  );
};

/**
 * Get unique node IDs from log entries
 */
export const getUniqueNodeIds = (entries: LogEntry[]): string[] => {
  const nodeIds = new Set<string>();
  entries.forEach((entry) => {
    if (entry.nodeId) nodeIds.add(entry.nodeId);
  });
  return Array.from(nodeIds).sort();
};

/**
 * Export log entries to CSV format
 */
export const exportToCSV = (
  entries: LogEntry[],
  filename: string = 'node-log.csv'
): void => {
  const headers = ['Timestamp', 'Level', 'Source', 'Node ID', 'Message'];
  const rows = entries.map((entry) => [
    entry.timestamp,
    entry.level,
    entry.source,
    entry.nodeId || 'N/A',
    `"${entry.message.replace(/"/g, '""')}"`, // Escape quotes
  ]);

  const csv = [
    headers.join(','),
    ...rows.map((row) => row.join(',')),
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Get severity count statistics
 */
export const getLogStatistics = (entries: LogEntry[]) => {
  const stats = {
    total: entries.length,
    info: 0,
    warning: 0,
    error: 0,
    debug: 0,
  };

  entries.forEach((entry) => {
    stats[entry.level.toLowerCase() as keyof typeof stats]++;
  });

  return stats;
};

/**
 * Format timestamp for display
 */
export const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
};

/**
 * Get color for log level
 */
export const getLevelColor = (level: string): 'cyan' | 'yellow' | 'red' | 'gray' | 'white' => {
  switch (level) {
    case 'INFO': return 'cyan';
    case 'DEBUG': return 'gray';
    case 'WARNING': return 'yellow';
    case 'ERROR': return 'red';
    default: return 'white';
  }
};

/**
 * Get icon for log level
 */
export const getLevelIcon = (level: string): string => {
  switch (level) {
    case 'INFO': return '●';
    case 'DEBUG': return '○';
    case 'WARNING': return '⚠';
    case 'ERROR': return '✖';
    default: return '·';
  }
};
