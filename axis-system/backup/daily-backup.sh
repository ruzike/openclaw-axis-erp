#!/bin/bash
# AXIS Daily Config Backup
# Бэкапит критические конфиги в ~/backups/
# Хранит последние 7 бэкапов

set -euo pipefail

BACKUP_DIR="/home/axis/backups"
DATE=$(date +%Y-%m-%d_%H%M)
BACKUP_FILE="$BACKUP_DIR/axis-backup-$DATE.tar.gz"
MAX_BACKUPS=7
FILELIST=$(mktemp)

mkdir -p "$BACKUP_DIR"

echo "📦 AXIS Backup started: $DATE"

# Собираем список файлов
{
    # OpenClaw main config
    echo ".openclaw/openclaw.json"

    # Auth profiles всех агентов
    find .openclaw/agents -name "auth-profiles.json" 2>/dev/null

    # SOUL, MEMORY, TOOLS всех агентов
    find openclaw/agents -maxdepth 2 \( -name "SOUL.md" -o -name "MEMORY.md" -o -name "TOOLS.md" \) 2>/dev/null

    # Knowledge базы
    find openclaw/agents -path "*/knowledge/*" -type f 2>/dev/null

    # Systemd services
    find .config/systemd/user -name "*.service" 2>/dev/null

    # Axis-system configs
    echo "openclaw/axis-system/monitor.py"
    echo "openclaw/axis-system/healthcheck/healthcheck-server.py"
    find openclaw/axis-system/trello-webhook -name "*.json" -o -name "*.py" 2>/dev/null

    # Crontab dump
} > "$FILELIST"

# Сохраняем crontab отдельно
crontab -l > /tmp/crontab-backup.txt 2>/dev/null || true

cd /home/axis
tar czf "$BACKUP_FILE" \
    --files-from="$FILELIST" \
    /tmp/crontab-backup.txt \
    --ignore-failed-read \
    2>/dev/null || true

rm -f "$FILELIST"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
COUNT=$(tar tzf "$BACKUP_FILE" 2>/dev/null | wc -l)
echo "✅ Backup created: $BACKUP_FILE ($SIZE, $COUNT files)"

# Ротация — удаляем старые
cd "$BACKUP_DIR"
ls -t axis-backup-*.tar.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f 2>/dev/null || true

TOTAL=$(ls axis-backup-*.tar.gz 2>/dev/null | wc -l)
echo "📊 Total backups: $TOTAL (max: $MAX_BACKUPS)"
echo "🏁 Backup finished: $(date +%H:%M:%S)"
