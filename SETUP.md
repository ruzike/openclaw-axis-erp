# 🚀 AXIS ERP — Полная инструкция по установке

## Что ты получишь
12 AI-агентов в Telegram, которые автоматизируют твой бизнес:
DevOps, HR, Finance, Sales, QC, Tech, Strategy, Coach, Ops и другие.

---

## Требования
- VPS сервер (минимум 2 GB RAM, Ubuntu 22.04+)
- Node.js 18+ (`curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install nodejs`)
- OpenClaw (`npm install -g openclaw`)
- Аккаунт Telegram (для создания ботов)
- API ключи: Anthropic или OpenAI (для языковых моделей)

---

## Шаг 1 — Клонируй репозиторий

```bash
git clone https://github.com/ruzike/openclaw-axis-erp
cd openclaw-axis-erp
```

---

## Шаг 2 — Создай Telegram ботов

Тебе нужно создать **12 ботов** через [@BotFather](https://t.me/BotFather) в Telegram.

Для каждого агента:
1. Напиши `/newbot` в @BotFather
2. Введи имя бота (например: `AXIS DevOps`)
3. Введи username (например: `axis_devops_bot`)
4. Скопируй токен (`123456789:AAF...`)

**Список агентов и рекомендуемые имена:**

| Агент | Имя бота | Username |
|-------|----------|----------|
| main | AXIS Main | `axis_main_bot` |
| devops | AXIS DevOps | `axis_devops_bot` |
| hr | AXIS HR | `axis_hr_bot` |
| finance | AXIS Finance | `axis_finance_bot` |
| sales | AXIS Sales | `axis_sales_bot` |
| ops | AXIS Ops | `axis_ops_bot` |
| qc | AXIS QC | `axis_qc_bot` |
| tech | AXIS Tech | `axis_tech_bot` |
| strategy | AXIS Strategy | `axis_strategy_bot` |
| coach | AXIS Coach | `axis_coach_bot` |
| shket | AXIS Shket | `axis_shket_bot` |
| draftsman | AXIS Draftsman | `axis_draftsman_bot` |

---

## Шаг 3 — Получи API ключи

### Anthropic (рекомендуется)
1. Зайди на [console.anthropic.com](https://console.anthropic.com)
2. API Keys → Create Key
3. Скопируй `sk-ant-api03-...`

### OpenAI (альтернатива)
1. Зайди на [platform.openai.com](https://platform.openai.com)
2. API Keys → Create new key
3. Скопируй `sk-...`

---

## Шаг 4 — Запусти установщик

```bash
chmod +x install.sh
./install.sh
```

Установщик задаст вопросы и сам всё настроит:
- Твой Telegram ID (напиши `/start` боту [@userinfobot](https://t.me/userinfobot))
- Токены всех 12 ботов
- API ключи моделей
- URL твоего сервера

---

## Шаг 5 — Запусти OpenClaw

```bash
openclaw start
```

После запуска напиши `/start` любому из своих ботов в Telegram — агент ответит!

---

## Шаг 6 — Настрой домен (опционально)

Для внешнего доступа и webhook-ов рекомендуем Cloudflare Tunnel:

```bash
# Установить cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Авторизоваться
cloudflared tunnel login

# Создать туннель
cloudflared tunnel create axis-gateway
```

---

## Частые вопросы

**Q: Какой VPS выбрать?**
A: Hetzner CX22 (€4/мес, 2 vCPU, 4 GB RAM) — оптимально для старта.

**Q: Сколько стоит в месяц?**
A: VPS ~€4 + API ключи (зависит от использования, ~$5-20/мес для команды из 5 человек).

**Q: Можно ли добавить своих агентов?**
A: Да! Скопируй папку любого агента, поменяй `SOUL.md` и добавь запись в `openclaw.json`.

**Q: Где хранятся данные?**
A: Всё на твоём сервере. Никакого облака, никаких третьих лиц.

---

## Поддержка

- GitHub Issues: [github.com/ruzike/openclaw-axis-erp/issues](https://github.com/ruzike/openclaw-axis-erp/issues)
- OpenClaw Docs: [docs.openclaw.ai](https://docs.openclaw.ai)
