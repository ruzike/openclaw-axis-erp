# Quick Start: 3ds Max → Revit

## Одной командой

```bash
python3 /home/axis/openclaw/agents/draftsman/scripts/mesh_to_revit_full.py
```

Результат: `revit_commands.jsonl` с командами CreateWall.

---

## Ручной запуск (3 шага)

### 1. Анализ mesh → распознавание стен
```bash
python3 scripts/mesh_to_bim.py
# Выход: temp/mesh_analysis.json (249 стеновых граней)
```

### 2. Группировка граней → логические стены
```bash
python3 scripts/group_walls.py
# Выход: temp/walls_grouped.json (135 стен → 75 валидных)
```

### 3. Экспорт → JSONL для Revit
```bash
python3 scripts/export_to_revit.py
# Выход: temp/revit_commands.jsonl (75 команд)
```

---

## Результат

**Файл:** `temp/revit_commands.jsonl`

**Формат:**
```jsonl
{"command": "CreateWall", "startX": 1187473, "startY": 324065, "endX": 1187473, "endY": 324465, "height": 3000, "thickness": 200, "level": "1 этаж", "wallId": "wall_1"}
```

**Копировать в Windows:**
```cmd
copy temp\revit_commands.jsonl C:\bridge\
```

**Запустить в Revit:** pyRevit → Bridge → Load Commands

---

## Параметры

| Параметр | Значение | Где изменить |
|----------|----------|--------------|
| Мин. высота стены | 2000 мм | `export_to_revit.py:88` |
| Толщина стены | 200 мм | `export_to_revit.py:39` |
| Уровень | "1 этаж" | `export_to_revit.py:49` |
| Порог группировки | 3000 мм | `group_walls.py:124` |

---

## Отладка

**Посмотреть детали одной стены:**
```bash
cat temp/walls_grouped.json | jq '.walls[] | select(.id=="wall_64")'
```

**Статистика высот:**
```bash
cat temp/walls_grouped.json | jq '.walls[].height' | sort -n | uniq -c
```

**Топ-20 стен:**
```bash
cat temp/walls_grouped.json | jq -r '.walls | sort_by(.length) | reverse | .[:20] | .[] | "\(.id): \(.length/1000)м × \(.height/1000)м"'
```
