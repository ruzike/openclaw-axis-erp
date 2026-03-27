# OPENCLAW СТРУКТУРА ФАЙЛОВ AXIS

**Knowledge Base:** DevOps Agent  
**Версия:** 1.0  
**Дата:** 2026-02-15

---

## 🎯 НАЗНАЧЕНИЕ

Этот документ содержит **полную карту файловой системы AXIS** на базе OpenClaw.

**Читать:**
- При старте каждой сессии
- Перед любыми операциями с файлами
- При создании новых агентов
- При диагностике проблем

**Полная версия:** `/home/axis/openclaw/FILESYSTEM.md`

---

## 📁 КРАТКАЯ СТРУКТУРА

### **SYSTEM: ~/.openclaw/**

```
~/.openclaw/                 # Служебные данные OpenClaw
├── openclaw.json            # ⚙️ Главный конфиг
├── openclaw.json.bak        # Последний автобэкап
├── openclaw.json.backup-*   # Timestamped бэкапы
├── .env.user                # Переменные окружения
│
├── memory/                  # 🧠 Vector Database
│   ├── main.sqlite         # 17 MB (108 сессий main агента)
│   ├── team.sqlite         # 15 MB (9 сессий team агента)
│   └── devops.sqlite       # Vector DB DevOps агента
│
├── agents/                  # 📝 История сессий (JSONL)
│   ├── main/sessions/      # 108 файлов истории
│   ├── team/sessions/      # 9 файлов истории
│   └── devops/sessions/    # История DevOps
│
├── credentials/             # 🔐 OAuth токены (НЕ коммитить в Git!)
│   ├── google-forms-oauth.json
│   ├── client_secret.json
│   └── telegram-*.json
│
├── cron/                    # ⏰ Автоматизация
│   ├── jobs.json           # 8 cron задач
│   └── runs/               # История запусков
│
├── logs/                    # 📊 Логи
│   └── openclaw.log        # Основной лог Gateway
│
├── subagents/               # Sub-agent сессии
├── telegram/                # Telegram plugin state
├── canvas/                  # Canvas snapshots
├── media/                   # Временные media файлы
├── identity/                # Device identity
├── devices/                 # Paired devices
└── exec-approvals.json     # Exec approval records
```

---

### **WORKSPACE: /home/axis/openclaw/**

```
/home/axis/openclaw/         # Контент, проекты, агенты
│
├── SOUL.md                  # 🤖 Main агент (@ruzClowdbot)
├── USER.md                  # 👤 Профиль Руслана
├── AGENTS.md                # 📋 Правила работы
├── MEMORY.md                # 💾 Долгосрочная память main
├── IDENTITY.md              # 🎭 Имя, эмодзи, аватар
├── HEARTBEAT.md             # 💓 Правила heartbeat
├── TOOLS.md                 # 🔧 Локальные заметки
├── FILESYSTEM.md            # 📁 ПОЛНАЯ ОФИЦИАЛЬНАЯ КАРТА
│
├── memory/                  # 📆 Daily logs main агента
│   ├── 2026-02-*.md
│   └── archive/             # Архив старых логов
│
├── agents/                  # 🤖 Агенты системы
│   ├── team/                # Team агент (Мирас + Бахытжан)
│   │   ├── SOUL.md
│   │   ├── AGENTS.md
│   │   ├── MEMORY.md (563 байт)
│   │   └── memory/
│   │
│   └── devops/              # 🔧 DevOps агент (я!)
│       ├── SOUL.md          # Этот промпт
│       ├── AGENTS.md
│       ├── MEMORY.md
│       ├── knowledge/       # 📚 База знаний
│       ├── runbooks/        # 📖 Инструкции
│       ├── migrations/      # 📝 История изменений
│       └── clients/         # 👥 Клиентские внедрения
│
├── projects/                # 🏗️ Проекты AXIS
│   ├── tokyo.md
│   ├── airport.md
│   ├── london.md
│   ├── sed_tower.md
│   └── apartment_5k.md
│
├── clients/                 # 👥 Клиенты
│   └── README.md
│
├── skills/                  # 🛠️ Кастомные навыки
│   ├── daily-usage/
│   └── google-forms/
│
├── trello-config.json       # 📋 Конфиг Trello (4 доски)
├── trello.py                # CLI для Trello
├── trello-report.py         # Утренние/вечерние отчёты
├── trello-briefing.py       # Обёртка для cron
├── trello-webhook.py        # Webhook сервер
├── .trello-state.json       # Состояние карточек
│
├── team-manager.py          # 👥 Управление командой
├── team-ping.py             # Пинги команде
├── team-report.py           # Отчёты команды
├── team-bridge.py           # Мост к Telegram
└── team-state.json          # Состояние Мираса + Бахытжана
```

---

## 🤖 TELEGRAM БОТЫ

| Бот | Username | Account ID | Агент | Роль |
|-----|----------|------------|-------|------|
| **Main** | `@ruzClowdbot` | `main` | `main` | Главный ассистент |
| **DevOps** | `@axis_devops_bot` | `devops` | `devops` | IT координатор |

**Routing:**
- `@ruzClowdbot` → main агент (Руслан: YOUR_TELEGRAM_ID)
- `@ruzClowdbot` → team агент (Мирас: MEMBER1_TELEGRAM_ID, Бахытжан: MEMBER2_TELEGRAM_ID, Группа: -5051416752)
- `@axis_devops_bot` → devops агент (все пользователи)

