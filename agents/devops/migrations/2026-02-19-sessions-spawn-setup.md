# Настройка sessions_spawn (межагентное взаимодействие)
**Дата:** 2026-02-19  
**Автор:** DevOps Agent  
**Статус:** ✅ Успешно настроено и протестировано  
**Время настройки:** ~3 часа (с учётом troubleshooting)

---

## 🎯 ЦЕЛЬ

Настроить межагентное делегирование задач через `sessions_spawn`:
- Main агент координирует и делегирует
- Специализированные агенты (DevOps, Tech, Ops, Sales) выполняют задачи
- Результаты автоматически возвращаются Main
- Main отчитывается пользователю

---

## 📋 ПРОБЛЕМЫ КОТОРЫЕ БЫЛИ

### Проблема 1: Неправильный ключ конфигурации
**Симптом:** spawn не работает, main делает задачи сам

**Попытки (НЕ работали):**
```json
// ❌ Попытка 1
"tools": {
  "subagents": {
    "enabled": true,
    "allowed": ["devops", ...]
  }
}

// ❌ Попытка 2
"subagents": {
  "allowed": ["*"]
}

// ❌ Попытка 3 (в defaults)
"defaults": {
  "subagents": {
    "maxConcurrent": 8,
    "allowed": "*"
  }
}
```

**Решение (✅ работает):**
```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "model": { ... },
        "subagents": {
          "allowAgents": ["*"]  // ← ПРАВИЛЬНЫЙ КЛЮЧ!
        }
      }
    ]
  }
}
```

**Источник:** `/docs/tools/subagents.md` (документация OpenClaw)

---

### Проблема 2: Конфиг слетает после перезапуска
**Симптом:** Добавляешь настройку → перезапускаешь gateway → конфиг становится `{}`

**Причина:** Gateway **нормализует** конфиг при старте и удаляет неправильные ключи

**Решение:**
1. Используй ТОЛЬКО правильные ключи из документации
2. Не добавляй кастомные поля без документации
3. После изменения конфига проверяй: `grep -A 15 '"id": "main"' ~/.openclaw/openclaw.json`

---

### Проблема 3: Rate limits (Anthropic API)
**Симптом:** 
```
FailoverError: ⚠️ API rate limit reached. Please try again later.
```

**Причина:** Main использовал Claude Opus/Sonnet → быстро исчерпал лимиты API

**Решение:**
```json
"main": {
  "model": {
    "primary": "zai/glm-5",        // Бесплатный, без лимитов
    "fallbacks": [
      "zai/glm-4.7-flash"          // Бесплатный резерв
    ]
  }
}
```

**Почему GLM-5:**
- ✅ Бесплатный (API от Z.AI)
- ✅ Нет rate limits
- ✅ 200k контекст
- ✅ Достаточно умный для координации
- ⚠️ Слабее Claude Opus для сложных задач

---

### Проблема 4: Gemini 503 (memorySearch)
**Симптом:**
```
{ "error": { "code": 503, "message": "high demand" } }
```

**Причина:** Main использовал Gemini для поиска в памяти (embeddings)

**Решение:**
```json
"defaults": {
  "memorySearch": {
    "provider": "openai"  // Вместо "gemini"
  }
}
```

---

### Проблема 5: Main не делегирует, делает сам
**Симптом:** Main отвечает с результатом, но spawn не происходит

**Причина:** SOUL.md недостаточно жёсткий

**Решение:** Добавить в `/home/axis/openclaw/SOUL.md`:

```markdown
## 🛡️ BOUNDARIES (ГРАНИЦЫ)

**❌ НИКОГДА НЕ ДЕЛАЙ САМ:**
*   Проверку серверов, агентов, инфраструктуры → ВСЕГДА `sessions_spawn(agentId='devops', ...)`
*   Создание регламентов, процессов → ВСЕГДА `sessions_spawn(agentId='tech', ...)`
*   Проведение планерок, координацию → ВСЕГДА `sessions_spawn(agentId='ops', ...)`

**⚠️ ПРАВИЛО:** Если задача требует технических команд (exec, openclaw status) 
— ОБЯЗАТЕЛЬНО делегируй через sessions_spawn!
```

---

## ✅ ФИНАЛЬНАЯ РАБОЧАЯ КОНФИГУРАЦИЯ

