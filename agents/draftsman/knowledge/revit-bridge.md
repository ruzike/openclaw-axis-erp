# Revit Bridge (pyRevit) — Протокол Интеграции

## 1. Архитектура
Работа идет через файл-очередь JSONL.
**Путь:** `/mnt/c/bridge/revit_commands.jsonl`

## 2. Формат команд (JSON Schema)
Каждая команда — это отдельная строка JSON.

### 2.1. Уровни (Levels)
Создавать ПЕРВЫМИ.
```json
{"command": "level", "name": "Level 1", "elevation_mm": 0}
{"command": "level", "name": "Level 2", "elevation_mm": 3000}
```

### 2.2. Оси (Grids)
Создавать ВТОРЫМИ.
```json
{"command": "grid", "name": "A", "x1_mm": 0, "y1_mm": 0, "x2_mm": 10000, "y2_mm": 0}
```

### 2.3. Стены (Walls)
Обязательно указывать `level` (имя, не ID).
```json
{
  "command": "wall",
  "x1_mm": 0, "y1_mm": 0,
  "x2_mm": 6000, "y2_mm": 0,
  "thickness_mm": 300,
  "height_mm": 3000,
  "type": "exterior",  // или "interior", "partition"
  "level": "Level 1"
}
```

### 2.4. Двери (Doors)
Вставляются в стену, ближайшую к точке (x, y).
```json
{
  "command": "door",
  "x_mm": 3000, "y_mm": 0,
  "width_mm": 900,
  "height_mm": 2100,
  "level": "Level 1",
  "family": ""  // Пока пустое, берет дефолт
}
```

### 2.5. Окна (Windows)
```json
{
  "command": "window",
  "x_mm": 1500, "y_mm": 0,
  "width_mm": 1200,
  "height_mm": 1400,
  "sill_mm": 900,  // Высота подоконника
  "level": "Level 1",
  "family": ""
}
```

## 3. Правила моделирования
1. **Стыковка стен:** Координаты начала новой стены должны точно совпадать с концом предыдущей (замкнутый контур).
2. **Порядок:** Сначала Level -> Grid -> Wall -> Door/Window.
3. **Многоэтажность:** Генерируй стены для каждого уровня отдельно (циклом).
