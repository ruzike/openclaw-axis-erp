#!/bin/bash
# OpenClaw AXIS ERP Installation Script

echo "🔧 Установка AXIS ERP Framework для OpenClaw..."

if ! command -v openclaw &> /dev/null; then
    echo "❌ Ошибка: OpenClaw не установлен. Установите через: npm install -g openclaw"
    exit 1
fi

echo "Введи твой Telegram ID (для владельца):"
read ADMIN_ID

# Заменяем плейсхолдеры на реальный ID
find ./agents -type f -exec sed -i "s/YOUR_TELEGRAM_ID/$ADMIN_ID/g" {} + 2>/dev/null
find ./axis-system -type f -exec sed -i "s/YOUR_TELEGRAM_ID/$ADMIN_ID/g" {} + 2>/dev/null

echo "📂 Копирую агентов и систему в ~/.openclaw/..."
cp -r agents/* ~/.openclaw/agents/ 2>/dev/null
mkdir -p ~/openclaw
cp -r axis-system ~/openclaw/
cp -r scripts ~/openclaw/
cp -r dashboard ~/openclaw/
cp -r knowledge ~/openclaw/
cp -r projects-history ~/openclaw/
cp trello-config.json ~/openclaw/

echo "✅ Установка завершена!"
echo "👉 Проверьте файл ~/openclaw/trello-config.json и добавьте туда ваши ключи Trello."
echo "👉 Настройте OpenClaw через: openclaw configure"
