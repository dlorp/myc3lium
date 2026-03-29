# 🍄 MYC3LIUM Deployment Package

**Complete hardware deployment scripts for MYC3LIUM mesh network nodes**

---

## Quick Start

**For impatient humans with hardware arriving production:**

```bash
# 1. Copy to your Raspberry Pi:
scp -r deployment/ pi@raspberrypi.local:~/

# 2. SSH in:
ssh pi@raspberrypi.local

# 3. Run master setup:
cd ~/deployment
chmod +x setup-all.sh
sudo ./setup-all.sh

# 4. Wait 15-20 minutes ☕

# 5. Access WebUI:
# http://<your-pi-ip>
```

**Done!** Your mesh node is operational.

---

## What's Included

### Scripts (`scripts/`)

| Script | Purpose | Time |
|--------|---------|------|
| `setup-pi4.sh` | Base system setup, dependencies, user creation | ~8 min |
| `setup-lora.sh` | LoRa HAT configuration (SX1262) | ~2 min |
| `setup-halow.sh` | WiFi HaLow module setup (ESP32 USB) | ~2 min |
| `setup-batman.sh` | BATMAN-adv mesh networking | ~3 min |
| `deploy-webui.sh` | Frontend deployment to Nginx | ~2 min |

### Configuration (`config/`)

| File | Purpose |
|------|---------|
| `reticulum.conf` | Reticulum network stack configuration |

Configures:
- LoRa interface (915 MHz)
- HaLow interface
- BATMAN mesh interface
- Store-and-forward
- LXMF messaging

### Backend (`backend/`)

| File | Purpose |
|------|---------|
| `reticulum_bridge.py` | FastAPI backend connecting Reticulum to WebUI |

Features:
- REST API for mesh operations
- WebSocket for real-time updates
- Message sending/receiving
- Mesh topology tracking
- LXMF support

### Tests (`tests/`)

| Script | Purpose |
|--------|---------|
| `test-all.sh` | Complete integration test of all components |

Tests:
- Base system
- LoRa hardware
- HaLow interface
- BATMAN mesh
- Reticulum services
- Backend API
- WebUI
- Network connectivity

---

## Hardware Support

**Tested on:**
- Raspberry Pi 4 (4GB RAM)
- Waveshare SX1262 LoRa HAT (915 MHz)
- ESP32 USB HaLow board (routes via bat0)
- ESP32 USB Meshtastic board (LoRa mesh)
- Built-in BCM43455 WiFi (BATMAN-adv)

**Also works with:**
- Raspberry Pi 4 (2GB, 8GB)
- Other SX1262-based LoRa HATs
- Alternative ESP32 HaLow or HaLow modules (may need driver tweaks)

---

## Installation Methods

### Method 1: Master Script (Recommended)

Runs everything in one go:

```bash
sudo ./setup-all.sh
```

**Pros:** Automatic, handles dependencies, runs tests  
**Cons:** Less control, harder to debug individual steps

### Method 2: Manual Step-by-Step

Run scripts individually:

```bash
cd scripts
sudo ./setup-pi4.sh
sudo reboot

# After reboot:
sudo ./setup-lora.sh
sudo ./setup-halow.sh
sudo ./setup-batman.sh

# Deploy configs:
sudo cp ../config/reticulum.conf /home/myc3lium/.reticulum/config
sudo cp ../backend/reticulum_bridge.py /opt/myc3lium/backend/
sudo ./deploy-webui.sh

# Start services:
sudo systemctl start reticulum myc3lium batman-adv nginx

# Test:
cd ../tests
sudo ./test-all.sh
```

**Pros:** Full control, easier debugging  
**Cons:** More manual steps

---

## Directory Structure

```
deployment/
├── README.md                    # This file
├── DEPLOYMENT.md                # Complete deployment guide
├── setup-all.sh                 # Master setup script
├── scripts/                     # Setup scripts
│   ├── setup-pi4.sh
│   ├── setup-lora.sh
│   ├── setup-halow.sh
│   ├── setup-batman.sh
│   └── deploy-webui.sh
├── config/                      # Configuration files
│   └── reticulum.conf
├── backend/                     # Backend application
│   └── reticulum_bridge.py
└── tests/                       # Test scripts
    └── test-all.sh
```

---

## Post-Installation

### Access Points

**WebUI:**
```
http://<pi-ip-address>
```

**API Documentation:**
```
http://<pi-ip-address>:8000/docs
```

