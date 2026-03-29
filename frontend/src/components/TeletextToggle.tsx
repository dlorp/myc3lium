import React, { CSSProperties } from 'react';

type ColorType = 'cyan' | 'yellow' | 'green' | 'white';

interface TeletextToggleProps {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
  color?: ColorType;
  disabled?: boolean;
}

const colorMap: Record<ColorType, string> = {
  cyan: '#00FFFF',
  yellow: '#FFFF00',
  green: '#00FF00',
  white: '#FFFFFF',
};

export const TeletextToggle: React.FC<TeletextToggleProps> = ({
  label,
  value,
  onChange,
  color = 'cyan',
  disabled = false,
}) => {
  const labelStyle: CSSProperties = {
    color: disabled ? '#808080' : colorMap[color],
    fontFamily: 'IBM VGA, monospace',
    fontSize: '16px',
    lineHeight: '1.5',
    textTransform: 'uppercase',
    marginRight: '8px',
  };

  const buttonStyle: CSSProperties = {
    background: 'none',
    border: 'none',
    padding: '0',
    fontFamily: 'IBM VGA, monospace',
    fontSize: '16px',
    lineHeight: '1.5',
    color: disabled
      ? '#808080'
      : value
        ? '#00FF00'
        : '#FF0000',
    cursor: disabled ? 'not-allowed' : 'pointer',
    outline: 'none',
  };

  return (
    <div
      style={{
        width: '100%',
        marginBottom: '8px',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <span style={labelStyle}>{label}</span>
      <button
        type="button"
        onClick={() => {
          if (!disabled) {
            onChange(!value);
          }
        }}
        disabled={disabled}
        style={buttonStyle}
      >
        {value ? '[ON]' : '[OFF]'}
      </button>
    </div>
  );
};

export default TeletextToggle;
