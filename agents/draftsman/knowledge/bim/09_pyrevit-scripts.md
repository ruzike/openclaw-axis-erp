# pyRevit Scripts — Библиотека скриптов агента

> Все скрипты написаны для Revit 2024 + pyRevit.
> Запуск: pyRevit → вкладка в ленте → кнопка скрипта.
> Стандарты именования берутся из `01_naming-standard.md`.
> Имена уровней, листов, шаблонов — из `08_template-structure.md`.

---

## КАК ЗАПУСКАТЬ СКРИПТЫ

```
1. Открыть проект в Revit
2. pyRevit → Tools → Run Script (или через кнопку в панели)
3. Вставить код скрипта
4. Запустить
```

Каждый скрипт начинается с одинакового заголовка — блок инициализации:

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script
doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()
```

---

## СКРИПТ 01 — Создать проект из шаблона

**Назначение:** Открыть новый проект на основе шаблона AXIS.

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script, forms
import os

# Путь к шаблону AXIS — изменить при необходимости
TEMPLATE_PATH = r"C:\AXIS\Templates\AXIS_Interior.rte"

if not os.path.exists(TEMPLATE_PATH):
    forms.alert("Шаблон не найден: " + TEMPLATE_PATH, exitscript=True)

app = revit.HOST_APP.app
doc = app.NewProjectDocument(TEMPLATE_PATH)

output = script.get_output()
output.print_md("✅ Проект создан на основе шаблона AXIS")
```

---

## СКРИПТ 02 — Проверка и отчёт по стадиям стен

**Назначение:** Найти все стены с неправильно заполненными стадиями.
Использовать перед сдачей — пункт чеклиста из `05_qa-checklist.md`.

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

walls = DB.FilteredElementCollector(doc)\
    .OfClass(DB.Wall)\
    .ToElements()

errors = []

for wall in walls:
    try:
        phase_created = wall.get_Parameter(
            DB.BuiltInParameter.PHASE_CREATED
        ).AsValueString()
        
        phase_demolished = wall.get_Parameter(
            DB.BuiltInParameter.PHASE_DEMOLISHED
        ).AsValueString()
        
        name = wall.WallType.Name
        
        # Проверка: у монтажных стен не должно быть стадии сноса
        if phase_created == "Монтаж" and phase_demolished and phase_demolished != "Нет":
            errors.append(f"⚠️ Стена [{name}] — создана в Монтаж, но помечена к сносу: {phase_demolished}")
        
        # Проверка: существующие стены должны быть в стадии "Существующая"
        if "Monolith" in name or "Кирпич" in name or "Блок" in name:
            if phase_created == "Монтаж":
                errors.append(f"⚠️ Несущая стена [{name}] — стадия 'Монтаж' вместо 'Существующая'")

    except Exception as e:
        pass

output.print_md("## Отчёт по стадиям стен")
output.print_md(f"Всего стен: **{len(walls)}**")

if errors:
    output.print_md(f"### ❌ Найдено ошибок: {len(errors)}")
    for e in errors:
        output.print_md(e)
else:
    output.print_md("### ✅ Ошибок стадий не найдено")
```

---

## СКРИПТ 03 — Назначить шаблон вида

**Назначение:** Найти все виды без шаблона (в папке "?") и назначить нужный.

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script, forms

doc = revit.doc
output = script.get_output()

# Все шаблоны видов из 08_template-structure.md
VIEW_TEMPLATE_MAP = {
    "Обмерный план":      "1_Обмерный план",
    "Демонтаж":           "2_Демонтаж",
    "Монтаж 0.1":         "3.1_Монтаж_1этап",
    "Монтаж 0.2":         "3.2_Монтаж_2этап",
    "Мебель":             "4.1_План мебели",
    "Коммуникации":       "5.1_План коммуникаций",
    "Напольные покрытия": "6_План напольных покрытий",
    "Тёплый пол":         "7_План теплого пола",
    "Потолок":            "8.1_План потолка",
    "Освещение":          "8.2_План осветительного оборудования",
    "Розетки":            "10_План розеток",
    "Отделка стен":       "11_План отделки",
}

# Собрать все шаблоны
all_views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
templates = {v.Name: v for v in all_views if v.IsTemplate}

fixed = []
not_found = []

for view in all_views:
    if view.IsTemplate:
        continue
    try:
        if view.ViewTemplateId == DB.ElementId.InvalidElementId:
            view_name = view.Name
            if view_name in VIEW_TEMPLATE_MAP:
                template_name = VIEW_TEMPLATE_MAP[view_name]
                if template_name in templates:
                    with revit.Transaction("Назначить шаблон вида"):
                        view.ViewTemplateId = templates[template_name].Id
                    fixed.append(f"✅ [{view_name}] → {template_name}")
                else:
                    not_found.append(f"❌ Шаблон не найден: {template_name}")
    except:
        pass

output.print_md("## Назначение шаблонов видов")
for msg in fixed:
    output.print_md(msg)
for msg in not_found:
    output.print_md(msg)
output.print_md(f"\n**Исправлено:** {len(fixed)} | **Не найдено:** {len(not_found)}")
```

