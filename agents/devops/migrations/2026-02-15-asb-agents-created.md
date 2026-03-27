# Миграция: Создание 6 агентов АСБ

**Дата:** 2026-02-15
**Автор:** DevOps Agent
**Статус:** ✅ Успешно

---

## Обзор

Создана система из 6 новых агентов по методологии АСБ (Академия Системного Бизнеса) для достижения 95% автономности компании AXIS.

---

## Созданные агенты

| # | ID | Бот | Модель | Роль |
|---|-----|-----|--------|------|
| 1 | ops | @axis_opps_bot | claude-sonnet-4-5 | Операционный Координатор |
| 2 | qc | @axis_qc_bot | claude-sonnet-4-5 | ОКК Контролёр |
| 3 | tech | @axis_arch_tech_bot | claude-sonnet-4-5 | Внедренец-Системщик |
| 4 | hr | @axis_teams_bot | glm-5 | HR Manager |
| 5 | finance | @axis_finance_bot | claude-sonnet-4-5 | Financial Manager |
| 6 | sales | @axis_sales_bot | claude-opus-4-5 | Sales Manager |

---

## Структура файлов

Для каждого агента создано:
```
/home/axis/openclaw/agents/{agent_id}/
├── SOUL.md      # System prompt
├── AGENTS.md    # Конфигурация агента
├── MEMORY.md    # Долгосрочная память
├── README.md    # Документация
├── knowledge/   # База знаний (пусто)
├── migrations/  # История изменений (пусто)
└── memory/      # Файлы памяти (пусто)
```

---

## Изменения в openclaw.json

### agents.list

Добавлено 6 записей:
```json
{ "id": "ops", "workspace": "/home/axis/openclaw/agents/ops", "model": { "primary": "anthropic/claude-sonnet-4-5" } }
{ "id": "qc", "workspace": "/home/axis/openclaw/agents/qc", "model": { "primary": "anthropic/claude-sonnet-4-5" } }
{ "id": "tech", "workspace": "/home/axis/openclaw/agents/tech", "model": { "primary": "anthropic/claude-sonnet-4-5" } }
{ "id": "hr", "workspace": "/home/axis/openclaw/agents/hr", "model": { "primary": "zai/glm-5" } }
{ "id": "finance", "workspace": "/home/axis/openclaw/agents/finance", "model": { "primary": "anthropic/claude-sonnet-4-5" } }
{ "id": "sales", "workspace": "/home/axis/openclaw/agents/sales", "model": { "primary": "anthropic/claude-opus-4-5" } }
```

### channels.telegram.accounts

Добавлено 6 Telegram ботов:
```json
"ops": { "botToken": "8337613414:AAH...", ... }
"qc": { "botToken": "7827887734:AAG...", ... }
"tech": { "botToken": "8181981026:AAG...", ... }
"hr": { "botToken": "7952950346:AAF...", ... }
"finance": { "botToken": "8382084483:AAE...", ... }
"sales": { "botToken": "8563664913:AAF...", ... }
```

### bindings

Добавлено 6 bindings для маршрутизации:
```json
{ "agentId": "ops", "match": { "channel": "telegram", "accountId": "ops" } }
{ "agentId": "qc", "match": { "channel": "telegram", "accountId": "qc" } }
{ "agentId": "tech", "match": { "channel": "telegram", "accountId": "tech" } }
{ "agentId": "hr", "match": { "channel": "telegram", "accountId": "hr" } }
{ "agentId": "finance", "match": { "channel": "telegram", "accountId": "finance" } }
{ "agentId": "sales", "match": { "channel": "telegram", "accountId": "sales" } }
```

---

## Проверка

```bash
openclaw status
# ✅ Agents: 9
# ✅ Telegram accounts: 8/8
# ✅ Gateway: reachable
```

---

## Backup

`~/.openclaw/openclaw.json.backup-20260215-*`

---

## Итоговая система агентов AXIS

| # | Агент | ID | Telegram | Модель | Статус |
|---|-------|-----|----------|--------|--------|
| 1 | Main/COO | main | @ruzClawdbot | claude-opus-4-6 | ✅ Активен |
| 2 | Team | team | (bindings) | glm-4.7-flash | ✅ Активен |
| 3 | DevOps | devops | @axis_devops_bot | claude-opus-4-5 | ✅ Активен |
| 4 | Ops Coordinator | ops | @axis_opps_bot | claude-sonnet-4-5 | ✅ Создан |
| 5 | QC Officer | qc | @axis_qc_bot | claude-sonnet-4-5 | ✅ Создан |
| 6 | Tech/Внедренец | tech | @axis_arch_tech_bot | claude-sonnet-4-5 | ✅ Создан |
| 7 | HR Manager | hr | @axis_teams_bot | glm-5 | ✅ Создан |
| 8 | Finance | finance | @axis_finance_bot | claude-sonnet-4-5 | ✅ Создан |
| 9 | Sales | sales | @axis_sales_bot | claude-opus-4-5 | ✅ Создан |

**Всего: 9 агентов**

---

## Следующие шаги

1. [ ] Протестировать каждого бота в Telegram
2. [ ] Активировать агентов (первое сообщение)
3. [ ] Настроить MEMORY.md для каждого агента
4. [ ] Добавить в групповой чат команды (по необходимости)
5. [ ] Настроить cross-agent взаимодействие

---

**Время выполнения:** ~30 минут
**Изменений в конфиге:** 18 (6 agents + 6 accounts + 6 bindings)
