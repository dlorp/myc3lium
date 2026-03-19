import React, { useState, useEffect, useRef, useCallback } from 'react';
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

type ConnectionState = 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'OFFLINE';
type StreamQuality = 'HIGH' | 'MEDIUM' | 'LOW';

interface StreamMetrics {
  signal: number; // 0-100%
  battery: number; // 0-100%
  bitrate: number; // kbps
  bandwidth: number; // 0-100% link quality
  connectionState: ConnectionState;
  isRecording: boolean;
  timestamp: string;
  gpsLat: number;
  gpsLon: number;
}

const P500: React.FC = () => {
  const [selectedCamera, setSelectedCamera] = useState<CameraNode | null>(null);
  const [frameCount, setFrameCount] = useState(0);
  const [quality, setQuality] = useState<StreamQuality>('HIGH');
  const [isPlaying, setIsPlaying] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Stream management refs
  const streamRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const animationFrameRef = useRef<number | null>(null);
  const lastFrameTimeRef = useRef(0);
  const snapshotCanvasRef = useRef<HTMLCanvasElement>(null);

  // Stream metrics state
  const [metrics, setMetrics] = useState<StreamMetrics>({
    signal: 95,
    battery: 87,
    bitrate: 2500,
    bandwidth: 85,
    connectionState: 'CONNECTING',
    isRecording: false,
    timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
    gpsLat: 63.1342,
    gpsLon: -149.9739,
  });

  const qualityBitrates = {
    HIGH: 3500,
    MEDIUM: 2000,
    LOW: 800,
  };

  const qualityResolutions = {
    HIGH: 1280,
    MEDIUM: 640,
    LOW: 320,
  };

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
  }, []);

  // Update timestamp and metrics every second
  useEffect(() => {
    const metricsInterval = setInterval(() => {
      setMetrics((prev) => ({
        ...prev,
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
        // Simulate battery drain (0.1% per 10s = 0.6% per min)
        battery: Math.max(0, prev.battery - 0.017),
        // Simulate signal variation
        signal: Math.max(30, Math.min(100, prev.signal + (Math.random() - 0.5) * 5)),
        // Simulate bandwidth variation
        bandwidth: Math.max(20, Math.min(100, prev.bandwidth + (Math.random() - 0.5) * 8)),
      }));
    }, 1000);

    return () => clearInterval(metricsInterval);
  }, []);

  // Frame counter
  useEffect(() => {
    const interval = setInterval(() => {
      setFrameCount((prev) => (prev + 1) % 1000);
    }, 100);
    return () => clearInterval(interval);
  }, []);

  // Adaptive bitrate based on bandwidth/signal
  useEffect(() => {
    const currentBitrate = qualityBitrates[quality];
    const targetBitrate = Math.round(
      currentBitrate * (metrics.bandwidth / 100) * 0.8 // 80% of available bandwidth
    );

    setMetrics((prev) => ({
      ...prev,
      bitrate: targetBitrate,
    }));

    // Auto-degrade quality on poor signal
    if (metrics.signal < 40 && quality === 'HIGH') {
      setQuality('MEDIUM');
    } else if (metrics.signal < 25 && quality === 'MEDIUM') {
      setQuality('LOW');
    }
  }, [metrics.bandwidth, metrics.signal, quality]);

  // Connection state machine
  useEffect(() => {
    if (!selectedCamera || selectedCamera.status === 'OFFLINE') {
      setMetrics((prev) => ({ ...prev, connectionState: 'OFFLINE' }));
      return;
    }

    if (!isPlaying) {
      return;
    }

    // Initiate stream connection
    const connectStream = async () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      setMetrics((prev) => ({ ...prev, connectionState: 'CONNECTING' }));

      try {
        // Simulate connection timeout check (3 seconds)
        const connectionTimeout = new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Connection timeout')), 3000)
        );

        // Attempt to load stream
        if (streamRef.current && selectedCamera.streamUrl) {
          const imgPromise = new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => {
              resolve(img);
              reconnectAttemptsRef.current = 0;
              setMetrics((prev) => ({
                ...prev,
                connectionState: 'CONNECTED',
                isRecording: true,
              }));
            };
            img.onerror = () => reject(new Error('Stream load failed'));
            img.src = selectedCamera.streamUrl!;
          });

          await Promise.race([imgPromise, connectionTimeout]);
        }
      } catch (error) {
        setMetrics((prev) => ({ ...prev, connectionState: 'RECONNECTING' }));

        // Exponential backoff reconnect: 1s → 2s → 4s → 8s (max 10s)
        const backoffMs = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
        reconnectAttemptsRef.current++;

        reconnectTimeoutRef.current = setTimeout(() => {
          connectStream();
        }, backoffMs);
      }
    };

    connectStream();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [selectedCamera, isPlaying]);

  // HUD overlay rendering on canvas (60fps target)
  useEffect(() => {
    const renderHUD = () => {
      const canvas = canvasRef.current;
      const stream = streamRef.current;

      if (!canvas || !stream) {
        animationFrameRef.current = requestAnimationFrame(renderHUD);
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        animationFrameRef.current = requestAnimationFrame(renderHUD);
        return;
      }

      // Clear canvas
      ctx.fillStyle = 'rgba(0, 0, 0, 0)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const fontSize = 12;
      const lineHeight = 14;
      ctx.font = `${fontSize}px monospace`;
      ctx.fillStyle = '#FB8B24'; // Amber demoscene color

      // Top-left HUD: Node ID, Timestamp, Recording indicator
      ctx.fillText(`${selectedCamera?.id || 'N/A'}`, 8, 20);
      ctx.fillText(`${metrics.timestamp}`, 8, 20 + lineHeight);
      ctx.fillText(`● REC`, 8, 20 + lineHeight * 2);

      // Top-right HUD: Signal, Battery
      const signalStr = `◐ ${Math.round(metrics.signal)}%`;
      const batteryStr = `🔋 ${Math.round(metrics.battery)}%`;
      const signalWidth = ctx.measureText(signalStr).width;
      const batteryWidth = ctx.measureText(batteryStr).width;

      ctx.fillText(signalStr, canvas.width - signalWidth - 8, 20);
      ctx.fillText(batteryStr, canvas.width - batteryWidth - 8, 20 + lineHeight);

      // Bottom bar: GPS, Bitrate, Connection status
      const gpsStr = `GPS: ${metrics.gpsLat.toFixed(2)}° ${metrics.gpsLon.toFixed(2)}°`;
      const bitrateStr = `${Math.round(metrics.bitrate)} kbps`;
      const connStatus =
        metrics.connectionState === 'CONNECTED'
          ? '● CONN'
          : metrics.connectionState === 'RECONNECTING'
            ? '◐ RECON'
            : '◯ OFFLINE';

      ctx.fillStyle = '#50D8D7'; // Turquoise accent
      ctx.fillText(gpsStr, 8, canvas.height - 8);
      ctx.fillText(bitrateStr, canvas.width / 2 - 50, canvas.height - 8);
      ctx.fillText(connStatus, canvas.width - 80, canvas.height - 8);

      animationFrameRef.current = requestAnimationFrame(renderHUD);
    };

    animationFrameRef.current = requestAnimationFrame(renderHUD);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [selectedCamera, metrics]);

  const handleCameraSelect = useCallback(
    (camera: CameraNode) => {
      if (camera.status !== 'OFFLINE') {
        setSelectedCamera(camera);
        reconnectAttemptsRef.current = 0;
        setMetrics((prev) => ({ ...prev, connectionState: 'CONNECTING' }));
      }
    },
    []
  );

  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const handleQualityChange = useCallback((newQuality: StreamQuality) => {
    setQuality(newQuality);
  }, []);

  const handleSnapshot = useCallback(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = `snapshot-${selectedCamera?.id}-${Date.now()}.png`;
    link.click();
  }, [selectedCamera]);

  const handleFullscreen = useCallback(() => {
    const container = document.querySelector('[data-camera-viewer]');
    if (container && !isFullscreen) {
      container.requestFullscreen?.().catch(() => {
        setIsFullscreen(true);
      });
    } else if (document.fullscreenElement) {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  }, [isFullscreen]);

  // Loading spinner component
  const LoadingSpinner = () => (
    <div
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          fontSize: '32px',
          animation: 'spin 1s linear infinite',
        }}
      >
        ⟳
      </div>
      <TeletextText color="cyan">CONNECTING...</TeletextText>
    </div>
  );

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>

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

          {/* Right panel - Video stream + controls */}
          <div style={{ flex: 1 }}>
            {selectedCamera ? (
              <>
                <TeletextText color="cyan">
                  STREAM: {selectedCamera.callsign} ({selectedCamera.id})
                </TeletextText>
                <br />
                <br />

                {/* Video container with HUD overlay */}
                <div
                  data-camera-viewer
                  style={{
                    border: '2px solid #00FFFF',
                    backgroundColor: '#001a1a',
                    minHeight: '400px',
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    aspectRatio: '16/9',
                    overflow: 'hidden',
                  }}
                >
                  {/* Hidden stream source */}
                  <img
                    ref={streamRef}
                    style={{ display: 'none' }}
                    alt="Stream"
                    onError={() => {
                      setMetrics((prev) => ({
                        ...prev,
                        connectionState: 'OFFLINE',
                        isRecording: false,
                      }));
                    }}
                  />

                  {/* Canvas for rendering stream + HUD overlay */}
                  {selectedCamera.status === 'ONLINE' && selectedCamera.streamUrl ? (
                    <>
                      <canvas
                        ref={canvasRef}
                        width={qualityResolutions[quality]}
                        height={Math.round((qualityResolutions[quality] * 9) / 16)}
                        style={{
                          width: '100%',
                          height: '100%',
                          display:
                            metrics.connectionState === 'CONNECTED' ? 'block' : 'none',
                          objectFit: 'contain',
                          backgroundColor: '#000',
                        }}
                      />

                      {/* Connection status overlay */}
                      {metrics.connectionState === 'CONNECTING' && <LoadingSpinner />}
                      {metrics.connectionState === 'RECONNECTING' && (
                        <div
                          style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            textAlign: 'center',
                          }}
                        >
                          <TeletextText color="yellow">◐ RECONNECTING...</TeletextText>
                        </div>
                      )}
                    </>
                  ) : (
                    <TeletextText color="yellow">
                      [ STREAM UNAVAILABLE - NODE DEGRADED ]
                    </TeletextText>
                  )}

                  {/* Hidden snapshot canvas */}
                  <canvas ref={snapshotCanvasRef} style={{ display: 'none' }} />
                </div>

                {/* Control bar */}
                <div
                  style={{
                    marginTop: '12px',
                    display: 'flex',
                    gap: '8px',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                  }}
                >
                  {/* Play/Pause */}
                  <button
                    onClick={handlePlayPause}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#FB8B24',
                      color: '#000',
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: 'bold',
                      fontFamily: 'monospace',
                    }}
                  >
                    {isPlaying ? '⏸ PAUSE' : '▶ PLAY'}
                  </button>

                  {/* Quality selector */}
                  <select
                    value={quality}
                    onChange={(e) => handleQualityChange(e.target.value as StreamQuality)}
                    style={{
                      padding: '6px 8px',
                      backgroundColor: '#636764',
                      color: '#FB8B24',
                      border: '1px solid #FB8B24',
                      cursor: 'pointer',
                      fontFamily: 'monospace',
                    }}
                  >
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>

                  {/* Snapshot */}
                  <button
                    onClick={handleSnapshot}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#50D8D7',
                      color: '#000',
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: 'bold',
                      fontFamily: 'monospace',
                    }}
                  >
                    📸 SNAP
                  </button>

                  {/* Fullscreen */}
                  <button
                    onClick={handleFullscreen}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#3B60E4',
                      color: '#FFF',
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: 'bold',
                      fontFamily: 'monospace',
                    }}
                  >
                    ⛶ FS
                  </button>

                  {/* Quality info */}
                  <TeletextText color="cyan" style={{ marginLeft: 'auto' }}>
                    {quality} | {Math.round(metrics.bitrate)} kbps
                  </TeletextText>
                </div>

                {/* Status bars */}
                <div style={{ marginTop: '12px' }}>
                  <StatusBar
                    value={metrics.signal}
                    color={metrics.signal > 60 ? 'cyan' : metrics.signal > 30 ? 'yellow' : 'magenta'}
                    label="SIGNAL"
                  />
                  <StatusBar
                    value={metrics.bandwidth}
                    color={metrics.bandwidth > 70 ? 'cyan' : metrics.bandwidth > 40 ? 'yellow' : 'magenta'}
                    label="LINK"
                  />
                  <StatusBar
                    value={metrics.battery}
                    color={metrics.battery > 50 ? 'green' : metrics.battery > 20 ? 'yellow' : 'magenta'}
                    label="BATTERY"
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
          Quality auto-degrades on poor signal | Snapshots saved to Downloads
        </TeletextText>
      </div>
    </div>
  );
};

export default P500;