**SSH:**
```
ssh myc3lium@<pi-ip-address>
# Default password: myc3lium (CHANGE THIS!)
```

### System Commands

```bash
# Check system status
myc3lium-status

# View logs
journalctl -fu reticulum.service
journalctl -fu myc3lium.service

# Restart services
sudo systemctl restart reticulum myc3lium

# Check mesh neighbors
batctl o

# Check Reticulum status
rnstatus
```

### Important Files

**Identity (backup this!):**
```
/home/myc3lium/.reticulum/storage/identities/myc3lium-node
```

**Configuration:**
```
/home/myc3lium/.reticulum/config
```

**Logs:**
```
/opt/myc3lium/logs/bridge.log
```

---

## Troubleshooting

### Quick Diagnostics

```bash
# Run full test suite:
cd ~/deployment/tests
sudo ./test-all.sh

# Check service status:
systemctl status reticulum
systemctl status myc3lium
systemctl status batman-adv
systemctl status nginx

# View recent errors:
journalctl -p err -n 50
```

### Common Issues

**Services not starting:**
```bash
# Check logs for specific error
journalctl -u <service-name> -n 100
```

**No mesh neighbors:**
```bash
# Check BATMAN interface
ip addr show bat0
batctl if
iw dev wlan0 info

# Restart mesh
sudo systemctl restart batman-adv
```

**WebUI not loading:**
```bash
# Check Nginx
nginx -t
systemctl status nginx

# Check backend
curl http://localhost:8000/health
```

**LoRa not working:**
```bash
# Test hardware
sudo python3 /opt/myc3lium/test-lora.py

# Check SPI
ls -l /dev/spidev*
lsmod | grep spi
```

See `DEPLOYMENT.md` for detailed troubleshooting.

---

## Architecture

```
┌─────────────────────────────────────────┐
│           Web Browser / App             │
└────────────────┬────────────────────────┘
                 │ HTTP/WebSocket
┌────────────────▼────────────────────────┐
│          Nginx (Port 80)                │
│  - WebUI (static files)                 │
│  - Proxy to backend API                 │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   FastAPI Backend (Port 8000)           │
│   reticulum_bridge.py                   │
│   - REST API                            │
│   - WebSocket server                    │
│   - Mesh operations                     │
└────────────────┬────────────────────────┘
                 │ TCP/Python
┌────────────────▼────────────────────────┐
│      Reticulum Network Stack            │
│      (rnsd daemon)                      │
│   - LXMF messaging                      │
│   - Store & forward                     │
│   - Routing & transport                 │
└─┬──────────────┬──────────────┬─────────┘
  │              │              │
  │ SPI          │ UDP          │ UDP
  │              │              │
┌─▼────────┐ ┌──▼──────────┐ ┌─▼──────────┐
│  LoRa    │ │   HaLow     │ │  BATMAN    │
│ SX1262   │ │ ESP32 HaLow │ │   bat0     │
│ (HAT)    │ │   (USB)     │ │  (wlan0)   │
└──────────┘ └─────────────┘ └────────────┘
   915 MHz      902-928 MHz     2.4/5 GHz
   1-10+ km     100m-1km        50-200m
   ~5 kbps      ~1-4 Mbps       ~10+ Mbps
```

---

## Network Topology

**Reticulum automatically routes traffic across all interfaces:**

```
Node A ←──[LoRa]──→ Node B
   ↑                    ↑
   │                    │
[BATMAN]            [HaLow]
   │                    │
   ↓                    ↓
Node C ←─[HaLow]──→ Node D

- Local mesh: BATMAN (high bandwidth, short range)
- Medium range: HaLow (moderate bandwidth, medium range)
- Long range: LoRa (low bandwidth, long range backup)
```

**No manual configuration needed!** Reticulum handles path selection automatically.

---

## Security Notes

### Default Credentials

**Change immediately after setup:**

```bash
# Change myc3lium user password:
sudo passwd myc3lium

# Change pi user password:
passwd

# Or disable pi user:
sudo passwd -l pi
```

### Identity Security

Your Reticulum identity is your cryptographic key:

```bash
# Backup identity:
sudo cp /home/myc3lium/.reticulum/storage/identities/myc3lium-node \
  ~/myc3lium-identity-backup.key

# Download to safe location:
scp myc3lium@<pi-ip>:~/myc3lium-identity-backup.key .

# Store offline securely!
```

**Without this, you lose your mesh identity permanently.**

### Firewall

