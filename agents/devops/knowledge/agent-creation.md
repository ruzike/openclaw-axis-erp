# СОЗДАНИЕ НОВОГО АГЕНТА

**Knowledge Base:** DevOps Agent  
**Версия:** 1.0  
**Дата:** 2026-02-15

---

## 🎯 НАЗНАЧЕНИЕ

Пошаговая инструкция по созданию нового AI-агента в системе OpenClaw.

**Используй перед:**
- Добавлением любого нового агента
- Внедрением АСБ методологии (8 агентов)
- Клиентскими внедрениями

---

## ✅ QUICK CHECKLIST

**Перед началом проверь:**
- [ ] Прочитал `knowledge/checklists.md` → "Создание агента"
- [ ] Создал backup: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d)`
- [ ] Выбрал модель для агента
- [ ] Создал Telegram бота (если нужен) через @BotFather

---

## 🚀 ШАГ 1: ПОДГОТОВКА WORKSPACE

### **Создать структуру папок:**

```bash
# Создать базовую структуру
mkdir -p /home/axis/openclaw/agents/{agent_id}
mkdir -p /home/axis/openclaw/agents/{agent_id}/knowledge
mkdir -p /home/axis/openclaw/agents/{agent_id}/migrations
mkdir -p /home/axis/openclaw/agents/{agent_id}/memory

# Создать базовые файлы
touch /home/axis/openclaw/agents/{agent_id}/SOUL.md
touch /home/axis/openclaw/agents/{agent_id}/AGENTS.md
touch /home/axis/openclaw/agents/{agent_id}/MEMORY.md
touch /home/axis/openclaw/agents/{agent_id}/README.md
```

**Пример:**
```bash
mkdir -p /home/axis/openclaw/agents/finance
mkdir -p /home/axis/openclaw/agents/finance/{knowledge,migrations,memory}
touch /home/axis/openclaw/agents/finance/{SOUL.md,AGENTS.md,MEMORY.md,README.md}
```

---

## 📝 ШАГ 2: НАПИСАТЬ SOUL.MD

### **Использовать шаблон:**

**См.:** `knowledge/agent-templates.md`

### **Структура System Prompt:**

```markdown
# SYSTEM PROMPT: {AGENT NAME}
# Версия: 1.0
# Компания: AXIS

---

## CORE IDENTITY
Кто я, моя роль, главная цель

## ЦЕЛЕВЫЕ МЕТРИКИ
Измеримые KPI

## ОБЯЗАННОСТИ
Что делаю, инструменты

## DECISION-MAKING
Уровни автономии (1/2/3)

## ВЗАИМОДЕЙСТВИЕ С АГЕНТАМИ
С кем работаю

## STYLE
Как общаюсь

## BOUNDARIES
Что можно/нельзя
```

### **Референсы:**
- Main агент: `/home/axis/openclaw/SOUL.md`
- Team агент: `/home/axis/openclaw/agents/team/SOUL.md`
- DevOps агент: `/home/axis/openclaw/agents/devops/SOUL.md`

### **Советы:**
- Будь конкретным в обязанностях
- Определи чёткие метрики
- Укажи уровни согласования
- Добавь примеры взаимодействия

---

## ⚙️ ШАГ 3: ДОБАВИТЬ В OPENCLAW.JSON

### **3.1. Создать backup:**

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)
```

### **3.2. Добавить агента в конфиг:**

```bash
# Открыть конфиг
nano ~/.openclaw/openclaw.json
```

**Добавить в `agents.list`:**

```json
{
  "agents": {
    "list": [
      // ... существующие агенты ...
      
      {
        "id": "{agent_id}",
        "workspace": "/home/axis/openclaw/agents/{agent_id}",
        "enabled": true,
        "model": {
          "primary": "anthropic/claude-opus-4-6"  // выбери модель
        },
        "tools": {
          "profile": "coding"  // или custom profile
        }
      }
    ]
  }
}
```

### **Выбор модели:**

