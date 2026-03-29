"""
MYC3LIUM Reticulum Configuration
Deploy to: /home/myc3lium/.reticulum/config

Configures three interfaces:
1. LoRa (SX1262 HAT) - Long range, low bandwidth
2. WiFi HaLow (HT-HC01P) - Medium range, higher bandwidth  
3. BATMAN-adv Mesh (wlan0) - Local mesh, highest bandwidth
"""

# Enable transport (routing) mode
[reticulum]
  enable_transport = True
  share_instance = True
  shared_instance_port = 37428
  instance_control_port = 37429
  
  # Panic button - use in emergencies
  panic_on_interface_error = False

# Logging
[logging]
  loglevel = 4  # 0=critical, 1=error, 2=warning, 3=info, 4=verbose, 5=debug

# ============================================================================
# INTERFACE 1: LoRa - Waveshare SX1262 HAT (915 MHz)
# Long range (1-10+ km), low bandwidth (~5 kbps), low power
# ============================================================================

[[LoRa Interface]]
  type = RNodeInterface
  interface_enabled = True
  
  # Serial port for SX1262
  # Note: SX1262 via SPI may require RNode firmware or direct SPI implementation
  # For RNode compatibility, flash RNode firmware to a serial-connected module
  # For direct SPI: Use custom interface implementation
  
  # Using RNode firmware approach (requires RNode-compatible firmware):
  # port = /dev/ttyUSB0
  
  # For direct SPI implementation, use AutoInterface with custom parameters:
  type = AutoInterface
  interface_enabled = True
  
  # SX1262 LoRa parameters for 915 MHz ISM band
  # These will be implemented in custom SPI driver or RNode firmware
  
  # Frequency: 915 MHz (US ISM band)
  frequency = 915000000
  
  # Bandwidth: 125 kHz (good balance of range and speed)
  bandwidth = 125000
  
  # Spreading factor: 7-12 (7 = faster/shorter range, 12 = slower/longer range)
  spreading_factor = 7
  
  # Coding rate: 5-8 (error correction)
  coding_rate = 5
  
  # TX power: 22 dBm max for SX1262
  txpower = 22
  
  # Announce rate
  outgoing_announce_rate_target = 60
  outgoing_announce_rate_grace = 120
  
  # Discovery
  discovery_scope = global
  discovery_port = 29716

# ============================================================================  
# INTERFACE 2: WiFi HaLow - Heltec HT-HC01P (902-928 MHz)
# Medium range (100m-1km), higher bandwidth (~1-4 Mbps)
# ============================================================================

[[HaLow Interface]]
  type = UDPInterface
  interface_enabled = True
  
  # Listen on HaLow interface
  listen_ip = 10.42.1.1
  listen_port = 4242
  
  # Broadcast to HaLow subnet
  forward_ip = 10.42.1.255
  forward_port = 4242
  
  # Announce settings
  outgoing_announce_rate_target = 30
  outgoing_announce_rate_grace = 60
  
  # Discovery
  discovery_scope = local
  discovery_port = 29716

# ============================================================================
# INTERFACE 3: BATMAN-adv Mesh - Built-in WiFi (2.4 GHz)
# Short range (50-200m), highest bandwidth (~10+ Mbps mesh)
# ============================================================================

[[Mesh Interface]]
  type = UDPInterface  
  interface_enabled = True
  
  # Listen on BATMAN interface
  listen_ip = 0.0.0.0
  listen_port = 4965
  
  # Broadcast to mesh subnet
  forward_ip = 10.13.255.255
  forward_port = 4965
  
  # High announce rate for local mesh
  outgoing_announce_rate_target = 10
  outgoing_announce_rate_grace = 20
  
  # Local discovery only
  discovery_scope = local
  discovery_port = 29716

# ============================================================================
# INTERFACE 4: TCP Server (for WebUI and local apps)
# ============================================================================

[[Local Server Interface]]
  type = TCPServerInterface
  interface_enabled = True
  
  listen_ip = 127.0.0.1
  listen_port = 4242
  
  # Only local announce
  outgoing_announce_rate_target = 300
  
  # Local scope only
  discovery_scope = none

# ============================================================================
# INTERFACE 5: Auto-peer discovery (optional)
# Finds other Reticulum instances on local networks
# ============================================================================

[[Auto Interface]]
  type = AutoInterface
  interface_enabled = True
  
  # Auto-discover on all available networks
  group_id = myc3lium
  
  discovery_scope = local
  discovery_port = 29716
  
  # Announce settings
  outgoing_announce_rate_target = 60

# ============================================================================
# Store and Forward (S&F) Configuration
# ============================================================================

[store_and_forward]
  # Enable S&F to cache messages when destinations are unreachable
  enabled = True
  
  # Store messages for up to 7 days
  max_message_age = 604800
  
  # Maximum stored messages
  max_messages = 1000
  
  # Storage path
  storage_path = /home/myc3lium/.reticulum/storage

# ============================================================================
# Identity Configuration
# ============================================================================

# Identities are auto-generated on first run
# Location: /home/myc3lium/.reticulum/storage/identities/

# To create additional identities:
# rnid -c /home/myc3lium/.reticulum/identities/myc3lium-node

# ============================================================================
# Announce Settings
# ============================================================================

[announce]
  # Hidden announces (encryption)
  allow_hidden_announces = True
  
  # Rate limiting
  max_announces_per_hour = 120

# ============================================================================
# Resource Transfer Settings  
# ============================================================================

[resources]
  # Maximum resource size (bytes)
  max_resource_size = 104857600  # 100 MB
  
  # Resource timeout
  resource_timeout = 300
  
  # Auto-accept resources from trusted peers
  auto_accept_resources = False

# ============================================================================
# LXMF Message Configuration
# ============================================================================

[lxmf]
  # Enable propagation node (store messages for offline peers)
  propagation_node = True
  
  # Storage path
  message_storage_path = /home/myc3lium/.reticulum/lxmf_storage
  
  # Max stored messages per destination
  max_messages_per_destination = 100
  
  # Message retention (7 days)
  message_retention = 604800

# ============================================================================
# Performance Tuning
# ============================================================================

[performance]
  # Maximum concurrent transfers
  max_concurrent_transfers = 4
  
  # Buffer sizes
  ingress_buffer_size = 4194304   # 4 MB
  egress_buffer_size = 4194304    # 4 MB
  
  # Thread pool size
  worker_threads = 4

# ============================================================================
# Security Settings
# ============================================================================

[security]
  # Only accept announces from known identities (when False, accepts all)
  use_implicit_proof = True
  
  # Require proof for path requests
  require_proof_for_paths = True

# ============================================================================
# Notes:
# ============================================================================

# 1. LoRa Interface: Currently configured as AutoInterface
#    For production, implement custom SPI interface or use RNode firmware
#    See: https://github.com/markqvist/Reticulum/discussions
#
# 2. Interface Priority: Reticulum automatically selects best path
#    Priority: Mesh > HaLow > LoRa (based on bandwidth/latency)
#
# 3. First Run: Reticulum will generate identity keys automatically
#    Backup: /home/myc3lium/.reticulum/storage/identities/
#
# 4. Testing: Use rnstatus, rnpath, and rnprobe commands
#
# 5. WebUI Integration: Use TCPClientInterface from FastAPI backend
#    Connect to: 127.0.0.1:4242
