# TROUBLESHOOTING
# Knowledge Base для DevOps Agent
# Версия: 1.0 | Дата: 2026-02-15

---

## 🚨 ЧАСТЫЕ ПРОБЛЕМЫ

### Gateway не запускается

**Диагностика:**
```bash
openclaw doctor
openclaw logs --follow
lsof -i :18789  # Порт занят?
```

**Решение:**
- Убить процесс: `pkill -9 -f "openclaw gateway"`
- Проверить конфиг: `openclaw config validate`
- Перезапустить: `openclaw gateway`

---

### Агент не отвечает

**Проверки:**
1. Gateway reachable? `openclaw status`
2. Агент exists? `openclaw agents list`
3. Routing правильный? `cat ~/.openclaw/openclaw.json | jq '.bindings'`
4. Логи: `tail -100 ~/.openclaw/logs/openclaw.log | grep -i error`

---

### Конфиг невалиден

```bash
# Детали ошибки
openclaw config validate 2>&1

# Проверить JSON синтаксис
jq . ~/.openclaw/openclaw.json

# Откатить
cp ~/.openclaw/openclaw.json.backup-* ~/.openclaw/openclaw.json
```

---

### Telegram бот не отвечает

**Проверки:**
1. Токен правильный? Скопируй заново из @BotFather
2. Твой ID в allowFrom? @userinfobot
3. Gateway видит бота? `tail ~/.openclaw/logs/openclaw.log | grep "Telegram.*connected"`
4. Binding настроен? `cat ~/.openclaw/openclaw.json | jq '.bindings'`

---

## 📋 ДИАГНОСТИЧЕСКИЙ ЧЕКЛИСТ

- [ ] `openclaw status` → Gateway reachable?
- [ ] `openclaw agents list` → Все агенты active?
- [ ] `openclaw config validate` → Конфиг valid?
- [ ] `tail -100 ~/.openclaw/logs/openclaw.log` → Нет errors?
- [ ] `lsof -i :18789` → Порт свободен/занят правильно?

---

**Версия:** 1.0 | **Дата:** 2026-02-15
