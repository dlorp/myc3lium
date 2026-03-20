# MYC3LIUM ESP32-S3 CAM Firmware

MJPEG streaming camera node with mesh integration.

## Hardware

- **Board:** Heltec ESP32-S3 CAM
- **Camera:** OV3660 (2MP)
- **Storage:** PSRAM
- **Connectivity:** WiFi 2.4GHz

## Features

- MJPEG streaming (800x600 @ 10 FPS)
- WebSocket connection to intelligence API
- ATAK integration (stream URL broadcast)
- Motion detection (coming soon)
- Low-power sleep modes

## Build & Flash

### Using PlatformIO

```bash
# Install PlatformIO
pip install platformio

# Build firmware
cd firmware/esp32_cam
pio run

# Upload to ESP32
pio run --target upload

# Monitor serial output
pio device monitor
```

### Configuration

Edit `src/main.cpp`:

```cpp
const char* WIFI_SSID = "MYCELIUM_MESH";
const char* WIFI_PASSWORD = "your_mesh_password";
const char* WS_SERVER = "ws://192.168.1.100:8000/ws/intelligence";
const char* API_TOKEN = "your_api_token_here";  // From intelligence API startup
const char* NODE_ID = "m3l_cam_01";
```

## Streaming

Once connected, camera streams to:

```
http://<ESP32_IP>:8080/stream
```

View in browser or VLC:
```bash
vlc http://192.168.1.101:8080/stream
```

## ATAK Integration

Automatically broadcasts stream URL via WebSocket heartbeat:

```json
{
  "type": "heartbeat",
  "node_id": "m3l_cam_01",
  "stream_url": "http://192.168.1.101:8080/stream"
}
```

Intelligence API converts to CoT video feed for ATAK display.

## Power Consumption

- **Active streaming:** ~150mA @ 3.3V
- **WiFi connected, idle:** ~80mA
- **Deep sleep:** ~10µA (coming soon)

With 18650 UPS HAT (2600mAh):
- Continuous streaming: ~17 hours
- Motion-triggered (1 min/hour): ~300 hours

## Troubleshooting

**Camera init failed:**
- Check camera ribbon cable connection
- Verify PSRAM detected (`psramFound()` returns true)

**WiFi won't connect:**
- Verify SSID/password correct
- Check 2.4GHz band enabled on mesh router
- Try static IP if DHCP fails

**WebSocket disconnects:**
- Check API_TOKEN matches server
- Verify intelligence API running on specified IP:port
- Check firewall rules

## Pin Configuration

See `main.cpp` for full pin mapping (ESP32-S3-CAM specific).
