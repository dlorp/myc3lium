# myc3lium - Technology Stack

**Last Updated:** 2026-03-15  
**Target Platform:** Raspberry Pi 4 (4GB RAM)  
**OS:** Raspberry Pi OS 64-bit (Debian 12 Bookworm)

---

## Python Environment

**Version:** Python 3.11+

**Core Dependencies:**

```txt
# GUI Framework
PyQt6==6.6.0
PyQt6-Qt6==6.6.0
PyOpenGL==3.1.7
ModernGL==5.10.0

# Graphics
Pillow==10.2.0
numpy==1.26.0

# Mesh Networking
rns==0.7.0              # Reticulum Network Stack
lxmf==0.4.0             # Encrypted messaging over RNS
nomadnet==0.4.0         # Optional: CLI mesh client

# SDR
SoapySDR==0.8.1
pyorbital==1.8.2        # Satellite tracking (TLE)

# GPS
gpsd-py3==0.3.0

# Configuration
toml==0.10.2

# System
psutil==5.9.8           # CPU/RAM monitoring
smbus2==0.4.3           # I2C (battery HAT)

# Development
pytest==8.0.0
black==24.1.0
```

**Install:**
```bash
pip3 install -r requirements.txt
```

---

## System Packages (apt)

```bash
# Core system
sudo apt update
sudo apt install -y \
    python3-pyqt6 \
    python3-pyqt6.qtopengl \
    python3-opengl \
    python3-numpy \
    python3-pil
```

**Mesh Networking:**
```bash
sudo apt install -y reticulum
# Or via pip: pip3 install rns lxmf
```

**SDR:**
```bash
sudo apt install -y \
    soapysdr-tools \
    soapysdr-module-rtlsdr \
    rtl-sdr \
    satdump           # Satellite decoder
```

**GPS:**
```bash
sudo apt install -y \
    gpsd \
    gpsd-clients \
    python3-gps
```

**Map Tools:**
```bash
sudo apt install -y \
    gdal-bin          # gdal2tiles.py for custom maps
    sqlite3           # MBTiles inspection
```

**Optional (development):**
```bash
sudo apt install -y \
    git \
    vim \
    tmux \
    htop
```

---

## Systemd Services

**1. Main GUI** (`/etc/systemd/system/mesh-gui.service`)

```ini
[Unit]
Description=Mesh Terminal GUI
After=network.target reticulum.service gpsd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/myc3lium
Environment="QT_QPA_PLATFORM=eglfs"
Environment="QT_QPA_EGLFS_ALWAYS_SET_MODE=1"
ExecStart=/usr/bin/python3 /home/pi/myc3lium/src/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**2. Reticulum Daemon** (`/etc/systemd/system/reticulum.service`)

```ini
[Unit]
Description=Reticulum Network Stack
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/rnsd --config /home/pi/.reticulum
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. Meshtastic Bridge** (`/etc/systemd/system/meshtastic-bridge.service`)

```ini
[Unit]
Description=Meshtastic Serial Bridge
After=network.target reticulum.service
Requires=reticulum.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mesh-terminal-gui
ExecStart=/usr/bin/python3 /home/pi/mesh-terminal-gui/src/daemons/meshtastic_bridge.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**4. SDR Manager** (`/etc/systemd/system/sdr-manager.service`)

```ini
[Unit]
Description=SDR Manager (Satellite Tracking)
After=network.target gpsd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mesh-terminal-gui
ExecStart=/usr/bin/python3 /home/pi/mesh-terminal-gui/src/daemons/sdr_manager.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**5. GPS Daemon** (already installed)

```bash
sudo systemctl enable gpsd.service
sudo systemctl start gpsd.service
```

**Enable all:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mesh-gui reticulum meshtastic-bridge sdr-manager
sudo systemctl start mesh-gui reticulum meshtastic-bridge sdr-manager
```

---

## EGLFS Configuration

**Display Setup** (direct framebuffer, no X11)

Edit `/boot/config.txt`:
```ini
# Enable VC4 graphics
dtoverlay=vc4-kms-v3d

# Allocate GPU memory
gpu_mem=256

# Optional: Force HDMI mode
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0  # For 1024x600 display
```

**Qt EGLFS Environment:**
```bash
export QT_QPA_PLATFORM=eglfs
export QT_QPA_EGLFS_ALWAYS_SET_MODE=1
export QT_QPA_EGLFS_PHYSICAL_WIDTH=154   # mm (adjust for your display)
export QT_QPA_EGLFS_PHYSICAL_HEIGHT=85   # mm
```

Add to `/etc/environment`:
```
QT_QPA_PLATFORM=eglfs
QT_QPA_EGLFS_ALWAYS_SET_MODE=1
```

**Test:**
```bash
QT_QPA_PLATFORM=eglfs python3 src/main.py
```

---

## GLSL Shader Files

**Directory:** `src/shaders/`

**Text Rendering:**
- `text.vert` - Vertex shader (character grid positioning)
- `text.frag` - Fragment shader (glyph atlas sampling + color)

**Map Rendering:**
- `map.vert` - Vertex shader (Web Mercator projection)
- `map.frag` - Fragment shader (tile sampling + teletext quantization)

**Post-Processing:**
- `crt.frag` - CRT effects (scanlines, vignette, phosphor glow, curvature)

**SDR Waterfall:**
- `waterfall.frag` - FFT waterfall (color map + scroll)

**Common:**
- `common.glsl` - Shared functions (teletext palette, Bayer dithering)

**Example:** `src/shaders/text.frag`
```glsl
#version 300 es
precision highp float;

