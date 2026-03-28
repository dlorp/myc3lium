# Meshtastic Backend Deployment Guide

Quick reference for deploying the Meshtastic integration to the Raspberry Pi.

## Prerequisites

- Heltec V3 connected to Pi via USB
- Device appears as `/dev/ttyUSB1`
- Heltec running Meshtastic firmware in CLIENT mode
- Backend service running (`myc3lium-backend`)

## Deployment Steps

### 1. Push Changes

On development machine:

```bash
cd ~/repos/myc3lium

# Add new files
git add backend/app/services/meshtastic_service.py
git add backend/app/routers/meshtastic.py
git add backend/app/main.py
git add backend/requirements.txt
git add test_meshtastic.py
git add PHASE2_MESHTASTIC_COMPLETE.md
git add DEPLOY_MESHTASTIC.md

# Commit
git commit -m "feat: Add Meshtastic backend integration (Phase 2)

- MeshtasticService: SerialInterface wrapper with callbacks
- Meshtastic API router: /api/meshtastic/* endpoints
- WebSocket support for real-time message streaming
- Ring buffer for last 100 messages
- Node tracking with position data
- Test script for validation

Hardware: Heltec V3 on /dev/ttyUSB1 (CLIENT mode)"

# Push
git push origin main
```

### 2. Pull on Pi

SSH to Pi:

```bash
ssh pi@myc3lium.local
cd ~/myc3lium
git pull
```

### 3. Install Dependencies

```bash
pip3 install -r backend/requirements.txt
```

Expected output:
```
...
Successfully installed meshtastic-2.x.x
...
```

### 4. Verify Device

```bash
ls -la /dev/ttyUSB*
```

Should show:
```
crw-rw---- 1 root dialout ... /dev/ttyUSB1
```

If not found:
```bash
# Check dmesg for device detection
sudo dmesg | grep ttyUSB

# List USB devices
lsusb | grep -i heltec
```

### 5. Check User Permissions

The backend needs access to serial device:

```bash
# Add user to dialout group (if not already)
sudo usermod -a -G dialout $USER

# Or check existing groups
groups

# If needed, restart for group changes to take effect
sudo reboot
```

### 6. Restart Backend Service

```bash
sudo systemctl restart myc3lium-backend
```

### 7. Check Service Status

```bash
# Check if service is running
sudo systemctl status myc3lium-backend

# Watch logs in real-time
sudo journalctl -u myc3lium-backend -f
```

Look for:
```
INFO: Connected to Meshtastic node: NODE1 (!a1b2c3d4)
INFO: Meshtastic service started successfully
```

### 8. Test Connection

Run the test script:

```bash
cd ~/myc3lium
python3 test_meshtastic.py
```

Expected output:
```
============================================================
Meshtastic Integration Test Suite
============================================================

Test 1: Connection to Heltec V3
✓ PASS - Connect to device
      Device: /dev/ttyUSB1, Node: NODE1 (!a1b2c3d4), Nodes: 8

Test 2: Read Node Information
✓ PASS - Node ID present
      ID: !a1b2c3d4
✓ PASS - Node name present
      Name: NODE1
✓ PASS - Node list
      Found 8 nodes

Test 3: Send Test Message
✓ PASS - Send message
      Sent: myc3lium test - 1711330000

Test 4: Message Reception
      Waiting 10 seconds for messages...
✓ PASS - Message buffer
      Buffer contains 12 messages

Test 5: API Endpoint Validation
✓ PASS - Health endpoint
      Status: 200
✓ PASS - Status endpoint
      Connected: True, Node: NODE1, Nodes: 8
✓ PASS - Nodes endpoint
      Returned 8 nodes
✓ PASS - Messages endpoint
      Returned 12 messages

============================================================
Test suite complete!
============================================================
```

### 9. Test API Manually

```bash
# Check health
curl http://localhost:8000/health | jq

# Get Meshtastic status
curl http://localhost:8000/api/meshtastic/status | jq

# Get nodes
curl http://localhost:8000/api/meshtastic/nodes | jq

# Get messages
curl http://localhost:8000/api/meshtastic/messages?limit=5 | jq

# Send message
curl -X POST http://localhost:8000/api/meshtastic/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Test from API", "channel": 0}' | jq
```

## Troubleshooting

### Device Not Found

**Problem:** `/dev/ttyUSB1` doesn't exist

**Solutions:**
1. Check if device is connected: `lsusb`
2. Check if it's on different port: `ls /dev/ttyUSB*`
3. Check dmesg: `sudo dmesg | tail -50`
4. Try reconnecting USB cable

### Permission Denied

**Problem:** `PermissionError: [Errno 13] Permission denied: '/dev/ttyUSB1'`

**Solutions:**
1. Add user to dialout group: `sudo usermod -a -G dialout myc3lium-user`
2. Check device permissions: `ls -la /dev/ttyUSB1`
3. Temporarily test with sudo: `sudo systemctl restart myc3lium-backend`
4. If sudo works, it's a permission issue

### Import Error

**Problem:** `ModuleNotFoundError: No module named 'meshtastic'`

**Solutions:**
1. Install library: `pip3 install meshtastic`
2. Check if using correct Python: `which python3`
3. Install in system Python: `sudo pip3 install meshtastic`

### No Messages Received

**Problem:** Test shows 0 messages

**Possible causes:**
1. No community traffic yet (normal for new/quiet mesh)
2. Heltec not joined mesh (check channels match community)
3. Signal issues (check antenna, location)

**Solutions:**
1. Wait longer (mesh may be quiet)
2. Send test message and receive it back
3. Check Meshtastic app on phone to verify mesh is active

### WebSocket Not Working

**Problem:** Frontend not receiving real-time updates

**Solutions:**
1. Check browser console for WebSocket errors
2. Test with `wscat`: `wscat -c ws://localhost:8000/ws/meshtastic`
3. Check CORS settings in main.py
4. Verify frontend is connecting to correct URL

## Monitoring

### Watch Logs

```bash
# Follow backend logs
sudo journalctl -u myc3lium-backend -f

# Filter for Meshtastic events
sudo journalctl -u myc3lium-backend | grep -i meshtastic

# Show last 100 lines
sudo journalctl -u myc3lium-backend -n 100
```

### Check Message Flow

```bash
# Watch messages in real-time
watch -n 5 'curl -s http://localhost:8000/api/meshtastic/messages?limit=10 | jq ".[].text"'

# Count nodes
curl -s http://localhost:8000/api/meshtastic/nodes | jq length

# Monitor connection
watch -n 10 'curl -s http://localhost:8000/api/meshtastic/status | jq ".connected, .nodes_count"'
```

## Performance Notes

- **Message Buffer:** 100 messages max (configurable in service constructor)
- **WebSocket Overhead:** ~1-2% CPU per active connection
- **Serial Latency:** ~50-200ms for send/receive
- **Memory:** ~5-10MB for service + message buffer

## Next Steps

After successful deployment:

1. **Frontend Integration:** Connect UI to Meshtastic WebSocket
2. **Message Display:** Show recent messages in frontend
3. **Node Visualization:** Display mesh nodes on map/graph
4. **Send UI:** Add message composition interface

---

**Need Help?**
- Check logs: `sudo journalctl -u myc3lium-backend -f`
- Test script: `python3 test_meshtastic.py`
- Manual API: `curl http://localhost:8000/api/meshtastic/status`
