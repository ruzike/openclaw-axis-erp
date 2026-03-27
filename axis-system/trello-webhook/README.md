# 🔄 Trello Webhook Server — Real-time синхронизация

Real-time синхронизация Trello → `axis-state.json` через Webhooks.

## 📊 Архитектура

```
Trello Board ──webhook──▶ Cloudflare Tunnel ──▶ Webhook Server ──▶ axis-state.json
     │                                               │
     │                                               ▼
     └───────────────── cron (fallback) ────▶ shared-state.py
```

**Основной режим:** Webhook-сервер получает события от Trello мгновенно  
**Fallback:** Cron job `1e5ea293` (каждый час) — остаётся активным на случай сбоя

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install flask requests
```

### 2. Запуск сервера

```bash
cd /home/axis/openclaw/axis-system/trello-webhook
python3 trello-webhook-server.py
```

Сервер стартует на порту `18790` (можно изменить через `TRELLO_WEBHOOK_PORT`).

### 3. Запуск Cloudflare Tunnel

```bash
# Установка cloudflared (один раз)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Запуск туннеля
cloudflared tunnel --url http://localhost:18790
```

Туннель выдаст URL вида: `https://xxx-xxx.trycloudflare.com`

### 4. Регистрация Webhooks

```bash
python3 setup-trello-webhooks.py --url https://xxx-xxx.trycloudflare.com
```

## 📁 Структура файлов

```
trello-webhook/
├── trello-webhook-server.py    # Flask сервер
├── setup-trello-webhooks.py    # Установка webhooks
├── remove-trello-webhooks.py   # Удаление webhooks
├── README.md                   # Эта документация
├── logs/
│   ├── webhook.log            # Основной лог сервера
│   └── events.log             # Лог событий Trello
└── test-events/               # Примеры событий для тестирования
```

## 🔧 Команды

### Сервер

```bash
# Запуск в foreground
python3 trello-webhook-server.py

# Запуск в background
nohup python3 trello-webhook-server.py > /dev/null 2>&1 &

# Проверка статуса
curl http://localhost:18790/health
curl http://localhost:18790/status
```

### Webhooks

```bash
# Показать текущие webhooks
python3 setup-trello-webhooks.py --list

# Проверить статус
python3 setup-trello-webhooks.py --check

# Установить webhooks
python3 setup-trello-webhooks.py --url https://your-tunnel.trycloudflare.com

# Удалить все webhooks
python3 remove-trello-webhooks.py --all

# Удалить конкретный
python3 remove-trello-webhooks.py --id <webhook_id>
```

## 🧪 Тестирование

### Локальный тест

```bash
# Отправить тестовое событие
curl -X POST http://localhost:18790/webhook/trello/test \
  -H "Content-Type: application/json" \
  -d @test-events/update-card.json
```

### Проверка через туннель

```bash
curl https://your-tunnel.trycloudflare.com/health
```

### Имитация Trello HEAD-запроса

```bash
curl -I https://your-tunnel.trycloudflare.com/webhook/trello
```

## 📝 Логи

```bash
# Основной лог сервера
tail -f logs/webhook.log

# Лог событий (только события Trello)
tail -f logs/events.log

# Последние 50 событий
tail -50 logs/events.log
```

## 🔒 Безопасность

1. **Верификация подписи** — Trello подписывает запросы через HMAC-SHA1
2. **HTTPS** — Cloudflare Tunnel обеспечивает TLS
3. **Фильтрация событий** — обрабатываются только релевантные события

## 🐛 Troubleshooting

### Webhook не срабатывает

1. Проверьте, что сервер запущен: `curl http://localhost:18790/health`
2. Проверьте туннель: `curl https://your-tunnel.trycloudflare.com/health`
3. Проверьте webhooks: `python3 setup-trello-webhooks.py --check`

### Trello отключил webhook

Trello отключает webhook после нескольких неудачных попыток (HTTP != 200).

