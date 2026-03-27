#!/usr/bin/env python3
"""
Быстрый экспорт 2D-плана (первые 200 объектов).
"""
import requests
import json

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '1619d895969b83cc67ff70e815e7483d'
OUTPUT_FILE = '/mnt/c/bridge/revit_commands.jsonl'

MIN_WALL_LENGTH = 300
LEVEL_NAME = "Level 1"
WALL_THICKNESS = 200
DEFAULT_HEIGHT = 3000
MAX_OBJECTS = 200  # Лимит для теста

def fetch(obj_id):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{obj_id}'
    r = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    return data[0] if isinstance(data, list) else data

print("=== БЫСТРЫЙ ЭКСПОРТ 2D-ПЛАНА ===\n")

root = fetch(ROOT_OBJECT_ID)
layer_ref = root['elements'][0]['referencedId']
layer = fetch(layer_ref)

print(f"Файл: {root['name']}")
print(f"Всего объектов: {len(layer['elements'])}")
print(f"Загружаем первые: {MAX_OBJECTS}\n")

polycurves = []

for i, elem in enumerate(layer['elements'][:MAX_OBJECTS]):
    if i % 50 == 0:
        print(f"  {i}/{MAX_OBJECTS}...")
    
    obj_ref = elem.get('referencedId')
    if not obj_ref:
        continue
    
    obj = fetch(obj_ref)
    obj_type = obj.get('speckle_type', '')
    
    if 'Polycurve' not in obj_type:
        continue
    
    length = obj.get('length', 0)
    
    if length < MIN_WALL_LENGTH:
        continue
    
    polycurves.append({'length': length, 'obj': obj})

print(f"\nНайдено полилиний: {len(polycurves)}\n")

commands = []
all_x = []
all_y = []

for pc in polycurves:
    obj = pc['obj']
    bbox = obj.get('bbox')
    
    if not bbox:
        continue
    
    # bbox может быть объектом с value или массивом
    if isinstance(bbox, dict) and 'value' in bbox:
        vals = bbox['value']
    elif isinstance(bbox, list):
        vals = bbox
    else:
        continue
    
    if len(vals) < 6:
        continue
    
    x1, y1, z1, x2, y2, z2 = vals[:6]
    all_x.extend([x1, x2])
    all_y.extend([y1, y2])
    
    # Определяем тип по длине
    wall_type = "exterior" if pc['length'] > 3000 else "interior"
    
    commands.append({
        "command": "wall",
        "x1_mm": int(x1),
        "y1_mm": int(y1),
        "x2_mm": int(x2),
        "y2_mm": int(y2),
        "thickness_mm": WALL_THICKNESS,
        "height_mm": DEFAULT_HEIGHT,
        "type": wall_type,
        "level": LEVEL_NAME
    })

if not commands:
    print("❌ Не найдено стен с валидными координатами")
    exit(1)

offset_x = min(all_x)
offset_y = min(all_y)

print(f"Стен для экспорта: {len(commands)}")
print(f"Сдвиг: x={offset_x:.0f}, y={offset_y:.0f}\n")

for cmd in commands:
    cmd['x1_mm'] = int(cmd['x1_mm'] - offset_x)
    cmd['y1_mm'] = int(cmd['y1_mm'] - offset_y)
    cmd['x2_mm'] = int(cmd['x2_mm'] - offset_x)
    cmd['y2_mm'] = int(cmd['y2_mm'] - offset_y)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for cmd in commands:
        f.write(json.dumps(cmd, ensure_ascii=False) + '\n')

print(f"Сохранено: {OUTPUT_FILE}")
print(f"Команд: {len(commands)}\n")

print("=== ПЕРВЫЕ 3 КОМАНДЫ ===\n")
for cmd in commands[:3]:
    print(json.dumps(cmd, indent=2, ensure_ascii=False))
    print()

print("✅ Готово к импорту в Revit")
