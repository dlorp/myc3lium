#!/bin/bash
# MYC3LIUM WebUI Deployment Script
# Builds and deploys frontend to Nginx

set -e

echo "🌐 MYC3LIUM WebUI Deployment"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# Configuration
FRONTEND_SRC="/opt/myc3lium/frontend"
NGINX_ROOT="/var/www/myc3lium"
NGINX_CONF="/etc/nginx/sites-available/myc3lium"
API_URL="http://localhost:8000"

log_info "Installing Nginx..."
apt-get update
apt-get install -y nginx

# Create frontend directory if doesn't exist
mkdir -p "$FRONTEND_SRC"
mkdir -p "$NGINX_ROOT"

# Check if frontend exists, if not create a basic HTML interface
if [ ! -f "$FRONTEND_SRC/index.html" ]; then
    log_info "Creating basic WebUI..."
    
    cat > "$FRONTEND_SRC/index.html" <<'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍄 MYC3LIUM Mesh</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #00ff88, #00ccff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #888;
            font-size: 1.2em;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .card h2 {
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        
        .stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stat:last-child {
            border-bottom: none;
        }
        
        .stat-value {
            color: #00ccff;
            font-weight: bold;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online {
            background: #00ff88;
            box-shadow: 0 0 10px #00ff88;
        }
        
        .status-offline {
            background: #ff4444;
            box-shadow: 0 0 10px #ff4444;
        }
        
        #messages {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
        }
        
        .message {
            padding: 10px;
            margin-bottom: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
            border-left: 3px solid #00ff88;
        }
        
        .message-time {
            color: #888;
            font-size: 0.8em;
        }
        
        button {
            background: linear-gradient(45deg, #00ff88, #00ccff);
            border: none;
            color: #000;
            padding: 12px 24px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            font-size: 1em;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: scale(1.05);
        }
        
        button:active {
            transform: scale(0.95);
        }
        
        .interface-list {
            list-style: none;
        }
        
        .interface-item {
            padding: 8px;
            margin: 5px 0;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 5px;
            border-left: 3px solid #00ff88;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🍄 MYC3LIUM</h1>
            <p class="subtitle">Decentralized Mesh Network</p>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>System Status</h2>
                <div class="stat">
                    <span>Reticulum</span>
                    <span><span class="status-indicator status-online" id="rns-status"></span><span id="rns-text">Checking...</span></span>
                </div>
                <div class="stat">
                    <span>Backend API</span>
                    <span><span class="status-indicator status-online" id="api-status"></span><span id="api-text">Checking...</span></span>
                </div>
                <div class="stat">
                    <span>Mesh Neighbors</span>
                    <span class="stat-value" id="neighbor-count">0</span>
                </div>
                <div class="stat">
                    <span>Node Identity</span>
                    <span class="stat-value" id="node-id" style="font-size: 0.8em;">Loading...</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Network Interfaces</h2>
                <ul class="interface-list" id="interfaces">
                    <li class="interface-item">📡 LoRa (SX1262) - Initializing...</li>
                    <li class="interface-item">📶 WiFi HaLow - Initializing...</li>
                    <li class="interface-item">🦇 BATMAN Mesh - Initializing...</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>Mesh Statistics</h2>
                <div class="stat">
                    <span>Known Destinations</span>
                    <span class="stat-value" id="dest-count">0</span>
                </div>
                <div class="stat">
                    <span>Active Paths</span>
                    <span class="stat-value" id="path-count">0</span>
                </div>
                <div class="stat">
                    <span>Data Sent</span>
                    <span class="stat-value" id="data-tx">0 KB</span>
                </div>
                <div class="stat">
                    <span>Data Received</span>
                    <span class="stat-value" id="data-rx">0 KB</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Recent Messages</h2>
            <div id="messages">
                <div class="message">
                    <div class="message-time">System</div>
                    <div>🍄 MYC3LIUM mesh node online. Waiting for messages...</div>
                </div>
            </div>
        </div>
        
        <div class="card" style="text-align: center;">
            <button onclick="announcePresence()">📢 Announce Presence</button>
            <button onclick="refreshStats()">🔄 Refresh Stats</button>
        </div>
        
        <div class="footer">
            <p>MYC3LIUM Mesh Network | Powered by Reticulum</p>
            <p>Build: v1.0.0-alpha | Node Uptime: <span id="uptime">Calculating...</span></p>
        </div>
    </div>
    
    <script>
        const API_URL = 'http://' + window.location.hostname + ':8000';
        let ws = null;
        let startTime = Date.now();
        
        // Update uptime
        setInterval(() => {
            const uptime = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            document.getElementById('uptime').textContent = 
                `${hours}h ${minutes}m ${seconds}s`;
        }, 1000);
        
        // WebSocket connection
        function connectWebSocket() {
            const wsUrl = 'ws://' + window.location.hostname + ':8000/ws';
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                addMessage('System', '✅ Real-time updates connected');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(connectWebSocket, 5000);
            };
        }
        
        function handleWebSocketMessage(data) {
            if (data.type === 'message') {
                const msg = data.data;
                addMessage(msg.source, msg.content);
            }
        }
        
        function addMessage(source, content) {
            const messagesDiv = document.getElementById('messages');
            const messageEl = document.createElement('div');
            messageEl.className = 'message';
            
            const time = new Date().toLocaleTimeString();
            messageEl.innerHTML = `
                <div class="message-time">${time} - ${source}</div>
                <div>${content}</div>
            `;
            
            messagesDiv.appendChild(messageEl);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // Keep only last 50 messages
            while (messagesDiv.children.length > 50) {
                messagesDiv.removeChild(messagesDiv.firstChild);
            }
        }
        
        async function fetchStats() {
            try {
                // Health check
                const health = await fetch(API_URL + '/health').then(r => r.json());
                document.getElementById('rns-text').textContent = 
                    health.reticulum === 'running' ? 'Online' : 'Offline';
                document.getElementById('rns-status').className = 
                    'status-indicator ' + (health.reticulum === 'running' ? 'status-online' : 'status-offline');
                document.getElementById('api-text').textContent = 'Online';
                document.getElementById('api-status').className = 'status-indicator status-online';
                
                // Identity
                const identity = await fetch(API_URL + '/identity').then(r => r.json());
                document.getElementById('node-id').textContent = identity.hash;
                
                // Mesh stats
                const stats = await fetch(API_URL + '/mesh/stats').then(r => r.json());
                document.getElementById('dest-count').textContent = 
                    stats.transport.destination_table_size || 0;
                document.getElementById('path-count').textContent = 
                    stats.transport.announce_table_size || 0;
                
                // Interface stats
                if (stats.interfaces && stats.interfaces.length > 0) {
                    let totalRx = 0, totalTx = 0;
                    stats.interfaces.forEach(iface => {
                        totalRx += iface.rxb || 0;
                        totalTx += iface.txb || 0;
                    });
                    document.getElementById('data-rx').textContent = 
                        Math.floor(totalRx / 1024) + ' KB';
                    document.getElementById('data-tx').textContent = 
                        Math.floor(totalTx / 1024) + ' KB';
                }
                
                // Destinations
                const destinations = await fetch(API_URL + '/mesh/destinations').then(r => r.json());
                document.getElementById('neighbor-count').textContent = 
                    destinations.destinations.length;
                
            } catch (e) {
                console.error('Failed to fetch stats:', e);
                document.getElementById('api-text').textContent = 'Offline';
                document.getElementById('api-status').className = 'status-indicator status-offline';
            }
        }
        
        async function announcePresence() {
            try {
                await fetch(API_URL + '/announce', { method: 'POST' });
                addMessage('System', '📢 Announced presence to mesh');
            } catch (e) {
                addMessage('System', '❌ Failed to announce: ' + e.message);
            }
        }
        
        function refreshStats() {
            fetchStats();
            addMessage('System', '🔄 Stats refreshed');
        }
        
        // Initialize
        connectWebSocket();
        fetchStats();
        setInterval(fetchStats, 10000); // Update every 10 seconds
    </script>
</body>
</html>
HTMLEOF
    
    log_info "✓ Basic WebUI created"
fi

# Copy frontend to nginx directory
log_info "Copying frontend to Nginx root..."
cp -r "$FRONTEND_SRC"/* "$NGINX_ROOT/"
chown -R www-data:www-data "$NGINX_ROOT"

# Create Nginx configuration
log_info "Configuring Nginx..."
cat > "$NGINX_CONF" <<'NGINXEOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    
    root /var/www/myc3lium;
    index index.html;
    
    # Frontend
    location / {
        try_files $uri $uri/ =404;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
}
NGINXEOF

# Enable site
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/myc3lium
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
log_info "Testing Nginx configuration..."
nginx -t

# Restart nginx
log_info "Restarting Nginx..."
systemctl restart nginx
systemctl enable nginx

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

log_info "✅ WebUI deployment complete!"
log_info ""
log_info "Access WebUI at:"
log_info "  http://$IP_ADDR"
log_info "  http://$(hostname).local (if mDNS is configured)"
log_info ""
log_info "API available at:"
log_info "  http://$IP_ADDR:8000"
log_info ""
log_info "Services:"
log_info "  Nginx: systemctl status nginx"
log_info "  Backend: systemctl status myc3lium-backend"
log_info ""
log_info "To rebuild frontend, edit files in:"
log_info "  $FRONTEND_SRC"
log_info "Then re-run this script to deploy"