```bash
# Переустановить webhooks
python3 remove-trello-webhooks.py --inactive
python3 setup-trello-webhooks.py --url https://new-tunnel.trycloudflare.com
```

### Туннель сменил URL

Cloudflare Quick Tunnel меняет URL при перезапуске.

```bash
# 1. Удалить старые webhooks
python3 remove-trello-webhooks.py --all

# 2. Запустить новый туннель
cloudflared tunnel --url http://localhost:18790

# 3. Установить webhooks с новым URL
python3 setup-trello-webhooks.py --url https://new-url.trycloudflare.com
```

## 🔐 Named Tunnel (Production)

**ВАЖНО:** Для стабильного URL, который не меняется при перезапусках, используйте Named Tunnel.

### Автоматическая миграция

```bash
# Один раз: авторизация в Cloudflare
cloudflared tunnel login
# Откройте URL в браузере и выберите зону

# Запустите скрипт миграции
./migrate-to-named-tunnel.sh
```

### Ручная настройка

```bash
# 1. Авторизация
cloudflared tunnel login

# 2. Создать туннель
cloudflared tunnel create axis-trello-webhook

# 3. Получить tunnel ID (запомнить!)
cloudflared tunnel list
# Стабильный URL: https://<TUNNEL_ID>.cfargotunnel.com

# 4. Создать config.yml
cat > ~/.cloudflared/config.yml << EOF
tunnel: <TUNNEL_ID>
credentials-file: /home/axis/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: <TUNNEL_ID>.cfargotunnel.com
    service: http://localhost:18790
  - service: http_status:404
EOF

# 5. Запуск
cloudflared tunnel run axis-trello-webhook
```

### Systemd для Named Tunnel

```bash
sudo systemctl stop cloudflared-tunnel
sudo cp cloudflared-tunnel.service.new /etc/systemd/system/cloudflared-tunnel.service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared-tunnel
sudo systemctl start cloudflared-tunnel
```

### Проверка стабильности

```bash
# Перезапуск туннеля
sudo systemctl restart cloudflared-tunnel

# URL не должен измениться
cat .tunnel_url
curl $(cat .tunnel_url)/health
```

### Quick Tunnel (Development)

Для тестов можно использовать Quick Tunnel (URL меняется при каждом перезапуске):

## 🔄 Systemd (автозапуск)

```bash
# Копировать unit file
sudo cp trello-webhook.service /etc/systemd/system/

# Включить и запустить
sudo systemctl daemon-reload
sudo systemctl enable trello-webhook
sudo systemctl start trello-webhook

# Статус
sudo systemctl status trello-webhook
journalctl -u trello-webhook -f
```

## 📊 Мониторируемые доски

Автоматически загружаются из `/home/axis/openclaw/trello-config.json`:

| Ключ | Название |
|------|----------|
| production / c1c2 | C1 C2 — Концепция и Визуализация |
| c3 | C3 — Рабочий проект |
| c5 | C5 — Авторский надзор |
| strategy | Стратегия |
| agents_ideas | 💡 Идеи: Агенты |

## 📡 Обрабатываемые события

| Событие | Описание |
|---------|----------|
| `createCard` | Создание карточки |
| `updateCard` | Обновление карточки (перемещение, изменение) |
| `deleteCard` | Удаление карточки |
| `moveCardToBoard` | Перемещение карточки на другую доску |
| `createList` | Создание списка |
| `updateList` | Обновление списка |

## 🔗 Связанные файлы

- **Конфиг Trello:** `/home/axis/openclaw/trello-config.json`
- **Shared State:** `/home/axis/openclaw/axis-system/axis-state.json`
- **Fallback скрипт:** `/home/axis/openclaw/axis-system/shared-state.py`
- **Cron job:** `1e5ea293` (hourly)

---

**Автор:** DevOps Agent (AXIS System)  
**Версия:** 1.0.0  
**Дата:** 2026-03-02