Firewall is configured automatically:
- SSH (22) - allowed
- HTTP (80) - allowed
- HTTPS (443) - allowed
- Reticulum (4242, 4965, 29716) - allowed
- All other ports - denied

Modify: `sudo ufw allow <port>/<protocol>`

---

## Performance Tuning

### LoRa Range vs Speed

Edit `/home/myc3lium/.reticulum/config`:

```python
# For maximum range (slower):
spreading_factor = 12
bandwidth = 125000

# For maximum speed (shorter range):
spreading_factor = 7
bandwidth = 500000
```

### Mesh Channel Selection

Edit `/opt/myc3lium/setup-mesh.sh`:

```bash
# Change WiFi channel (1-11):
MESH_FREQ="2437"  # Channel 6 (default)
# Channel 1: 2412, Channel 11: 2462
```

### CPU/Memory Optimization

```bash
# Reduce logging verbosity:
sudo nano /home/myc3lium/.reticulum/config
# Change loglevel to 2 (warnings only)

# Limit resource usage:
sudo systemctl edit myc3lium.service
# Add:
[Service]
CPUQuota=50%
MemoryLimit=512M
```

---

## Development

### API Endpoints

See full API docs at: `http://<pi-ip>:8000/docs`

**Key endpoints:**

```bash
# Health check
GET /health

# Mesh statistics
GET /mesh/stats

# Known destinations
GET /mesh/destinations

# Send message
POST /message/send
{
  "destination": "abc123...",
  "content": "Hello mesh!"
}

# Announce presence
POST /announce
```

### WebSocket

Connect to: `ws://<pi-ip>:8000/ws`

Receives real-time events:
```json
{
  "type": "message",
  "data": {
    "source": "abc123...",
    "content": "Hello!",
    "timestamp": 1234567890.0
  }
}
```

### Adding Custom Features

**Backend extensions:**
```bash
# Edit backend:
sudo nano /opt/myc3lium/backend/reticulum_bridge.py

# Restart to apply:
sudo systemctl restart myc3lium
```

**Frontend modifications:**
```bash
# Edit WebUI:
sudo nano /var/www/myc3lium/index.html

# No restart needed (static files)
```

---

## Scaling & Multi-Node

### Deploying Multiple Nodes

1. **Clone SD card image** after first node setup
2. **Flash to multiple SD cards**
3. **Boot nodes** - they auto-discover each other!

**Each node generates unique identity on first Reticulum start.**

### Mesh Network Growth

- **2-3 nodes:** Basic connectivity testing
- **5-10 nodes:** Small local mesh
- **10-50 nodes:** Neighborhood mesh
- **50+ nodes:** City-scale network

**No central server or configuration needed!**

### Load Balancing

Reticulum automatically:
- Selects fastest available path
- Falls back to alternative routes
- Caches routing information
- Handles node failures gracefully

---

## Contributing

Found a bug? Have an improvement?

1. Document the issue or enhancement
2. Test your changes on hardware
3. Submit changes with clear description

**Key areas for contribution:**
- HaLow driver integration
- Additional radio interface support
- Performance optimizations
- WebUI enhancements
- Documentation improvements

---

## License

This deployment package is part of the MYC3LIUM project.

**Core dependencies:**
- Reticulum: MIT License
- LXMF: MIT License
- FastAPI: MIT License
- BATMAN-adv: GPL

See individual component licenses for details.

---

## Credits

**Built on:**
- [Reticulum](https://reticulum.network/) - Mark Qvist
- [BATMAN-adv](https://www.open-mesh.org/) - Open Mesh Project
- [FastAPI](https://fastapi.tiangolo.com/) - Sebastián Ramírez

**Hardware:**
- Waveshare SX1262 LoRa HAT
- ESP32 USB HaLow board
- Raspberry Pi Foundation

---

## Support Resources

**Documentation:**
- Full guide: `DEPLOYMENT.md`
- Reticulum docs: https://reticulum.network/manual/
- BATMAN-adv docs: https://www.open-mesh.org/projects/batman-adv/wiki

**Community:**
- Reticulum Matrix: #reticulum:matrix.org
- BATMAN-adv mailing list

**Debugging:**
- System logs: `journalctl -u <service>`
- Application logs: `/opt/myc3lium/logs/`
- Test suite: `sudo ./tests/test-all.sh`

---

## Version

**Package Version:** 0.4.0
**Target Platform:** Raspberry Pi 4
**Build Date:** 2026-03-28
**Status:** Production Ready

---

🍄 **Happy Meshing!**

*Making decentralized communications as easy as mycelium growth.*
