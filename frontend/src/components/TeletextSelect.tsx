import React, { useState, CSSProperties } from 'react';

type ColorType = 'cyan' | 'yellow' | 'green' | 'white';

interface TeletextSelectProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  color?: ColorType;
  disabled?: boolean;
}

const colorMap: Record<ColorType, string> = {
  cyan: '#00FFFF',
  yellow: '#FFFF00',
  green: '#00FF00',
  white: '#FFFFFF',
};

export const TeletextSelect: React.FC<TeletextSelectProps> = ({
  label,
  value,
  onChange,
  options,
  color = 'cyan',
  disabled = false,
}) => {
  const [focused, setFocused] = useState(false);
  const borderColor = disabled ? '#404040' : colorMap[color];
  const focusBorderColor = disabled ? '#404040' : '#FFFFFF';

  const labelStyle: CSSProperties = {
    color: disabled ? '#808080' : colorMap[color],
    fontFamily: 'IBM VGA, monospace',
    fontSize: '16px',
    lineHeight: '1.5',
    textTransform: 'uppercase',
    marginBottom: '4px',
  };

  const selectStyle: CSSProperties = {
    width: '100%',
    boxSizing: 'border-box',
    backgroundColor: '#000000',
    color: disabled ? '#808080' : '#00FFFF',
    fontFamily: 'IBM VGA, monospace',
    fontSize: '16px',
    lineHeight: '1.5',
    padding: '4px 8px',
    border: `1px solid ${focused ? focusBorderColor : borderColor}`,
    borderRadius: '0',
    outline: 'none',
    boxShadow: focused && !disabled ? `0 0 4px ${colorMap[color]}` : 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    appearance: 'none',
    WebkitAppearance: 'none',
  };

  return (
    <div style={{ width: '100%', marginBottom: '8px' }}>
      <div style={labelStyle}>{label}</div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        disabled={disabled}
        style={selectStyle}
      >
        {options.map((opt) => (
          <option
            key={opt.value}
            value={opt.value}
            style={{
              backgroundColor: '#000000',
              color: '#00FFFF',
              fontFamily: 'IBM VGA, monospace',
            }}
          >
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default TeletextSelect;
