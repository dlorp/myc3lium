import React, { useState, useEffect, KeyboardEvent } from 'react';

interface CommandInputProps {
  onSubmit: (command: string) => void;
  placeholder?: string;
}

export const CommandInput: React.FC<CommandInputProps> = ({ 
  onSubmit, 
  placeholder = 'THREAD LIST | SENSOR GRID' 
}) => {
  const [input, setInput] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);

  // Blinking cursor animation
  useEffect(() => {
    const interval = setInterval(() => {
      setCursorVisible((prev) => !prev);
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && input.trim()) {
      onSubmit(input.trim());
      setInput('');
    }
  };

  return (
    <div
      style={{
        fontFamily: 'IBM VGA, monospace',
        fontSize: '16px',
        backgroundColor: '#000000',
        color: '#00FFFF',
        padding: '8px',
        borderTop: '1px solid #00FFFF',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <span style={{ marginRight: '8px' }}>COMMAND:</span>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        style={{
          flex: 1,
          backgroundColor: 'transparent',
          border: 'none',
          outline: 'none',
          color: '#FFFFFF',
          fontFamily: 'IBM VGA, monospace',
          fontSize: '16px',
          caretColor: 'transparent', // Hide default caret
        }}
      />
      <span style={{ opacity: cursorVisible ? 1 : 0, marginLeft: '4px' }}>▐</span>
    </div>
  );
};

export default CommandInput;
