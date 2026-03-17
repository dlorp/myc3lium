import React, { useState, useRef, useEffect } from 'react';
import {
  TeletextPanel,
  TeletextText,
  CommandInput,
} from '../components';

interface CommandHistoryEntry {
  command: string;
  timestamp: string;
  output: string;
  exitCode: number;
}

const P800: React.FC = () => {
  const [history, setHistory] = useState<CommandHistoryEntry[]>([
    {
      command: 'help',
      timestamp: '14:30:45',
      output: 'Available commands: help, thread, sensor, radio, clear, exit',
      exitCode: 0,
    },
  ]);


  const historyEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when history changes
  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const executeCommand = (cmd: string) => {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });

    // Add to input history
    setInputHistory((prev) => [...prev, cmd]);
    setHistoryIndex(-1);

    // Parse and execute command
    const parts = cmd.toLowerCase().trim().split(' ');
    const baseCmd = parts[0];
    let output = '';
    let exitCode = 0;

    switch (baseCmd) {
      case 'help':
        output = [
          'MYCELIUM CLI v0.3.0',
          '',
          'Available commands:',
          '  help              - Show this help message',
          '  thread [list|info <id>] - Thread operations',
          '  sensor [grid|node <id>] - Sensor data queries',
          '  radio [status|config]   - Radio configuration',
          '  sat [list|predict]      - Satellite pass data',
          '  camera [list|stream <id>] - Camera operations',
          '  clear             - Clear terminal',
          '  exit              - Return to menu',
        ].join('\n');
        break;

      case 'thread':
        if (parts[1] === 'list') {
          output = [
            'ACTIVE THREADS:',
            '  THR-001  SPORE-01 <-> HYPHA-03  [GOOD]',
            '  THR-002  HYPHA-03 <-> RHIZOME-02  [FAIR]',
            '  THR-003  RHIZOME-02 <-> SPORE-01  [DEGRADED]',
          ].join('\n');
        } else if (parts[1] === 'info' && parts[2]) {
          output = [
            `Thread: ${parts[2].toUpperCase()}`,
            `Status: GOOD`,
            `Latency: 45ms`,
            `Throughput: 2.3 Mbps`,
            `Packet loss: 0.2%`,
          ].join('\n');
        } else {
          output = 'Usage: thread [list|info <id>]';
          exitCode = 1;
        }
        break;

      case 'sensor':
        if (parts[1] === 'grid') {
          output = [
            'SENSOR GRID STATUS:',
            '  Temperature: 6.4°C',
            '  Humidity: 87%',
            '  Pressure: 1013 mb',
            '  Wind: 3.2 m/s NW',
            '  Soil moisture: 42%',
          ].join('\n');
        } else if (parts[1] === 'node' && parts[2]) {
          output = [
            `Node: ${parts[2].toUpperCase()}`,
            `Battery: 85%`,
            `Signal: -67 dBm`,
            `Uptime: 3d 14h 22m`,
          ].join('\n');
        } else {
          output = 'Usage: sensor [grid|node <id>]';
          exitCode = 1;
        }
        break;

      case 'radio':
        if (parts[1] === 'status') {
          output = [
            'RADIO STATUS:',
            '  LoRa: ONLINE (868 MHz, SF7, BW125)',
            '  HaLow: ONLINE (SSID: MYC3LIUM-MESH)',
            '  SDR: IDLE (RTL-SDR v3)',
          ].join('\n');
        } else if (parts[1] === 'config') {
          output = [
            'RADIO CONFIG:',
            '  LoRa Frequency: 868.1 MHz',
            '  Spread Factor: 7',
            '  Bandwidth: 125 kHz',
            '  TX Power: 14 dBm',
          ].join('\n');
        } else {
          output = 'Usage: radio [status|config]';
          exitCode = 1;
        }
        break;

      case 'sat':
        if (parts[1] === 'list') {
          output = [
            'UPCOMING SATELLITE PASSES:',
            '  NOAA 18      AOS: 14:35  MAX: 45°',
            '  NOAA 19      AOS: 15:55  MAX: 67°',
            '  METEOR-M 2   AOS: 16:52  MAX: 52°',
          ].join('\n');
        } else if (parts[1] === 'predict') {
          output = 'Calculating TLE predictions... Use "sat list" for results.';
        } else {
          output = 'Usage: sat [list|predict]';
          exitCode = 1;
        }
        break;

      case 'camera':
        if (parts[1] === 'list') {
          output = [
            'AVAILABLE CAMERAS:',
            '  FROND-01  "Creek Watch"    [ONLINE]',
            '  FROND-02  "Trail Cam"      [ONLINE]',
            '  FROND-03  "Cabin View"     [DEGRADED]',
            '  FROND-04  "Ridge Monitor"  [OFFLINE]',
          ].join('\n');
        } else if (parts[1] === 'stream' && parts[2]) {
          output = `Starting stream from ${parts[2].toUpperCase()}... Navigate to P500.`;
        } else {
          output = 'Usage: camera [list|stream <id>]';
          exitCode = 1;
        }
        break;

      case 'clear':
        setHistory([]);
        return; // Don't add clear command to history display

      case 'exit':
        output = 'Returning to main menu...';
        break;

      case '':
        return; // Empty command, do nothing

      default:
        output = `Command not found: ${baseCmd}\nType "help" for available commands.`;
        exitCode = 127;
    }

    // Add to command history
    const entry: CommandHistoryEntry = {
      command: cmd,
      timestamp,
      output,
      exitCode,
    };

    setHistory((prev) => [...prev, entry]);
  };

  const handleCommandSubmit = (cmd: string) => {
    executeCommand(cmd);
  };

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <TeletextPanel title="P800 ─══─ COMMAND LINE INTERFACE ─══─ MYCELIUM CLI" color="cyan">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
          {/* Command history display */}
          <div
            style={{
              maxHeight: '500px',
              overflowY: 'auto',
              fontFamily: 'IBM VGA, monospace',
              fontSize: '16px',
              lineHeight: '1.5',
            }}
          >
            {history.map((entry, index) => (
              <div key={index} style={{ marginBottom: '12px' }}>
                {/* Command prompt */}
                <div>
                  <TeletextText color="green">[{entry.timestamp}]</TeletextText>
                  {' '}
                  <TeletextText color="cyan">mycelium$</TeletextText>
                  {' '}
                  <TeletextText color="white">{entry.command}</TeletextText>
                </div>

                {/* Command output */}
                <div style={{ marginLeft: '16px', whiteSpace: 'pre-wrap' }}>
                  <TeletextText color={entry.exitCode === 0 ? 'white' : 'red'}>
                    {entry.output}
                  </TeletextText>
                </div>
              </div>
            ))}
            <div ref={historyEndRef} />
          </div>

          {/* Command input */}
          <div style={{ marginTop: '16px' }}>
            <CommandInput
              onSubmit={handleCommandSubmit}
              placeholder="Type 'help' for available commands"
            />
          </div>
        </div>
      </TeletextPanel>

      <div style={{ marginTop: '12px' }}>
        <TeletextText color="gray">
          Type &ldquo;help&rdquo; for available commands | &ldquo;clear&rdquo; to clear screen | &ldquo;exit&rdquo; to return to menu
        </TeletextText>
      </div>

      {/* Help panel */}
      <div style={{ marginTop: '16px' }}>
        <TeletextPanel title="QUICK REFERENCE" color="magenta">
          <div style={{ display: 'flex', gap: '24px' }}>
            <div>
              <TeletextText color="yellow">NAVIGATION:</TeletextText>
              <br />
              <TeletextText color="white">thread list</TeletextText>
              <br />
              <TeletextText color="white">sensor grid</TeletextText>
              <br />
              <TeletextText color="white">camera list</TeletextText>
            </div>
            <div>
              <TeletextText color="yellow">STATUS:</TeletextText>
              <br />
              <TeletextText color="white">radio status</TeletextText>
              <br />
              <TeletextText color="white">sat list</TeletextText>
              <br />
              <TeletextText color="white">thread info THR-001</TeletextText>
            </div>
            <div>
              <TeletextText color="yellow">SYSTEM:</TeletextText>
              <br />
              <TeletextText color="white">help</TeletextText>
              <br />
              <TeletextText color="white">clear</TeletextText>
              <br />
              <TeletextText color="white">exit</TeletextText>
            </div>
          </div>
        </TeletextPanel>
      </div>
    </div>
  );
};

export default P800;
