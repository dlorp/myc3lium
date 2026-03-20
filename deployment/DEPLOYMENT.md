# 🍄 MYC3LIUM Hardware Deployment Guide

**Quick Start Guide for production Deployment**

This guide will get your MYC3LIUM mesh node running in under 30 minutes.

---

## 📦 What's In The Box

**Hardware:**
- Raspberry Pi 4 (4GB RAM)
- Waveshare SX1262 LoRa HAT with GPS
- Heltec HT-HC01P WiFi HaLow module (USB)
- Waveshare UPS HAT or PiSugar 3 Plus
- 7-10" touchscreen
- MicroSD card (32GB+ recommended)
- Power supply

**Software (this package):**
- All setup scripts
- Reticulum configuration
- Backend API bridge
- WebUI interface
- Test scripts

---

## 🚀 Quick Start (30 Minutes)

### Step 1: Prepare SD Card (5 min)

1. **Download Raspberry Pi OS Lite:**
   ```bash
   # On your computer:
   # Download from: https://www.raspberrypi.com/software/operating-systems/
   # Choose: Raspberry Pi OS Lite (64-bit)
   ```

2. **Flash to SD card:**
   ```bash
   # Using Raspberry Pi Imager (recommended):
   # - Select "Raspberry Pi OS Lite (64-bit)"
   # - Select your SD card
   # - Click "Write"
   
   # Or using dd (Linux/Mac):
   sudo dd if=2024-xx-xx-raspios-lite-arm64.img of=/dev/sdX bs=4M status=progress
   sync
   ```

3. **Enable SSH (for headless setup):**
   ```bash
   # Mount boot partition and create empty ssh file:
   touch /Volumes/boot/ssh
   # or on Linux:
   touch /media/$USER/boot/ssh
   ```

4. **Configure WiFi (optional for initial setup):**
   ```bash
   # Create wpa_supplicant.conf on boot partition:
   cat > /Volumes/boot/wpa_supplicant.conf <<EOF
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1
   
   network={
       ssid="YourWiFiNetwork"
       psk="YourWiFiPassword"
   }
   EOF
   ```

### Step 2: First Boot & Initial Setup (10 min)

1. **Insert SD card and boot Pi:**
   - Insert SD card
   - Connect power
   - Wait 1-2 minutes for first boot
   - Pi will reboot once automatically

2. **SSH into Pi:**
   ```bash
   # Find Pi on network:
   ping raspberrypi.local
   # or scan network:
   sudo nmap -sn 192.168.1.0/24 | grep -i raspberry
   
   # SSH in (default password: raspberry):
   ssh pi@raspberrypi.local
   ```

3. **Copy deployment package to Pi:**
   ```bash
   # From your computer:
   scp -r deployment/ pi@raspberrypi.local:~/
   ```

4. **On the Pi, run base setup:**
   ```bash
   cd ~/deployment/scripts
   chmod +x *.sh
   sudo ./setup-pi4.sh
   ```

   This will:
   - Update system packages
   - Install all dependencies
   - Create myc3lium user
   - Configure services
   - Set up directory structure
   
   ⏱️ Takes ~5-8 minutes

5. **Reboot:**
   ```bash
   sudo reboot
   ```

### Step 3: Assemble Hardware (5 min)

**While Pi is rebooting, assemble the hardware:**

1. **Attach LoRa HAT:**
   - Power OFF the Pi
   - Carefully seat Waveshare SX1262 HAT onto GPIO pins
   - Press down firmly but gently
   - Ensure all pins are aligned

2. **Connect HaLow module:**
   - Plug Heltec HT-HC01P into USB port
   - Use USB 3.0 port (blue) for better power

3. **Attach UPS HAT (optional but recommended):**
   - Mount PiSugar or UPS HAT according to manufacturer instructions
   - Provides power backup and clean shutdown

4. **Connect touchscreen:**
   - Connect via DSI ribbon cable or HDMI
   - Touch via USB
   - Follow screen manufacturer instructions

