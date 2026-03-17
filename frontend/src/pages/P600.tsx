import React, { useState, useEffect } from 'react';
import {
  TeletextPanel,
  TeletextText,
  ProgressBar,
} from '../components';

interface SatellitePass {
  satelliteName: string;
  aos: Date;
  los: Date;
  maxElevation: number;
}

/**
 * P600: SatellitePage - Pass predictions
 * Displays upcoming satellite passes with countdown and capture controls
 */
export const SatellitePage: React.FC = () => {
  const [autoCapture, setAutoCapture] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // Mock satellite pass data
  const upcomingPasses: SatellitePass[] = [
    {
      satelliteName: 'NOAA-18',
      aos: new Date(Date.now() + 15 * 60 * 1000), // 15 minutes from now
      los: new Date(Date.now() + 30 * 60 * 1000),
      maxElevation: 78,
    },
    {
      satelliteName: 'METEOR-M2',
      aos: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
      los: new Date(Date.now() + 2 * 60 * 60 * 1000 + 18 * 60 * 1000),
      maxElevation: 45,
    },
    {
      satelliteName: 'NOAA-19',
      aos: new Date(Date.now() + 5 * 60 * 60 * 1000), // 5 hours from now
      los: new Date(Date.now() + 5 * 60 * 60 * 1000 + 22 * 60 * 1000),
      maxElevation: 62,
    },
  ];

  const nextPass = upcomingPasses[0];

  // Update countdown every second
  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      const timeUntilAOS = Math.max(0, nextPass.aos.getTime() - now);
      setCountdown(Math.floor(timeUntilAOS / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [nextPass.aos]);

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit',
      hour12: false 
    });
  };

  const formatCountdown = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const getElevationColor = (elevation: number): 'green' | 'yellow' | 'orange' => {
    if (elevation >= 60) return 'green';
    if (elevation >= 40) return 'yellow';
    return 'orange';
  };

  const getCountdownColor = (seconds: number): 'red' | 'yellow' | 'cyan' => {
    if (seconds < 60) return 'red';
    if (seconds < 300) return 'yellow';
    return 'cyan';
  };

  const passDuration = (los: Date, aos: Date): number => {
    return Math.floor((los.getTime() - aos.getTime()) / 60000); // minutes
  };

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <TeletextPanel title="P600 ─══─ SATELLITE TRACKING ─══─ PASS PREDICTIONS" color="cyan">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Next Pass Countdown */}
          <section>
            <TeletextPanel title="NEXT PASS" color="magenta">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <TeletextText color="yellow">SATELLITE:</TeletextText>
                  <br />
                  <TeletextText color="white" style={{ fontSize: '20px' }}>
                    {nextPass.satelliteName}
                  </TeletextText>
                </div>

                <div>
                  <TeletextText color="yellow">COUNTDOWN TO AOS:</TeletextText>
                  <br />
                  <TeletextText 
                    color={getCountdownColor(countdown)} 
                    blink={countdown < 60}
                  >
                    {formatCountdown(countdown)}
                  </TeletextText>
                </div>

                <div style={{ display: 'flex', gap: '24px' }}>
                  <div>
                    <TeletextText color="white">AOS: </TeletextText>
                    <TeletextText color="cyan">{formatTime(nextPass.aos)}</TeletextText>
                  </div>
                  <div>
                    <TeletextText color="white">LOS: </TeletextText>
                    <TeletextText color="cyan">{formatTime(nextPass.los)}</TeletextText>
                  </div>
                  <div>
                    <TeletextText color="white">Duration: </TeletextText>
                    <TeletextText color="cyan">
                      {passDuration(nextPass.los, nextPass.aos)} min
                    </TeletextText>
                  </div>
                </div>

                <div>
                  <TeletextText color="white">Max Elevation: </TeletextText>
                  <TeletextText color={getElevationColor(nextPass.maxElevation)}>
                    {nextPass.maxElevation}°
                  </TeletextText>
                  <span style={{ marginLeft: '12px' }}>
                    <ProgressBar 
                      value={nextPass.maxElevation} 
                      max={90} 
                      color={getElevationColor(nextPass.maxElevation)}
                      showPercentage={false}
                    />
                  </span>
                </div>
              </div>
            </TeletextPanel>
          </section>

          {/* Auto-Capture Control */}
          <section>
            <TeletextText color="yellow">CAPTURE SETTINGS:</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', gap: '16px', alignItems: 'center' }}>
              <button
                onClick={() => setAutoCapture(!autoCapture)}
                style={{
                  fontFamily: 'IBM VGA, monospace',
                  fontSize: '16px',
                  padding: '8px 16px',
                  backgroundColor: autoCapture ? '#003300' : '#000',
                  color: autoCapture ? '#00FF00' : '#808080',
                  border: autoCapture ? '1px solid #00FF00' : '1px solid #808080',
                  cursor: 'pointer',
                }}
              >
                {autoCapture ? '◉ AUTO-CAPTURE: ON' : '○ AUTO-CAPTURE: OFF'}
              </button>
              {autoCapture && (
                <TeletextText color="green" blink>
                  [ARMED]
                </TeletextText>
              )}
            </div>
          </section>

          {/* Upcoming Passes List */}
          <section>
            <TeletextText color="yellow">UPCOMING PASSES:</TeletextText>
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {upcomingPasses.map((pass, idx) => (
                <div
                  key={idx}
                  style={{
                    border: '1px solid #444',
                    padding: '8px',
                    backgroundColor: idx === 0 ? '#001a1a' : 'transparent',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <TeletextText color="cyan">{pass.satelliteName}</TeletextText>
                    </div>
                    <div>
                      <TeletextText color="white">
                        AOS: {formatTime(pass.aos)} | 
                        LOS: {formatTime(pass.los)} | 
                        Max El: {pass.maxElevation}°
                      </TeletextText>
                    </div>
                  </div>
                  <div style={{ marginTop: '4px' }}>
                    <TeletextText color="gray">
                      Duration: {passDuration(pass.los, pass.aos)} minutes
                    </TeletextText>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Status Info */}
          <section>
            <TeletextPanel title="TRACKING STATUS" color="green">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div>
                  <TeletextText color="white">TLE Age: </TeletextText>
                  <TeletextText color="green">2 days</TeletextText>
                </div>
                <div>
                  <TeletextText color="white">Last Update: </TeletextText>
                  <TeletextText color="cyan">2026-03-15 18:42:00 UTC</TeletextText>
                </div>
                <div>
                  <TeletextText color="white">Tracking Mode: </TeletextText>
                  <TeletextText color="cyan">AUTOMATIC</TeletextText>
                </div>
                <div>
                  <TeletextText color="white">Antenna Status: </TeletextText>
                  <TeletextText color="green">READY</TeletextText>
                </div>
              </div>
            </TeletextPanel>
          </section>

        </div>
      </TeletextPanel>
    </div>
  );
};

export default SatellitePage;
