import React, { ReactNode, CSSProperties } from 'react';

type ColorType = 'cyan' | 'magenta' | 'yellow' | 'green' | 'blue' | 'white' | 'gray' | 'red';

interface TeletextTextProps {
  color: ColorType;
  children: ReactNode;
  blink?: boolean;
}

const colorMap: Record<ColorType, string> = {
  cyan: '#00FFFF',
  magenta: '#FF00FF',
  yellow: '#FFFF00',
  green: '#00FF00',
  blue: '#0080FF',
  white: '#FFFFFF',
  gray: '#808080',
  red: '#FF0000',
};

export const TeletextText: React.FC<TeletextTextProps> = ({ 
  color, 
  children, 
  blink = false 
}) => {
  const textColor = colorMap[color];
  
  const style: CSSProperties = {
    color: textColor,
    fontFamily: 'IBM VGA, monospace',
    fontSize: '16px',
    lineHeight: '1.5',
  };

  if (blink) {
    style.animation = 'blink 1s step-start infinite';
  }

  return (
    <>
      <style>{`
        @keyframes blink {
          50% { opacity: 0; }
        }
      `}</style>
      <span style={style}>{children}</span>
    </>
  );
};

export default TeletextText;
