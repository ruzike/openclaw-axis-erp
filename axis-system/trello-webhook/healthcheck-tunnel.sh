#!/bin/bash
# =============================================================================
# healthcheck-tunnel.sh — Проверка живости Cloudflare Tunnel
# Запускается каждые 5 минут через OpenClaw cron
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/healthcheck.log"
TUNNEL_URL_FILE="$SCRIPT_DIR/.tunnel_url"
RESTART_SCRIPT="$SCRIPT_DIR/restart-tunnel.sh"
FLASK_PORT=18790
MAX_FAILURES=2

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# --- Проверка Flask сервера ---
check_flask() {
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:$FLASK_PORT/health" 2>/dev/null)
    echo "$code"
}

# --- Проверка Cloudflare Tunnel ---
check_tunnel() {
    if [ ! -f "$TUNNEL_URL_FILE" ]; then
        echo "no_url_file"
        return
    fi

    local url
    url=$(cat "$TUNNEL_URL_FILE" 2>/dev/null)

    if [ -z "$url" ]; then
        echo "empty_url"
        return
    fi

    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${url}/health" 2>/dev/null)
    echo "$code"
}

# --- Проверка cloudflared процесса ---
check_cloudflared_process() {
    pgrep -x cloudflared > /dev/null 2>&1
    return $?
}

# --- Основная логика ---
log "=== Healthcheck started ==="

# 1. Проверяем Flask
FLASK_CODE=$(check_flask)
if [ "$FLASK_CODE" = "200" ] || [ "$FLASK_CODE" = "404" ]; then
    log "✅ Flask OK (HTTP $FLASK_CODE)"
else
    log "⚠️ Flask не отвечает (HTTP $FLASK_CODE) — пробуем перезапустить"
    cd "$SCRIPT_DIR"
    bash start.sh >> "$LOG_FILE" 2>&1
    sleep 5
fi

# 2. Проверяем cloudflared процесс
if check_cloudflared_process; then
    log "✅ cloudflared процесс жив"
else
    log "❌ cloudflared не запущен — перезапускаем туннель"
    bash "$RESTART_SCRIPT" >> "$LOG_FILE" 2>&1
    sleep 15
fi

# 3. Проверяем публичный URL
TUNNEL_CODE=$(check_tunnel)
if [ "$TUNNEL_CODE" = "200" ] || [ "$TUNNEL_CODE" = "404" ]; then
    log "✅ Tunnel OK (HTTP $TUNNEL_CODE)"
else
    TUNNEL_URL=$(cat "$TUNNEL_URL_FILE" 2>/dev/null)
    log "❌ Tunnel недоступен (HTTP $TUNNEL_CODE, URL: $TUNNEL_URL) — перезапускаем"
    bash "$RESTART_SCRIPT" >> "$LOG_FILE" 2>&1
    sleep 15

    # Повторная проверка после рестарта
    TUNNEL_CODE2=$(check_tunnel)
    if [ "$TUNNEL_CODE2" = "200" ] || [ "$TUNNEL_CODE2" = "404" ]; then
        log "✅ Tunnel восстановлен после рестарта"
    else
        log "🚨 Tunnel всё ещё недоступен после рестарта (HTTP $TUNNEL_CODE2)"
        # Ротация логов (последние 1000 строк)
        tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
        exit 1
    fi
fi

# Ротация лога (последние 2000 строк)
if [ $(wc -l < "$LOG_FILE" 2>/dev/null || echo 0) -gt 2000 ]; then
    tail -2000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

log "=== Healthcheck done ==="
exit 0