5. **Power on and SSH back in:**
   ```bash
   ssh myc3lium@raspberrypi.local
   # Password: myc3lium (change this later!)
   ```

### Step 4: Configure Network Interfaces (10 min)

**Run setup scripts in order:**

1. **LoRa setup:**
   ```bash
   cd ~/deployment/scripts
   sudo ./setup-lora.sh
   ```
   
   Tests SPI connection and configures LoRa HAT.
   
2. **HaLow setup:**
   ```bash
   sudo ./setup-halow.sh
   ```
   
   Configures WiFi HaLow interface (may warn about drivers - see Troubleshooting).

3. **BATMAN mesh setup:**
   ```bash
   sudo ./setup-batman.sh
   ```
   
   Sets up mesh networking on built-in WiFi.

4. **Deploy Reticulum config:**
   ```bash
   sudo cp ~/deployment/config/reticulum-config.py /home/myc3lium/.reticulum/config
   sudo chown myc3lium:myc3lium /home/myc3lium/.reticulum/config
   ```

5. **Deploy backend:**
   ```bash
   sudo cp ~/deployment/backend/reticulum_bridge.py /opt/myc3lium/backend/
   sudo chown myc3lium:myc3lium /opt/myc3lium/backend/reticulum_bridge.py
   ```

6. **Deploy WebUI:**
   ```bash
   sudo ./deploy-webui.sh
   ```

### Step 5: Start Services & Test (5 min)

1. **Start all services:**
   ```bash
   sudo systemctl start reticulum.service
   sudo systemctl start myc3lium-backend.service
   sudo systemctl start batman-adv.service
   sudo systemctl start nginx
   ```

2. **Check status:**
   ```bash
   myc3lium-status
   ```

3. **Run integration test:**
   ```bash
   cd ~/deployment/tests
   sudo ./test-all.sh
   ```

4. **Access WebUI:**
   ```
   Open browser to: http://<pi-ip-address>
   
   You should see the MYC3LIUM mesh interface!
   ```

---

## 🧪 Testing

### Quick Tests

**Test LoRa:**
```bash
sudo -u myc3lium python3 /opt/myc3lium/test-lora.py
```

**Test HaLow:**
```bash
bash /opt/myc3lium/test-halow.sh
```

**Test BATMAN mesh:**
```bash
bash /opt/myc3lium/test-mesh.sh
```

**Test full system:**
```bash
cd ~/deployment/tests
sudo ./test-all.sh
```

### Manual Testing

**Check Reticulum status:**
```bash
rnstatus
```

**Check mesh neighbors:**
```bash
batctl o
```

**Send test message (between two nodes):**
```bash
# On node 1, get identity:
rnid /home/myc3lium/.reticulum/storage/identities/myc3lium-node

# On node 2, send message:
curl -X POST http://localhost:8000/message/send \
  -H "Content-Type: application/json" \
  -d '{"destination": "<node-1-hash>", "content": "Hello from node 2!"}'
```

---

## 📊 Monitoring

### System Status

```bash
myc3lium-status
```

Shows:
- Hostname and uptime
- Network interfaces
- Service status
- Storage and memory

### Service Logs

```bash
# Reticulum logs:
journalctl -fu reticulum.service

# Backend logs:
journalctl -fu myc3lium-backend.service
tail -f /opt/myc3lium/logs/bridge.log

# BATMAN mesh logs:
journalctl -fu batman-adv.service

# Nginx logs:
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Mesh Status

```bash
# BATMAN mesh status:
bash /opt/myc3lium/mesh-status.sh

# Reticulum network:
rnpath -v
rnprobe <destination-hash>
```

---

## 🛠️ Troubleshooting

### Common Issues

**1. LoRa HAT not detected**

```bash
# Check SPI is enabled:
ls /dev/spidev*
# Should show: /dev/spidev0.0

# Check kernel module:
lsmod | grep spi

