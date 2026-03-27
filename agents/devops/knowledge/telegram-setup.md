# TELEGRAM SETUP: MULTI-ACCOUNT БОТЫ
# Knowledge Base для DevOps Agent  
# Версия: 1.0 | Дата: 2026-02-15

---

## 🎯 QUICK START (TL;DR)

```bash
# 1. @BotFather: /newbot → скопируй TOKEN
# 2. Добавь в openclaw.json:
{
  "channels": {"telegram": {"accounts": {
    "finance": {"botToken": "TOKEN", "allowFrom": [YOUR_TELEGRAM_ID]}
  }}},
  "bindings": [{
    "agentId": "finance",
    "match": {"channel": "telegram", "accountId": "finance"}
  }]
}
# 3. openclaw gateway stop && openclaw gateway
# 4. Тест: @axis_finance_bot → /start
```

---

## 📱 СОЗДАНИЕ БОТА

**@BotFather → `/newbot`:**
- Имя: "Finance Bot"  
- Username: `axis_finance_bot`  
- Скопируй ВЕСЬ токен: `123456:ABC...`

---

## ⚙️ КОНФИГУРАЦИЯ

```json
{
  "channels": {
    "telegram": {
      "accounts": {
        "finance": {
          "botToken": "TOKEN_HERE",
          "dmPolicy": "pairing",
          "allowFrom": [YOUR_TELEGRAM_ID]
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "finance",
      "match": {"channel": "telegram", "accountId": "finance"}
    }
  ]
}
```

**Узнать свой ID:** @userinfobot

---

## ✅ ПРОВЕРКА

```bash
openclaw config validate
openclaw gateway stop && openclaw gateway
openclaw status  # должно быть "Telegram: X accounts"
```

Telegram → @axis_finance_bot → /start → должен ответить

---

## 🚨 TROUBLESHOOTING

**Бот не отвечает:**
- Gateway запущен? `openclaw status`
- Токен правильный? Скопируй заново из @BotFather
- Твой ID в allowFrom? @userinfobot
- Логи: `tail ~/.openclaw/logs/openclaw.log | grep error`

**"Unauthorized":** Неправильный токен  
**"User not allowed":** Твой ID не в allowFrom

---

**Полная версия документа:** См. `knowledge/telegram-setup-FULL.md`

**Версия:** 1.0 | **Дата:** 2026-02-15
