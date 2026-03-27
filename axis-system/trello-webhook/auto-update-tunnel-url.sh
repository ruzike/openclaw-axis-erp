#!/bin/bash
# Auto-update Trello webhook URLs after Quick Tunnel restart
# Вызывается из systemd ExecStartPost

set -euo pipefail

LOGFILE="/home/axis/openclaw/axis-system/trello-webhook/logs/tunnel-update.log"
CONFIG="/home/axis/openclaw/trello-config.json"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOGFILE"; }

log "Waiting for tunnel URL..."
sleep 15

# Ловим URL из journalctl
TUNNEL_URL=$(journalctl --user -u cloudflared-trello.service --no-pager -n 50 2>/dev/null | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)

if [ -z "$TUNNEL_URL" ]; then
    log "ERROR: Could not find tunnel URL"
    exit 1
fi

CALLBACK_URL="$TUNNEL_URL/webhook/trello"
log "New tunnel URL: $TUNNEL_URL"

# Обновляем все webhooks
python3 -c "
import json, requests

with open('$CONFIG') as f:
    config = json.load(f)
key = config['api']['key']
token = config['api']['token']

r = requests.get(f'https://api.trello.com/1/tokens/{token}/webhooks', params={'key': key})
webhooks = r.json()

updated = 0
for wh in webhooks:
    r = requests.put(
        f'https://api.trello.com/1/webhooks/{wh[\"id\"]}',
        params={'key': key, 'token': token},
        json={'callbackURL': '$CALLBACK_URL'}
    )
    if r.status_code == 200:
        updated += 1

print(f'{updated}/{len(webhooks)} webhooks updated')
" 2>&1 | while read line; do log "$line"; done

log "Done"