uniform sampler2D u_glyphAtlas;
uniform vec3 u_palette[8];
uniform int u_colorIndex;

in vec2 v_texCoord;
out vec4 fragColor;

void main() {
    float alpha = texture(u_glyphAtlas, v_texCoord).r;
    vec3 color = u_palette[u_colorIndex];
    fragColor = vec4(color * alpha, alpha);
}
```

---

## Reticulum Configuration

**Location:** `~/.reticulum/config`

**Example:**
```ini
[reticulum]
  enable_transport = True
  share_instance = Yes
  shared_instance_port = 37428
  instance_control_port = 37429

[interfaces]
  [[RNode LoRa]]
    type = RNodeInterface
    enabled = True
    port = /dev/ttyUSB0
    frequency = 915000000
    bandwidth = 125000
    txpower = 17
    spreadingfactor = 8
    codingrate = 5

  [[WiFi HaLow]]
    type = AutoInterface
    enabled = True
    interface_name = wlan1
    group_id = reticulum-mesh

  [[WiFi Mesh]]
    type = AutoInterface
    enabled = True
    interface_name = bat0
    group_id = reticulum-mesh
```

**Identify LoRa serial port:**
```bash
ls -l /dev/ttyUSB* /dev/ttyACM*
# Or: dmesg | grep tty
```

---

## GPS Configuration

**Location:** `/etc/default/gpsd`

```bash
# Serial device for GNSS on LoRa HAT
DEVICES="/dev/ttyAMA0"

# gpsd options
GPSD_OPTIONS="-n -G"

# Start on boot
START_DAEMON="true"
```

**Enable serial on GPIO:**
Edit `/boot/config.txt`:
```ini
enable_uart=1
dtoverlay=disable-bt
```

**Test:**
```bash
cgps -s
# Should show GPS fix data
```

---

## Map Data Structure

**Storage:** `data/maps/`

**MBTiles Format:**
```
data/maps/
├── osm-street.mbtiles          # OSM street map
├── osm-topo.mbtiles            # Topographic
├── satellite.mbtiles           # Satellite imagery
└── custom/
    └── meteor-20260315.mbtiles # Custom SDR capture
```

**MBTiles Schema** (SQLite):
```sql
CREATE TABLE metadata (
    name TEXT,
    value TEXT
);

CREATE TABLE tiles (
    zoom_level INTEGER,
    tile_column INTEGER,
    tile_row INTEGER,
    tile_data BLOB
);

CREATE UNIQUE INDEX tile_index ON tiles (
    zoom_level, tile_column, tile_row
);
```

**Query tiles:**
```sql
SELECT tile_data FROM tiles
WHERE zoom_level = 14
  AND tile_column = 2745
  AND tile_row = 6312;
```

---

## Message Database

**Location:** `data/messages.db`

**Schema:**
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,  -- Unix timestamp
    sender TEXT NOT NULL,         -- Node ID or name
    recipient TEXT NOT NULL,      -- Node ID, "ALL", or channel
    transport TEXT NOT NULL,      -- "meshtastic", "lxmf-lora", "lxmf-halow", "lxmf-wifi"
    body TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT 1,
    read BOOLEAN DEFAULT 0,
    direction TEXT NOT NULL       -- "inbound" or "outbound"
);

CREATE INDEX idx_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_read ON messages(read);
```

**Query inbox:**
```sql
SELECT * FROM messages
WHERE direction = 'inbound'
  AND read = 0
ORDER BY timestamp DESC
LIMIT 20;
```

---

## Configuration Schema

**Location:** `data/config/user.toml`

**Example:**
```toml
[display]
resolution = [1024, 600]
brightness = 100  # Percent
crt_effects = true
fps_target = 60

[radios]
  [radios.lora]
  enabled = true
  frequency = 915.0  # MHz
  bandwidth = 125    # kHz
  spreading_factor = 8
  tx_power = 17      # dBm

  [radios.halow]
  enabled = true
  frequency = 915.0  # MHz
  channel = "auto"
  tx_power = 20      # dBm

  [radios.wifi_mesh]
  enabled = true
  band = "2.4"       # "2.4" or "5"
  channel = 11
  mode = "802.11s"

[mesh]
announce_interval = 300  # seconds
enable_transport = true

[maps]
cache_size = 512         # MB
default_zoom = 14
tile_sources = [
    "data/maps/osm-street.mbtiles",
    "data/maps/osm-topo.mbtiles"
]

[sdr]
enabled = true
device = "rtlsdr"
sample_rate = 2048000    # 2.048 MHz
gain = 30                # dB
upconverter = true
upconverter_offset = 125000000  # 125 MHz

  [sdr.satellites]
  track = ["NOAA 19", "NOAA 18", "METEOR-M N2-3"]
  auto_capture = true
  pre_warm_seconds = 120

[power]
mode = "normal"          # "normal", "eco", "ultra_save"
low_battery_threshold = 30   # Percent (switch to ECO)
critical_battery = 15        # Percent (switch to ULTRA_SAVE)
shutdown_battery = 5         # Percent (auto-shutdown)
```

