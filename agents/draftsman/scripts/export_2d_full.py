#!/usr/bin/env python3
"""
Полный экспорт 2D-плана (все 1065 объектов).
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

def fetch(obj_id):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{obj_id}'
    r = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    return data[0] if isinstance(data, list) else data

print("=== ПОЛНЫЙ ЭКСПОРТ 2D-ПЛАНА → REVIT ===\n")

root = fetch(ROOT_OBJECT_ID)
layer_ref = root['elements'][0]['referencedId']
layer = fetch(layer_ref)

total = len(layer['elements'])

print(f"Файл: {root['name']}")
print(f"Объектов: {total}")
print(f"Загружаем ВСЕ объекты (займёт ~5-10 мин)...\n")

walls = []
all_x = []
all_y = []

for i, elem in enumerate(layer['elements']):
    if i % 100 == 0:
        print(f"  Загружено: {i}/{total} ({int(i/total*100)}%)...")
    
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
    
    # Каждый сегмент полилинии → стена
    for seg in segments:
        start = seg.get('start')
        end = seg.get('end')
        
        if not start or not end:
            continue
        
        # Координаты: метры → мм
        x1 = start['x'] * 1000
        y1 = start['y'] * 1000
        x2 = end['x'] * 1000
        y2 = end['y'] * 1000
        
        length = seg.get('length', 0)
        
        if length < MIN_SEGMENT_LENGTH:
            continue
        
        all_x.extend([x1, x2])
        all_y.extend([y1, y2])
        
        # Тип стены
        wall_type = "exterior" if length > 3000 else "interior"
        
        walls.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "length": length,
            "type": wall_type
        })

print(f"\n✅ Загрузка завершена!\n")
print(f"Найдено стеновых сегментов: {len(walls)}\n")

if not walls:
    print("❌ Не найдено стен")
    exit(1)

# Сдвиг к началу
offset_x = min(all_x)
offset_y = min(all_y)

print(f"Сдвиг координат:")
print(f"  x: {offset_x/1000:.2f} м")
print(f"  y: {offset_y/1000:.2f} м\n")

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

# Сохраняем
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for cmd in commands:
        f.write(json.dumps(cmd, ensure_ascii=False) + '\n')

print(f"Сохранено: {OUTPUT_FILE}")
print(f"Команд: {len(commands)}\n")

# Статистика
exterior = [c for c in commands if c['type'] == 'exterior']
interior = [c for c in commands if c['type'] == 'interior']

print("=== СТАТИСТИКА ===")
print(f"Всего стен: {len(commands)}")
print(f"  Exterior (длина > 3м): {len(exterior)}")
print(f"  Interior (длина ≤ 3м): {len(interior)}")
print()

print("=== ПЕРВЫЕ 5 КОМАНД ===\n")
for cmd in commands[:5]:
    print(json.dumps(cmd, indent=2, ensure_ascii=False))
    print()

print("🎯 Готово к импорту в Revit!")
print(f"Файл: C:\\bridge\\revit_commands.jsonl")
