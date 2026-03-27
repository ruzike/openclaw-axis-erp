#!/bin/bash
BACKUP_DIR="/home/axis/openclaw/config-backup"
CONFIG_FILE="/home/axis/.openclaw/openclaw.json"
DATE=$(date '+%Y-%m-%d %H:%M')

cd "$BACKUP_DIR"

python3 - << 'PYEOF'
import json
with open('/home/axis/.openclaw/openclaw.json') as f:
    config = json.load(f)

def redact(obj):
    if isinstance(obj, dict):
        return {k: '__REDACTED__' if any(s in k.lower() for s in ['token','password','secret','key','apikey']) else redact(v) for k,v in obj.items()}
    elif isinstance(obj, list):
        return [redact(i) for i in obj]
    return obj

with open('openclaw-backup.json', 'w') as f:
    json.dump(redact(config), f, indent=2, ensure_ascii=False)
PYEOF

git add openclaw-backup.json
git diff --cached --quiet && echo "No changes" && exit 0
git commit -m "Config backup: $DATE"
git push origin main 2>&1 | tail -2
echo "✅ Backup pushed: $DATE"
