import React from 'react';

type QualityType = 'GOOD' | 'FAIR' | 'DEGRADED';

interface ThreadIndicatorProps {
  quality: QualityType;
}

const qualityMap: Record<QualityType, { filled: number; color: string }> = {
  GOOD: { filled: 5, color: '#00FFFF' },      // cyan, all dots filled
  FAIR: { filled: 3, color: '#FFFF00' },      // yellow, 3/5 filled
  DEGRADED: { filled: 1, color: '#FF8000' },  // orange, 1/5 filled
};

export const ThreadIndicator: React.FC<ThreadIndicatorProps> = ({ quality }) => {
  const { filled, color } = qualityMap[quality];
  const total = 5;
  
  const filledDots = '●'.repeat(filled);
  const emptyDots = '○'.repeat(total - filled);

  return (
    <span
      style={{
        fontFamily: 'IBM VGA, monospace',
        fontSize: '16px',
        lineHeight: '1.5',
        color: color,
        letterSpacing: '2px',
      }}
    >
      {filledDots}{emptyDots}
    </span>
  );
};

export default ThreadIndicator;