# If missing, enable in /boot/config.txt:
sudo nano /boot/config.txt
# Add: dtparam=spi=on
sudo reboot
```

**2. HaLow module not detected**

```bash
# Check USB devices:
lsusb

# HaLow driver may need manual installation
# See: /opt/myc3lium/install-halow-driver.sh

# For now, system will work without HaLow (uses LoRa + BATMAN only)
```

**3. BATMAN mesh not starting**

```bash
# Check wlan0 status:
iw dev wlan0 info

# Manually start mesh:
sudo systemctl restart batman-adv.service

# Check logs:
journalctl -u batman-adv.service
```

**4. Reticulum not starting**

```bash
# Check config syntax:
rnsd --config /home/myc3lium/.reticulum/config --validate

# Run in foreground for debugging:
sudo -u myc3lium rnsd --config /home/myc3lium/.reticulum/config -vvv
```

**5. Backend API not responding**

```bash
# Check service status:
systemctl status myc3lium-backend.service

# Check if port is listening:
sudo netstat -tlnp | grep 8000

# Run manually for debugging:
sudo -u myc3lium python3 /opt/myc3lium/backend/reticulum_bridge.py
```

**6. WebUI not loading**

```bash
# Check nginx:
systemctl status nginx
nginx -t

# Check if files exist:
ls -la /var/www/myc3lium/

# Check nginx logs:
tail -f /var/log/nginx/error.log
```

### Hardware Issues

**LoRa not transmitting:**
- Check antenna is connected
- Verify frequency matches region (915 MHz for US)
- Check TX power settings in config
- Ensure HAT is properly seated

**GPS not working:**
- Check UART is enabled: `ls /dev/ttyAMA0`
- Antenna must have clear view of sky
- Can take 5-10 minutes for first fix
- Check with: `cgps -s`

**WiFi mesh unstable:**
- Ensure nodes are within range (50-200m)
- Check for interference on channel 6
- Try different mesh channel in setup-batman.sh
- Verify wlan0 is not managed by NetworkManager

### Recovery

**Reset to defaults:**
```bash
cd ~/deployment/scripts
sudo ./setup-pi4.sh
# Re-run all setup scripts
```

**Clean reinstall:**
```bash
# Backup important data first!
sudo rm -rf /opt/myc3lium
sudo rm -rf /home/myc3lium/.reticulum
sudo userdel -r myc3lium

# Re-run setup:
sudo ./setup-pi4.sh
```

---

## 🔐 Security

### Change Default Passwords

```bash
# Change myc3lium user password:
sudo passwd myc3lium

# Change pi user password:
passwd

# Or disable pi user entirely:
sudo passwd -l pi
```

### Firewall Configuration

Firewall is configured during setup. To modify:

```bash
# View current rules:
sudo ufw status

# Allow additional port:
sudo ufw allow 1234/tcp

# Deny port:
sudo ufw deny 1234/tcp
```

### Identity Backup

**CRITICAL:** Back up your Reticulum identity!

```bash
# Copy identity to safe location:
sudo cp /home/myc3lium/.reticulum/storage/identities/myc3lium-node \
  ~/myc3lium-identity-backup.key

# Download to your computer:
scp myc3lium@<pi-ip>:~/myc3lium-identity-backup.key .

# Store securely offline!
```

Without this, you'll need to regenerate identity and won't be recognized by other nodes.

---

## 🔧 Advanced Configuration

### Customize Mesh ID

Edit BATMAN mesh ID:
```bash
sudo nano /opt/myc3lium/setup-mesh.sh
# Change MESH_ID="myc3lium-mesh" to your desired ID
sudo systemctl restart batman-adv.service
```

### Adjust LoRa Parameters

Edit Reticulum config:
```bash
sudo nano /home/myc3lium/.reticulum/config

# Adjust:
# - frequency (915000000 for US, 868000000 for EU)
# - spreading_factor (7=fast/short, 12=slow/long)
# - bandwidth (125000, 250000, 500000)
# - txpower (0-22 dBm)

