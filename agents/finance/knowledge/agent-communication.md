# Межагентная коммуникация

## Как отправить сообщение другому агенту

**ПРАВИЛЬНО:**
```
sessions_send(agentId: "devops", message: "текст")
sessions_send(agentId: "ops", message: "текст")
```

**НЕПРАВИЛЬНО:**
```
sessions_send(label: "axis_devops_bot", ...)  ❌
sessions_send(label: "devops", ...)  ❌
```

## ID агентов системы AXIS

| Telegram бот | agentId |
|--------------|---------|
| @axis_main_bot | `main` |
| @axis_devops_bot | `devops` |
| @axis_opps_bot | `ops` |
| @axis_qc_bot | `qc` |
| @axis_arch_tech_bot | `tech` |
| @axis_teams_bot | `hr` |
| @axis_finance_bot | `finance` |
| @axis_sales_bot | `sales` |

## Примеры

**Отправить DevOps:**
```
sessions_send(agentId: "devops", message: "Нужна помощь с сервером")
```

**Отправить Ops:**
```
sessions_send(agentId: "ops", message: "Задача выполнена")
```

## Если нужен конкретный sessionKey

Формат: `agent:{agentId}:telegram:direct:{userId}`

Пример для Руслана (YOUR_TELEGRAM_ID):
- DevOps: `agent:devops:telegram:direct:YOUR_TELEGRAM_ID`
- Ops: `agent:ops:telegram:direct:YOUR_TELEGRAM_ID`
