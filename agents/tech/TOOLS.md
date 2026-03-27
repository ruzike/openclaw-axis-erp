# TOOLS.md - Tech Agent

## 🧠 Memory Infrastructure

### Семантический поиск (замена grep)
```bash
# Поиск по смыслу в корпоративной памяти
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --top 10
```

### Проверка контекста
```bash
# Проверить не переполнен ли контекст
python3 ~/.openclaw/skills/context-watchdog/check_context.py --agent tech
```

### Сжатие памяти
```bash
# Посмотреть размеры MEMORY.md
python3 /home/axis/openclaw/axis-system/memory-compact.py --list

# Сжать свою память
python3 /home/axis/openclaw/axis-system/memory-compact.py --agent tech
```

### Документация
- `/home/axis/openclaw/axis-system/MEMORY-INFRASTRUCTURE.md`

---

## 🔧 Прочее

Добавляй сюда заметки по инструментам.
