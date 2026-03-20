import { describe, it, expect, beforeEach } from 'vitest';
import {
  calculateAQI,
  getAlertStatus,
  getThresholdColor,
  getSortFunction,
  exportToCSV,
  type SensorReading,
} from './P400.utils';

describe('P400 - Sensor Grid Utilities', () => {
  describe('calculateAQI', () => {
    it('should calculate AQI correctly for ideal conditions', () => {
      const aqi = calculateAQI(22.5, 50, 1013);
      expect(aqi).toBeGreaterThan(95); // Should be very high for ideal conditions
    });

    it('should return lower AQI for extreme temperatures', () => {
      const aqiHot = calculateAQI(40, 50, 1013);
      const aqiIdeal = calculateAQI(22.5, 50, 1013);
      expect(aqiHot).toBeLessThan(aqiIdeal);
    });

    it('should handle low humidity', () => {
      const aqi = calculateAQI(22.5, 20, 1013);
      expect(aqi).toBeLessThan(90);
    });

    it('should handle high humidity', () => {
      const aqi = calculateAQI(22.5, 80, 1013);
      expect(aqi).toBeLessThan(90);
    });

    it('should return numeric value between 0 and 100', () => {
      const aqi = calculateAQI(0, 0, 900);
      expect(aqi).toBeGreaterThanOrEqual(0);
      expect(aqi).toBeLessThanOrEqual(100);
    });
  });

  describe('getAlertStatus', () => {
    it('should return GOOD for safe values', () => {
      const status = getAlertStatus(22, 50, 50);
      expect(status).toBe('GOOD');
    });

    it('should return WARNING for elevated temperature', () => {
      const status = getAlertStatus(31, 50, 50);
      expect(status).toBe('WARNING');
    });

    it('should return WARNING for high humidity', () => {
      const status = getAlertStatus(22, 76, 50);
      expect(status).toBe('WARNING');
    });

    it('should return WARNING for low battery', () => {
      const status = getAlertStatus(22, 50, 19);
      expect(status).toBe('WARNING');
    });

    it('should return CRITICAL for critical temperature', () => {
      const status = getAlertStatus(36, 50, 50);
      expect(status).toBe('CRITICAL');
    });

    it('should return CRITICAL for critical humidity', () => {
      const status = getAlertStatus(22, 86, 50);
      expect(status).toBe('CRITICAL');
    });

    it('should return CRITICAL for critical battery', () => {
      const status = getAlertStatus(22, 50, 9);
      expect(status).toBe('CRITICAL');
    });
  });

  describe('getThresholdColor', () => {
    it('should return blue for cold temperature', () => {
      expect(getThresholdColor(5, 'temperature')).toBe('#0080FF');
    });

    it('should return green for ideal temperature', () => {
      expect(getThresholdColor(23, 'temperature')).toBe('#00FF00');
    });

    it('should return red for critical temperature', () => {
      expect(getThresholdColor(36, 'temperature')).toBe('#FF0000');
    });

    it('should return green for ideal humidity', () => {
      expect(getThresholdColor(50, 'humidity')).toBe('#00FF00');
    });

    it('should return red for very dry humidity', () => {
      expect(getThresholdColor(20, 'humidity')).toBe('#FF0000');
    });

    it('should return green for ideal pressure', () => {
      expect(getThresholdColor(1013, 'pressure')).toBe('#00FF00');
    });

    it('should return green for healthy battery', () => {
      expect(getThresholdColor(75, 'battery')).toBe('#00FF00');
    });

    it('should return red for critical battery', () => {
      expect(getThresholdColor(5, 'battery')).toBe('#FF0000');
    });
  });

  describe('getSortFunction', () => {
    let readings: SensorReading[];

    beforeEach(() => {
      readings = [
        {
          nodeId: 'NODE-C',
          callsign: 'Charlie',
          temperature: 25,
          humidity: 50,
          pressure: 1013,
          aqi: 80,
          battery: 75,
          rssi: -70,
          status: 'GOOD',
          tempHistory: Array(20).fill(25),
          humidityHistory: Array(20).fill(50),
          pressureHistory: Array(20).fill(1013),
          batteryHistory: Array(20).fill(75),
          timestamps: Array(20).fill(Date.now()),
        },
        {
          nodeId: 'NODE-A',
          callsign: 'Alpha',
          temperature: 20,
          humidity: 45,
          pressure: 1010,
          aqi: 85,
          battery: 80,
          rssi: -75,
          status: 'GOOD',
          tempHistory: Array(20).fill(20),
          humidityHistory: Array(20).fill(45),
          pressureHistory: Array(20).fill(1010),
          batteryHistory: Array(20).fill(80),
          timestamps: Array(20).fill(Date.now()),
        },
        {
          nodeId: 'NODE-B',
          callsign: 'Bravo',
          temperature: 30,
          humidity: 55,
          pressure: 1015,
          aqi: 75,
          battery: 50,
          rssi: -80,
          status: 'WARNING',
          tempHistory: Array(20).fill(30),
          humidityHistory: Array(20).fill(55),
          pressureHistory: Array(20).fill(1015),
          batteryHistory: Array(20).fill(50),
          timestamps: Array(20).fill(Date.now()),
        },
      ];
    });

    it('should sort by nodeId ascending', () => {
      const sortFn = getSortFunction('nodeId', true);
      const sorted = [...readings].sort(sortFn);
      expect(sorted[0].nodeId).toBe('NODE-A');
      expect(sorted[1].nodeId).toBe('NODE-B');
      expect(sorted[2].nodeId).toBe('NODE-C');
    });

    it('should sort by nodeId descending', () => {
      const sortFn = getSortFunction('nodeId', false);
      const sorted = [...readings].sort(sortFn);
      expect(sorted[0].nodeId).toBe('NODE-C');
      expect(sorted[1].nodeId).toBe('NODE-B');
      expect(sorted[2].nodeId).toBe('NODE-A');
    });

    it('should sort by temperature ascending', () => {
      const sortFn = getSortFunction('temperature', true);
      const sorted = [...readings].sort(sortFn);
      expect(sorted[0].temperature).toBe(20);
      expect(sorted[2].temperature).toBe(30);
    });

    it('should sort by battery descending', () => {
      const sortFn = getSortFunction('battery', false);
      const sorted = [...readings].sort(sortFn);
      expect(sorted[0].battery).toBe(80);
      expect(sorted[2].battery).toBe(50);
    });

    it('should sort by status with proper order (GOOD -> WARNING -> CRITICAL)', () => {
      const reading3: SensorReading = {
        ...readings[0],
        nodeId: 'NODE-D',
        status: 'CRITICAL',
      };

      const testReadings = [...readings, reading3];
      const sortFn = getSortFunction('status', true);
      const sorted = testReadings.sort(sortFn);
      expect(sorted[0].status).toBe('GOOD');
      expect(sorted[sorted.length - 1].status).toBe('CRITICAL');
    });
  });

  describe('exportToCSV', () => {
    let readings: SensorReading[];

    beforeEach(() => {
      readings = [
        {
          nodeId: 'NODE-001',
          callsign: 'TestNode',
          temperature: 22.5,
          humidity: 50,
          pressure: 1013,
          aqi: 80,
          battery: 85,
          rssi: -70,
          status: 'GOOD',
          tempHistory: [20, 21, 22, 23, 24, 25],
          humidityHistory: [45, 48, 50, 52, 55],
          pressureHistory: Array(5).fill(1013),
          batteryHistory: Array(5).fill(85),
          timestamps: Array(5).fill(Date.now()),
        },
      ];

      // Mock URL.createObjectURL and document methods
      global.URL.createObjectURL = () => 'blob:mock-url';
      global.document.createElement = (tag) => {
        if (tag === 'a') {
          return {
            setAttribute: () => {},
            click: () => {},
            style: {},
          } as HTMLElement;
        }
        return {} as HTMLElement;
      };
      // Mock body methods without replacing body itself
      document.body.appendChild = (() => {}) as any;
      document.body.removeChild = (() => {}) as any;
    });

    it('should export data without errors', () => {
      expect(() => {
        exportToCSV(readings, 'test.csv');
      }).not.toThrow();
    });

    it('should handle multiple readings', () => {
      const moreReadings = [
        ...readings,
        {
          ...readings[0],
          nodeId: 'NODE-002',
          callsign: 'TestNode2',
        },
      ];

      expect(() => {
        exportToCSV(moreReadings);
      }).not.toThrow();
    });

    it('should use provided filename', () => {
      const filename = 'custom_export.csv';
      let capturedFilename = '';

      global.document.createElement = (tag) => {
        if (tag === 'a') {
          return {
            setAttribute: (attr: string, value: string) => {
              if (attr === 'download') capturedFilename = value;
            },
            click: () => {},
            style: {},
          } as HTMLElement;
        }
        return {} as HTMLElement;
      };

      exportToCSV(readings, filename);
      expect(capturedFilename).toBe(filename);
    });

    it('should generate filename with timestamp if not provided', () => {
      let capturedFilename = '';

      global.document.createElement = (tag) => {
        if (tag === 'a') {
          return {
            setAttribute: (attr: string, value: string) => {
              if (attr === 'download') capturedFilename = value;
            },
            click: () => {},
            style: {},
          } as HTMLElement;
        }
        return {} as HTMLElement;
      };

      exportToCSV(readings);
      expect(capturedFilename).toContain('P400_SensorData_');
      expect(capturedFilename).toContain('.csv');
    });
  });

  describe('Integration Tests', () => {
    it('should handle full sensor reading workflow', () => {
      const reading: SensorReading = {
        nodeId: 'TEST-001',
        callsign: 'Integration',
        temperature: 25,
        humidity: 55,
        pressure: 1013,
        aqi: 0,
        battery: 75,
        rssi: -75,
        status: 'GOOD',
        tempHistory: Array(20).fill(25),
        humidityHistory: Array(20).fill(55),
        pressureHistory: Array(20).fill(1013),
        batteryHistory: Array(20).fill(75),
        timestamps: Array(20).fill(Date.now()),
      };

      // Calculate AQI
      const aqi = calculateAQI(reading.temperature, reading.humidity, reading.pressure);
      reading.aqi = aqi;

      // Get alert status
      const status = getAlertStatus(reading.temperature, reading.humidity, reading.battery);
      reading.status = status;

      // Get colors
      const tempColor = getThresholdColor(reading.temperature, 'temperature');
      const batColor = getThresholdColor(reading.battery, 'battery');

      expect(reading.aqi).toBeGreaterThan(0);
      expect(reading.status).toBe('GOOD');
      expect(tempColor).toBeDefined();
      expect(batColor).toBeDefined();
    });

    it('should handle sorting mixed status readings', () => {
      const readings: SensorReading[] = [
        {
          nodeId: 'NODE-1',
          callsign: 'Alpha',
          temperature: 20,
          humidity: 50,
          pressure: 1013,
          aqi: 85,
          battery: 90,
          rssi: -70,
          status: 'GOOD',
          tempHistory: Array(20).fill(20),
          humidityHistory: Array(20).fill(50),
          pressureHistory: Array(20).fill(1013),
          batteryHistory: Array(20).fill(90),
          timestamps: Array(20).fill(Date.now()),
        },
        {
          nodeId: 'NODE-2',
          callsign: 'Bravo',
          temperature: 32,
          humidity: 60,
          pressure: 1010,
          aqi: 60,
          battery: 15,
          rssi: -85,
          status: 'CRITICAL',
          tempHistory: Array(20).fill(32),
          humidityHistory: Array(20).fill(60),
          pressureHistory: Array(20).fill(1010),
          batteryHistory: Array(20).fill(15),
          timestamps: Array(20).fill(Date.now()),
        },
        {
          nodeId: 'NODE-3',
          callsign: 'Charlie',
          temperature: 28,
          humidity: 70,
          pressure: 1015,
          aqi: 70,
          battery: 35,
          rssi: -75,
          status: 'WARNING',
          tempHistory: Array(20).fill(28),
          humidityHistory: Array(20).fill(70),
          pressureHistory: Array(20).fill(1015),
          batteryHistory: Array(20).fill(35),
          timestamps: Array(20).fill(Date.now()),
        },
      ];

      // Sort by status
      const sortFn = getSortFunction('status', true);
      const sorted = [...readings].sort(sortFn);

      // Status order should be GOOD -> WARNING -> CRITICAL
      expect(sorted[0].status).toBe('GOOD');
      expect(sorted[1].status).toBe('WARNING');
      expect(sorted[2].status).toBe('CRITICAL');
    });
  });
});
