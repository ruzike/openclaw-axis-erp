#!/bin/bash
# Автоочистка старых сессий OpenClaw
# Удаляет сессии старше 30 дней, кроме активных

SESSIONS_DIR="/home/axis/.openclaw/agents"
DAYS_OLD=30
LOG_FILE="/tmp/cleanup-sessions.log"

echo "$(date '+%Y-%m-%d %H:%M') Запуск очистки сессий (>${DAYS_OLD} дней)" >> $LOG_FILE

# Найти и удалить старые сессии
DELETED=0
TOTAL_SIZE=0

while IFS= read -r file; do
    SIZE=$(stat -c%s "$file" 2>/dev/null || echo 0)
    rm -f "$file"
    DELETED=$((DELETED + 1))
    TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
done < <(find "$SESSIONS_DIR" -name "*.jsonl" -mtime +$DAYS_OLD 2>/dev/null)

FREED_MB=$((TOTAL_SIZE / 1024 / 1024))
echo "$(date '+%Y-%m-%d %H:%M') Удалено: $DELETED файлов, освобождено: ~${FREED_MB}MB" >> $LOG_FILE

echo "Готово: удалено $DELETED сессий, освобождено ~${FREED_MB}MB"
