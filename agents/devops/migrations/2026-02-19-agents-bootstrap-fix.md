# Починка агентов после openclaw configure
**Дата:** 2026-02-19  
**Проблема:** Main и 6 других агентов перестали работать  
**Причина:** Запуск `openclaw configure` восстановил BOOTSTRAP.md файлы  
**Ответственный:** DevOps Agent  

---

## 🚨 ПРОБЛЕМА

### Симптомы:
- @axis_main_bot не отвечал в Telegram
- 7 из 12 агентов в статусе "bootstrapping"
- Пользователь жаловался что main агент не работает

### Проверка:
```bash
openclaw status
# Agents: 12 · 8 bootstrapping · sessions 46
```

---

## 🔍 ДИАГНОСТИКА

### Шаг 1: Проверка workspace main агента
```bash
ls -la /home/axis/openclaw/ | grep BOOTSTRAP
# -rw-r--r--  1 user user  1465 Jan 26 12:45 BOOTSTRAP.md
```

**Найден BOOTSTRAP.md** — агент в режиме первого запуска!

### Шаг 2: Проверка конфига
```bash
cat ~/.openclaw/openclaw.json | grep -A 5 "wizard"
```

**Результат:**
```json
"wizard": {
  "lastRunAt": "2026-02-19T07:05:44.767Z",
  "lastRunVersion": "2026.2.17",
  "lastRunCommand": "configure"
}
```

**Вывод:** Сегодня утром в 07:05 кто-то запустил `openclaw configure`, который восстановил BOOTSTRAP.md у всех агентов.

### Шаг 3: Поиск всех BOOTSTRAP.md
```bash
find /home/axis/openclaw -name "BOOTSTRAP.md" -type f
```

**Результат:**
```
/home/axis/openclaw/BOOTSTRAP.md          (main)
/home/axis/openclaw/agents/devops/BOOTSTRAP.md
/home/axis/openclaw/agents/ops/BOOTSTRAP.md
/home/axis/openclaw/agents/tech/BOOTSTRAP.md
/home/axis/openclaw/agents/qc/BOOTSTRAP.md
/home/axis/openclaw/agents/hr/BOOTSTRAP.md
/home/axis/openclaw/agents/finance/BOOTSTRAP.md
/home/axis/openclaw/agents/sales/BOOTSTRAP.md
```

**7 агентов в режиме bootstrap!**

---

## ✅ РЕШЕНИЕ

### Шаг 1: Удаление BOOTSTRAP.md у всех агентов
```bash
# Удалить main
rm /home/axis/openclaw/BOOTSTRAP.md

# Удалить у всех остальных
rm -f /home/axis/openclaw/agents/*/BOOTSTRAP.md

# Проверка
find /home/axis/openclaw -name "BOOTSTRAP.md" -type f
# (пусто — все удалены)
```

### Шаг 2: Перезапуск gateway
```bash
# Найти процесс
ps aux | grep "openclaw-gateway" | grep -v grep
# user  88220  ...

# Убить и перезапустить
kill 88220
nohup openclaw gateway > /tmp/gateway.log 2>&1 &
```

### Шаг 3: Проверка результата
```bash
openclaw status
# Agents: 12 · 0 bootstrapping ✅
```

**Все агенты активированы!**

---

## 📊 ДО И ПОСЛЕ

### ДО:
- **Статус:** 12 агентов, 7 в bootstrap
- **Main:** не отвечал
- **DevOps:** не отвечал
- **Ops/QC/Tech/HR/Finance/Sales:** не работали

### ПОСЛЕ:
- **Статус:** 12 агентов, 0 в bootstrap
- **Main:** ✅ работает (@axis_main_bot)
- **DevOps:** ✅ работает (@axis_devops_bot)
- **Все агенты:** ✅ активны

---

## 🛡️ ПРОФИЛАКТИКА НА БУДУЩЕЕ

### 1. Не запускать openclaw configure без нужды
**Почему:** Эта команда:
- Восстанавливает BOOTSTRAP.md
- Сбрасывает агентов в режим первого запуска
- Ломает работающую систему

**Когда можно:**
- Добавление нового канала (Telegram, WhatsApp)
- Смена модели по умолчанию
- Настройка Gateway (loopback → network)

### 2. Backup критичных файлов
```bash
# Создать backup скрипт
cat > /home/axis/openclaw/backup-configs.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d-%H%M%S)
BACKUP_DIR="/home/axis/openclaw/backups/$DATE"
mkdir -p "$BACKUP_DIR"

# Backup конфига
cp ~/.openclaw/openclaw.json "$BACKUP_DIR/"

# Backup SOUL.md всех агентов
cp /home/axis/openclaw/SOUL.md "$BACKUP_DIR/main-SOUL.md"
cp /home/axis/openclaw/agents/*/SOUL.md "$BACKUP_DIR/" 2>/dev/null

echo "✅ Backup создан: $BACKUP_DIR"
EOF

chmod +x /home/axis/openclaw/backup-configs.sh
```

### 3. Мониторинг BOOTSTRAP.md
```bash
# Создать проверку (можно в cron)
cat > /home/axis/openclaw/check-bootstrap.sh << 'EOF'
#!/bin/bash
BOOTSTRAP_FILES=$(find /home/axis/openclaw -name "BOOTSTRAP.md" -type f)

if [ ! -z "$BOOTSTRAP_FILES" ]; then
  echo "⚠️ Найдены BOOTSTRAP.md файлы:"
  echo "$BOOTSTRAP_FILES"
  echo ""
  echo "Агенты могут не работать!"
else
  echo "✅ BOOTSTRAP.md не найдены. Все OK."
fi
EOF

chmod +x /home/axis/openclaw/check-bootstrap.sh
```

### 4. После обновления OpenClaw
```bash
# После npm update openclaw или pnpm update openclaw
openclaw status | grep bootstrapping

# Если есть bootstrapping агенты:
find /home/axis/openclaw -name "BOOTSTRAP.md" -type f -delete
openclaw gateway restart
```

---

## 📝 КОМАНДЫ ДЛЯ БЫСТРОЙ ПОЧИНКИ

Если проблема повторится:

```bash
# 1. Удалить все BOOTSTRAP.md
rm -f /home/axis/openclaw/BOOTSTRAP.md
rm -f /home/axis/openclaw/agents/*/BOOTSTRAP.md

# 2. Перезапустить gateway
pkill openclaw-gateway
nohup openclaw gateway > /tmp/gateway.log 2>&1 &

# 3. Проверить
sleep 3
openclaw status | grep bootstrapping
```

**Ожидаемый результат:** `0 bootstrapping`

---

## 🔗 СВЯЗАННЫЕ ДОКУМЕНТЫ

- `/home/axis/openclaw/agents/devops/MEMORY.md` — память DevOps агента
- `/home/axis/openclaw/SOUL.md` — main агент
- `~/.openclaw/openclaw.json` — главный конфиг

---

## 📞 КОНТАКТЫ

**Если проблема повторилась:**
1. Напиши @axis_devops_bot
2. Отправь вывод `openclaw status`
3. DevOps агент починит за 2 минуты

---

*Документ создан: 2026-02-19 12:58 GMT+5*  
*Автор: DevOps Agent*
