import React, { useState, useEffect } from 'react';
import {
  TeletextPanel,
  TeletextText,
  ProgressBar,
} from '../components';

interface SatellitePass {
  satellite: string;
  aos: Date; // Acquisition of Signal
  los: Date; // Loss of Signal
  maxElevation: number;
  direction: string;
  frequency: string;
  autoCapture: boolean;
}

const P600: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedPass, setSelectedPass] = useState<SatellitePass | null>(null);

  // Mock satellite pass predictions
  const passes: SatellitePass[] = [
    {
      satellite: 'NOAA 18',
      aos: new Date(Date.now() + 5 * 60 * 1000), // 5 minutes from now
      los: new Date(Date.now() + 20 * 60 * 1000),
      maxElevation: 45,
      direction: 'N→S',
      frequency: '137.9125 MHz',
      autoCapture: true,
    },
    {
      satellite: 'NOAA 19',
      aos: new Date(Date.now() + 85 * 60 * 1000), // 1h 25m
      los: new Date(Date.now() + 100 * 60 * 1000),
      maxElevation: 67,
      direction: 'S→N',
      frequency: '137.1000 MHz',
      autoCapture: true,
    },
    {
      satellite: 'METEOR-M 2',
      aos: new Date(Date.now() + 142 * 60 * 1000), // 2h 22m
      los: new Date(Date.now() + 157 * 60 * 1000),
      maxElevation: 52,
      direction: 'N→S',
      frequency: '137.1000 MHz',
      autoCapture: false,
    },
    {
      satellite: 'ISS',
      aos: new Date(Date.now() + 215 * 60 * 1000), // 3h 35m
      los: new Date(Date.now() + 222 * 60 * 1000),
      maxElevation: 28,
      direction: 'W→E',
      frequency: '145.800 MHz',
      autoCapture: false,
    },
  ];

  // Update current time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Auto-select first upcoming pass
  useEffect(() => {
    if (!selectedPass && passes.length > 0) {
      setSelectedPass(passes[0]);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  const formatCountdown = (targetDate: Date): string => {
    const diff = targetDate.getTime() - currentTime.getTime();
    if (diff <= 0) return '00:00:00';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const getPassProgress = (pass: SatellitePass): number => {
    const now = currentTime.getTime();
    const start = pass.aos.getTime();
    const end = pass.los.getTime();

    if (now < start) return 0;
    if (now > end) return 100;

    return ((now - start) / (end - start)) * 100;
  };

  const isPassActive = (pass: SatellitePass): boolean => {
    const now = currentTime.getTime();
    return now >= pass.aos.getTime() && now <= pass.los.getTime();
  };

  const getTimeUntilAOS = (pass: SatellitePass): number => {
    return Math.max(0, pass.aos.getTime() - currentTime.getTime());
  };

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <TeletextPanel title="P600 ─══─ SATELLITE PASS PREDICTIONS ─══─ APT/LRPT" color="cyan">
        <div style={{ display: 'flex', gap: '20px' }}>
          {/* Left sidebar - Pass list */}
          <div style={{ width: '350px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <TeletextText color="yellow">UPCOMING PASSES:</TeletextText>
            {passes.map((pass, index) => {
              const isActive = isPassActive(pass);
              const isSelected = selectedPass?.satellite === pass.satellite;
              const color = isActive ? 'green' : isSelected ? 'cyan' : 'white';

              return (
                <div
                  key={index}
                  onClick={() => setSelectedPass(pass)}
                  style={{ cursor: 'pointer' }}
                >
                  <TeletextText color={color}>
                    {isActive ? '► ' : '  '}
                    {pass.satellite}
                  </TeletextText>
                  <br />
                  <TeletextText color="gray">
                    {'  '}AOS: {formatTime(pass.aos)} | MAX: {pass.maxElevation}°
                  </TeletextText>
                  {isSelected && <TeletextText color="cyan"> ◄</TeletextText>}
                </div>
              );
            })}
          </div>

          {/* Right panel - Pass details */}
          <div style={{ flex: 1 }}>
            {selectedPass ? (
              <>
                <TeletextPanel title={`PASS: ${selectedPass.satellite}`} color="green">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div>
                      <TeletextText color="yellow">ACQUISITION OF SIGNAL (AOS):</TeletextText>
                      <br />
                      <TeletextText color="white">
                        {'  '}Time: {formatTime(selectedPass.aos)}
                      </TeletextText>
                      <br />
                      <TeletextText color="cyan">
                        {'  '}Countdown: {formatCountdown(selectedPass.aos)}
                      </TeletextText>
                    </div>

                    <div>
                      <TeletextText color="yellow">LOSS OF SIGNAL (LOS):</TeletextText>
                      <br />
                      <TeletextText color="white">
                        {'  '}Time: {formatTime(selectedPass.los)}
                      </TeletextText>
                    </div>

                    <div>
                      <TeletextText color="yellow">PASS PARAMETERS:</TeletextText>
                      <br />
                      <TeletextText color="white">
                        {'  '}Max Elevation: {selectedPass.maxElevation}°
                      </TeletextText>
                      <br />
                      <TeletextText color="white">
                        {'  '}Direction: {selectedPass.direction}
                      </TeletextText>
                      <br />
                      <TeletextText color="white">
                        {'  '}Frequency: {selectedPass.frequency}
                      </TeletextText>
                    </div>

                    <div>
                      <TeletextText color="yellow">AUTO-CAPTURE:</TeletextText>
                      <br />
                      <TeletextText color={selectedPass.autoCapture ? 'green' : 'red'}>
                        {'  '}
                        {selectedPass.autoCapture ? '◉ ENABLED' : '○ DISABLED'}
                      </TeletextText>
                    </div>

                    {/* Progress bar for active pass */}
                    {isPassActive(selectedPass) && (
                      <div style={{ marginTop: '8px' }}>
                        <TeletextText color="green">PASS IN PROGRESS:</TeletextText>
                        <br />
                        <ProgressBar
                          value={getPassProgress(selectedPass)}
                          max={100}
                          color="green"
                          showPercentage
                        />
                      </div>
                    )}

                    {/* Countdown progress for upcoming pass */}
                    {!isPassActive(selectedPass) && getTimeUntilAOS(selectedPass) > 0 && (
                      <div style={{ marginTop: '8px' }}>
                        <TeletextText color="cyan">TIME UNTIL AOS:</TeletextText>
                        <br />
                        <ProgressBar
                          value={100 - Math.min(100, (getTimeUntilAOS(selectedPass) / (60 * 60 * 1000)) * 100)}
                          max={100}
                          color="cyan"
                          showPercentage={false}
                        />
                        <TeletextText color="white">
                          {'  '}{formatCountdown(selectedPass.aos)}
                        </TeletextText>
                      </div>
                    )}
                  </div>
                </TeletextPanel>

                {/* System status */}
                <div style={{ marginTop: '16px' }}>
                  <TeletextPanel title="RECEIVER STATUS" color="magenta">
                    <TeletextText color="white">SDR: RTL-SDR v3</TeletextText>
                    <br />
                    <TeletextText color="white">Antenna: 137 MHz Dipole</TeletextText>
                    <br />
                    <TeletextText color="white">Decoder: SatDump</TeletextText>
                    <br />
                    <TeletextText color="green">Status: READY</TeletextText>
                  </TeletextPanel>
                </div>
              </>
            ) : (
              <TeletextText color="gray">[ SELECT A PASS FROM THE LIST ]</TeletextText>
            )}
          </div>
        </div>
      </TeletextPanel>

      <div style={{ marginTop: '12px' }}>
        <TeletextText color="gray">
          Current time: {formatTime(currentTime)} | Press A to toggle auto-capture | ESC to exit
        </TeletextText>
      </div>
    </div>
  );
};

export default P600;
