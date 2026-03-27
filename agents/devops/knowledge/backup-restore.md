# BACKUP & RESTORE
# Knowledge Base для DevOps Agent
# Версия: 1.0 | Дата: 2026-02-15

---

## 🎯 СТРАТЕГИЯ BACKUP

**Критично (ежедневно):**
- `~/.openclaw/openclaw.json`
- `/home/axis/openclaw/SOUL.md` (main)
- `/home/axis/openclaw/agents/*/SOUL.md`
- `~/.openclaw/credentials/`

**Важно (еженедельно):**
- `/home/axis/openclaw/MEMORY.md`
- `~/.openclaw/memory/*.sqlite`
- `/home/axis/openclaw/projects/`

**Можно (ежемесячно):**
- `/home/axis/openclaw/memory/` (daily logs)
- `~/.openclaw/agents/*/sessions/`

---

## 💾 BACKUP КОМАНДЫ

**Ежедневный:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/home/axis/openclaw/devops/backups/daily/$DATE"

mkdir -p "$BACKUP_DIR"

cp ~/.openclaw/openclaw.json "$BACKUP_DIR/"
cp ~/.openclaw/credentials/* "$BACKUP_DIR/credentials/"
cp /home/axis/openclaw/SOUL.md "$BACKUP_DIR/main-SOUL.md"
cp /home/axis/openclaw/agents/*/SOUL.md "$BACKUP_DIR/"

echo "✅ Daily backup: $BACKUP_DIR"
```

**Еженедельный:**
```bash
tar -czf /home/axis/openclaw/devops/backups/weekly/projects-$(date +%Y%m%d).tar.gz /home/axis/openclaw/projects/
tar -czf /home/axis/openclaw/devops/backups/weekly/vector-db-$(date +%Y%m%d).tar.gz ~/.openclaw/memory/*.sqlite
```

---

## 🔄 RESTORE

**Восстановить конфиг:**
```bash
cp /path/to/backup/openclaw.json ~/.openclaw/openclaw.json
openclaw config validate
openclaw gateway stop && openclaw gateway
```

**Восстановить промпт:**
```bash
cp /path/to/backup/main-SOUL.md /home/axis/openclaw/SOUL.md
```

---

## 📋 ЧЕКЛИСТ

**Перед изменениями:**
- [ ] Создал backup конфига
- [ ] Знаю путь к backup
- [ ] Протестировал restore процесс

**После изменений:**
- [ ] Проверил работоспособность
- [ ] Задокументировал изменения
- [ ] Создал новый backup

---

**Версия:** 1.0 | **Дата:** 2026-02-15
