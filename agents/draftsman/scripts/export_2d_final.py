#!/usr/bin/env python3
"""
Финальный экспорт 2D-плана (segments → стены).
"""
import requests
import json

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '1619d895969b83cc67ff70e815e7483d'
OUTPUT_FILE = '/mnt/c/bridge/revit_commands.jsonl'

MIN_SEGMENT_LENGTH = 300  # мм
LEVEL_NAME = "Level 1"
WALL_THICKNESS = 200
DEFAULT_HEIGHT = 3000
MAX_OBJECTS = 300  # Первые 300 объектов

def fetch(obj_id):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{obj_id}'
    r = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    return data[0] if isinstance(data, list) else data

print("=== ЭКСПОРТ 2D-ПЛАНА → REVIT ===\n")

root = fetch(ROOT_OBJECT_ID)
layer_ref = root['elements'][0]['referencedId']
layer = fetch(layer_ref)

print(f"Файл: {root['name']}")
print(f"Объектов: {len(layer['elements'])}")
print(f"Загружаем: {MAX_OBJECTS}\n")

walls = []
all_x = []
all_y = []

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
    
    segments = obj.get('segments', [])
    if not segments:
        continue
    
    # Для каждого сегмента полилинии → стена
    for seg in segments:
        start = seg.get('start')
        end = seg.get('end')
        
        if not start or not end:
            continue
        
        # Координаты в метрах → мм
        x1 = start['x'] * 1000
        y1 = start['y'] * 1000
        x2 = end['x'] * 1000
        y2 = end['y'] * 1000
        
        # Длина сегмента
        length = seg.get('length', 0)
        
        if length < MIN_SEGMENT_LENGTH:
            continue
        
        all_x.extend([x1, x2])
        all_y.extend([y1, y2])
        
        # Тип стены (по длине)
        wall_type = "exterior" if length > 3000 else "interior"
        
        walls.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "length": length,
            "type": wall_type
        })

print(f"\nНайдено стеновых сегментов: {len(walls)}\n")

if not walls:
    print("❌ Не найдено стен")
    exit(1)

# Сдвиг к началу координат
offset_x = min(all_x)
offset_y = min(all_y)

print(f"Сдвиг: x={offset_x/1000:.2f}м, y={offset_y/1000:.2f}м\n")

commands = []

for w in walls:
    cmd = {
        "command": "wall",
        "x1_mm": int(w['x1'] - offset_x),
        "y1_mm": int(w['y1'] - offset_y),
        "x2_mm": int(w['x2'] - offset_x),
        "y2_mm": int(w['y2'] - offset_y),
        "thickness_mm": WALL_THICKNESS,
        "height_mm": DEFAULT_HEIGHT,
        "type": w['type'],
        "level": LEVEL_NAME
    }
    commands.append(cmd)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for cmd in commands:
        f.write(json.dumps(cmd, ensure_ascii=False) + '\n')

print(f"Сохранено: {OUTPUT_FILE}")
print(f"Команд: {len(commands)}\n")

print("=== ПЕРВЫЕ 5 КОМАНД ===\n")
for cmd in commands[:5]:
    print(json.dumps(cmd, indent=2, ensure_ascii=False))
    print()

print("✅ Готово к импорту в Revit!")
