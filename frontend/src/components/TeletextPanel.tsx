import React, { ReactNode } from 'react';

type ColorType = 'cyan' | 'magenta' | 'yellow' | 'green';

interface TeletextPanelProps {
  title: string;
  children: ReactNode;
  color?: ColorType;
}

const colorMap: Record<ColorType, string> = {
  cyan: '#00FFFF',
  magenta: '#FF00FF',
  yellow: '#FFFF00',
  green: '#00FF00',
};

export const TeletextPanel: React.FC<TeletextPanelProps> = ({ 
  title, 
  children, 
  color = 'cyan' 
}) => {
  const borderColor = colorMap[color];
  
  return (
    <div
      style={{
        border: `1px solid ${borderColor}`,
        padding: '0',
        fontFamily: 'IBM VGA, monospace',
        backgroundColor: '#000000',
        position: 'relative',
      }}
    >
      <div
        style={{
          color: borderColor,
          padding: '4px 8px',
          borderBottom: `1px solid ${borderColor}`,
          fontSize: '16px',
          lineHeight: '1',
        }}
      >
        ┌─ {title} ─┐
      </div>
      <div style={{ padding: '8px' }}>
        {children}
      </div>
    </div>
  );
};

export default TeletextPanel;