---

## СКРИПТ 04 — Создать стену по стандарту AXIS

**Назначение:** Создать стену нужного типа с правильными параметрами.
Типы стен из `01_naming-standard.md` и `04_family-catalog.md`.

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script, forms

doc = revit.doc
output = script.get_output()

# Параметры — задаются агентом при вызове
WALL_TYPE_NAME = "Блок 300"       # имя типа стены по стандарту AXIS
PHASE_NAME = "Существующая"       # "Существующая" или "Монтаж"
DEMOLISH_PHASE = None             # None или "Монтаж" (для демонтируемых)

# Найти тип стены
wall_types = DB.FilteredElementCollector(doc)\
    .OfClass(DB.WallType).ToElements()

target_type = None
for wt in wall_types:
    if wt.Name == WALL_TYPE_NAME:
        target_type = wt
        break

if not target_type:
    available = [wt.Name for wt in wall_types]
    forms.alert(
        f"Тип стены '{WALL_TYPE_NAME}' не найден.\n\nДоступные:\n" + "\n".join(available),
        exitscript=True
    )

# Найти фазы
phases = doc.Phases
phase_created = None
phase_demolished = None

for i in range(phases.Size):
    ph = phases.get_Item(i)
    if ph.Name == PHASE_NAME:
        phase_created = ph
    if DEMOLISH_PHASE and ph.Name == DEMOLISH_PHASE:
        phase_demolished = ph

output.print_md(f"## Стена готова к размещению")
output.print_md(f"- Тип: **{WALL_TYPE_NAME}**")
output.print_md(f"- Стадия возведения: **{PHASE_NAME}**")
output.print_md(f"- Стадия сноса: **{DEMOLISH_PHASE or 'Нет'}**")
output.print_md(f"- Уровень снизу: **1 эт (черный пол)**")
output.print_md(f"- Уровень сверху: **2 этаж**")
output.print_md("\n⚠️ Разместите стену вручную на плане, стадии будут применены автоматически.")
```

---

## СКРИПТ 05 — Экспорт PDF всех листов

**Назначение:** Экспортировать все листы проекта в PDF по стандарту студии.
Стандарт из `03_workflow.md` раздел "Экспорт PDF".

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script, forms
import os

doc = revit.doc
output = script.get_output()

# Папка для сохранения — рядом с файлом проекта
project_path = doc.PathName
if not project_path:
    forms.alert("Сохраните проект перед экспортом.", exitscript=True)

export_folder = os.path.join(os.path.dirname(project_path), "PDF")
if not os.path.exists(export_folder):
    os.makedirs(export_folder)

# Настройки печати
pdf_options = DB.PDFExportOptions()
pdf_options.Combine = False                          # Отдельный файл на каждый лист
pdf_options.ZoomType = DB.ZoomType.FitPage          # Вписать в страницу — НЕТ, нам нужен 100%
pdf_options.ZoomType = DB.ZoomType.Zoom             # Сто-процентный масштаб
pdf_options.ZoomPercentage = 100
pdf_options.PaperFormat = DB.ExportPaperFormat.Default
pdf_options.HideScopeBox = True
pdf_options.HideUnreferencedViewTags = True

# Собрать все листы
sheets = DB.FilteredElementCollector(doc)\
    .OfClass(DB.ViewSheet)\
    .ToElements()

sheet_ids = [s.Id for s in sheets if not s.IsPlaceholder]

if not sheet_ids:
    forms.alert("Листы не найдены.", exitscript=True)

# Экспорт
try:
    doc.Export(export_folder, pdf_options, sheet_ids)
    output.print_md(f"## ✅ Экспорт завершён")
    output.print_md(f"Листов: **{len(sheet_ids)}**")
    output.print_md(f"Папка: `{export_folder}`")
except Exception as e:
    output.print_md(f"## ❌ Ошибка экспорта")
    output.print_md(str(e))
```

