# AXIS Cron Registry
Последнее обновление: 2026-03-25

## 📊 Мониторинг и статус

| Расписание | Скрипт | Назначение | Лог | Статус |
|-----------|--------|-----------|-----|--------|
| `*/5 * * * *` | `uptime-check.sh` | Проверка доступности YOUR_GATEWAY_URL → алерт в Telegram при падении | `/tmp/axis-uptime-status.txt` | ✅ |
| `*/15 * * * *` | `monitor.py` | Мониторинг сервисов: gateway, cloudflared, trello-webhook, healthcheck | `/tmp/monitor.log` | ✅ |
| `*/30 * * * *` | `cron-monitor.py` | Мониторинг OpenClaw кронов — проверяет lastRunAtMs, алертит при зависании | `/tmp/cron-monitor.log` | ✅ |

## 📋 Дашборды

| Расписание | Скрипт | Назначение | Лог | Статус |
|-----------|--------|-----------|-----|--------|
| `*/5 * * * *` | `rituals-generate.py` | Генерация rituals.html для дашборда ритуалов | `/tmp/rituals-generate.log` | ✅ ⚠️ Слишком часто |
| `*/30 * * * *` | `cron-dashboard.py` | Генерация automation.html и обновление дашбордов | `/tmp/dashboard.log` | ✅ |
| `0 9-20 * * 1-6` | `generate_dashboard.py` | Основной дашборд index.html (каждый час 9-20, пн-сб) | `/tmp/dashboard.log` | ✅ |

## 🔧 Trello автоматизация

| Расписание | Скрипт | Назначение | Лог | Статус |
|-----------|--------|-----------|-----|--------|
| `0 9 * * *` | `trello-automation.py --action check-due-dates` | Проверка дедлайнов Trello | `/tmp/trello-butler.log` | ✅ |
| `5 9 * * *` | `trello-automation.py --action send-reminders` | Напоминания по Trello | `/tmp/trello-butler.log` | ✅ |
| `0 18 * * 5` | `trello-automation.py --action generate-report` | Еженедельный отчёт по Trello (пятница 18:00) | `/tmp/trello-report.log` | ✅ |

## 🧠 AI и память

| Расписание | Скрипт | Назначение | Лог | Статус |
|-----------|--------|-----------|-----|--------|
| `0 3 * * *` | `semantic-index.py` | Индексация projects-history в ChromaDB для семантического поиска | `/tmp/semantic-index.log` | ⚠️ 0 чанков (нет OPENAI_API_KEY в cron env) |
| `0 * * * *` | `ingress-automation.py` | Обработка входящих задач для агентов | `/tmp/ingress.log` | ✅ (нет задач) |

## 💾 Бэкапы

| Расписание | Скрипт | Назначение | Лог | Статус |
|-----------|--------|-----------|-----|--------|
| `0 2 * * *` | `backup/daily-backup.sh` | Полный бэкап сервера → tar.gz в /home/axis/backups | `/tmp/backup.log` | ✅ |
| `5 2 * * *` | `backup/gdrive-backup.sh` | Заливка последнего бэкапа на Google Drive | `/tmp/backup.log` | ✅ |
| `0 2 * * *` | `backup-config.sh` | Бэкап openclaw.json (без секретов) → GitHub ruzike/axis-config | `/tmp/backup-config.log` | ✅ |

## 🧹 Обслуживание

| Расписание | Скрипт | Назначение | Лог | Статус |
|-----------|--------|-----------|-----|--------|
| `0 0 * * 0` | `find /tmp/*.log -mtime +7 -delete` | Удаление логов старше 7 дней | — | ✅ |
| `0 4 * * 0` | `rotate-logs.sh` | Ротация больших логов >5MB (воскресенье 04:00) | `/tmp/rotate-logs.log` | ✅ |
| `0 3 * * 0` | DevOps агент | Очистка сессий OpenClaw старше 30 дней | — | ✅ |

## ⚠️ Известные проблемы

1. **semantic-index.py** — `OPENAI_API_KEY` не передаётся в cron, 0 чанков индексируется
2. **rituals-generate.py** — запускается каждые 5 мин, достаточно 30 мин
3. **Main агент** — Anthropic токен истёк, не отвечает

## 📈 Нагрузка (запусков в день)

| Скрипт | Запусков/день |
|--------|--------------|
| uptime-check.sh | 288 |
| rituals-generate.py | 288 ⚠️ |
| monitor.py | 96 |
| cron-monitor.py | 48 |
| cron-dashboard.py | 48 |
| generate_dashboard.py | 72 |
| ingress-automation.py | 24 |
| semantic-index.py | 1 |
| **ИТОГО** | **~865/день** |