### ~/.openclaw/openclaw.json

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "sources": ["memory", "sessions"],
        "provider": "openai",  // НЕ gemini!
        "store": {
          "vector": { "enabled": true }
        }
      },
      "subagents": {
        "maxConcurrent": 8
      }
    },
    "list": [
      {
        "id": "main",
        "model": {
          "primary": "zai/glm-5",
          "fallbacks": [
            "zai/glm-4.7-flash"
          ]
        },
        "subagents": {
          "allowAgents": ["*"]  // ← КЛЮЧЕВАЯ НАСТРОЙКА!
        }
      }
    ]
  },
  "tools": {
    "agentToAgent": {
      "enabled": true
    }
  }
}
```

---

## 🧪 КАК ПРОТЕСТИРОВАТЬ

### Тест 1: Проверка конфигурации
```bash
# Проверить что allowAgents на месте
grep -A 13 '"id": "main"' ~/.openclaw/openclaw.json

# Должно быть:
# "subagents": {
#   "allowAgents": ["*"]
# }
```

### Тест 2: Проверка через main бота
Напиши @axis_main_bot в Telegram:

```
Делегируй DevOps проверку системы.

Задача: проверь статус gateway и агентов, создай отчет.

Сохрани в /home/axis/openclaw/reports/test-spawn.md

Дедлайн: 3 минуты
```

### Тест 3: Проверка что spawn сработал

**Признаки успеха:**
1. Main ответил: "Передаю задачу DevOps агенту"
2. Main упомянул: `childSessionKey: agent:devops:subagent:...`
3. Через 2-3 минуты пришел результат
4. Файл создан: `ls -la /home/axis/openclaw/reports/test-spawn.md`

**Проверка в логах:**
```bash
tail -50 /tmp/gateway.log | grep -i "subagent\|spawn"
```

Должно быть что-то про "subagent отработал".

---

## 📐 АРХИТЕКТУРА SPAWN

```
┌─────────────────────────────────────────┐
│         Руслан (Собственник)            │
│         Telegram: YOUR_TELEGRAM_ID             │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      @axis_main_bot (COO)               │
│      Модель: GLM-5                      │
│      sessions_spawn(agentId='devops')   │
└──────┬────────┬─────────┬──────────┬────┘
       │        │         │          │
       ▼        ▼         ▼          ▼
   DevOps    Tech      Ops        Sales
   (spawn) (spawn)  (spawn)     (spawn)
     │        │         │          │
     ▼        ▼         ▼          ▼
  Выполнение задачи в отдельной сессии
     │        │         │          │
     └────────┴─────────┴──────────┘
              │
              ▼ (announce back)
          Main агент
              │
              ▼
           Руслан
```

**Ключевые моменты:**
1. Main НЕ выполняет задачи сам
2. Main создаёт subagent сессию через `sessions_spawn`
3. Subagent работает изолированно
4. Результат автоматически возвращается Main (announce)
5. Main пересылает результат пользователю

---

## 🔧 КОМАНДЫ ДЛЯ TROUBLESHOOTING

### Проверить активные subagents
```bash
# Через slash-команду (в Telegram @axis_main_bot)
/subagents list

# Через tool (от DevOps)
subagents(action='list')
```

### Проверить логи spawn
```bash
tail -100 /tmp/gateway.log | grep -i "spawn\|subagent"
```

### Проверить конфиг после перезапуска
```bash
grep -A 15 '"id": "main"' ~/.openclaw/openclaw.json
```

### Перезапустить gateway (правильно)
```bash
# Найти PID
ps aux | grep "openclaw-gateway" | grep -v grep

# Убить процесс
kill <PID>

# Запустить заново
nohup openclaw gateway > /tmp/gateway.log 2>&1 &

