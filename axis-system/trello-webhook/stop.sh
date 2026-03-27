#!/bin/bash
# Stop Trello Webhook Server and Cloudflare Tunnel

echo "🛑 Останавливаем Trello Webhook System..."

# Остановка сервера
if pkill -f "trello-webhook-server.py" 2>/dev/null; then
    echo "   ✅ Webhook сервер остановлен"
else
    echo "   ⏭️ Webhook сервер не был запущен"
fi

# Остановка туннеля
if pkill -f "cloudflared tunnel" 2>/dev/null; then
    echo "   ✅ Cloudflare Tunnel остановлен"
else
    echo "   ⏭️ Cloudflare Tunnel не был запущен"
fi

echo ""
echo "💡 Cron fallback (1e5ea293) продолжает работать"
