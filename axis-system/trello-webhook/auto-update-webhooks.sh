#!/bin/bash
# Auto-update Trello webhooks if tunnel URL changed
# Used by systemd after tunnel restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="logs/webhook-auto-update.log"
TUNNEL_URL_FILE=".tunnel_url"
TUNNEL_LOG="logs/tunnel.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Auto-update webhooks started ==="

# Wait for tunnel to start (max 30 seconds)
log "Waiting for tunnel to establish..."
for i in {1..30}; do
    if grep -q "https://" "$TUNNEL_LOG" 2>/dev/null; then
        log "Tunnel log found"
        break
    fi
    sleep 1
done

# Extract current URL from tunnel log
CURRENT_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -1)

if [ -z "$CURRENT_URL" ]; then
    log "ERROR: Could not extract tunnel URL from logs"
    exit 1
fi

log "Current tunnel URL: $CURRENT_URL"

# Read previous URL
if [ -f "$TUNNEL_URL_FILE" ]; then
    PREVIOUS_URL=$(cat "$TUNNEL_URL_FILE")
    log "Previous tunnel URL: $PREVIOUS_URL"
else
    PREVIOUS_URL=""
    log "No previous URL found (first run)"
fi

# Compare URLs
if [ "$CURRENT_URL" = "$PREVIOUS_URL" ]; then
    log "URL unchanged. No webhook update needed."
    exit 0
fi

# URL changed - update webhooks
log "URL CHANGED! Updating webhooks..."

# Save new URL
echo "$CURRENT_URL" > "$TUNNEL_URL_FILE"
log "Saved new URL to $TUNNEL_URL_FILE"

# Remove old webhooks (only if previous URL existed)
if [ -n "$PREVIOUS_URL" ]; then
    log "Removing old webhooks..."
    python3 remove-trello-webhooks.py --all >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "Old webhooks removed successfully"
    else
        log "WARNING: Failed to remove old webhooks (may not exist)"
    fi
fi

# Setup new webhooks
log "Setting up new webhooks with URL: $CURRENT_URL"
python3 setup-trello-webhooks.py --url "$CURRENT_URL" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "✓ Webhooks updated successfully!"
    log "Active webhooks are now pointing to: $CURRENT_URL"
else
    log "✗ ERROR: Failed to setup webhooks"
    exit 1
fi

log "=== Auto-update completed ==="
exit 0
