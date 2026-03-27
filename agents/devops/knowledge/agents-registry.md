# Реестр агентов AXIS
_Обновлено: 2026-03-26_
_Источник: /home/axis/.openclaw/openclaw.json + agents/*/SOUL.md_

---

## Агенты системы

| ID | Роль | Статус | Telegram Bot | Модель (primary → fallback) | Workspace |
|----|------|--------|-------------|----------------------------|-----------|
| `main` | Исполнительный Директор (COO) / Главный Агент | 🟢 active | @axis_main_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` → `zai/glm-4.7` | `/home/axis/openclaw` |
| `devops` | IT-Архитектор / DevOps | 🟢 active | @axis_devops_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/devops` |
| `opps` | Операционный Контролёр (OPS) | 🟢 active | @axis_opps_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/opps` |
| `qc` | ОКК Контролёр (Quality Control Officer) | 🟢 active | @axis_qc_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/qc` |
| `tech` | Технолог и Внедренец | 🟢 active | @axis_arch_tech_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` → `zai/glm-4.7` | `/home/axis/openclaw/agents/tech` |
| `hr` | HR Manager | 🟢 active | @axis_teams_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/hr` |
| `finance` | Financial Manager (CFO) | 🟢 active | @axis_finance_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/finance` |
| `shket` | СММ-специалист | 🟢 active | @axis_shket_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` → `zai/glm-4.7` | `/home/axis/openclaw/agents/shket` |
| `draftsman` | Чертежник / BIM-специалист | 🟢 active | @axis_draftsman_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/draftsman` |
| `strategy` | Стратегический агент | 🟢 active | @axis_strategy_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/strategy` |
| `coach` | Insight Coach | 🟢 active | @axis_coach_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/coach` |
| `mobile` | Mobile Developer | 🟢 active | @axis_devmobile_bot | `anthropic/claude-sonnet-4-6` → `google/gemini-3.1-pro-preview` | `/home/axis/openclaw/agents/mobile` |

---

## Агенты без Telegram-бота (legacy/директории)

| ID | Путь | Статус |
|----|------|--------|
| `ops_RENAMED_BACKUP` | `/home/axis/openclaw/agents/ops_RENAMED_BACKUP` | 🔴 archived |

---

## Примечания

- Все агенты используют общую модель `anthropic/claude-sonnet-4-6` как primary
- Fallback цепочка: Google Gemini → ZAI GLM (для main, tech, shket)
- `default` account в telegram без токена — служебный
- Реестр обновляется вручную при добавлении/удалении агентов
- Источник токенов: `/home/axis/.openclaw/openclaw.json` → `channels.telegram.accounts`
