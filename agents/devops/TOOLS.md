# TOOLS.md - DevOps Agent

## 🧠 Memory Infrastructure

### Семантический поиск
```bash
# Поиск по смыслу (замена grep)
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --top 10
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --grep  # fallback
```

### Индексация projects-history (Vector DB)
```bash
# Инкрементальная индексация
python3 /home/axis/openclaw/axis-system/semantic-index.py

# Проверка статуса
python3 /home/axis/openclaw/axis-system/semantic-index.py --check

# Полная перестройка
python3 /home/axis/openclaw/axis-system/semantic-index.py --rebuild
```

### Документация семантического поиска
- `/home/axis/openclaw/axis-system/SEMANTIC-SEARCH-README.md`

### Сжатие памяти агентов
```bash
# Список агентов и размеры
python3 /home/axis/openclaw/axis-system/memory-compact.py --list

# Сжать одного
python3 /home/axis/openclaw/axis-system/memory-compact.py --agent devops

# Сжать всех
python3 /home/axis/openclaw/axis-system/memory-compact.py --all

# Dry run
python3 /home/axis/openclaw/axis-system/memory-compact.py --all --dry
```

### Context Watchdog
```bash
# Проверить контекст
python3 ~/.openclaw/skills/context-watchdog/check_context.py --agent devops

# Принудительный экспорт
python3 ~/.openclaw/skills/context-watchdog/check_context.py --agent devops --force-export
```

### Документация
- `/home/axis/openclaw/axis-system/MEMORY-INFRASTRUCTURE.md`

---

## 🔧 Прочее

Добавляй сюда заметки по инструментам.
