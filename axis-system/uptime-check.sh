#!/bin/bash
# Проверка доступности сервисов и алерт в Telegram

GATEWAY_URL="https://YOUR_GATEWAY_URL"
TELEGRAM_TOKEN=$(cat /home/axis/.openclaw/openclaw.json | python3 -c "
import sys,json
c=json.load(sys.stdin)
accounts = c.get('channels',{}).get('telegram',{}).get('accounts',{})
main = accounts.get('main',{})
print(main.get('botToken',''))
")
CHAT_ID="YOUR_TELEGRAM_ID"
STATUS_FILE="/tmp/axis-uptime-status.txt"

send_alert() {
    local msg="$1"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}&text=${msg}&parse_mode=HTML" > /dev/null 2>&1
}

# Check gateway
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$GATEWAY_URL" 2>/dev/null)
PREV_STATUS=$(cat "$STATUS_FILE" 2>/dev/null || echo "ok")

if [ "$HTTP_CODE" != "200" ]; then
    if [ "$PREV_STATUS" = "ok" ]; then
        send_alert "🚨 <b>AXIS ALERT</b>%0AGateway недоступен!%0AURL: ${GATEWAY_URL}%0ACode: ${HTTP_CODE}%0AВремя: $(date '+%H:%M %d.%m.%Y')"
        echo "down" > "$STATUS_FILE"
    fi
else
    if [ "$PREV_STATUS" = "down" ]; then
        send_alert "✅ <b>AXIS RECOVERED</b>%0AGateway снова доступен%0AВремя: $(date '+%H:%M %d.%m.%Y')"
    fi
    echo "ok" > "$STATUS_FILE"
fi