---

## Development Setup

**Desktop Development (X11/Wayland):**

```bash
git clone <repo-url> mesh-terminal-gui
cd mesh-terminal-gui
pip3 install -r requirements.txt
python3 src/main.py --dev
```

**`--dev` flag:**
- Uses X11/Wayland instead of EGLFS
- Mock GPS (fixed position: Anchorage)
- Mock radios (simulated mesh nodes)
- Hot reload on file changes

**Mock Configuration:**
Create `data/config/dev.toml`:
```toml
[dev]
mock_gps = true
mock_radios = true
mock_nodes = [
    {name = "NODE_02", lat = 61.2245, lon = -149.8876},
    {name = "NODE_03", lat = 61.2198, lon = -149.9156}
]
```

---

## Build & Deployment

**Build Script:** `build.sh`

```bash
#!/bin/bash
# Build for Raspberry Pi 4

set -e

echo "Building mesh-terminal-gui for Pi 4..."

# Create dist directory
mkdir -p dist

# Copy source
cp -r src data assets systemd dist/

# Generate requirements
pip3 freeze > dist/requirements.txt

# Create tarball
tar -czf dist/mesh-terminal-gui-pi4.tar.gz -C dist .

echo "Build complete: dist/mesh-terminal-gui-pi4.tar.gz"
```

**Deploy to Pi 4:**
```bash
scp dist/mesh-terminal-gui-pi4.tar.gz pi@192.168.1.100:~/
ssh pi@192.168.1.100
tar -xzf mesh-terminal-gui-pi4.tar.gz
cd mesh-terminal-gui
sudo ./install.sh
```

**Install Script:** `install.sh`

```bash
#!/bin/bash
# Install on Raspberry Pi 4

set -e

echo "Installing mesh-terminal-gui..."

# Install dependencies
sudo apt update
sudo apt install -y \
    python3-pyqt6 \
    python3-opengl \
    reticulum \
    gpsd \
    soapysdr-module-rtlsdr \
    satdump

pip3 install -r requirements.txt

# Install systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mesh-gui reticulum meshtastic-bridge sdr-manager

# Configure EGLFS
echo "QT_QPA_PLATFORM=eglfs" | sudo tee -a /etc/environment

echo "Installation complete!"
echo "Reboot and GUI will auto-start."
```

---

## API Integration Points

**For future plugins/extensions:**

**1. Mesh Manager API:**
```python
from core.mesh_manager import MeshManager

mesh = MeshManager()
nodes = mesh.get_nodes()  # List of mesh nodes
mesh.send_message(destination, body)
mesh.get_link_quality(node_id)
```

**2. Map Engine API:**
```python
from core.map_engine import MapEngine

map_engine = MapEngine("data/maps/osm-street.mbtiles")
tile = map_engine.get_tile(zoom=14, x=2745, y=6312)
lat, lon = map_engine.screen_to_latlon(screen_x, screen_y)
```

**3. SDR Engine API:**
```python
from core.sdr_engine import SDREngine

sdr = SDREngine()
sdr.set_frequency(915.0e6)
sdr.set_gain(30)
fft_data = sdr.get_fft()  # numpy array
```

**4. Message Router API:**
```python
from core.message_router import MessageRouter

router = MessageRouter()
router.send(recipient, body, transport="auto")
messages = router.get_inbox(unread_only=True)
```

---

## Logging

**Configuration:** `src/core/logging_config.py`

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('data/logs/mesh-gui.log'),
        logging.StreamHandler()
    ]
)
```

**View logs:**
```bash
tail -f data/logs/mesh-gui.log
journalctl -u mesh-gui -f
```

---

## Testing

**Unit Tests:** `tests/`

```bash
pytest tests/
```

**Integration Tests:**
```bash
pytest tests/integration/
```

**Hardware Tests** (on Pi 4):
```bash
sudo pytest tests/hardware/ --hardware
```

---

## License

**Code:** MIT License (permissive)

**PyQt6:** GPL v3 (copyleft)
- **Implication:** Your GUI must be GPL-licensed if distributed
- **Alternative:** Purchase PyQt6 commercial license (~$500/year) for proprietary use

**Reticulum/LXMF:** MIT License

**SoapySDR:** Boost Software License (permissive)

---

## Performance Benchmarks

**Target (Pi 4, 4GB):**
- GUI FPS: 60
- Map tile load: <200ms
- Message send: <1s
- SDR waterfall: 30 FPS
- RAM usage: ~2 GB (50%)
- CPU usage: <40% (idle), <80% (active)

**Actual** (to be measured in Phase 7):
- TBD

---

**Next:** See **SHADERS.md** and **MAPS.md** for rendering details.
