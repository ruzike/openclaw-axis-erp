#!/bin/bash
# Migrate from Quick Tunnel to Named Cloudflare Tunnel
# For stable webhook URLs that survive restarts

set -e

TUNNEL_NAME="axis-trello-webhook"
WEBHOOK_DIR="/home/axis/openclaw/axis-system/trello-webhook"
CLOUDFLARED_DIR="$HOME/.cloudflared"
CONFIG_FILE="$CLOUDFLARED_DIR/config.yml"
SERVICE_DIR="/etc/systemd/system"

echo "=== Cloudflare Named Tunnel Migration ==="
echo "Tunnel name: $TUNNEL_NAME"
echo ""

# Step 1: Check if logged in
if [ ! -f "$CLOUDFLARED_DIR/cert.pem" ]; then
    echo "❌ Not logged into Cloudflare!"
    echo ""
    echo "Run: cloudflared tunnel login"
    echo "Then open the URL in your browser to authorize."
    exit 1
fi
echo "✅ Cloudflare auth: OK"

# Step 2: Check if tunnel exists or create it
EXISTING=$(cloudflared tunnel list --output json 2>/dev/null | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)
for t in tunnels:
    if t['name'] == '$TUNNEL_NAME':
        print(t['id'])
        break
" 2>/dev/null || echo "")

if [ -n "$EXISTING" ]; then
    TUNNEL_ID="$EXISTING"
    echo "✅ Tunnel '$TUNNEL_NAME' already exists: $TUNNEL_ID"
else
    echo "Creating tunnel '$TUNNEL_NAME'..."
    cloudflared tunnel create "$TUNNEL_NAME"
    TUNNEL_ID=$(cloudflared tunnel list --output json | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)
for t in tunnels:
    if t['name'] == '$TUNNEL_NAME':
        print(t['id'])
        break
")
    echo "✅ Created tunnel: $TUNNEL_ID"
fi

# Step 3: Get credentials file path
CREDS_FILE="$CLOUDFLARED_DIR/${TUNNEL_ID}.json"
if [ ! -f "$CREDS_FILE" ]; then
    echo "❌ Credentials file not found: $CREDS_FILE"
    exit 1
fi
echo "✅ Credentials: $CREDS_FILE"

# Step 4: Generate stable URL
STABLE_URL="https://${TUNNEL_ID}.cfargotunnel.com"
echo "✅ Stable URL: $STABLE_URL"

# Step 5: Create config.yml
cat > "$CONFIG_FILE" << EOF
# Cloudflare Tunnel config for Trello Webhooks
# Generated: $(date -Iseconds)

tunnel: $TUNNEL_ID
credentials-file: $CREDS_FILE

ingress:
  - hostname: ${TUNNEL_ID}.cfargotunnel.com
    service: http://localhost:18790
  - service: http_status:404
EOF
echo "✅ Config: $CONFIG_FILE"

# Step 6: Update .tunnel_url
echo "$STABLE_URL" > "$WEBHOOK_DIR/.tunnel_url"
echo "✅ Updated: $WEBHOOK_DIR/.tunnel_url"

# Step 7: Create systemd service
cat > "$WEBHOOK_DIR/cloudflared-tunnel.service.new" << EOF
[Unit]
Description=Cloudflare Named Tunnel for Trello Webhooks (axis-trello-webhook)
Documentation=https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
After=network-online.target trello-webhook.service
Wants=network-online.target
Requires=trello-webhook.service

[Service]
Type=simple
User=user
Group=user

# Named Tunnel - stable URL: $STABLE_URL
ExecStart=$HOME/.local/bin/cloudflared tunnel run $TUNNEL_NAME

Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloudflared-tunnel

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created: cloudflared-tunnel.service.new"

# Step 8: Stop old services
echo ""
echo "Stopping old services..."
sudo systemctl stop cloudflared-tunnel.service 2>/dev/null || true
pkill -f "cloudflared tunnel --url" 2>/dev/null || true

# Step 9: Install new service
echo "Installing new systemd service..."
sudo cp "$WEBHOOK_DIR/cloudflared-tunnel.service.new" "$SERVICE_DIR/cloudflared-tunnel.service"
sudo systemctl daemon-reload
sudo systemctl enable cloudflared-tunnel.service

# Step 10: Start tunnel
echo "Starting named tunnel..."
sudo systemctl start cloudflared-tunnel.service
sleep 3

# Step 11: Verify
if sudo systemctl is-active --quiet cloudflared-tunnel.service; then
    echo "✅ Tunnel running!"
else
    echo "❌ Tunnel failed to start"
    sudo journalctl -u cloudflared-tunnel.service --no-pager -n 20
    exit 1
fi

# Step 12: Test connectivity
echo ""
echo "Testing tunnel connectivity..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${STABLE_URL}/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check: OK (HTTP $HTTP_CODE)"
else
    echo "⚠️  Health check returned HTTP $HTTP_CODE (may take a minute to propagate)"
fi

echo ""
echo "=== Migration Complete ==="
echo ""
echo "Stable URL: $STABLE_URL"
echo ""
echo "Next steps:"
echo "1. Re-register Trello webhooks with new URL:"
echo "   cd $WEBHOOK_DIR && python3 setup-trello-webhooks.py"
echo ""
echo "2. Remove old webhooks (if any):"
echo "   python3 remove-trello-webhooks.py"
echo ""
