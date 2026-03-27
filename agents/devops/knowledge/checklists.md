# ЧЕКЛИСТЫ DEVOPS AGENT

**Knowledge Base:** DevOps Agent  
**Версия:** 1.0  
**Дата:** 2026-02-15

---

## 🎯 НАЗНАЧЕНИЕ

Все чеклисты для DevOps задач в одном месте.

**Используй перед:**
- ЛЮБОЙ технической задачей
- Миграциями
- Добавлением агентов
- Изменением конфигов

---

## ✅ ЧЕКЛИСТ: СОЗДАНИЕ НОВОГО АГЕНТА

**Перед началом:**
- [ ] Определена роль и ответственность агента
- [ ] Выбрана модель (Opus 4.6 / Sonnet 4.5 / GLM-5)
- [ ] Создан backup конфига: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d)`

**Workspace:**
- [ ] Создана структура папок: `/home/axis/openclaw/agents/{id}/`
- [ ] Создан SOUL.md (по шаблону из `knowledge/agent-templates.md`)
- [ ] Создан AGENTS.md
- [ ] Создан MEMORY.md
- [ ] Создан README.md

**Конфигурация:**
- [ ] Добавлен в `openclaw.json` → `agents.list`
- [ ] Указан workspace path
- [ ] Выбрана модель
- [ ] Настроен tools profile
- [ ] Валидация: `openclaw config validate` → ✅

**Telegram (опционально):**
- [ ] Создан бот через @BotFather
- [ ] Скопирован токен
- [ ] Добавлен в `channels.telegram.accounts.{id}`
- [ ] Настроен binding в `bindings[]`
- [ ] Указан `allowFrom` (список user ID)

**Проверка:**
- [ ] Gateway перезапущен: `openclaw gateway stop && openclaw gateway`
- [ ] Агент в списке: `openclaw agents list`
- [ ] Статус OK: `openclaw status`
- [ ] Логи без ошибок: `openclaw logs`
- [ ] Telegram бот отвечает (если есть)
- [ ] Или TUI тест: `openclaw tui --agent {id}`

**Документация:**
- [ ] Создан файл миграции: `migrations/YYYY-MM-DD-created.md`
- [ ] Обновлён CHANGELOG.md
- [ ] Обновлён README.md агента

---

## 📱 ЧЕКЛИСТ: СОЗДАНИЕ TELEGRAM БОТА

**BotFather:**
- [ ] Открыт @BotFather в Telegram
- [ ] Отправлена команда `/newbot`
- [ ] Введено имя: "{Agent Name} Bot"
- [ ] Введен username: `axis_{id}_bot`
- [ ] Скопирован токен полностью

**Конфигурация:**
- [ ] Создан backup: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d)`
- [ ] Добавлен account в `channels.telegram.accounts.{id}`
- [ ] Указан `botToken`
- [ ] Указан `dmPolicy: "pairing"`
- [ ] Добавлен `label: "{Name} Bot"`
- [ ] Настроен `allowFrom` (список ID)
- [ ] Добавлен binding: `{ agentId: "{id}", match: { channel: "telegram", accountId: "{id}" }}`
- [ ] Валидация: `openclaw config validate` → ✅

**Проверка:**
- [ ] Gateway перезапущен
- [ ] В логах: "Telegram account {id} connected"
- [ ] Открыт бот в Telegram
- [ ] Отправлено `/start`
- [ ] Бот ответил
- [ ] Routing работает (сообщения идут на правильного агента)

**Документация:**
- [ ] Задокументирован токен в безопасном месте
- [ ] Обновлена миграция

---

## 🔄 ЧЕКЛИСТ: ИЗМЕНЕНИЕ КОНФИГА

**Перед изменениями:**
- [ ] Создан backup: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)`
- [ ] Прочитана документация по изменяемому разделу
- [ ] Определён уровень согласования (1/2/3)

**Процесс:**
- [ ] Изменения внесены в конфиг
- [ ] JSON синтаксис проверен: `jq . ~/.openclaw/openclaw.json`
- [ ] Валидация: `openclaw config validate` → ✅

**Применение:**
- [ ] Gateway остановлен: `openclaw gateway stop`
- [ ] Gateway запущен: `openclaw gateway`
- [ ] Статус проверен: `openclaw status`
- [ ] Логи без ошибок: `tail -50 ~/.openclaw/logs/openclaw.log`

**Документация:**
- [ ] Создана миграция: `migrations/YYYY-MM-DD-description.md`
- [ ] Обновлён CHANGELOG.md
- [ ] Отчёт отправлен (если Уровень 2+)

**Откат (если нужен):**
- [ ] `cp ~/.openclaw/openclaw.json.backup-* ~/.openclaw/openclaw.json`
- [ ] Gateway перезапущен
- [ ] Проверка статуса

---

## 🗑️ ЧЕКЛИСТ: УДАЛЕНИЕ АГЕНТА

**⚠️ КРИТИЧНО: Требует одобрения Руслана/Main (Уровень 3)**

**Согласование:**
- [ ] Получено одобрение от Руслана
- [ ] Подтверждена причина удаления
- [ ] Определён план миграции данных (если нужен)

**Backup:**
- [ ] Создан FULL backup: `tar -czf devops/backups/agent-{id}-$(date +%Y%m%d).tar.gz /home/axis/openclaw/agents/{id}/`
- [ ] Backup конфига: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d)`
- [ ] Backup Vector DB: `cp ~/.openclaw/memory/{id}.sqlite devops/backups/`
- [ ] Backup sessions: `tar -czf devops/backups/sessions-{id}-$(date +%Y%m%d).tar.gz ~/.openclaw/agents/{id}/sessions/`

