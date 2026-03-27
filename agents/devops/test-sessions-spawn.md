# Тест межагентного взаимодействия (sessions_spawn)
**Дата:** 2026-02-19
**Цель:** Проверить что main агент может делегировать задачи другим агентам

## Как работает sessions_spawn

**Синтаксис:**
```javascript
sessions_spawn({
  agentId: 'devops',           // Какому агенту
  task: 'Проверь статус...',   // Что сделать
  label: 'Тест делегирования', // Метка для отслеживания
  runTimeoutSeconds: 120       // Таймаут
})
```

**Возвращает:**
```json
{
  "status": "running",
  "runId": "uuid",
  "childSessionKey": "agent:devops:..."
}
```

## Тест 1: DevOps → Tech (простая задача)

**Команда:**
```bash
# Я (DevOps) делегирую Tech агенту
sessions_spawn(
  agentId='tech',
  task='Напиши короткий регламент: как перезапустить OpenClaw Gateway',
  label='test-tech-регламент',
  runTimeoutSeconds=60
)
```

**Ожидаемый результат:**
- Tech агент получит задачу
- Создаст регламент
- Вернет результат

## Тест 2: Main → DevOps (системная задача)

**Команда (от main агента):**
```bash
sessions_spawn(
  agentId='devops',
  task='Проверь статус всех агентов и создай краткий отчет',
  label='test-devops-статус',
  runTimeoutSeconds=90
)
```

## Тест 3: Main → Ops (координация)

**Команда (от main агента):**
```bash
sessions_spawn(
  agentId='ops',
  task='Составь план утренней планерки на завтра',
  label='test-ops-планерка',
  runTimeoutSeconds=120
)
```

## Как отследить выполнение

**1. Проверить список sub-агентов:**
```bash
subagents(action='list')
```

**2. Проверить сессии:**
```bash
sessions_list(kinds=['direct'], limit=20)
```

**3. Получить результат:**
Sub-агент автоматически отправит результат в исходную сессию (push-based).

## Проверка доставки результата

**Где искать ответ:**
1. В той же сессии где запустили spawn
2. Sub-агент пришлет сообщение напрямую
3. Можно проверить через sessions_history

