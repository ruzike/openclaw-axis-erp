# Инфраструктура AXIS

## 🏗️ ПЛАТФОРМА
**OpenClaw:** 2026.3.1 (настроен на Ubuntu 24 WSL2)
**Серверы:** Текущий - локальный WSL2. Ожидается переезд на VPS (Hetzner/Beget).
**Gateway:** Порт 18789.

## 🤖 АГЕНТЫ СИСТЕМЫ
- **main** (@axis_main_bot) - Главный агент, стратегия
- **devops** (@axis_devops_bot) - IT координатор
- **ops** (@axis_opps_bot) - Ритуалы управления, координация
- **qc** (@axis_qc_bot) - Контроль качества
- **tech** (@axis_arch_tech_bot) - Регламенты, автоматизация
- **hr** (@axis_teams_bot) - Найм, развитие команды
- **finance** (@axis_finance_bot) - Бюджеты, счета
- **sales** (@axis_sales_bot) - Продажи, клиенты
- **draftsman** (@axis_draftsman_bot) - BIM/CAD
- **shket** (@neuro_dir) - SMM автопубликации

## 🔧 ИНТЕГРАЦИИ
- **Trello:** 5 досок. Webhooks через Flask (порт 18790) + Cloudflare Quick Tunnel. Буфер SQLite.
- **Google:** OAuth настроен для Docs, Sheets, Drive.
- **Midjourney:** Интеграция через Discord token.
- **Semantic Search:** ChromaDB (port 8000) + OpenAI text-embedding-ada-002.

## 📚 КЛЮЧЕВЫЕ ПУТИ
- `~/.openclaw/openclaw.json` - Главный конфиг
- `~/.openclaw/agents/<agent_id>/agent/auth-profiles.json` - Токены агентов
- `/home/axis/openclaw/axis-system/` - Ядро скриптов (webhooks, state, search)
- `~/.openclaw/logs/` - Логи Gateway и кронов
- `/home/axis/openclaw/axis-system/trello-webhook/logs/` - Логи Trello Webhooks

## 💡 ИЗВЕСТНЫЕ ПРОБЛЕМЫ / РЕШЕНИЯ
- **Cron Jobs (Isolated):** Требуют пустого `BOOTSTRAP.md` в папке агента (баг 2026.3.1).
- **Trello Webhooks:** Настроен debounce 10 сек во избежание спама API Trello. При рестарте туннеля URL меняется -> крон обновляет вебхуки автоматически.
- **Токены:** Claude session tokens (sk-ant-sid02-) часто протухают. Платный API key (sk-ant-api03-) самый надежный. Модели в `openclaw.json` больше не поддерживают префиксы `anthropic:профиль/`. Выбор профиля идет через ORDER в `auth-profiles.json`.
