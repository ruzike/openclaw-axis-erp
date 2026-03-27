#!/bin/bash
# Ротация логов AXIS — запускается еженедельно

MAX_SIZE=$((5 * 1024 * 1024))  # 5MB

LOGS=(
    /tmp/cron-monitor.log
    /tmp/monitor.log
    /tmp/rituals-generate.log
    /tmp/dashboard.log
    /tmp/ingress.log
    /tmp/backup.log
    /tmp/trello-butler.log
)

for LOG in "${LOGS[@]}"; do
    if [ -f "$LOG" ]; then
        SIZE=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
        if [ "$SIZE" -gt "$MAX_SIZE" ]; then
            # Rotate: keep last 500 lines, archive the rest
            ARCHIVE="${LOG}.$(date '+%Y%m%d').gz"
            head -n -500 "$LOG" | gzip > "$ARCHIVE"
            tail -n 500 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
            echo "$(date '+%Y-%m-%d %H:%M') Rotated: $(basename $LOG) (${SIZE} bytes → archive)"
        fi
    fi
done

# Delete archives older than 30 days
find /tmp -name "*.log.*.gz" -mtime +30 -delete 2>/dev/null

echo "$(date '+%Y-%m-%d %H:%M') Log rotation complete"