**Удаление:**
- [ ] Остановлен Gateway
- [ ] Удалён из `openclaw.json` → `agents.list`
- [ ] Удалён binding (если был Telegram)
- [ ] Удалён Telegram account (если был)
- [ ] Валидация: `openclaw config validate` → ✅
- [ ] Gateway запущен
- [ ] Статус проверен: агента НЕТ в списке

**Архивация:**
- [ ] Workspace перемещён в архив: `mv /home/axis/openclaw/agents/{id} /home/axis/openclaw/agents/.archived/{id}`
- [ ] Vector DB архивирован
- [ ] Sessions архивированы

**Документация:**
- [ ] Создана миграция: `migrations/YYYY-MM-DD-deleted-{id}.md`
- [ ] Указана причина удаления
- [ ] Указано где хранится backup
- [ ] Обновлён CHANGELOG.md
- [ ] Отчёт отправлен Руслану

---

## 💾 ЧЕКЛИСТ: BACKUP

### **Ежедневный Backup:**

- [ ] Конфиг: `cp ~/.openclaw/openclaw.json devops/backups/daily/openclaw-$(date +%Y%m%d).json`
- [ ] Credentials: `cp -r ~/.openclaw/credentials devops/backups/daily/credentials-$(date +%Y%m%d)/`
- [ ] System prompts:
  ```bash
  cp /home/axis/openclaw/SOUL.md devops/backups/daily/main-SOUL-$(date +%Y%m%d).md
  cp /home/axis/openclaw/agents/*/SOUL.md devops/backups/daily/
  ```

### **Еженедельный Backup:**

- [ ] Vector DB: `tar -czf devops/backups/weekly/vector-db-$(date +%Y%m%d).tar.gz ~/.openclaw/memory/*.sqlite`
- [ ] Projects: `tar -czf devops/backups/weekly/projects-$(date +%Y%m%d).tar.gz /home/axis/openclaw/projects/`
- [ ] MEMORY.md: `cp /home/axis/openclaw/MEMORY.md devops/backups/weekly/MEMORY-$(date +%Y%m%d).md`

### **Ежемесячный Backup:**

- [ ] Sessions: `tar -czf devops/backups/monthly/sessions-$(date +%Y%m).tar.gz ~/.openclaw/agents/*/sessions/`
- [ ] Daily logs: `tar -czf devops/backups/monthly/memory-$(date +%Y%m).tar.gz /home/axis/openclaw/memory/`
- [ ] Full system: `tar -czf devops/backups/monthly/full-$(date +%Y%m).tar.gz ~/.openclaw/ /home/axis/openclaw/`

---

## 🔧 ЧЕКЛИСТ: МИГРАЦИЯ ДАННЫХ

**Подготовка:**
- [ ] Создан FULL backup системы
- [ ] Прочитан `runbooks/migrate-data.md`
- [ ] Определён план миграции (что куда)
- [ ] Определён откат план

**Процесс:**
- [ ] Остановлен Gateway
- [ ] Выполнены команды миграции
- [ ] Обновлены пути в конфигах
- [ ] Валидация: `openclaw config validate` → ✅
- [ ] Gateway запущен
- [ ] Проверка: все агенты работают

**Проверка:**
- [ ] Статус OK: `openclaw status`
- [ ] Все агенты в списке: `openclaw agents list`
- [ ] Workspace paths правильные
- [ ] Vector DB доступны
- [ ] Логи без ошибок

**Документация:**
- [ ] Миграция задокументирована: `migrations/YYYY-MM-DD-migration.md`
- [ ] Указаны все изменённые пути
- [ ] Указан backup для отката

---

## 🚨 ЧЕКЛИСТ: TROUBLESHOOTING

**Диагностика:**
- [ ] Проверен статус: `openclaw status`
- [ ] Проверены логи: `tail -100 ~/.openclaw/logs/openclaw.log`
- [ ] Проверен конфиг: `openclaw config validate`
- [ ] Проверены процессы: `ps aux | grep openclaw`

**Базовые проверки:**
- [ ] Gateway запущен и reachable?
- [ ] Агенты в списке: `openclaw agents list`
- [ ] Конфиг валиден?
- [ ] Нет ошибок в логах?
- [ ] Порт 18789 свободен: `lsof -i :18789`

**Откат (если нужен):**
- [ ] Восстановлен конфиг из backup
- [ ] Gateway перезапущен
- [ ] Статус проверен

**Эскалация:**
- [ ] Проблема задокументирована
- [ ] Логи сохранены
- [ ] Отправлен запрос Main/Руслану

---

## 👥 ЧЕКЛИСТ: КЛИЕНТСКОЕ ВНЕДРЕНИЕ

**Pre-Sales:**
- [ ] Техаудит клиента проведён
- [ ] Определён пакет услуг (Basic/Full/Enterprise)
- [ ] Подписан контракт

**Подготовка:**
- [ ] Создана папка клиента: `clients/{client-name}/`
- [ ] Создан документ: `clients/{client-name}/setup.md`
- [ ] Определена архитектура (сколько агентов)

**Установка:**
- [ ] OpenClaw установлен на сервере клиента
- [ ] Конфигурация создана
- [ ] Агенты настроены
- [ ] Telegram боты созданы
- [ ] Интеграции подключены

**Проверка:**
- [ ] Все агенты работают
- [ ] Routing настроен
- [ ] Backup настроен

**Обучение:**
- [ ] Команда клиента обучена
- [ ] Документация передана
- [ ] Runbook создан для клиента

**Post-Launch:**
- [ ] 30 дней поддержки
- [ ] Lessons learned задокументированы
- [ ] Обновлён `clients/lessons-learned.md`

---

**Версия:** 1.0  
**Обновлено:** 2026-02-15  
**Статус:** ✅ Готово к использованию
