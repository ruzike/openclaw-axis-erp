# TOOLS.md - Инструменты агента Draftsman

## 1. REVIT BRIDGE (pyRevit)

### Путь к командам
```
C:\bridge\revit_commands.jsonl
```

### Формат команд (JSONL)
```jsonl
{"command": "CreateWall", "startX": 0, "startY": 0, "endX": 6000, "endY": 0, "height": 2800, "thickness": 200, "level": "1 этаж"}
{"command": "CreateDoor", "wallId": "wall_1", "locationX": 3000, "width": 900, "height": 2100, "level": "1 этаж"}
```

**Единицы:** миллиметры (мм)

---

## 2. SPECKLE API

### Аутентификация
```bash
# Токен хранится в:
/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt

# Сервер:
https://app.speckle.systems
```

### Проект Ruslan (тестовый)
```
Project ID: 30eb4c8084
Model ID: 3e8863886e
Model Name: new
```

---

## 3. SPECKLE BIM API — CHEAT SHEET

### Список проектов
```bash
python3 ~/.nvm/.../skills/speckle-integration/tools/speckle_list_projects.py
```

### Анализ модели
```bash
python3 ~/.nvm/.../skills/speckle-integration/tools/speckle_analyze.py <project_id> <version_id>
```

### Загрузка модели (Python)
```python
from specklepy.api.client import SpeckleClient
from specklepy.api import operations
from specklepy.transports.server import ServerTransport

# Подключение
TOKEN_PATH = "/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt"
with open(TOKEN_PATH) as f:
    token = f.read().strip()

client = SpeckleClient(host="app.speckle.systems")
client.authenticate_with_token(token)

# Получить модель
transport = ServerTransport(stream_id="30eb4c8084", client=client)
root = operations.receive("d94b7ce4f56389f50fdc27deb5454c35", remote_transport=transport)
```

---

## 4. КОНВЕРТАЦИЯ SketchUp → Revit

### Основной workflow
```
1. SketchUp → Publish to Speckle (архитектор)
2. Draftsman читает через Speckle API
3. Распознаёт: стены (вертикальные плоскости), двери/окна (проёмы), помещения (группы)
4. Генерирует JSONL для Revit
5. pyRevit строит модель
```

### Запуск конвертации
```bash
# Из командной строки
python3 /home/axis/openclaw/agents/draftsman/scripts/sketchup_to_revit.py --project-id 30eb4c8084

# Или через Draftsman (когда Ruslan напишет)
"Конвертируй проект 30eb4c8084 из SketchUp в Revit"
```

### Алгоритм распознавания

**Стены:**
- Вертикальные плоскости (угол > 80°)
- Высота > 2.0 м
- Длина > 0.3 м

**Двери:**
- Прямоугольник в стене
- Размер: 0.7-1.2м × 2.0-2.5м
- Низ на полу (z ≈ 0)

**Окна:**
- Прямоугольник в стене
- Размер: 0.5-2.5м × 0.8-2.0м
- Низ выше пола (z > 0.7м)

**Помещения:**
- Группа элементов
- Содержит пол (горизонтальная плоскость)
- Окружена стенами

---

## 5. ЕДИНИЦЫ ИЗМЕРЕНИЯ

| Источник | Единицы | Конвертация |
|----------|---------|-------------|
| SketchUp | метры (м) | × 1000 = мм |
| Speckle API | метры (м) | × 1000 = мм |
| Revit JSONL | миллиметры (мм) | — |
| Revit UI | метры (м) | ÷ 1000 = м |

```python
def to_revit_mm(meters):
    return int(meters * 1000)
```

---

## 6. БАЗА ЗНАНИЙ (memory/)

### Документация
```
01_BIM_DATA_PATTERNS.md          # Структура данных Revit
02_PYTHON_SDK.md                 # REST API workaround
03_PYTHON_SDK_OFFICIAL.md        # Официальный SDK
04_BIM_DATA_PATTERNS_V3.md       # Speckle v3 API
05_SKETCHUP_TO_REVIT_WORKFLOW.md # Конвертация SketchUp
```

### Поиск в документации
```python
# Используй memory_search() для поиска нужной информации
memory_search("распознавание стен SketchUp")
memory_search("Speckle DataObject v3")
memory_search("JSONL команда CreateDoor")
```

---

## 7. ПРИМЕРЫ ЗАДАЧ

### Задача 1: Анализ Revit модели
```
"Проанализируй модель 30eb4c8084 версии 14c97bc6f1"

→ Запускаешь speckle_analyze.py
→ Отчёт: 72 стены, 13 дверей, 61 окно
```

### Задача 2: Конвертация SketchUp
```
"Конвертируй SketchUp проект 30eb4c8084 в Revit"

→ Запускаешь sketchup_to_revit.py
→ Генерируешь JSONL
→ Отчёт: "Готово. 15 стен, 3 двери, 8 окон. Файл: C:\bridge\revit_commands.jsonl"
```

### Задача 3: Исправление ошибок
```
"Найди ошибки в модели и сгенерируй исправления"

→ Запускаешь анализ
→ Находишь зазоры, двери вне стен
→ Генерируешь исправленный JSONL
```

---

## 8. ОГРАНИЧЕНИЯ (v1)

### Что поддерживается:
- ✅ Прямоугольные стены
- ✅ Стандартные двери/окна
- ✅ Простые помещения
- ✅ Одноуровневые здания

### Что НЕ поддерживается:
- ❌ Криволинейные стены
- ❌ Навесные фасады
- ❌ Сложные крыши
- ❌ Лестницы
- ❌ Многоэтажные здания

---

## 9. КОНТАКТЫ

**Владелец:** Ruslan Khalitov (Telegram ID: YOUR_TELEGRAM_ID)  
**Проект:** AXIS Autonomous System  
**Команда:** Main, Ops, Tech, DevOps, QC, HR, Finance, Sales, Shket, Draftsman

**Моя роль:** Чертежник (BIM Agent) — анализ и конвертация архитектурных моделей


## 🧠 Поиск по базе знаний (Semantic Search)

### Поиск по прошлым проектам и памяти
```bash
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --top 10
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --grep  # fallback без OpenAI
```
База: ChromaDB (381+ документов — прошлые проекты, память агентов).
Используй при получении новых задач для поиска похожих прошлых проектов.

