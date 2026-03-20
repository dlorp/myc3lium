import React, { useEffect, useRef } from 'react';

type ColorType = 'cyan' | 'magenta' | 'yellow' | 'green' | 'blue' | 'white' | 'red' | 'orange';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: ColorType;
}

const colorMap: Record<ColorType, string> = {
  cyan: '#00FFFF',
  magenta: '#FF00FF',
  yellow: '#FFFF00',
  green: '#00FF00',
  blue: '#0080FF',
  white: '#FFFFFF',
  red: '#FF0000',
  orange: '#FF8000',
};

export const Sparkline: React.FC<SparklineProps> = ({ 
  data, 
  width = 120, 
  height = 30, 
  color = 'cyan' 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const lineColor = colorMap[color];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Find min/max for scaling
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1; // Prevent division by zero

    // Draw line
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.beginPath();

    data.forEach((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();
  }, [data, width, height, lineColor]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        display: 'inline-block',
        verticalAlign: 'middle',
        imageRendering: 'pixelated',
      }}
    />
  );
};

export default Sparkline;
