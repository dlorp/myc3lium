import React from 'react';
import {
  TeletextPanel,
  TeletextText,
  StatusBar,
  ProgressBar,
  Sparkline,
  CommandInput,
  NodeBadge,
  ThreadIndicator,
} from '../components';

/**
 * Component Library Demo Page
 * Showcases all 8 teletext UI components
 */
export const ComponentDemo: React.FC = () => {
  const handleCommand = (cmd: string) => {
    console.log('Command submitted:', cmd);
    alert(`Command: ${cmd}`);
  };

  // Sample data for Sparkline
  const sampleData = [12, 15, 18, 14, 20, 22, 19, 24, 21, 18];

  // Sample nodes for NodeBadge
  const nodes = [
    { id: 'SPORE-01', callsign: 'Nexus', type: 'SPORE', status: 'ONLINE' as const },
    { id: 'HYPHA-03', callsign: 'Ranger', type: 'HYPHA', status: 'OFFLINE' as const },
    { id: 'RHIZOME-02', callsign: 'Ravine Stream', type: 'RHIZOME', status: 'DEGRADED' as const },
  ];

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <TeletextPanel title="MYC3LIUM ─══─ COMPONENT LIBRARY ─══─ 13:05" color="cyan">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* TeletextText Demo */}
          <section>
            <TeletextText color="yellow">1. TeletextText Component</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <TeletextText color="cyan">Cyan text with IBM VGA font</TeletextText>
              <TeletextText color="magenta">Magenta text</TeletextText>
              <TeletextText color="yellow">Yellow text</TeletextText>
              <TeletextText color="green">Green text</TeletextText>
              <TeletextText color="white" blink>Blinking white text</TeletextText>
            </div>
          </section>

          {/* StatusBar Demo */}
          <section>
            <TeletextText color="yellow">2. StatusBar Component</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <StatusBar value={90} color="cyan" label="GOOD" />
              <StatusBar value={60} color="yellow" label="FAIR" />
              <StatusBar value={30} color="orange" label="DEGRADED" />
              <StatusBar value={0} color="gray" label="OFFLINE" />
            </div>
          </section>

          {/* ProgressBar Demo */}
          <section>
            <TeletextText color="yellow">3. ProgressBar Component</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div>
                <TeletextText color="white">Battery: </TeletextText>
                <ProgressBar value={85} max={100} color="green" showPercentage />
              </div>
              <div>
                <TeletextText color="white">Signal: </TeletextText>
                <ProgressBar value={45} max={100} color="yellow" showPercentage />
              </div>
              <div>
                <TeletextText color="white">Storage: </TeletextText>
                <ProgressBar value={20} max={100} color="red" showPercentage />
              </div>
            </div>
          </section>

          {/* Sparkline Demo */}
          <section>
            <TeletextText color="yellow">4. Sparkline Component</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', gap: '16px', alignItems: 'center' }}>
              <TeletextText color="white">Temperature trend: </TeletextText>
              <Sparkline data={sampleData} width={120} height={30} color="cyan" />
            </div>
          </section>

          {/* NodeBadge Demo */}
          <section>
            <TeletextText color="yellow">5. NodeBadge Component</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {nodes.map((node) => (
                <NodeBadge key={node.id} node={node} />
              ))}
            </div>
          </section>

          {/* ThreadIndicator Demo */}
          <section>
            <TeletextText color="yellow">6. ThreadIndicator Component</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div>
                <TeletextText color="white">Connection Quality: </TeletextText>
                <ThreadIndicator quality="GOOD" />
                <TeletextText color="gray"> (GOOD)</TeletextText>
              </div>
              <div>
                <TeletextText color="white">Connection Quality: </TeletextText>
                <ThreadIndicator quality="FAIR" />
                <TeletextText color="gray"> (FAIR)</TeletextText>
              </div>
              <div>
                <TeletextText color="white">Connection Quality: </TeletextText>
                <ThreadIndicator quality="DEGRADED" />
                <TeletextText color="gray"> (DEGRADED)</TeletextText>
              </div>
            </div>
          </section>

          {/* Nested Panel Demo */}
          <section>
            <TeletextText color="yellow">7. Nested TeletextPanel</TeletextText>
            <div style={{ marginTop: '8px' }}>
              <TeletextPanel title="SENSOR READINGS" color="green">
                <TeletextText color="white">Temperature: 6.4°C</TeletextText>
                <br />
                <TeletextText color="white">Humidity: 87%</TeletextText>
                <br />
                <TeletextText color="white">Pressure: 1013mb</TeletextText>
              </TeletextPanel>
            </div>
          </section>

        </div>
      </TeletextPanel>

      {/* CommandInput Demo (fixed at bottom) */}
      <div style={{ marginTop: '20px' }}>
        <TeletextText color="yellow">8. CommandInput Component</TeletextText>
        <div style={{ marginTop: '8px' }}>
          <CommandInput onSubmit={handleCommand} placeholder="THREAD LIST | SENSOR GRID" />
        </div>
      </div>
    </div>
  );
};

export default ComponentDemo;