**Конфигурация:** `~/.openclaw/openclaw.json` → `channels.telegram.accounts` + `bindings`

---

## 🎯 КРИТИЧНЫЕ ПУТИ

### **System Prompts агентов:**

```bash
# Main агент
/home/axis/openclaw/SOUL.md

# Team агент
/home/axis/openclaw/agents/team/SOUL.md

# DevOps агент (я!)
/home/axis/openclaw/agents/devops/SOUL.md
```

### **Конфигурация:**

```bash
# Главный конфиг OpenClaw
~/.openclaw/openclaw.json

# Backup конфига
~/.openclaw/openclaw.json.backup-$(date +%Y%m%d)

# Переменные окружения
~/.openclaw/.env.user
```

### **Логи:**

```bash
# Основной лог Gateway
~/.openclaw/logs/openclaw.log

# Через CLI
openclaw logs --follow
```

### **Vector DB:**

```bash
# Main агент (17 MB, 108 сессий)
~/.openclaw/memory/main.sqlite

# Team агент (15 MB, 9 сессий)
~/.openclaw/memory/team.sqlite

# DevOps агент
~/.openclaw/memory/devops.sqlite
```

### **Sessions (история диалогов):**

```bash
# Main агент (108 файлов)
~/.openclaw/agents/main/sessions/

# Team агент (9 файлов)
~/.openclaw/agents/team/sessions/

# DevOps агент
~/.openclaw/agents/devops/sessions/
```

---

## 📋 ПРАВИЛА РАБОТЫ

### **WORKSPACE (`/home/axis/openclaw/`)**

**Назначение:** Контент, проекты, скрипты, агенты

**✅ Можно:**
- Создавать новые файлы
- Редактировать документы (SOUL.md, MEMORY.md, проекты)
- Добавлять проекты в `projects/`
- Создавать агентов в `agents/{id}/`
- Писать скрипты
- Коммитить в Git (кроме секретов)

**❌ Нельзя:**
- Удалять без backup
- Коммитить `.json` с токенами

**Структура агентов:**
- **Main:** файлы в корне (`/home/axis/openclaw/SOUL.md`)
- **Остальные:** в папках (`/home/axis/openclaw/agents/{id}/SOUL.md`)

---

### **SYSTEM (`~/.openclaw/`)**

**Назначение:** Системные файлы OpenClaw

**✅ Можно:**
- Редактировать `openclaw.json` (через CLI или вручную)
- Читать логи
- Читать Vector DB (только просмотр)
- Бэкапить `credentials/` (в безопасное место)

**❌ Нельзя:**
- Удалять Vector DB без backup
- Менять credentials напрямую
- Трогать sessions вручную
- Коммитить в Git (особенно credentials!)

**⚠️ КРИТИЧНО:** НЕ добавляй `~/.openclaw/` в Git!

---

## 🔍 БЫСТРЫЕ КОМАНДЫ

### **Проверка структуры:**

```bash
# Workspace
ls -la /home/axis/openclaw/
ls -la /home/axis/openclaw/agents/

# System
ls -lh ~/.openclaw/memory/
ls -1 ~/.openclaw/agents/main/sessions/ | wc -l

# Конфиг
cat ~/.openclaw/openclaw.json | jq .
```

### **Статус системы:**

```bash
# Общий статус
openclaw status

# Список агентов
openclaw agents list

# Валидация конфига
openclaw config validate
```

### **Логи:**

```bash
# В реальном времени
openclaw logs --follow

# Последние строки
tail -100 ~/.openclaw/logs/openclaw.log

# Поиск ошибок
grep -i error ~/.openclaw/logs/openclaw.log
```

---

## 📦 ЧТО БЭКАПИТЬ

### **Критично (ежедневно):**
- `~/.openclaw/openclaw.json`
- `/home/axis/openclaw/SOUL.md`
- `/home/axis/openclaw/agents/*/SOUL.md`
- `~/.openclaw/credentials/`

### **Важно (еженедельно):**
- `/home/axis/openclaw/MEMORY.md`
- `/home/axis/openclaw/projects/`
- `~/.openclaw/memory/*.sqlite`

### **Можно (ежемесячно):**
- `/home/axis/openclaw/memory/` (daily logs)
- `~/.openclaw/agents/*/sessions/`

---

## ⚠️ ВАЖНЫЕ ЗАМЕТКИ

1. **Main агент** хранится в корне workspace, не в `agents/main/`
2. **Team и DevOps** агенты в `agents/{id}/`
3. **Конфиг системы** в `~/.openclaw/`, не в workspace
4. **Проекты** в `/home/axis/openclaw/projects/`
5. **Vector DB автоматический** — OpenClaw сам создаёт и обновляет
6. **Credentials изолированы** — не попадают в Git случайно

---

## 🔗 СВЯЗАННЫЕ ДОКУМЕНТЫ

- **Полная карта:** `/home/axis/openclaw/FILESYSTEM.md`
- **Создание агентов:** `knowledge/agent-creation.md`
- **Telegram setup:** `knowledge/telegram-setup.md`
- **Backup:** `knowledge/backup-restore.md`

---

**Версия:** 1.0  
**Обновлено:** 2026-02-15  
**Статус:** ✅ Актуально
