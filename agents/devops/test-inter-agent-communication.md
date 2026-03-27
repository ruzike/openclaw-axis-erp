# Тест межагентного взаимодействия
**Дата:** 2026-02-19  
**Автор:** DevOps Agent  
**Статус:** Готов к тестированию  

---

## 🎯 ЦЕЛЬ

Проверить что main агент может делегировать задачи другим агентам через:
1. `sessions_spawn` (неблокирующий)
2. `sessions_send` (блокирующий)

---

## 🔧 ТЕКУЩАЯ КОНФИГУРАЦИЯ

### Проверка настроек:
```bash
grep -A 10 '"tools":' ~/.openclaw/openclaw.json
```

**Результат:**
```json
"tools": {
  "message": {
    "crossContext": {
      "allowWithinProvider": true,
      "allowAcrossProviders": true
    }
  },
  "agentToAgent": {
    "enabled": true  ✅
  }
}
```

**Subagents:**
```json
"subagents": {
  "maxConcurrent": 8  ✅
}
```

✅ **Межагентное взаимодействие включено!**

---

## 📋 ТЕСТОВЫЕ СЦЕНАРИИ

### Тест 1: Main → DevOps (sessions_spawn)

**Кто тестирует:** Руслан через @axis_main_bot  
**Команда в Telegram:**

```
@axis_main_bot

Делегирую задачу DevOps агенту:

Проверь статус всех 12 агентов и создай краткий отчет:
- Сколько агентов работает
- Сколько в bootstrap
- Статус gateway
- Какие боты активны в Telegram

Сохрани отчет в /home/axis/openclaw/reports/agent-status-report.md
```

**Ожидаемый результат:**
1. Main агент использует `sessions_spawn(agentId='devops', ...)`
2. DevOps агент получит задачу
3. DevOps выполнит проверку
4. DevOps создаст отчет
5. DevOps вернет результат main агенту

**Проверка:**
```bash
# Проверить что отчет создан
ls -la /home/axis/openclaw/reports/agent-status-report.md

# Проверить логи spawn
openclaw logs | grep -i "spawn\|devops"
```

---

### Тест 2: Main → Tech (sessions_spawn)

**Кто тестирует:** Руслан через @axis_main_bot  
**Команда:**

```
@axis_main_bot

Поручи Tech агенту создать регламент:

"Как проверить что все агенты AXIS работают корректно"

Регламент должен включать:
1. Проверку openclaw status
2. Поиск BOOTSTRAP.md файлов
3. Проверку gateway
4. Тест Telegram ботов

Сохрани в /home/axis/openclaw/agents/tech/regulations/check-agents-health.md
```

**Ожидаемый результат:**
- Tech агент создаст регламент
- Файл появится в указанной директории

---

### Тест 3: Main → Ops (sessions_spawn)

**Команда:**

```
@axis_main_bot

Попроси Ops координатора составить план утренней планерки на завтра (20 февраля).

Включи:
- Проверку задач с дедлайном
- Обсуждение блокеров
- Метрики за вчера
- План на день

Формат: markdown, 5-7 пунктов
```

---

### Тест 4: DevOps ↔️ Tech (sessions_send - блокирующий)

**Кто тестирует:** DevOps агент (я)  
**Что проверяем:** Прямое сообщение между агентами

**Команда:**
```bash
# Я отправлю Tech агенту запрос
sessions_send(
  agentId='tech',
  message='Привет Tech! Это тест связи от DevOps. Ответь кратко: ты получил это сообщение?',
  timeoutSeconds=30
)
```

**Ожидаемый результат:**
- Tech получит сообщение
- Ответит в течение 30 секунд
- sessions_send вернет ответ

---

## 🧪 АЛЬТЕРНАТИВНЫЙ СПОСОБ: Проверка через subagents

Если нужно проверить активные задачи:

**1. Запустить задачу:**
```
@axis_main_bot делегируй DevOps проверку системы
```

**2. Проверить список sub-агентов:**
```
@axis_main_bot покажи активные subagents
```

Main агент выполнит:
```javascript
subagents(action='list')
```

**3. Увидеть результат:**
```json
{
  "subagents": [
    {
      "runId": "...",
      "agentId": "devops",
      "label": "проверка системы",
      "status": "running",
      "startedAt": "2026-02-19T..."
    }
  ]
}
```

