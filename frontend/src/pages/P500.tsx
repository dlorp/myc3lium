import React, { useState, useEffect } from 'react';
import {
  TeletextPanel,
  TeletextText,
  NodeBadge,
  StatusBar,
} from '../components';

interface CameraNode {
  id: string;
  callsign: string;
  type: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  streamUrl?: string;
  location?: string;
  fps?: number;
  resolution?: string;
}

const P500: React.FC = () => {
  const [selectedCamera, setSelectedCamera] = useState<CameraNode | null>(null);
  const [frameCount, setFrameCount] = useState(0);

  // Mock camera nodes
  const cameras: CameraNode[] = [
    {
      id: 'FROND-01',
      callsign: 'Creek Watch',
      type: 'FROND',
      status: 'ONLINE',
      streamUrl: 'http://192.168.1.101:8080/stream.mjpg',
      location: 'North Ravine',
      fps: 15,
      resolution: '1280x720',
    },
    {
      id: 'FROND-02',
      callsign: 'Trail Cam',
      type: 'FROND',
      status: 'ONLINE',
      streamUrl: 'http://192.168.1.102:8080/stream.mjpg',
      location: 'East Trail',
      fps: 10,
      resolution: '640x480',
    },
    {
      id: 'FROND-03',
      callsign: 'Cabin View',
      type: 'FROND',
      status: 'DEGRADED',
      streamUrl: 'http://192.168.1.103:8080/stream.mjpg',
      location: 'Cabin Exterior',
      fps: 5,
      resolution: '640x480',
    },
    {
      id: 'FROND-04',
      callsign: 'Ridge Monitor',
      type: 'FROND',
      status: 'OFFLINE',
      location: 'West Ridge',
    },
  ];

  // Auto-select first online camera
  useEffect(() => {
    if (!selectedCamera) {
      const firstOnline = cameras.find((c) => c.status === 'ONLINE');
      if (firstOnline) setSelectedCamera(firstOnline);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Frame counter animation
  useEffect(() => {
    const interval = setInterval(() => {
      setFrameCount((prev) => (prev + 1) % 1000);
    }, 100);
    return () => clearInterval(interval);
  }, []);

  const handleCameraSelect = (camera: CameraNode) => {
    if (camera.status !== 'OFFLINE') {
      setSelectedCamera(camera);
    }
  };

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <TeletextPanel title="P500 ─══─ FROND CAMERA STREAMS ─══─ LIVE" color="cyan">
        <div style={{ display: 'flex', gap: '20px' }}>
          {/* Left sidebar - Camera list */}
          <div style={{ width: '300px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <TeletextText color="yellow">AVAILABLE CAMERAS:</TeletextText>
            {cameras.map((camera) => (
              <div
                key={camera.id}
                onClick={() => handleCameraSelect(camera)}
                style={{ cursor: camera.status !== 'OFFLINE' ? 'pointer' : 'default' }}
              >
                <NodeBadge node={camera} />
                {selectedCamera?.id === camera.id && (
                  <TeletextText color="cyan"> ◄ ACTIVE</TeletextText>
                )}
              </div>
            ))}

            {selectedCamera && (
              <div style={{ marginTop: '16px' }}>
                <TeletextPanel title="NODE INFO" color="green">
                  <TeletextText color="white">ID: {selectedCamera.id}</TeletextText>
                  <br />
                  <TeletextText color="white">Location: {selectedCamera.location}</TeletextText>
                  <br />
                  <TeletextText color="white">
                    Resolution: {selectedCamera.resolution || 'N/A'}
                  </TeletextText>
                  <br />
                  <TeletextText color="white">FPS: {selectedCamera.fps || 0}</TeletextText>
                </TeletextPanel>
              </div>
            )}
          </div>

          {/* Right panel - Video stream */}
          <div style={{ flex: 1 }}>
            {selectedCamera ? (
              <>
                <TeletextText color="cyan">
                  STREAM: {selectedCamera.callsign} ({selectedCamera.id})
                </TeletextText>
                <br />
                <br />
                <div
                  style={{
                    border: '2px solid #00FFFF',
                    backgroundColor: '#001a1a',
                    minHeight: '400px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                  }}
                >
                  {selectedCamera.status === 'ONLINE' && selectedCamera.streamUrl ? (
                    <>
                      <img
                        src={selectedCamera.streamUrl}
                        alt={selectedCamera.callsign}
                        style={{
                          maxWidth: '100%',
                          maxHeight: '400px',
                          display: 'block',
                        }}
                        onError={(e) => {
                          // Fallback placeholder if stream fails
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                      {/* Node overlay */}
                      <div
                        style={{
                          position: 'absolute',
                          top: '8px',
                          left: '8px',
                          backgroundColor: 'rgba(0, 0, 0, 0.7)',
                          padding: '4px 8px',
                        }}
                      >
                        <TeletextText color="cyan">{selectedCamera.id}</TeletextText>
                      </div>
                      {/* Frame counter */}
                      <div
                        style={{
                          position: 'absolute',
                          top: '8px',
                          right: '8px',
                          backgroundColor: 'rgba(0, 0, 0, 0.7)',
                          padding: '4px 8px',
                        }}
                      >
                        <TeletextText color="green">
                          {selectedCamera.fps}fps | F{frameCount.toString().padStart(3, '0')}
                        </TeletextText>
                      </div>
                    </>
                  ) : (
                    <TeletextText color="yellow">
                      [ STREAM UNAVAILABLE - NODE DEGRADED ]
                    </TeletextText>
                  )}
                </div>

                {/* Status bars */}
                <div style={{ marginTop: '16px' }}>
                  <StatusBar
                    value={selectedCamera.status === 'ONLINE' ? 95 : 30}
                    color={selectedCamera.status === 'ONLINE' ? 'cyan' : 'yellow'}
                    label="SIGNAL"
                  />
                  <StatusBar
                    value={selectedCamera.fps ? (selectedCamera.fps / 30) * 100 : 0}
                    color="green"
                    label="FRAMERATE"
                  />
                  <StatusBar
                    value={frameCount % 100}
                    color="magenta"
                    label="BUFFER"
                  />
                </div>
              </>
            ) : (
              <TeletextText color="gray">[ SELECT A CAMERA FROM THE LIST ]</TeletextText>
            )}
          </div>
        </div>
      </TeletextPanel>

      <div style={{ marginTop: '12px' }}>
        <TeletextText color="gray">
          Press 1-4 to select camera | ESC to return to menu
        </TeletextText>
      </div>
    </div>
  );
};

export default P500;
