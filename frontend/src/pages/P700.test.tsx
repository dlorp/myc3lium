import { describe, it, expect } from 'vitest';
import {
  LogEntry,
  filterLogEntries,
  searchLogEntries,
  getUniqueNodeIds,
  getLogStatistics,
  formatTime,
  getLevelColor,
  getLevelIcon,
} from './P700.utils';

describe('P700 Utilities', () => {
  const mockEntries: LogEntry[] = [
    {
      id: '1',
      timestamp: '2024-03-19T00:30:00Z',
      level: 'INFO',
      source: 'NODE',
      nodeId: 'NODE-01',
      message: 'Node online',
    },
    {
      id: '2',
      timestamp: '2024-03-19T00:31:00Z',
      level: 'WARNING',
      source: 'BATTERY',
      nodeId: 'NODE-02',
      message: 'Low battery warning',
    },
    {
      id: '3',
      timestamp: '2024-03-19T00:32:00Z',
      level: 'ERROR',
      source: 'RADIO',
      nodeId: 'NODE-03',
      message: 'Connection lost',
    },
    {
      id: '4',
      timestamp: '2024-03-19T00:33:00Z',
      level: 'DEBUG',
      source: 'TELEMETRY',
      nodeId: 'NODE-01',
      message: 'Sensor data collected',
    },
  ];

  describe('filterLogEntries', () => {
    it('should return all entries when nodeId is ALL and eventType is ALL', () => {
      const result = filterLogEntries(mockEntries, 'ALL', 'ALL');
      expect(result).toHaveLength(4);
    });

    it('should filter by node ID', () => {
      const result = filterLogEntries(mockEntries, 'NODE-01', 'ALL');
      expect(result).toHaveLength(2);
      expect(result.every((e) => e.nodeId === 'NODE-01')).toBe(true);
    });

    it('should filter by event type', () => {
      const result = filterLogEntries(mockEntries, 'ALL', 'INFO');
      expect(result).toHaveLength(1);
      expect(result[0].level).toBe('INFO');
    });

    it('should filter by both node ID and event type', () => {
      const result = filterLogEntries(mockEntries, 'NODE-01', 'INFO');
      expect(result).toHaveLength(1);
      expect(result[0].nodeId).toBe('NODE-01');
      expect(result[0].level).toBe('INFO');
    });
  });

  describe('searchLogEntries', () => {
    it('should return all entries for empty query', () => {
      const result = searchLogEntries(mockEntries, '');
      expect(result).toHaveLength(4);
    });

    it('should search by message content', () => {
      const result = searchLogEntries(mockEntries, 'battery');
      expect(result).toHaveLength(1);
      expect(result[0].message).toContain('battery');
    });

    it('should search by source', () => {
      const result = searchLogEntries(mockEntries, 'BATTERY');
      expect(result).toHaveLength(1);
      expect(result[0].source).toBe('BATTERY');
    });

    it('should be case insensitive', () => {
      const result = searchLogEntries(mockEntries, 'CONNECTION');
      expect(result).toHaveLength(1);
      expect(result[0].message).toContain('Connection');
    });
  });

  describe('getUniqueNodeIds', () => {
    it('should return unique node IDs sorted', () => {
      const result = getUniqueNodeIds(mockEntries);
      expect(result).toEqual(['NODE-01', 'NODE-02', 'NODE-03']);
    });

    it('should handle entries without nodeId', () => {
      const entriesWithoutNode: LogEntry[] = [
        {
          id: '1',
          timestamp: '2024-03-19T00:30:00Z',
          level: 'INFO',
          source: 'SYSTEM',
          message: 'System startup',
        },
      ];
      const result = getUniqueNodeIds(entriesWithoutNode);
      expect(result).toHaveLength(0);
    });
  });

  describe('getLogStatistics', () => {
    it('should count entries by level', () => {
      const result = getLogStatistics(mockEntries);
      expect(result.total).toBe(4);
      expect(result.info).toBe(1);
      expect(result.warning).toBe(1);
      expect(result.error).toBe(1);
      expect(result.debug).toBe(1);
    });
  });

  describe('formatTime', () => {
    it('should format timestamp correctly', () => {
      const result = formatTime('2024-03-19T00:30:45Z');
      expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
    });
  });

  describe('getLevelColor', () => {
    it('should return correct colors for levels', () => {
      expect(getLevelColor('INFO')).toBe('cyan');
      expect(getLevelColor('WARNING')).toBe('yellow');
      expect(getLevelColor('ERROR')).toBe('red');
      expect(getLevelColor('DEBUG')).toBe('gray');
    });
  });

  describe('getLevelIcon', () => {
    it('should return correct icons for levels', () => {
      expect(getLevelIcon('INFO')).toBe('●');
      expect(getLevelIcon('DEBUG')).toBe('○');
      expect(getLevelIcon('WARNING')).toBe('⚠');
      expect(getLevelIcon('ERROR')).toBe('✖');
    });
  });
});
