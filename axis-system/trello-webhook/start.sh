#!/bin/bash
# Quick start script for Trello Webhook Server + Cloudflare Tunnel

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Trello Webhook System Startup${NC}"
echo "=================================="

# Проверка зависимостей
echo -e "\n${YELLOW}1. Проверка зависимостей...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден${NC}"
    exit 1
fi

if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}📦 Установка Flask...${NC}"
    pip install flask requests
fi

CLOUDFLARED=""
if command -v cloudflared &> /dev/null; then
    CLOUDFLARED="cloudflared"
elif [ -x "$HOME/.local/bin/cloudflared" ]; then
    CLOUDFLARED="$HOME/.local/bin/cloudflared"
else
    echo -e "${YELLOW}📦 Установка cloudflared...${NC}"
    mkdir -p ~/.local/bin
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o ~/.local/bin/cloudflared
    chmod +x ~/.local/bin/cloudflared
    CLOUDFLARED="$HOME/.local/bin/cloudflared"
fi

echo -e "${GREEN}✅ Все зависимости установлены${NC}"

# Запуск сервера
echo -e "\n${YELLOW}2. Запуск Webhook сервера...${NC}"

# Убиваем старые процессы
pkill -f "trello-webhook-server.py" 2>/dev/null || true

mkdir -p logs

nohup python3 trello-webhook-server.py > logs/server.out 2>&1 &
SERVER_PID=$!
echo "   PID: $SERVER_PID"

sleep 2

if curl -s http://localhost:18790/health > /dev/null; then
    echo -e "${GREEN}✅ Сервер запущен на порту 18790${NC}"
else
    echo -e "${RED}❌ Сервер не отвечает${NC}"
    exit 1
fi

# Запуск туннеля
echo -e "\n${YELLOW}3. Запуск Cloudflare Tunnel...${NC}"

# Убиваем старые туннели
pkill -f "cloudflared tunnel" 2>/dev/null || true

$CLOUDFLARED tunnel --url http://localhost:18790 2>&1 | tee logs/tunnel.log &
TUNNEL_PID=$!

echo "   PID: $TUNNEL_PID"
echo -e "${YELLOW}   Ожидание URL туннеля...${NC}"

sleep 5

# Извлекаем URL туннеля
TUNNEL_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" logs/tunnel.log | head -1)

if [ -n "$TUNNEL_URL" ]; then
    echo -e "${GREEN}✅ Туннель: $TUNNEL_URL${NC}"
    
    # Сохраняем URL для скриптов
    echo "$TUNNEL_URL" > .tunnel_url
    
    echo -e "\n${YELLOW}4. Настройка webhooks...${NC}"
    echo "   Выполните:"
    echo -e "   ${GREEN}python3 setup-trello-webhooks.py --url $TUNNEL_URL${NC}"
else
    echo -e "${RED}⚠️ URL туннеля ещё не доступен${NC}"
    echo "   Проверьте: tail -f logs/tunnel.log"
fi

echo -e "\n${GREEN}=================================="
echo "📊 Статус системы:"
echo "   Сервер:  http://localhost:18790/status"
echo "   Health:  http://localhost:18790/health"
echo "   Логи:    tail -f logs/webhook.log"
echo "   События: tail -f logs/events.log"
echo "==================================${NC}"