# Проверить статус через 3-4 секунды
sleep 4 && openclaw status | head -15
```

---

## 📚 ПОЛЕЗНЫЕ ССЫЛКИ

**Документация OpenClaw:**
- Subagents: `~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/docs/tools/subagents.md`
- Agent-to-agent: `~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/docs/tools/agent-send.md`
- Online: https://docs.openclaw.ai/tools/subagents

**Наши документы:**
- Тест spawn: `/home/axis/openclaw/agents/devops/test-inter-agent-communication.md`
- Отчёт: `/home/axis/openclaw/reports/inter-agent-testing-summary.md`
- Этот файл: `/home/axis/openclaw/agents/devops/migrations/2026-02-19-sessions-spawn-setup.md`

---

## 🎓 УРОКИ ДЛЯ БУДУЩИХ ИНТЕГРАЦИЙ

### ✅ Что работает:
1. **Правильный ключ:** `"subagents": { "allowAgents": ["*"] }` в агенте
2. **GLM-5 для координации:** Бесплатный, без rate limits
3. **OpenAI для embeddings:** Стабильнее Gemini
4. **Жёсткие инструкции в SOUL.md:** Main должен знать что делегировать обязательно
5. **Проверка после каждого изменения:** `grep` конфиг перед перезапуском

### ❌ Что НЕ работает:
1. **Неправильные ключи:** `allowed`, `tools.subagents.enabled`
2. **Claude Opus для main:** Быстро rate limit
3. **Gemini для memorySearch:** Перегружается (503)
4. **Мягкие инструкции:** Main будет делать сам вместо делегирования
5. **Не проверять конфиг:** Он может слететь после перезапуска

### 💡 Best Practices:
1. **Всегда читай документацию:** `docs/tools/subagents.md` — источник истины
2. **Тестируй после каждого изменения:** Не делай 5 изменений разом
3. **Используй бесплатные модели:** GLM-5 для координации, Claude для сложных задач
4. **Документируй всё:** Создавай migration файлы как этот
5. **Проверяй конфиг после перезапуска:** Gateway может нормализовать

---

## 🚀 БЫСТРЫЙ СТАРТ (для новой интеграции)

**Шаг 1: Добавь в конфиг main агента**
```json
"subagents": {
  "allowAgents": ["*"]
}
```

**Шаг 2: Усиль SOUL.md**
Добавь секцию BOUNDARIES с жёсткими правилами делегирования.

**Шаг 3: Перезапусти gateway**
```bash
pkill openclaw-gateway
nohup openclaw gateway > /tmp/gateway.log 2>&1 &
```

**Шаг 4: Проверь конфиг**
```bash
grep -A 13 '"id": "main"' ~/.openclaw/openclaw.json
```

**Шаг 5: Протестируй**
Напиши main боту: "Делегируй DevOps проверку системы"

**Шаг 6: Проверь что сработало**
```bash
tail -50 /tmp/gateway.log | grep subagent
```

---

## 📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ

**Дата тестов:** 2026-02-19 15:45-15:50

| Тест | Статус | Время |
|------|--------|-------|
| Конфигурация spawn | ✅ | 15:40 |
| SOUL.md усилен | ✅ | 15:42 |
| Gateway перезапущен | ✅ | 15:45 |
| Main → DevOps spawn | ✅ | 15:47 |
| Subagent создан | ✅ | 15:47 |
| Задача выполнена | ✅ | 15:48 |
| Отчёт создан | ✅ | 15:48 |
| Результат вернулся | ✅ | 15:48 |

**Первый успешный spawn:**
```
childSessionKey: agent:devops:subagent:87c50ddf-c889-4c93-95d2-878ac3272942
Файл: /home/axis/openclaw/reports/spawn-test-success.md
Время выполнения: ~1 минута
```

---

## ⚠️ ПРЕДУПРЕЖДЕНИЯ

1. **Не используй openclaw configure без нужды** — может сбросить настройки
2. **Проверяй конфиг после каждого перезапуска** — может слететь
3. **Не добавляй кастомные ключи** — используй только из документации
4. **GLM-5 слабее Claude** — для сложных задач может понадобиться Claude
5. **Rate limits реальны** — следи за usage, используй бесплатные модели где можно

---

## 🎉 ИТОГ

**sessions_spawn настроен и работает!**

Теперь main агент может:
- ✅ Делегировать задачи DevOps, Tech, Ops, Sales
- ✅ Получать результаты автоматически
- ✅ Координировать команду без ручной работы
- ✅ Масштабировать через параллельные spawn (до 8 одновременно)

**Следующие шаги:**
1. Протестировать spawn с другими агентами (tech, ops, sales)
2. Настроить orchestrator pattern (main → ops → tech/devops)
3. Добавить мониторинг spawn в dashboard
4. Создать регламент использования spawn

---

*Документ создан: 2026-02-19 15:55 GMT+5*  
*DevOps Agent | sessions_spawn работает!*
