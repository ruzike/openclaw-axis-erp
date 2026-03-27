# TOOLS.md - Main Agent

## Memory Infrastructure

### Семантический поиск (вместо grep)
```bash
# Поиск по смыслу в корпоративной памяти
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"

# Больше результатов
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --top 10
```

### Проверка контекста
```bash
# Проверить не переполнен ли контекст
python3 ~/.openclaw/skills/context-watchdog/check_context.py --agent main
```

### Сжатие памяти
```bash
# Посмотреть размеры MEMORY.md всех агентов
python3 /home/axis/openclaw/axis-system/memory-compact.py --list

# Сжать конкретного агента
python3 /home/axis/openclaw/axis-system/memory-compact.py --agent main
```

### Индексация (для DevOps)
```bash
# Переиндексировать базу знаний
python3 /home/axis/openclaw/axis-system/memory-indexer.py
```

---

## Прочее

Добавляй сюда свои заметки по инструментам.