| Модель | Когда использовать | Стоимость |
|--------|-------------------|-----------|
| `anthropic/claude-opus-4-6` | Критичные агенты (Sales, Projects) | $15/1M tokens |
| `anthropic/claude-sonnet-4-5` | Средние задачи (Marketing, Analytics) | $3/1M tokens |
| `zai/glm-5` | Некритичные задачи (Team, Finance) | Бесплатно |

### **3.3. Проверить валидность:**

```bash
openclaw config validate
```

**Если ошибка:**
```bash
# Посмотреть детали
openclaw config validate 2>&1

# Проверить JSON синтаксис
jq . ~/.openclaw/openclaw.json

# Откатить если нужно
cp ~/.openclaw/openclaw.json.backup-* ~/.openclaw/openclaw.json
```

---

## 📱 ШАГ 4: TELEGRAM БОТ (ОПЦИОНАЛЬНО)

**Если агенту нужен отдельный Telegram бот:**

### **4.1. Создать бота через @BotFather:**

1. Открыть Telegram → найти **@BotFather**
2. Команда: `/newbot`
3. Имя бота: `{Agent Name} Bot` (например: "Finance Bot")
4. Username: `axis_{agent_id}_bot` (например: `axis_finance_bot`)
5. **Скопировать токен:** `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### **4.2. Добавить в openclaw.json:**

**См. детали:** `knowledge/telegram-setup.md`

**Краткая версия:**

```json
{
  "channels": {
    "telegram": {
      "accounts": {
        "{agent_id}": {
          "botToken": "ТОКЕН_ОТ_BOTFATHER",
          "dmPolicy": "pairing",
          "label": "{Agent Name} Bot",
          "allowFrom": [YOUR_TELEGRAM_ID, MEMBER1_TELEGRAM_ID, MEMBER2_TELEGRAM_ID]
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "{agent_id}",
      "match": {
        "channel": "telegram",
        "accountId": "{agent_id}"
      }
    }
  ]
}
```

---

## 🔍 ШАГ 5: ПРОВЕРКА РАБОТОСПОСОБНОСТИ

### **5.1. Валидация конфига:**

```bash
openclaw config validate
```

**Ожидаемый результат:** `✅ Config valid`

### **5.2. Перезапуск Gateway:**

```bash
# Остановить
openclaw gateway stop

# Или через процесс
pkill -f "openclaw gateway"

# Запустить заново
openclaw gateway
```

### **5.3. Проверка статуса:**

```bash
# Общий статус
openclaw status

# Список агентов
openclaw agents list

# Должен быть в списке: {agent_id}
```

### **5.4. Проверка логов:**

```bash
# В реальном времени
openclaw logs --follow

# Должно быть:
# [Gateway] Agent {agent_id} registered
# [Agent {agent_id}] Ready
```

### **5.5. Тест агента:**

**Через Telegram:**
```
1. Открыть бота @axis_{agent_id}_bot
2. Отправить /start
3. Написать: "Привет, кто ты?"
4. Агент должен ответить
```

**Через TUI:**
```bash
openclaw tui --agent {agent_id}
# Написать сообщение
```

---

## 📝 ШАГ 6: ДОКУМЕНТАЦИЯ

### **6.1. Создать файл миграции:**

```bash
cat > /home/axis/openclaw/agents/{agent_id}/migrations/$(date +%Y-%m-%d)-created.md << 'EOF'
# Агент {agent_id} создан

**Дата:** $(date +%Y-%m-%d)
**Автор:** DevOps Agent
**Роль:** [описание роли агента]

## Конфигурация:
- **ID:** {agent_id}
- **Workspace:** /home/axis/openclaw/agents/{agent_id}/
- **Модель:** [модель]
- **Telegram:** @axis_{agent_id}_bot (опционально)

## Изменения в openclaw.json:
```json
{
  "id": "{agent_id}",
  "workspace": "/home/axis/openclaw/agents/{agent_id}",
  "enabled": true
}
```

## Проверка:
```bash
openclaw status
# ✅ Gateway: reachable
# ✅ Agents: [количество] (включая {agent_id})

openclaw agents list
# ✅ {agent_id} в списке
```

## Backup:
~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)

## Результат:
✅ Агент создан и работает
EOF
```

### **6.2. Обновить README.md агента:**

```bash
cat > /home/axis/openclaw/agents/{agent_id}/README.md << 'EOF'
# {Agent Name} Agent

**Роль:** [описание]
**Модель:** [модель]
**Telegram:** @axis_{agent_id}_bot (если есть)

## Обязанности:
- [что делает]

## Взаимодействие:
- Вызывает: [других агентов]
- Вызывается: [кем]

## Метрики:
- [KPI 1]: [цель]
- [KPI 2]: [цель]

## Файлы:
- `SOUL.md` - System prompt
- `MEMORY.md` - Долгосрочная память
- `knowledge/` - База знаний (если есть)
EOF
```

### **6.3. Обновить CHANGELOG:**

```bash
cat >> /home/axis/openclaw/agents/devops/migrations/CHANGELOG.md << EOF

## $(date +%Y-%m-%d)
- ✅ Создан агент {agent_id}
- Модель: [модель]
- Telegram: @axis_{agent_id}_bot
- Workspace: /home/axis/openclaw/agents/{agent_id}/
EOF
```

---

## 🎯 ФИНАЛЬНЫЙ ЧЕКЛИСТ

После завершения проверь:

- [ ] ✅ Workspace создан: `/home/axis/openclaw/agents/{agent_id}/`
- [ ] ✅ SOUL.md написан (по шаблону)
- [ ] ✅ Агент добавлен в `openclaw.json`
- [ ] ✅ Telegram бот создан (если нужен)
- [ ] ✅ Binding настроен (если Telegram)
- [ ] ✅ Backup создан: `~/.openclaw/openclaw.json.backup-*`
- [ ] ✅ Конфиг валиден: `openclaw config validate`
- [ ] ✅ Gateway перезапущен
- [ ] ✅ Агент в списке: `openclaw agents list`
- [ ] ✅ Логи без ошибок: `openclaw logs`
- [ ] ✅ Тест пройден (Telegram или TUI)
- [ ] ✅ Миграция задокументирована
- [ ] ✅ README.md создан

---

## 🚨 TROUBLESHOOTING

### **Агент не появляется в списке:**

```bash
# Проверить конфиг
openclaw config validate

# Проверить agents.list
cat ~/.openclaw/openclaw.json | jq '.agents.list[] | select(.id=="{agent_id}")'

# Перезапустить Gateway
openclaw gateway stop && openclaw gateway
```

### **Конфиг невалиден:**

```bash
# Детали ошибки
openclaw config validate 2>&1

# Проверить JSON синтаксис
jq . ~/.openclaw/openclaw.json

# Откатить
cp ~/.openclaw/openclaw.json.backup-* ~/.openclaw/openclaw.json
```

### **Gateway не запускается:**

```bash
# Проверить логи
tail -100 ~/.openclaw/logs/openclaw.log

# Проверить порт
lsof -i :18789

# Убить процесс если завис
pkill -9 -f "openclaw gateway"
```

### **Telegram бот не отвечает:**

**См.:** `knowledge/telegram-setup.md` → Troubleshooting

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

- **Шаблоны SOUL:** `knowledge/agent-templates.md`
- **Telegram setup:** `knowledge/telegram-setup.md`
- **АСБ методология:** `knowledge/asb-methodology.md`
- **Чеклисты:** `knowledge/checklists.md`
- **Troubleshooting:** `knowledge/troubleshooting.md`

---

## 📊 СТАТИСТИКА

**Время создания агента:** ~30 минут
- Подготовка workspace: 5 мин
- Написание SOUL.md: 15 мин
- Конфигурация: 5 мин
- Проверка: 3 мин
- Документация: 2 мин

**Создано агентов:** [tracking]

---

**Версия:** 1.0  
**Обновлено:** 2026-02-15  
**Статус:** ✅ Готово к использованию
