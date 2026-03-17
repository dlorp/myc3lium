import React from 'react';

type ColorType = 'cyan' | 'magenta' | 'yellow' | 'green' | 'orange' | 'red' | 'gray';

interface StatusBarProps {
  value: number; // 0-100
  color: ColorType;
  label: string;
}

const colorMap: Record<ColorType, string> = {
  cyan: '#00FFFF',
  magenta: '#FF00FF',
  yellow: '#FFFF00',
  green: '#00FF00',
  orange: '#FF8000',
  red: '#FF0000',
  gray: '#808080',
};

export const StatusBar: React.FC<StatusBarProps> = ({ value, color, label }) => {
  const barColor = colorMap[color];
  const clampedValue = Math.max(0, Math.min(100, value));
  const barWidth = `${clampedValue}%`;
  
  // Fill character based on percentage ranges
  const getFillChar = (percentage: number): string => {
    if (percentage >= 75) return '█';
    if (percentage >= 50) return '▓';
    if (percentage >= 25) return '▒';
    return '░';
  };

  const fillChar = getFillChar(clampedValue);
  const numChars = Math.round((clampedValue / 100) * 40); // 40 chars max width
  const barText = fillChar.repeat(numChars).padEnd(40, '░');

  return (
    <div
      style={{
        fontFamily: 'IBM VGA, monospace',
        fontSize: '16px',
        lineHeight: '1.5',
        color: barColor,
      }}
    >
      {label}: {barText}
    </div>
  );
};

export default StatusBar;
