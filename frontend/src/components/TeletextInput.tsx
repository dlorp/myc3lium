import React, { useState, CSSProperties } from 'react';

type ColorType = 'cyan' | 'yellow' | 'green' | 'white';

interface TeletextInputProps {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: 'text' | 'number';
  color?: ColorType;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

const colorMap: Record<ColorType, string> = {
  cyan: '#00FFFF',
  yellow: '#FFFF00',
  green: '#00FF00',
  white: '#FFFFFF',
};

export const TeletextInput: React.FC<TeletextInputProps> = ({
  label,
  value,
  onChange,
  type = 'text',
  color = 'cyan',
  disabled = false,
  placeholder,
  maxLength,
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

  const inputStyle: CSSProperties = {
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
    cursor: disabled ? 'not-allowed' : 'text',
  };

  return (
    <div style={{ width: '100%', marginBottom: '8px' }}>
      <div style={labelStyle}>{label}</div>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        disabled={disabled}
        placeholder={placeholder}
        maxLength={maxLength}
        style={inputStyle}
      />
    </div>
  );
};

export default TeletextInput;