---

## СКРИПТ 06 — Отчёт по проекту (полный аудит)

**Назначение:** Запустить перед сдачей. Проверяет все пункты `05_qa-checklist.md`.

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

output.print_md("# 📋 Аудит проекта AXIS")
output.print_md("---")

errors = []
warnings = []
ok = []

# 1. Проверка видов без шаблона
all_views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
views_no_template = []
for v in all_views:
    if v.IsTemplate:
        continue
    try:
        if v.ViewTemplateId == DB.ElementId.InvalidElementId:
            if v.ViewType in [
                DB.ViewType.FloorPlan,
                DB.ViewType.CeilingPlan,
                DB.ViewType.Elevation,
                DB.ViewType.Section,
            ]:
                views_no_template.append(v.Name)
    except:
        pass

if views_no_template:
    errors.append(f"❌ Виды без шаблона ({len(views_no_template)}): " + ", ".join(views_no_template[:5]))
else:
    ok.append("✅ Все виды имеют шаблоны")

# 2. Проверка стен — стадии
walls = DB.FilteredElementCollector(doc).OfClass(DB.Wall).ToElements()
walls_no_phase = 0
for wall in walls:
    try:
        phase = wall.get_Parameter(DB.BuiltInParameter.PHASE_CREATED).AsValueString()
        if not phase:
            walls_no_phase += 1
    except:
        pass

if walls_no_phase > 0:
    errors.append(f"❌ Стен без стадии возведения: {walls_no_phase}")
else:
    ok.append(f"✅ Стадии стен заполнены ({len(walls)} стен)")

# 3. Проверка листов
sheets = DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements()
ok.append(f"✅ Листов в проекте: {len([s for s in sheets if not s.IsPlaceholder])}")

# 4. Проверка помещений
rooms = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_Rooms)\
    .ToElements()
unplaced = [r for r in rooms if r.Area == 0]
if unplaced:
    warnings.append(f"⚠️ Помещений без площади (не размещены): {len(unplaced)}")
else:
    ok.append(f"✅ Помещения размещены: {len(rooms)}")

# 5. Семейства не из шаблона AXIS
families = DB.FilteredElementCollector(doc).OfClass(DB.Family).ToElements()
ok.append(f"✅ Загружено семейств: {len(families)}")

# Вывод
output.print_md("## ❌ Ошибки")
for e in errors: output.print_md(e)
if not errors: output.print_md("Ошибок нет")

output.print_md("## ⚠️ Предупреждения")
for w in warnings: output.print_md(w)
if not warnings: output.print_md("Предупреждений нет")

output.print_md("## ✅ Проверено")
for o in ok: output.print_md(o)

output.print_md("---")
output.print_md(f"**Итого:** {len(errors)} ошибок, {len(warnings)} предупреждений")
```

---

## СКРИПТ 07 — Переименовать элементы по стандарту AXIS

**Назначение:** Проверить что типы стен названы по стандарту `01_naming-standard.md`.
Выводит список нестандартных имён для ручного исправления.

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

# Стандартные имена из 01_naming-standard.md
AXIS_WALL_NAMES = [
    "Monolith 300", "Monolith 200", "Monolith 250",
    "Кирпич 250", "Кирпич 120",
    "Блок 300", "Блок 200", "Блок 100",
    "Теплоизоляция балкон", "Звукоизоляция",
    "ГКЛ 75", "НГКЛ 100", "ГКЛ 25",
    "Штукатурка выравнивающая",
]

wall_types = DB.FilteredElementCollector(doc)\
    .OfClass(DB.WallType).ToElements()

non_standard = []
standard = []

for wt in wall_types:
    name = wt.Name
    # Пропускаем системные
    if name.startswith("Basic") or name.startswith("Generic") or name.startswith("Exterior"):
        non_standard.append(f"⚠️ Системное имя: **{name}** → переименовать по стандарту AXIS")
    elif name in AXIS_WALL_NAMES:
        standard.append(f"✅ {name}")
    else:
        # Проверяем формат [Материал Толщина]
        parts = name.split()
        if len(parts) >= 2 and parts[-1].isdigit():
            standard.append(f"✅ {name} (формат OK)")
        else:
            non_standard.append(f"❌ Нестандартное имя: **{name}**")

output.print_md("## Проверка именования стен")
output.print_md(f"Всего типов: {len(wall_types)}")
output.print_md("\n### ❌ Требуют переименования:")
for m in non_standard: output.print_md(m)
output.print_md("\n### ✅ Соответствуют стандарту:")
for m in standard: output.print_md(m)
```

