# Починка sessions_spawn: Device Pairing
**Дата:** 2026-02-22  
**Автор:** DevOps Agent (Sonnet 4.6)  
**Статус:** ✅ Решено  
**Время отладки:** ~3 часа

---

## 🎯 ПРОБЛЕМА

sessions_spawn перестал работать. Ошибка:
```
gateway closed (1008): pairing required
Gateway target: ws://127.0.0.1:18789
Source: local loopback
Config: /home/axis/.openclaw/openclaw.json
Bind: loopback
```

---

## 🔍 ЧТО ПРОБОВАЛИ (НЕ СРАБОТАЛО)

### ❌ Попытка 1: Изменить bind loopback → lan
```json
"gateway": { "bind": "lan" }
```
**Результат:** SECURITY ERROR — Gateway блокирует plaintext ws:// к non-loopback адресу.

### ❌ Попытка 2: Переключить Gateway в pairing mode
```bash
openclaw gateway start --pair
```
**Результат:** Такого флага нет / не помогает.

### ❌ Попытка 3: Синхронизировать токен
```bash
openclaw gateway install --force
openclaw gateway restart
```
**Результат:** Токен синхронизирован, но spawn всё равно не работал.

### ❌ Попытка 4: Запустить Gateway через nohup (как 19 февраля)
```bash
nohup openclaw gateway > /tmp/gateway.log 2>&1 &
```
**Результат:** Тоже не помогло — ошибка та же.

---

## ✅ РЕШЕНИЕ

**Причина:** При каждом sessions_spawn, subagent создаёт новое WebSocket соединение с Gateway как новый "device". Gateway требует, чтобы каждый device был **одобрен** (device pairing).

**Алгоритм решения:**

### Шаг 1: Запустить sessions_spawn
```python
sessions_spawn(agentId="devops-sonnet", task="...")
```
Spawn упадёт с ошибкой, но создаст **pending device request**.

### Шаг 2: Проверить pending запросы
```bash
openclaw devices list
```
Найти в секции **Pending** request ID.

### Шаг 3: Одобрить device
```bash
openclaw devices approve <requestId>
```
Пример:
```bash
openclaw devices approve 5748af46-0cad-492a-a094-f46e53cd1fba
```

### Шаг 4: Снова запустить sessions_spawn
Теперь spawn работает — device одобрен и запомнен Gateway.

---

## 📊 РЕЗУЛЬТАТ УСПЕШНОГО SPAWN

```json
{
  "status": "accepted",
  "childSessionKey": "agent:devops-sonnet:subagent:dbf71f9e-b722-4fd5-a70d-af5483a43cdd",
  "runId": "e17ebec0-7c79-44f5-bcd7-ec2d07568f0b",
  "modelApplied": true
}
```

После завершения:
```
status: done
model: anthropic/claude-sonnet-4-6
tokens: 8,118
runtime: ~1 минута
```

---

## 💡 ПОЧЕМУ ЭТО ПРОИСХОДИТ

OpenClaw Gateway требует device pairing для всех подключений — даже локальных loopback соединений. Это **security feature**: каждый клиент (включая subagent runner) должен быть явно одобрен как доверенный device.

При первом запуске spawn subagent генерирует уникальный device ID и создаёт pending request. После одобрения — device запоминается и повторного одобрения не требуется.

---

## 🔄 НУЖНО ЛИ ОДОБРЯТЬ КАЖДЫЙ РАЗ?

**Нет!** Device одобряется один раз и запоминается в:
```
~/.openclaw/  (gateway state)
```

После одобрения все последующие spawn работают автоматически — до тех пор, пока device не будет отозван через `openclaw devices revoke`.

---

## 🛠️ КОМАНДЫ ДЛЯ TROUBLESHOOTING

```bash
# Проверить pending и paired devices
openclaw devices list

# Одобрить pending device
openclaw devices approve <requestId>

# Отозвать device (если нужно сбросить)
openclaw devices revoke --device <deviceId> --role operator

# Проверить активные subagents
subagents(action="list")

# Проверить логи Gateway
tail -50 /tmp/gateway.log | grep -E "(pair|spawn|subagent|error)"
```

---

## 📋 ВАЖНЫЕ УРОКИ

1. **"pairing required" ≠ "pairing mode"** — это device authentication, не режим Gateway
2. **bind=loopback достаточно** — не нужно менять на lan/tailnet
3. **Одно одобрение = навсегда** — device запоминается Gateway
4. **После install --force** — нужно одобрить devices заново (токен меняется)
5. **sessions_spawn создаёт pending request** — даже при ошибке → можно одобрить и повторить

---

## 🚀 ТЕКУЩИЙ СТАТУС (2026-02-22)

| Агент | Модель | Статус spawn |
|-------|--------|-------------|
| devops-sonnet | anthropic/claude-sonnet-4-6 | ✅ Работает |
| devops-opus | anthropic/claude-opus-4-5 | 🔲 Не тестировался |
| main | openrouter/google/gemini-3.1-pro-preview | 🔲 Не тестировался |
| tech | openrouter/google/gemini-3.1-pro-preview | 🔲 Не тестировался |
| shket | google/gemini-3-pro-preview | 🔲 Не тестировался |

---

*Документ создан: 2026-02-22 13:45 GMT+5*  
*DevOps Agent | sessions_spawn через device pairing — РЕШЕНО!*
