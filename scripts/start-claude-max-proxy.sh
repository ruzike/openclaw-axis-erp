#!/bin/bash
# Автозапуск claude-max-api-proxy (использует Claude Max/Pro подписку)
# Запускается при старте WSL через cron @reboot

LOGFILE="/tmp/claude-max-api.log"
PIDFILE="/tmp/claude-max-api.pid"

# Если уже запущен — выходим
if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
  echo "claude-max-api уже запущен (PID: $(cat $PIDFILE))"
  exit 0
fi

# Запускаем без ANTHROPIC_API_KEY чтобы использовал OAuth (Max подписку)
export -n ANTHROPIC_API_KEY
nohup claude-max-api > "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
echo "claude-max-api запущен (PID: $!, порт 3456)"