---

## СКРИПТ 08 — Быстрая информация о текущем проекте

**Назначение:** Вывести сводку по проекту — для агента как контекст перед работой.

```python
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

output.print_md("# 📁 Сводка проекта")

# Имя файла
output.print_md(f"**Файл:** `{doc.Title}`")
output.print_md(f"**Путь:** `{doc.PathName}`")

# Уровни
levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
output.print_md(f"\n## Уровни ({len(levels)})")
for l in levels:
    elev = round(l.Elevation * 304.8)
    output.print_md(f"- {l.Name}: {elev} мм")

# Фазы
phases = doc.Phases
output.print_md(f"\n## Стадии ({phases.Size})")
for i in range(phases.Size):
    output.print_md(f"- {phases.get_Item(i).Name}")

# Листы
sheets = DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements()
real_sheets = [s for s in sheets if not s.IsPlaceholder]
output.print_md(f"\n## Листы ({len(real_sheets)})")
for s in sorted(real_sheets, key=lambda x: x.SheetNumber):
    output.print_md(f"- {s.SheetNumber} — {s.Name}")

# Помещения
rooms = DB.FilteredElementCollector(doc)\
    .OfCategory(DB.BuiltInCategory.OST_Rooms)\
    .ToElements()
placed = [r for r in rooms if r.Area > 0]
output.print_md(f"\n## Помещения ({len(placed)} размещено)")
for r in placed:
    area = round(r.Area * 0.0929, 2)  # кв.футы → кв.метры
    output.print_md(f"- {r.Number}. {r.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()}: {area} м²")

# Стены
walls = DB.FilteredElementCollector(doc).OfClass(DB.Wall).ToElements()
output.print_md(f"\n## Стены: {len(walls)} шт.")

output.print_md("\n---\n✅ Сводка готова. Агент может приступать к задаче.")
```

---

## СТРУКТУРА ПАПКИ СКРИПТОВ pyRevit

Сохрани скрипты в папку расширения pyRevit:

```
%APPDATA%\pyRevit\Extensions\AXIS.extension\
└── AXIS.tab\
    └── BIM.panel\
        ├── 01_create_project.pushbutton\
        │   └── script.py
        ├── 02_check_phases.pushbutton\
        │   └── script.py
        ├── 03_assign_templates.pushbutton\
        │   └── script.py
        ├── 04_wall_info.pushbutton\
        │   └── script.py
        ├── 05_export_pdf.pushbutton\
        │   └── script.py
        ├── 06_full_audit.pushbutton\
        │   └── script.py
        ├── 07_check_naming.pushbutton\
        │   └── script.py
        └── 08_project_summary.pushbutton\
            └── script.py
```

После создания структуры — нажать **Обновить** в панели pyRevit.

---

## КАК АГЕНТ ИСПОЛЬЗУЕТ СКРИПТЫ

Когда агент получает задачу — он выбирает нужный скрипт:

| Задача от пользователя | Скрипт агента |
|---|---|
| "Проверь проект перед сдачей" | Скрипт 06 — полный аудит |
| "Создай стену Блок 300 существующую" | Скрипт 04 |
| "Экспортируй все листы в PDF" | Скрипт 05 |
| "Назначь шаблоны видов" | Скрипт 03 |
| "Покажи что есть в проекте" | Скрипт 08 |
| "Проверь стадии стен" | Скрипт 02 |
| "Проверь именование стен" | Скрипт 07 |