sudo systemctl restart reticulum.service
```

### Add Additional Nodes

For each new node:
1. Flash same SD card image
2. Run through setup process
3. They will auto-discover each other via:
   - BATMAN mesh (if in WiFi range)
   - LoRa (long range)
   - HaLow (medium range)

No manual peering required!

### Enable GPS Tracking

If your LoRa HAT has GPS:

```bash
# Check GPS status:
cgps -s

# Enable GPS logging in Reticulum (advanced):
# Edit config to add GPS coordinates to announces
```

---

## 📝 Post-Deployment Checklist

- [ ] All services running (`myc3lium-status`)
- [ ] WebUI accessible
- [ ] At least one mesh interface working
- [ ] Identity backed up
- [ ] Default passwords changed
- [ ] Firewall configured
- [ ] GPS fix acquired (if applicable)
- [ ] Second node deployed and peered
- [ ] Test message sent and received
- [ ] Touchscreen working (if connected)

---

## 📚 Reference

### File Locations

```
/opt/myc3lium/              # Main application directory
├── backend/                # FastAPI backend
├── frontend/               # Web UI source
├── logs/                   # Application logs
└── data/                   # Runtime data

/home/myc3lium/.reticulum/  # Reticulum data
├── config                  # Main config file
└── storage/                # Identities, announces, etc.

/var/www/myc3lium/          # Nginx web root
/etc/nginx/sites-available/myc3lium  # Nginx config
```

### Important Commands

```bash
# System status
myc3lium-status

# Service management
sudo systemctl {start|stop|restart|status} reticulum.service
sudo systemctl {start|stop|restart|status} myc3lium-backend.service
sudo systemctl {start|stop|restart|status} batman-adv.service

# Logs
journalctl -fu <service-name>
tail -f /opt/myc3lium/logs/bridge.log

# Mesh status
bash /opt/myc3lium/mesh-status.sh
batctl o  # BATMAN neighbors
rnstatus  # Reticulum status

# Tests
sudo ./test-all.sh
```

### Network Ports

- **80**: WebUI (HTTP)
- **8000**: Backend API
- **4242**: Reticulum TCP server
- **4965**: Reticulum UDP (mesh)
- **29716**: Reticulum discovery

---

## 🆘 Support

**Documentation:**
- Reticulum: https://reticulum.network/
- LXMF: https://github.com/markqvist/LXMF
- BATMAN-adv: https://www.open-mesh.org/

**Logs to collect for debugging:**
```bash
# Create debug bundle:
mkdir ~/debug-logs
journalctl -u reticulum.service > ~/debug-logs/reticulum.log
journalctl -u myc3lium-backend.service > ~/debug-logs/backend.log
journalctl -u batman-adv.service > ~/debug-logs/batman.log
cp /opt/myc3lium/logs/bridge.log ~/debug-logs/
dmesg > ~/debug-logs/dmesg.log
ip addr > ~/debug-logs/ip-addr.txt
batctl o > ~/debug-logs/batman-neighbors.txt
rnstatus > ~/debug-logs/reticulum-status.txt

# Compress:
tar -czf myc3lium-debug-$(date +%Y%m%d-%H%M%S).tar.gz ~/debug-logs/
```

---

## 🎉 You're Done!

Your MYC3LIUM mesh node is now operational!

**What's working:**
- ✅ Autonomous mesh networking
- ✅ Multi-interface routing (LoRa, HaLow, BATMAN)
- ✅ Store-and-forward messaging
- ✅ Real-time WebUI
- ✅ REST API access
- ✅ Auto-discovery of peers

**Next steps:**
- Deploy more nodes to build the mesh
- Integrate with applications via API
- Monitor mesh topology
- Enjoy decentralized communications!

**Access your node:**
```
WebUI: http://<your-pi-ip>
API: http://<your-pi-ip>:8000/docs
```

🍄 **Welcome to the mycelium network!**
