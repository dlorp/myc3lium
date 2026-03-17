import React from 'react';

type ColorType = 'cyan' | 'magenta' | 'yellow' | 'green' | 'orange' | 'red' | 'gray';

interface ProgressBarProps {
  value: number;
  max: number;
  color: ColorType;
  showPercentage?: boolean;
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

export const ProgressBar: React.FC<ProgressBarProps> = ({ 
  value, 
  max, 
  color, 
  showPercentage = true 
}) => {
  const barColor = colorMap[color];
  const percentage = Math.max(0, Math.min(100, (value / max) * 100));
  
  const barLength = 10; // Total bar width in characters
  const filled = Math.round((percentage / 100) * barLength);
  const empty = barLength - filled;
  
  const filledChars = '█'.repeat(filled);
  const emptyChars = '░'.repeat(empty);
  
  const percentageText = showPercentage ? ` ${Math.round(percentage)}%` : '';

  return (
    <span
      style={{
        fontFamily: 'IBM VGA, monospace',
        fontSize: '16px',
        lineHeight: '1.5',
        color: barColor,
      }}
    >
      [{filledChars}{emptyChars}]{percentageText}
    </span>
  );
};

export default ProgressBar;
