/**
 * P400 Sensor Grid Utilities
 * Production-ready helpers for telemetry data processing, export, and visualization
 */

export type SortColumn = 'nodeId' | 'temperature' | 'humidity' | 'pressure' | 'aqi' | 'battery' | 'status';
export type AlertLevel = 'GOOD' | 'WARNING' | 'CRITICAL';
export type MetricType = 'temperature' | 'humidity' | 'pressure' | 'battery';

export interface SensorReading {
  nodeId: string;
  callsign: string;
  temperature: number;
  humidity: number;
  pressure: number;
  aqi: number;
  battery: number;
  rssi: number;
  status: AlertLevel;
  tempHistory: number[];
  humidityHistory: number[];
  pressureHistory: number[];
  batteryHistory: number[];
  timestamps: number[];
}

export interface MetricHistoryPoint {
  timestamp: number;
  value: number;
}

/**
 * Calculate Air Quality Index based on sensor metrics
 * Simple formula: (temp_score + humidity_score + pressure_score) / 3
 */
export const calculateAQI = (temp: number, humidity: number, pressure: number): number => {
  // Temperature: ideal 20-25°C
  const tempScore = Math.max(0, 100 - Math.abs(temp - 22.5) * 4);
  
  // Humidity: ideal 40-60%
  const humidityScore = Math.max(0, 100 - Math.abs(humidity - 50) * 2);
  
  // Pressure: ideal 1013 hPa
  const pressureScore = Math.max(0, 100 - Math.abs(pressure - 1013) * 0.1);
  
  return Math.round((tempScore + humidityScore + pressureScore) / 3);
};

/**
 * Determine alert level based on sensor readings
 */
export const getAlertStatus = (temp: number, humidity: number, battery: number): AlertLevel => {
  // Critical thresholds
  if (temp > 35 || humidity > 85 || battery < 10) {
    return 'CRITICAL';
  }
  
  // Warning thresholds
  if (temp > 30 || humidity > 75 || battery < 20) {
    return 'WARNING';
  }
  
  return 'GOOD';
};

/**
 * Get color for a metric value based on type and thresholds
 * Returns hex color code
 */
export const getThresholdColor = (value: number, type: MetricType): string => {
  switch (type) {
    case 'temperature':
      if (value < 10) return '#0080FF'; // Blue - cold
      if (value < 20) return '#00FFFF'; // Cyan - cool
      if (value < 25) return '#00FF00'; // Green - ideal
      if (value < 30) return '#FFFF00'; // Yellow - warm
      if (value < 35) return '#FF8000'; // Orange - hot
      return '#FF0000'; // Red - critical
    
    case 'humidity':
      if (value < 30) return '#FF0000'; // Red - too dry
      if (value < 40) return '#FF8000'; // Orange - dry
      if (value < 60) return '#00FF00'; // Green - ideal
      if (value < 75) return '#FFFF00'; // Yellow - humid
      return '#FF0000'; // Red - critical
    
    case 'pressure':
      if (value < 1000) return '#FF0000'; // Red - low
      if (value < 1010) return '#FF8000'; // Orange - below ideal
      if (value < 1020) return '#00FF00'; // Green - ideal
      return '#FFFF00'; // Yellow - high
    
    case 'battery':
      if (value > 50) return '#00FF00'; // Green
      if (value > 20) return '#FFFF00'; // Yellow
      return '#FF0000'; // Red - critical
    
    default:
      return '#808080'; // Gray
  }
};

/**
 * Get sort function for a given column
 */
export const getSortFunction = (column: SortColumn, ascending: boolean) => {
  return (a: SensorReading, b: SensorReading): number => {
    let aVal: string | number;
    let bVal: string | number;

    switch (column) {
      case 'nodeId':
        aVal = a.nodeId;
        bVal = b.nodeId;
        break;
      case 'temperature':
        aVal = a.temperature;
        bVal = b.temperature;
        break;
      case 'humidity':
        aVal = a.humidity;
        bVal = b.humidity;
        break;
      case 'pressure':
        aVal = a.pressure;
        bVal = b.pressure;
        break;
      case 'aqi':
        aVal = a.aqi;
        bVal = b.aqi;
        break;
      case 'battery':
        aVal = a.battery;
        bVal = b.battery;
        break;
      case 'status':
        const statusOrder = { GOOD: 0, WARNING: 1, CRITICAL: 2 };
        aVal = statusOrder[a.status];
        bVal = statusOrder[b.status];
        break;
      default:
        return 0;
    }

    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }

    const diff = (aVal as number) - (bVal as number);
    return ascending ? diff : -diff;
  };
};

/**
 * Export sensor data to CSV format
 */
export const exportToCSV = (readings: SensorReading[], filename?: string): void => {
  const timestamp = new Date().toISOString();
  const csv_filename = filename || `P400_SensorData_${timestamp.replace(/[:.]/g, '-')}.csv`;

  // CSV header
  const headers = [
    'Node ID',
    'Callsign',
    'Current Temp (°C)',
    'Current Humidity (%)',
    'Current Pressure (hPa)',
    'AQI',
    'Battery (%)',
    'RSSI (dBm)',
    'Status',
    'Temp History (20 points)',
    'Humidity History (20 points)',
    'Pressure History (20 points)',
    'Battery History (20 points)',
  ];

  const rows = readings.map((reading) => [
    reading.nodeId,
    reading.callsign,
    reading.temperature.toFixed(1),
    reading.humidity.toFixed(1),
    reading.pressure.toFixed(1),
    reading.aqi.toString(),
    reading.battery.toFixed(1),
    reading.rssi.toString(),
    reading.status,
    reading.tempHistory.map((v) => v.toFixed(1)).join(';'),
    reading.humidityHistory.map((v) => v.toFixed(1)).join(';'),
    reading.pressureHistory.map((v) => v.toFixed(1)).join(';'),
    reading.batteryHistory.map((v) => v.toFixed(1)).join(';'),
  ]);

  const csvContent = [
    headers.join(','),
    ...rows.map((row) =>
      row
        .map((cell) => {
          // Escape quotes and wrap in quotes if contains comma
          const escaped = String(cell).replace(/"/g, '""');
          return escaped.includes(',') ? `"${escaped}"` : escaped;
        })
        .join(',')
    ),
  ].join('\n');

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', csv_filename);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Smooth interpolation between old and new values
 * Used for smooth animation of metric transitions
 */
export const smoothInterpolation = (oldVal: number, newVal: number, progress: number): number => {
  // Easing function: ease-in-out
  const easeProgress = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
  return oldVal + (newVal - oldVal) * easeProgress;
};