---

## 📊 МАТРИЦА ДОСТУПОВ

| Агент | sessions_spawn | sessions_send | subagents |
|-------|----------------|---------------|-----------|
| **main** | ✅ (к любым) | ✅ (к любым) | ✅ list/kill |
| **devops** | ❌ (forbidden) | ❓ (надо тестить) | ❓ |
| **ops** | ❓ | ❓ | ❓ |
| **tech** | ❓ | ❓ | ❓ |
| **sales** | ❓ | ❓ | ❓ |

**Вывод:** Main агент — единственный кто может запускать subagents через spawn.

---

## ✅ КАК ВКЛЮЧИТЬ SPAWN ДЛЯ ДРУГИХ АГЕНТОВ

Если нужно разрешить DevOps или Ops делегировать задачи:

**Вариант 1: Через конфиг (рекомендуется для main)**

В `~/.openclaw/openclaw.json` для агента добавить:

```json
{
  "id": "devops",
  "workspace": "/home/axis/openclaw/agents/devops",
  "model": { "primary": "anthropic/claude-sonnet-4-5" },
  "subagents": {
    "allowed": ["tech", "ops", "qc"],  // Кому может делегировать
    "maxConcurrent": 3
  }
}
```

**Вариант 2: Использовать sessions_send**

Вместо spawn использовать прямое сообщение (синхронное):

```javascript
sessions_send(
  agentId='tech',
  message='Создай регламент...',
  timeoutSeconds=120
)
```

Разница:
- `spawn` = fire and forget (неблокирующий)
- `send` = request-response (блокирующий, жду ответ)

---

## 🚀 БЫСТРЫЙ СТАРТ ТЕСТИРОВАНИЯ

**Шаг 1:** Напиши @axis_main_bot в Telegram:

```
Делегируй DevOps проверку всех агентов системы AXIS
```

**Шаг 2:** Main должен ответить:

```
Задача принята.
Ответственный: @axis_devops_bot
Дедлайн: 13:30
ЦКП: Отчет о статусе агентов
```

**Шаг 3:** DevOps выполнит и вернет результат main агенту

**Шаг 4:** Main отправит результат тебе

---

## 📈 ОЖИДАЕМОЕ ПОВЕДЕНИЕ

### Правильная цепочка:
```
Руслан → @axis_main_bot
         ↓ (sessions_spawn)
       @axis_devops_bot выполняет задачу
         ↓ (push результат)
       @axis_main_bot получает ответ
         ↓
       Руслан получает отчет
```

### Неправильно (не должно быть):
```
Руслан → @axis_main_bot
       Main: "Я сам всё проверю" ❌
```

Main должен делегировать, а не выполнять сам!

---

## 🔍 ДЕБАГ

### Если spawn не работает:

**1. Проверить логи:**
```bash
openclaw logs --follow | grep -i "spawn\|subagent"
```

**2. Проверить конфиг:**
```bash
grep -A 10 '"agentToAgent"' ~/.openclaw/openclaw.json
```

**3. Проверить что main использует spawn:**
В ответе main агента должно быть упоминание spawn или делегирования.

**4. Проверить права:**
```bash
# В конфиге main агента должно быть:
"subagents": {
  "maxConcurrent": 8,
  "allowed": "*"  // или список агентов
}
```

---

## 📝 ЧЕКЛИСТ УСПЕШНОГО ТЕСТА

- [ ] Main получил задачу от Руслана
- [ ] Main использовал sessions_spawn (не сделал сам)
- [ ] DevOps получил задачу в отдельной сессии
- [ ] DevOps выполнил задачу
- [ ] DevOps вернул результат main
- [ ] Main переслал результат Руслану
- [ ] Файл отчета создан

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. **Тест main → devops** (базовый)
2. **Тест main → tech** (создание регламента)
3. **Тест main → ops** (координация)
4. **Тест main → sales** (работа с лидами)
5. **Тест цепочки:** main → ops → tech (сложное делегирование)

---

**Готов к тестированию!** 🚀

Просто напиши @axis_main_bot и попроси его делегировать задачу.

---

*Документ создан: 2026-02-19 13:05 GMT+5*  
*DevOps Agent*
