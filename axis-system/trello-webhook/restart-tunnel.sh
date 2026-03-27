#!/bin/bash
# Restart Cloudflare tunnel and auto-update webhooks
# Use this instead of systemctl restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Restarting Cloudflare Tunnel ==="

# Kill existing tunnel process
echo "Stopping existing tunnel..."
pkill -f "cloudflared tunnel --url http://localhost:18790"
sleep 2

# Clear old log
> logs/tunnel.log

# Start new tunnel in background
echo "Starting new tunnel..."
nohup ~/.local/bin/cloudflared tunnel --url http://localhost:18790 > logs/tunnel.log 2>&1 &
TUNNEL_PID=$!
echo "Tunnel started with PID: $TUNNEL_PID"

# Wait and auto-update webhooks
echo "Waiting 10 seconds for tunnel to establish..."
sleep 10

echo "Running auto-update webhooks..."
./auto-update-webhooks.sh

echo "=== Restart complete ==="
echo "Check logs/webhook-auto-update.log for details"
