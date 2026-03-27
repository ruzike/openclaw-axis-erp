#!/usr/bin/env python3
"""
Экспорт 2D-плана AutoCAD (полилинии → стены).
"""
import requests
import json

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '1619d895969b83cc67ff70e815e7483d'
OUTPUT_FILE = '/mnt/c/bridge/revit_commands.jsonl'

MIN_WALL_LENGTH = 300  # мм (игнорируем короткие)
LEVEL_NAME = "Level 1"
WALL_THICKNESS = 200
DEFAULT_HEIGHT = 3000

def fetch(obj_id):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{obj_id}'
    r = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    return data[0] if isinstance(data, list) else data

print("=== ЭКСПОРТ 2D-ПЛАНА → REVIT ===\n")

# Загружаем структуру
root = fetch(ROOT_OBJECT_ID)
layer_ref = root['elements'][0]['referencedId']
layer = fetch(layer_ref)

print(f"Файл: {root['name']}")
print(f"Объектов: {len(layer['elements'])}\n")

# Загружаем все объекты
print("Загружаю объекты...")
polycurves = []
total = len(layer['elements'])

for i, elem in enumerate(layer['elements']):
    if i % 100 == 0:
        print(f"  {i}/{total}...")
    
    obj_ref = elem.get('referencedId')
    if not obj_ref:
        continue
    
    obj = fetch(obj_ref)
    obj_type = obj.get('speckle_type', '')
    
    # Фильтр: только полилинии
    if 'Polycurve' not in obj_type:
        continue
    
    length = obj.get('length', 0)
    
    # Игнорируем короткие (<300мм)
    if length < MIN_WALL_LENGTH:
        continue
    
    # Получаем координаты
    # У Polycurve есть segments (список кривых)
    # Или displayValue (геометрия для визуализации)
    
    # Попробуем извлечь начало/конец
    # Для простоты: берём bbox или segments
    
    polycurves.append({
        'id': obj.get('id'),
        'length': length,
        'obj': obj
    })

print(f"\nНайдено полилиний (длина > 300мм): {len(polycurves)}\n")

# Находим минимальные координаты для сдвига
print("Извлекаю координаты...\n")

commands = []
all_x = []
all_y = []

for pc in polycurves[:50]:  # Пробуем первые 50
    obj = pc['obj']
    
    # Проверяем наличие bbox
    bbox = obj.get('bbox')
    if bbox and 'value' in bbox:
        vals = bbox['value']
        if len(vals) >= 6:
            x1, y1, z1, x2, y2, z2 = vals[:6]
            all_x.extend([x1, x2])
            all_y.extend([y1, y2])
            
            # Создаём стену
            commands.append({
                "command": "wall",
                "x1_mm": int(x1),
                "y1_mm": int(y1),
                "x2_mm": int(x2),
                "y2_mm": int(y2),
                "thickness_mm": WALL_THICKNESS,
                "height_mm": DEFAULT_HEIGHT,
                "type": "interior",
                "level": LEVEL_NAME
            })

if not commands:
    print("❌ Не удалось извлечь координаты из bbox")
    print("Попробуем другой метод...")
    # TODO: парсинг segments
    exit(1)

# Сдвиг координат
offset_x = min(all_x)
offset_y = min(all_y)

print(f"Сдвиг координат:")
print(f"  offset_x: {offset_x:.0f} мм")
print(f"  offset_y: {offset_y:.0f} мм\n")

# Применяем сдвиг
for cmd in commands:
    cmd['x1_mm'] = int(cmd['x1_mm'] - offset_x)
    cmd['y1_mm'] = int(cmd['y1_mm'] - offset_y)
    cmd['x2_mm'] = int(cmd['x2_mm'] - offset_x)
    cmd['y2_mm'] = int(cmd['y2_mm'] - offset_y)

# Сохраняем
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for cmd in commands:
        f.write(json.dumps(cmd, ensure_ascii=False) + '\n')

print(f"Сохранено: {OUTPUT_FILE}")
print(f"Команд: {len(commands)}\n")

# Первые 5
print("=== ПЕРВЫЕ 5 КОМАНД ===\n")
for cmd in commands[:5]:
    print(json.dumps(cmd, indent=2, ensure_ascii=False))
    print()
