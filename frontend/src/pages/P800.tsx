import React, { useState, useRef, useEffect } from 'react';
import {
  TeletextPanel,
  TeletextText,
  CommandInput,
} from '../components';

interface CommandHistoryEntry {
  command: string;
  output: string[];
  timestamp: Date;
}

/**
 * P800: CommandPage - CLI interface
 * Provides a command-line interface with history and suggestions
 */
export const CommandPage: React.FC = () => {
  const [history, setHistory] = useState<CommandHistoryEntry[]>([]);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const outputEndRef = useRef<HTMLDivElement>(null);

  // Available commands
  const availableCommands = [
    'THREAD LIST',
    'THREAD STATUS <id>',
    'SENSOR GRID',
    'NODE STATUS',
    'NODE LIST',
    'CAMERA STREAM <id>',
    'SATELLITE TRACK',
    'TELEMETRY DUMP',
    'MESH STATUS',
    'SIGNAL STRENGTH',
    'UPTIME',
    'MEMORY',
    'HELP',
    'CLEAR',
  ];

  // Mock command execution
  const executeCommand = (cmd: string): string[] => {
    const upperCmd = cmd.toUpperCase();

    if (upperCmd === 'HELP') {
      return [
        'Available commands:',
        '  THREAD LIST       - List all active threads',
        '  THREAD STATUS     - Show thread status',
        '  SENSOR GRID       - Display sensor readings',
        '  NODE STATUS       - Show node health',
        '  NODE LIST         - List all nodes',
        '  CAMERA STREAM     - View camera streams',
        '  SATELLITE TRACK   - Show satellite passes',
        '  TELEMETRY DUMP    - Export telemetry data',
        '  MESH STATUS       - Network mesh status',
        '  SIGNAL STRENGTH   - Signal quality report',
        '  UPTIME            - System uptime',
        '  MEMORY            - Memory usage',
        '  CLEAR             - Clear output',
      ];
    }

    if (upperCmd === 'CLEAR') {
      setHistory([]);
      return [];
    }

    if (upperCmd === 'THREAD LIST') {
      return [
        'Active threads:',
        '  THREAD-001: SPORE-01 <-> HYPHA-03 (GOOD, 12ms)',
        '  THREAD-002: HYPHA-03 <-> RHIZOME-02 (FAIR, 45ms)',
        '  THREAD-003: SPORE-01 <-> FROND-01 (DEGRADED, 120ms)',
        '  THREAD-004: RHIZOME-02 <-> FROND-02 (GOOD, 8ms)',
        'Total: 4 threads active',
      ];
    }

    if (upperCmd.startsWith('THREAD STATUS')) {
      return [
        'THREAD-001 Status:',
        '  Source: SPORE-01',
        '  Destination: HYPHA-03',
        '  Quality: GOOD',
        '  Latency: 12ms',
        '  Packet Loss: 0.2%',
        '  Bandwidth: 2.4 Mbps',
      ];
    }

    if (upperCmd === 'SENSOR GRID') {
      return [
        'Sensor Grid Status:',
        '  Temperature: 6.4°C',
        '  Humidity: 87%',
        '  Pressure: 1013mb',
        '  Light Level: 240 lux',
        '  Battery: 85%',
        '  Last Update: 2 seconds ago',
      ];
    }

    if (upperCmd === 'NODE STATUS' || upperCmd === 'NODE LIST') {
      return [
        'MYC3LIUM Node Registry:',
        '  ◉ SPORE-01   "Nexus"          [ONLINE]   Signal: 95%',
        '  ◉ HYPHA-03   "Ranger"         [ONLINE]   Signal: 82%',
        '  ◐ RHIZOME-02 "Ravine Stream"  [DEGRADED] Signal: 45%',
        '  ◉ FROND-01   "Canopy Watch"   [ONLINE]   Signal: 85%',
        '  ○ FROND-02   "Forest Eye"     [OFFLINE]  Signal: 0%',
        'Total: 5 nodes (4 online, 1 degraded, 1 offline)',
      ];
    }

    if (upperCmd.startsWith('CAMERA STREAM')) {
      return [
        'Camera Stream P500:',
        '  Available streams: 2',
        '  FROND-01: Canopy Watch (ACTIVE)',
        '  FROND-02: Forest Eye (OFFLINE)',
        '  Use P500 page for live view',
      ];
    }

    if (upperCmd === 'SATELLITE TRACK') {
      return [
        'Satellite Tracking P600:',
        '  Next pass: NOAA-18 in 00:14:32',
        '  AOS: 13:34:18 | LOS: 13:49:45',
        '  Max Elevation: 78°',
        '  Auto-Capture: OFF',
        '  Use P600 page for full details',
      ];
    }

    if (upperCmd === 'TELEMETRY DUMP') {
      return [
        'Exporting telemetry data...',
        '  Collecting sensor readings...',
        '  Collecting node status...',
        '  Collecting thread metrics...',
        '  Export complete: telemetry_2026-03-17.json',
        '  Size: 124 KB',
      ];
    }

    if (upperCmd === 'MESH STATUS') {
      return [
        'Mesh Network Status:',
        '  Active Nodes: 4/5',
        '  Active Threads: 4',
        '  Network Health: GOOD',
        '  Average Latency: 46ms',
        '  Total Throughput: 8.2 Mbps',
      ];
    }

    if (upperCmd === 'SIGNAL STRENGTH') {
      return [
        'Signal Strength Report:',
        '  SPORE-01:   ████████████████████ 95%',
        '  HYPHA-03:   ████████████████░░░░ 82%',
        '  RHIZOME-02: █████████░░░░░░░░░░░ 45%',
        '  FROND-01:   █████████████████░░░ 85%',
        '  FROND-02:   ░░░░░░░░░░░░░░░░░░░░ 0% (OFFLINE)',
      ];
    }

    if (upperCmd === 'UPTIME') {
      return [
        'System Uptime:',
        '  Core System: 7 days, 14 hours, 23 minutes',
        '  Network Mesh: 7 days, 14 hours, 12 minutes',
        '  Last Reboot: 2026-03-10 00:15:42 UTC',
      ];
    }

    if (upperCmd === 'MEMORY') {
      return [
        'Memory Usage:',
        '  Total: 8192 MB',
        '  Used: 3472 MB (42%)',
        '  Free: 4720 MB (58%)',
        '  Buffers: 512 MB',
        '  Cached: 1024 MB',
      ];
    }

    return [`Unknown command: ${cmd}`, 'Type HELP for available commands'];
  };

  const handleCommand = (cmd: string) => {
    const output = executeCommand(cmd);
    
    if (cmd.toUpperCase() !== 'CLEAR') {
      const entry: CommandHistoryEntry = {
        command: cmd,
        output,
        timestamp: new Date(),
      };
      
      setHistory([...history, entry]);
      setCommandHistory([...commandHistory, cmd]);
    }
  };

  // Auto-scroll to bottom when new output appears
  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  // Get command suggestions based on partial input
  const getCommandSuggestions = (partial: string): string[] => {
    if (!partial) return availableCommands.slice(0, 5);
    
    const upperPartial = partial.toUpperCase();
    return availableCommands
      .filter(cmd => cmd.startsWith(upperPartial))
      .slice(0, 5);
  };

  const [suggestions] = useState(getCommandSuggestions(''));

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <TeletextPanel title="P800 ─══─ COMMAND INTERFACE ─══─ CLI" color="cyan">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Command Suggestions */}
          <section>
            <TeletextText color="yellow">AVAILABLE COMMANDS:</TeletextText>
            <div style={{ 
              marginTop: '8px', 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '8px' 
            }}>
              {suggestions.map((cmd, idx) => (
                <span
                  key={idx}
                  style={{
                    fontFamily: 'IBM VGA, monospace',
                    fontSize: '14px',
                    padding: '4px 8px',
                    backgroundColor: '#003333',
                    color: '#00FFFF',
                    border: '1px solid #00FFFF',
                  }}
                >
                  {cmd}
                </span>
              ))}
              <TeletextText color="gray">... type HELP for full list</TeletextText>
            </div>
          </section>

          {/* Command Output Display */}
          <section>
            <TeletextPanel title="OUTPUT" color="green">
              <div
                style={{
                  maxHeight: '400px',
                  overflowY: 'auto',
                  fontFamily: 'IBM VGA, monospace',
                  fontSize: '16px',
                }}
              >
                {history.length === 0 ? (
                  <TeletextText color="gray">
                    MYC3LIUM Command Interface v3.0
                    <br />
                    Type HELP for available commands
                    <br />
                    <br />
                  </TeletextText>
                ) : (
                  history.map((entry, idx) => (
                    <div key={idx} style={{ marginBottom: '16px' }}>
                      {/* Command */}
                      <div>
                        <TeletextText color="cyan">
                          &gt; {entry.command}
                        </TeletextText>
                      </div>
                      
                      {/* Output */}
                      <div style={{ marginTop: '4px' }}>
                        {entry.output.map((line, lineIdx) => (
                          <div key={lineIdx}>
                            <TeletextText color="white">{line}</TeletextText>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                )}
                <div ref={outputEndRef} />
              </div>
            </TeletextPanel>
          </section>

          {/* Command Input */}
          <section>
            <CommandInput 
              onSubmit={handleCommand} 
              placeholder="THREAD LIST | SENSOR GRID | HELP" 
            />
          </section>

          {/* Quick Stats */}
          <section>
            <div style={{ display: 'flex', gap: '24px' }}>
              <div>
                <TeletextText color="gray">Commands Executed: </TeletextText>
                <TeletextText color="cyan">{commandHistory.length}</TeletextText>
              </div>
              <div>
                <TeletextText color="gray">Session Time: </TeletextText>
                <TeletextText color="cyan">00:42:15</TeletextText>
              </div>
            </div>
          </section>

        </div>
      </TeletextPanel>
    </div>
  );
};

export default CommandPage;
