# sessions_spawn - Быстрая справка
**Обновлено:** 2026-02-19

---

## ✅ Правильная конфигурация

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "subagents": {
          "allowAgents": ["*"]  // или ["devops", "ops", "tech", ...]
        }
      }
    ]
  }
}
```

**Путь:** `~/.openclaw/openclaw.json`

---

## 🚀 Как использовать (от main агента)

```javascript
sessions_spawn({
  agentId: 'devops',
  task: 'Проверь статус всех агентов',
  label: 'health-check',
  runTimeoutSeconds: 120
})
```

**Возвращает:**
```json
{
  "status": "running",
  "runId": "uuid",
  "childSessionKey": "agent:devops:subagent:uuid"
}
```

---

## 🔍 Проверка spawn

### Активные subagents
```bash
# Через tool
subagents(action='list')

# Через slash-команду в Telegram
/subagents list
```

### Логи
```bash
tail -50 /tmp/gateway.log | grep -i "spawn\|subagent"
```

### Конфиг
```bash
grep -A 13 '"id": "main"' ~/.openclaw/openclaw.json
```

---

## ⚠️ Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `forbidden` | Нет `allowAgents` | Добавь в main конфиг |
| Main делает сам | Слабые инструкции | Усиль SOUL.md |
| Конфиг слетел | Неправильный ключ | Используй `allowAgents` |
| Rate limit | Claude Opus/Sonnet | Переключи на GLM-5 |

---

## 📚 Документация

**Полная:** `/home/axis/openclaw/agents/devops/migrations/2026-02-19-sessions-spawn-setup.md`

**OpenClaw:** `~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/docs/tools/subagents.md`

---

## 🧪 Тестовая команда

Напиши @axis_main_bot:

```
Делегируй DevOps проверку системы.
Сохрани отчет в /home/axis/openclaw/reports/test.md
Дедлайн: 3 минуты
```

**Признак успеха:** main упоминает `childSessionKey`

---

*Quick reference | DevOps Agent*
